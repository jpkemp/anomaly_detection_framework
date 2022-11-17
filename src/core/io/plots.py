'''functions for creating and saving plot figures'''
import pickle
from datetime import datetime
from statistics import mean
import numpy as np
import matplotlib
from matplotlib import pyplot as plt
matplotlib.use('Agg')
class PlotUtils:
    '''functions for creating and saving plot figures'''
    def __init__(self, logger):
        self.logger = logger

    def basic_histogram(self, data, filename, n_bins="unique_values", title=None, xlabel="Count", ylabel="Frequency"):
        '''creates and saves a histogram'''
        self.logger.log("Plotting histogram")
        path = self.logger.get_file_path(filename)
        if n_bins == "unique_values":
            n_bins = len(set(data))

        fig = plt.figure()
        ax = fig.add_subplot(111)
        ax.hist(data, n_bins, edgecolor='black', linewidth=1.2)
        ax.set_xlabel(xlabel)
        ax.set_ylabel(ylabel)
        if title is not None:
            ttl = fig.suptitle(title)

        self.save_plt_fig(fig, path)

    def categorical_plot_group(self, x, y, legend_labels, title, filename, axis_labels=None):
        '''creates a categorical plot'''
        self.logger.log(f"Plotting bar chart: {title}")
        fig = plt.figure()
        ax = fig.add_subplot(111)
        assert len(x) == len(y)
        for i, _ in enumerate(y):
            ax.scatter([str(q) for q in x[i]], y[i], label=legend_labels[i])

        lgd = ax.legend(loc='center left', bbox_to_anchor=(1, 0.5))
        ttl = fig.suptitle(title)
        if axis_labels is not None:
            ax.set_xlabel(axis_labels[0])
            ax.set_ylabel(axis_labels[1])

        self.save_plt_fig(fig, filename, (lgd, ttl, ))

    def create_boxplot(self, data, title, filename, axis_labels=None, ext="png"):
        '''creates and saves a single boxplot'''
        self.logger.log(f"Plotting boxplot: {title}")
        fig = plt.figure()
        ax = fig.add_subplot(111)
        ax.boxplot(data)
        fig.suptitle(title)
        tight = False
        if axis_labels is not None:
            ax.set_xlabel(axis_labels[0])
            ax.set_ylabel(axis_labels[1])
            tight = True

        self.save_plt_fig(fig, filename, tight=tight, ext=ext)

    def create_boxplot_group(self, data, labels, title, filename, axis_labels=None, ext="png"):
        '''creates and saves a group of boxplots'''
        self.logger.log(f"Plotting boxplot group: {title}")
        fig = plt.figure()
        ax = fig.add_subplot(111)
        ax.boxplot(data)
        fig.suptitle(title)
        ax.set_xticklabels(labels, rotation=45, ha='right')
        if axis_labels is not None:
            ax.set_xlabel(axis_labels[0])
            ax.set_ylabel(axis_labels[1])

        self.save_plt_fig(fig, filename, ext=ext, tight=True)

    def create_grouped_barchart(self, data, bar_labels, group_labels, title, filename, axis_labels):
        '''create several bar charts in one graph from a list of lists'''
        bar_width = 0.25
        r = []
        r.append(np.arange(len(data[0])))
        fig = plt.figure()
        ax = fig.add_subplot(111)
        for i, _ in enumerate(data):
            ax.bar(r[-1], data[i], width=bar_width, label=bar_labels[i])
            r.append([x + bar_width for x in r[-1]])

        ax.set_xticks([r + bar_width for r in range(len(group_labels))])
        ax.set_xticklabels(group_labels, rotation=45, ha="right")
        if axis_labels is not None:
            ax.set_xlabel(axis_labels[0])
            ax.set_ylabel(axis_labels[1])

        lgd = ax.legend(loc='center left', bbox_to_anchor=(1, 0.5))
        ttl = fig.suptitle(title)
        self.save_plt_fig(fig, filename, (lgd, ttl, ))

    def create_scatter_plot(self, x, y, labels, title, filename, legend_names=None, axis_labels=None, invert_x=False):
        '''creates and saves a scatter plot'''
        fig = plt.figure()
        ax = fig.add_subplot(111)
        if labels is None:
            scatter = ax.scatter(x, y)
        else:
            scatter = ax.scatter(x, y, c=labels)

        if legend_names is not None:
            handles, _ = scatter.legend_elements(num=None)
            legend = ax.legend(handles,
                            legend_names,
                            loc="upper left",
                            title="Legend",
                            bbox_to_anchor=(1, 0.5))

        if axis_labels is not None:
            ax.set_xlabel(axis_labels[0])
            ax.set_ylabel(axis_labels[1])

        if invert_x:
            ax.invert_xaxis()

        ttl = fig.suptitle(title)
        filename = self.logger.output_path / filename

        if legend_names is None:
            self.save_plt_fig(fig, filename, [ttl])
        else:
            self.save_plt_fig(fig, filename, [ttl, legend])

    def create_scatter_plot_with_colourbar(self, x,
                                           y,
                                           colours,
                                           title,
                                           filename,
                                           axis_labels=None,
                                           marker_size=None,
                                           cmap='cividis',
                                           cbar_label=None,
                                           legend_title='Legend',
                                           invert_x=False):
        fig = plt.figure()
        ax = fig.add_subplot(111)
        if marker_size is None:
            scatter = ax.scatter(x, y, c=colours, cmap=cmap)
        else:
            scatter = ax.scatter(x, y, c=colours, cmap=cmap, s=marker_size)

        if invert_x:
            ax.invert_xaxis()

        if axis_labels is not None:
            ax.set_xlabel(axis_labels[0])
            ax.set_ylabel(axis_labels[1])

        ttl = fig.suptitle(title)

        n_ticks = 5
        tick_vals = list(np.linspace(min(colours), max(colours), n_ticks, endpoint=True))
        cbar = fig.colorbar(scatter, ticks=tick_vals)
        cbar.ax.set_ylabel(cbar_label)
        cbar.ax.set_yticklabels(['{:.2f}'.format(x) for x in tick_vals])

        if marker_size is not None:
            max_size = max(marker_size)
            min_size = min(marker_size)
            sizes = [min_size, (max_size - min_size) / 2, max_size]
            for x in sizes:
                plt.scatter([], [], alpha=1, c='0.8', s=x, label='{:.0f}'.format(x))

            legend = plt.legend(
                            loc="lower center",
                            title=legend_title,
                            # bbox_to_anchor=(1.35, 0.5),
                            ncol=1,
                            fancybox=True,
                            shadow=True)
            obs = [ttl, legend]
        else:
            obs = [ttl]
        filename = self.logger.output_path / filename
        # self.save_plt_fig(fig, filename, obs, ext="png")
        self.save_plt_fig(fig, filename, obs, ext="svg")

    def save_plt_fig(self, fig, filename, bbox_extra_artists=None, ext="png", tight=False):
        '''Save a plot figure to file with timestamp'''
        current = datetime.now().strftime("%Y%m%dT%H%M%S")
        output_path = self.logger.get_file_path(f"{filename}_{current}.{ext}")
        pickle_path = self.logger.get_file_path(f"{output_path}.pkl")
        with open(pickle_path, 'wb') as f:
            pickle.dump(fig, f)

        if bbox_extra_artists is not None and not tight:
            fig.savefig(output_path, bbox_extra_artists=bbox_extra_artists, bbox_inches='tight')
        elif tight:
            fig.savefig(output_path, format=ext, bbox_inches='tight')
        else:
            fig.savefig(output_path, format=ext)

        plt.close(fig)
