'''Test cases for GraphUtils'''
import unittest
from dataclasses import dataclass
from src.core.algorithms.graphs.graph_utils import GraphUtils
from src.core.mbs_info.mbs_labeller import ComponentLabeller
from tests.mock_logger import MockLogger

class GraphUtilsTest(unittest.TestCase):
    '''Test cases for GraphUtils'''
    def setUp(self):
        self.graphs = GraphUtils(MockLogger())

    def test_graph_conversion(self):
        '''Confirm graph and adjacency matrices are correctly converted'''
        model = {
            1: {2: {}},
            3: {4: {}},
            4: {5: {}, 6: {}, 1: {}},
            5: {4: {}},
            6: {1: {}},
            7: {6: {}}
        }

        am = self.graphs.convert_graph_to_adjacency_matrix(model)
        assert am.at[1, 2] == 1
        assert am.loc[1].sum() == 1
        assert am[1].sum() == 2

        graph = self.graphs.convert_adjacency_matrix_to_graph(am)
        assert len(model.keys()) == len(graph.keys())
        for ante in model:
            for con in model[ante].keys():
                assert graph[ante][con] is None

    def test_component_finder(self):
        '''Confirm separate components are correctly found'''
        model = {
            1: {2: {}},
            3: {4: {}},
            4: {5: {}},
            5: {3: {}}
        }

        components = self.graphs.graph_component_finder(model)
        self.assertNotEqual(len(components[0]), len(components[1]))
        for component in components:
            if len(component) == 2:
                self.assertTrue(1 in component)
                self.assertTrue(2 in component)
            elif len(component) == 3:
                self.assertTrue(3 in component)
                self.assertTrue(4 in component)
                self.assertTrue(5 in component)
            else:
                self.fail()

    def test_closest_component(self):
        '''test component finder returns the correct component ids'''
        model = {
            1: {2: {}},
            3: {4: {}},
            4: {5: {}, 6: {}},
            5: {4: {}},
            7: {6: {}}
        }

        tests = [
            ({1: {}}, 0),
            ({1: {}, 2: {}, 3:{}}, 0),
            ({5: {}}, 1),
            ({4: {}, 7: {}, 8: {}}, 1),
            ({8: {}, 9: {}}, 2)
        ]

        components = self.graphs.graph_component_finder(model)
        def test_expected_component(expected, component):
            if expected == 0:
                self.assertTrue(len(components[component]) == 2)
            elif expected == 1:
                self.assertTrue(len(components[component]) == 5)
            elif expected == 2:
                self.assertTrue(component == 2)
            else:
                self.fail()

        for test_graph, expected in tests:
            closest_component = self.graphs.identify_closest_component(components, test_graph)
            test_expected_component(expected, closest_component)

    def test_graph_edit_distance(self):
        '''Confirm graph edit distance scoring is correct'''
        model = {
            1: {2: {}},
            3: {4: {}},
            4: {5: {}, 6: {}, 1: {}},
            5: {4: {}},
            6: {1: {}},
            7: {6: {}}
        }
        tests = [
            ({2: {}}, 0, 0),
            ({3: {}}, 0, 12),
            ({3: {7: {}}}, 1, 13),
            ({7: {3: {}}}, 1, 13),
            ({7: {}, 3: {}}, 0, 13),
            ({7: {3: {}}, 8: {7: {}}}, 3, 13),
            ({7: {3: {}}, 4: {7: {}}}, 2, 12),
            ({1: {}, 2: {}}, 0, 1)
        ]
        for test, plus_val, minus_val in tests:
            (plus_ged, minus_ged), _, _ = self.graphs.graph_edit_distance(model, test, edge_distance_costs=True)
            assert plus_ged == plus_val
            assert minus_ged == minus_val

    def test_bipartite_collapse(self):
        initial = {
            "A": {1: {}, 2: {}, 3: {}},
            "B": {3: {}, 4: {}, 5: {}},
            "C": {1: {}, 2: {}, 3: {}}
        }

        graph, attrs, node_info = self.graphs.collapse_same_connection_bipartite_nodes(initial)
        assert len(graph) == 2
        assert len(node_info) == 2
        assert "A" in node_info['gr_0']["providers"]
        assert "B" not in node_info['gr_0']["providers"]
        assert "C" in node_info['gr_0']["providers"]
        assert "A" not in node_info['gr_1']["providers"]
        assert "B" in node_info['gr_1']["providers"]
        assert "C" not in node_info['gr_1']["providers"]
        simple = self.graphs.convert_pgv_to_simple(graph)
        assert not set(simple['gr_0']).symmetric_difference({1, 2, 3})
        assert not set(simple['gr_1']).symmetric_difference({3, 4, 5})

class ComponentLabellerTest(unittest.TestCase):
    '''Test cases for provider labelling'''
    def test_label(self):
        '''test labelling'''
        model = {
            1: {2: {}},
            3: {4: {}},
            4: {5: {}, 6: {}},
            5: {4: {}},
            8: {9: {}, 10: {}}
        }
        tests = [
            ({1: {}, 2: {}}, "B", 1),
            ({4: {}, 5: {}, 8: {}}, "A", 0),
            ({1: {}, 2: {}, 4: {}}, "B", 1),
            ({1: {}, 4: {}, 5: {}}, "A", 0),
            ({7: {}, 8: {}, 9: {}}, "C", 2),
            ({11: {}, 12: {}}, None, 3)
        ]
        labels = [
            (4, "A"),
            (1, "B")
        ]
        labeller = ComponentLabeller(model, labels, "C")

        @dataclass
        class ProviderInfo:
            '''mock provider info class'''
            closest_component: int = -1
            provider_label: str = "FAIL"
            model_graph: dict = None

        def test_expected_component(expected, provider_info, labeller):
            if expected == 0:
                self.assertTrue(len(labeller.components[provider_info.closest_component]) == 4)
            elif expected == 1:
                self.assertTrue(len(labeller.components[provider_info.closest_component]) == 2)
            elif expected == 2:
                self.assertTrue(len(labeller.components[provider_info.closest_component]) == 3)
            elif expected == 3:
                self.assertTrue(11 in provider_info.model_graph)
            else:
                self.fail()

        for graph, expected, val in tests:
            provider_info = ProviderInfo()
            provider_info.model_graph = graph
            labeller.label_provider(provider_info)
            self.assertEqual(provider_info.provider_label, expected)
            test_expected_component(val, provider_info, labeller)
