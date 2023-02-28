'''functions for quick graphing'''
import os
import random
from copy import deepcopy
import pandas as pd
try:
    import pygraphviz as pgv
    import igraph
except ImportError:
    pass

from rpy2.robjects import pandas2ri
from rpy2.robjects.packages import importr
from tqdm import tqdm

pandas2ri.activate()

class GraphUtils():
    '''Functions for visualising, saving, and manipulating plots and graphs'''
    def __init__(self, logger):
        self.logger = logger

    @classmethod
    def bron_kerbosch(cls, graph):
        '''find maximal cliques in graph'''
        def iterative_bk(P, R, X):
            if not any((P, X)):
                yield R

            try:
                u = random.choice(list(P.union(X)))
                S = P.difference(graph[u])
            # if union of P and X is empty
            except IndexError:
                S = P
            for v in S:
                yield from iterative_bk(P.intersection(graph[v]), R.union([v]), X.intersection(graph[v]))
                P.remove(v)
                X.add(v)

        P = cls.flatten_graph_dict(graph)
        graph = cls.convert_pgv_to_simple(graph)
        X = set()
        R = set()

        return list(iterative_bk(P, X, R))

    @classmethod
    def contract_largest_maximum_cliques(cls, graph):
        '''Contracts cliques of size greater than 2'''
        nodes = cls.flatten_graph_dict(graph)
        maximum_cliques = cls.bron_kerbosch(graph)
        clique_conversion = {}
        for node in nodes:
            max_size = 0
            max_id = None
            for i, clique in enumerate(maximum_cliques):
                if node in clique:
                    size = len(clique)
                    if size > max_size and size > 2:
                        max_size = size
                        max_id = i

            clique_conversion[node] = f"clique_{max_id}"

        converted_graph = {}
        for key in tqdm(graph):
            new_key = clique_conversion.get(key, None)
            if new_key is None:
                new_key = key

            converted_graph[new_key] = set()
            for node in graph[key]:
                new_node = clique_conversion.get(node, None)
                if new_node is None:
                    new_node = node

                converted_graph[new_key].add(new_node)

        converted_graph = cls.convert_simple_to_pgv(converted_graph)

        return converted_graph

    @classmethod
    def collapse_same_connection_bipartite_nodes(cls, graph):
        '''For a bipartite graph with one set of nodes as keys and one set as values,
           collapse the keys which share the same connections'''
        temp = {k: set(v) for k, v in cls.convert_pgv_to_simple(graph).items()}
        new_graph = {}
        attrs = {}
        node_info = {}
        n_keys = 0
        for k, v in temp.items():
            found = False
            for name, test in new_graph.items():
                if not test.symmetric_difference(v):
                    node_info[name]["count"] += 1
                    node_info[name]["providers"].append(k)
                    found = True
                    break

            if not found:
                new_graph[f"gr_{n_keys}"] = v
                attrs[f"gr_{n_keys}"] = {"type": "provider", "shape": "triangle"} # Not generalised here
                node_info[f"gr_{n_keys}"] = {"count": 1, "providers": [k]}
                n_keys += 1

        return cls.convert_simple_to_pgv(new_graph), attrs, node_info

    @classmethod
    def convert_adjacency_matrix_to_graph(cls, a_m, use_values_as_edge_weights=False):
        '''convert a pandas format adjacency matrix to a graph dictionary'''
        items = a_m.columns
        graph = {}
        for ante in items:
            for con in items:
                val = a_m.at[ante, con]
                if val != 0:
                    if use_values_as_edge_weights:
                        attr = {"weight": val}
                    else:
                        attr = None

                    if ante in graph:
                        graph[ante][con] = attr
                    else:
                        graph[ante] = {con: attr}

        return graph

    @classmethod
    def convert_graph_to_adjacency_matrix(cls, graph):
        '''convert a graph dictionary to an adjacency matrix in pandas format'''
        items = cls.flatten_graph_dict(graph)
        a_m = pd.DataFrame(0, index=items, columns=items)
        for ante in graph.keys():
            for con in graph[ante].keys():
                a_m.at[ante, con] += 1

        return a_m

    @classmethod
    def convert_pgv_to_simple(cls, graph):
        '''convert a pygraphviz format dictionary to a simpler format'''
        ng = {}
        for k, v in graph.items():
            ng[k] = set(v.keys())

        return ng

    @classmethod
    def convert_simple_to_pgv(cls, graph):
        '''convert a simple graph dictionary to pygraphviz format'''
        ng = {}
        for k, v in graph.items():
            ng[k] = {x: {} for x in v}

        return ng

    @classmethod
    def create_feature_matrix_from_graph(cls, graph):
        '''create a graph feature matrix in pandas format from a graph dictionary'''
        idx = cls.flatten_graph_dict(graph)
        mat = pd.DataFrame(0, index=idx, columns=idx)
        for item in idx:
            mat.at[item, item] = 1

        return mat

    def create_rchord(self, graph, name, title):
        '''create and save a chord diagram from a graph dictionary'''
        from_nodes = []
        to_nodes = []
        values = []
        for key, val in graph.items():
            for k in val.keys():
                from_nodes.append(key)
                to_nodes.append(k)
                values.append(10)

        edges = pd.DataFrame([from_nodes, to_nodes, values])
        edges = edges.transpose()
        edges.columns = ['from', 'to', 'value']

        aplot = importr('graphics')
        circlize = importr('circlize')
        rDevices = importr('grDevices')
        r_am = pandas2ri.conversion.py2rpy(edges)
        filename = self.logger.output_path / f'{name}.png'
        rDevices.png(str(filename), width=800, height=800) # pylint: disable=no-member
        circlize.chordDiagram(r_am, # pylint: disable=no-member
                              directional=1,
                              direction_type="arrows",
                              link_arr_type="big.arrow")
        aplot.title(title, cex=0.8) # pylint: disable=no-member
        rDevices.dev_off() # pylint: disable=no-member


    def create_visnetwork(self, graph, name, title, attrs=None, save_image=True):
        '''Create and save a visnetwork graph from a graph dictionary'''
        if attrs:
            nodes = pd.DataFrame(attrs)
            nodes = nodes.transpose()
            nodes['id'] = nodes.index
            nodes['label'] = nodes.index
            nodes['groupname'] = nodes['color']
        else:
            nodes = pd.DataFrame(self.flatten_graph_dict(graph), columns=['id'])
            nodes['label'] = nodes['id']

        from_nodes = []
        to_nodes = []
        colors = []
        for key, val in graph.items():
            for k in val.keys():
                from_nodes.append(key)
                to_nodes.append(k)
                color = graph[key][k].get('color', 'black')
                colors.append(color)

        edges = pd.DataFrame([from_nodes, to_nodes, colors])
        edges = edges.transpose()
        edges.columns = ['from', 'to', 'color']

        vn = importr('visNetwork')
        r_nodes = pandas2ri.conversion.py2rpy(nodes)
        r_edges = pandas2ri.conversion.py2rpy(edges)

        net = vn.visNetwork(r_nodes, r_edges, main=title, width="100%", improvedLayout=False) # pylint: disable=no-member
        net = vn.visEdges(net, arrows='to') # pylint: disable=no-member
        net = vn.visNodes(net, shape='circle', widthConstraint=50) # pylint: disable=no-member
        # net = vn.visLegend(net)

        vispath = self.logger.output_path / f"{name}"
        vishtml = f"{vispath}.html"
        vn.visSave(net, vishtml) # pylint: disable=no-member
        if save_image:
            ws = importr('webshot')
            ws.webshot(vishtml, zoom = 1, file = f"{vispath}.png") # pylint: disable=no-member

    @classmethod
    def find_graph_components(cls, graph):
        '''find separate graph components'''
        am = cls.convert_graph_to_adjacency_matrix(graph)
        keys = am.index.tolist()
        ITEMS = am.index.tolist()
        def search_matrix(node, current_component, connected_nodes):
            for item in ITEMS:
                row = am.at[node, item]
                col = am.at[item, node]
                if (row > 0 or col > 0) and item not in current_component:
                    current_component.add(item)
                    connected_nodes.add(item)

        identified = set()
        components = []
        while keys:
            component = set()
            connected_nodes = set()
            node = keys.pop()
            if node in identified:
                continue

            component.add(node)
            while True:
                search_matrix(node, component, connected_nodes)
                if not connected_nodes:
                    break

                node = connected_nodes.pop()

            identified.update(component)
            components.append(component)

        return components

    @classmethod
    def flatten_graph_dict(cls, dictionary):
        ''' Returns a set of all keys and values in a graph dictionary'''
        temp = set()
        for k, v in dictionary.items():
            temp.add(k)
            for key in v.keys():
                temp.add(key)

        return temp

    @classmethod
    def graph_component_finder(cls, graph):
        '''find separate graph components'''
        return cls.find_graph_components(graph)

    @classmethod
    def graph_edit_distance(cls, expected, test, attrs=None, edge_distance_costs=False, split_missing_unexpected=True):
        '''get the graph edit distance between two graphs using MBS item fees if available'''
        if not test: # this is used to ignore providers with no associated claims
            if split_missing_unexpected:
                return (0, 0), {}, {}
            else:
                return 0, {}, {}

        expected = cls.stringify_graph(expected)
        test = cls.stringify_graph(test)

        unexpected_score = 0
        missing_score = 0
        d = {x: {} for x in cls.flatten_graph_dict(test)}
        if attrs is None:
            attrs = {x: {} for x in d}

        possible_nodes = list(x for x in cls.flatten_graph_dict(expected))
        keys = list(d.keys())
        edit_attrs = {}
        edit_history = deepcopy(test)
        for key in keys:
            if key not in possible_nodes:
                if key in attrs:
                    unexpected_score += attrs[key].get('weight', 1) # fee
                else:
                    unexpected_score += 1

                if key in test:
                    edges = test[key]
                    if edge_distance_costs:
                        unexpected_score += sum([test[key][x].get('weight', 1) for x in edges])# confidence

                    for k in edges:
                        edit_history[key][k]['color'] = '#D55E00'

                # edit_attrs[key] = {'shape': 'database'}
                edit_attrs[key] = {'shape': 'house'}
                d.pop(key)
            else:
                edit_attrs[key] = {'shape': 'circle'}

        nodes_to_add = set()
        edges_to_add = {}
        for key in d.keys():
            if key not in expected:
                continue

            possible_edges = set(x for x in expected[key].keys())
            if key in test:
                actual_edges = set(test[key].keys())
            else:
                actual_edges = set()

            missing_edges = possible_edges - actual_edges
            should_have = possible_edges.intersection(actual_edges)
            should_have.update(missing_edges)
            should_not_have = actual_edges - possible_edges
            d[key] = {x: {} for x in should_have}
            missing_nodes = set()
            for node in missing_edges:
                if node not in d:
                    missing_nodes.add(node)

            edges_to_add[key] = missing_edges

            nodes_to_add.update(missing_nodes)
            if edge_distance_costs:
                missing_score += sum([expected[key][x].get('weight', 1) for x in missing_edges])
                unexpected_score += sum([test[key][x].get('weight', 1) for x in should_not_have])# confidence

            for k in should_not_have:
                edit_history[key][k]['color'] = '#D55E00'

        for key in edges_to_add:
            for k in edges_to_add[key]:
                if key not in edit_history:
                    edit_history[key] = {}

                edit_history[key][k] = {'color': '#F0E442'}

        while nodes_to_add:
            ignore_list = []
            node = nodes_to_add.pop()
            if node in attrs:
                missing_score += attrs[node].get('weight', 1) # fee
            else:
                missing_score += 1

            # edit_attrs[node] = {'shape': 'box'}
            edit_attrs[node] = {'shape': 'invhouse'}

            if node not in expected:
                ignore_list.append(node)
                continue


            edges = expected[node]
            if edge_distance_costs:
                missing_score += sum([expected[node][x].get('weight', 1) for x in edges]) # confidence

            d[node] = edges
            edit_history[node] = edges
            for k in edit_history[node]:
                edit_history[node][k]['color'] = '#F0E442'

            for new_node in edges:
                if new_node not in d and new_node not in ignore_list:
                    nodes_to_add.add(new_node)

        if split_missing_unexpected:
            score = (unexpected_score, missing_score)
        else:
            score = unexpected_score + missing_score

        return score, edit_history, edit_attrs

    @classmethod
    def identify_closest_component(cls, components, d):
        '''Identify component a model is closest to'''
        test_items = cls.flatten_graph_dict(d)
        component_score = []
        for component in components:
            joint_items = test_items.intersection(component)
            component_score.append(len(joint_items))

        max_score = max(component_score)
        if max_score == 0:
            return len(components)

        return component_score.index(max_score)

    @classmethod
    def stringify_graph(cls, graph):
        '''Ensures all graph dictionary keys and values are in string format'''
        str_graph = {}
        for key in graph:
            str_graph[str(key)] = {}
            for k in graph[key]:
                str_graph[str(key)][str(k)] = graph[key][k]

        return str_graph

    @classmethod
    def visual_graph(cls,
                     data_dict,
                     output_file,
                     title=None,
                     directed=True,
                     node_attrs=None,
                     graph_style='fdp'):
        '''Create a pygraphviz graph from a graph dictionary'''
        max_len = 0
        full_list = cls.flatten_graph_dict(data_dict)
        for s in full_list:
            if len(s) > max_len:
                max_len = len(s)

        if max_len < 10:
            width = 2
        else:
            width = 2.5

        graph = pgv.AGraph(data=data_dict, directed=directed)
        if title is not None:
            graph.graph_attr['fontsize'] = 30
            graph.graph_attr['label'] = title
            graph.graph_attr['labelloc'] = 't'

        graph.node_attr['style'] = 'filled'
        graph.node_attr['shape'] = 'circle'
        graph.node_attr['fixedsize'] = 'true'
        graph.node_attr['fontsize'] = 25
        graph.node_attr['height'] = width
        graph.node_attr['width'] = width
        graph.node_attr['fontcolor'] = '#000000'
        graph.edge_attr['penwidth'] = 7
        if directed:
            # graph.edge_attr['style'] = 'tapered'
            graph.edge_attr['style'] = 'solid'
        else:
            graph.edge_attr['style'] = 'solid'

        for k, v in data_dict.items():
            for node, d in v.items():
                if d is not None:
                    edge = graph.get_edge(k, node)
                    for att, val in d.items():
                        edge.attr[att] = val # pylint: disable=no-member

        if node_attrs is not None:
            for k, v in node_attrs.items():
                node = graph.get_node(k)
                for attr, val in v.items():
                    node.attr[attr] = val


        graph.draw(str(output_file), prog=graph_style)

    @classmethod
    def graph_legend(cls, data_dict, output_file, title=None):
        '''Create a legend for a pygraphviz graph'''
        max_len = 0
        full_list = cls.flatten_graph_dict(data_dict)
        for s in full_list:
            if len(s) > max_len:
                max_len = len(s)

        if max_len < 10:
            width = 2
        else:
            width = 5

        graph = pgv.AGraph(data={})
        if title is not None:
            graph.graph_attr['fontsize'] = 15
            graph.graph_attr['label'] = title
            graph.graph_attr['labelloc'] = 't'

        graph.node_attr['style'] = 'filled'
        graph.node_attr['shape'] = 'circle'
        graph.node_attr['fixedsize'] = 'true'
        graph.node_attr['height'] = width
        graph.node_attr['width'] = width
        graph.node_attr['fontcolor'] = '#000000'
        graph.edge_attr['penwidth'] = 7
        graph.edge_attr['style'] = 'invis'

        nbunch = list(data_dict.keys())
        for i, node in enumerate(nbunch):
            graph.add_node(node)
            n = graph.get_node(node)
            n.attr['shape'] = 'rectangle' # pylint: disable=E1101
            n.attr['rank'] = 'max' # pylint: disable=E1101
            n.attr['fontsize'] = 15 # pylint: disable=E1101
            for attr, val in data_dict[node].items():
                n.attr[attr] = val # pylint: disable=E1101

            if i < len(nbunch) - 1:
                graph.add_edge(node, nbunch[i+1])# , style='invis')

        graph.add_subgraph(nbunch=nbunch, name='Legend')
        legend = graph.get_subgraph('Legend')
        legend.rank = 'max'
        legend.label = 'Legend'
        legend.style = 'filled'
        legend.shape = 'rectangle'
        legend.labelloc = 't'
        legend.fontcolor = '#000000'
        legend.color = 'grey'
        legend.pack = True

        graph.draw(str(output_file), prog='dot')
