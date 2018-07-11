# ==============================================================================
#
#     Charts.py
#
#     This file is part of ANNarchyProfiler.
#
#     Copyright (C) 2016-2019  Toni Freitag <tfreitag93@gmail.com>,
#     Helge Uelo Dinkelbach <helge.dinkelbach@gmail.com>
#
#     This program is free software: you can redistribute it and/or modify
#     it under the terms of the GNU General Public License as published by
#     the Free Software Foundation, either version 3 of the License, or
#     (at your option) any later version.
#
#     ANNarchyProfiler is distributed in the hope that it will be useful,
#     but WITHOUT ANY WARRANTY; without even the implied warranty of
#     MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#     GNU General Public License for more details.
#
#     You should have received a copy of the GNU General Public License
#     along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
# ==============================================================================
from PyQt4 import QtGui, QtCore

from matplotlib.backends.backend_qt4agg import FigureCanvasQTAgg as FigureCanvas
import matplotlib.pyplot as plt

import numpy as np


class MatplotlibWidget(QtGui.QWidget):
    """
    A Widget to include matplotlib figures in Qt-Applications.
    """
    def __init__(self, parent=None):
        """
        Set layout of widget.

        Arguments:
            * parent -- parent element of this widget -- default = None
        """
        super(MatplotlibWidget, self).__init__(parent)

        self._figure = plt.figure(facecolor='white')
        self._canvas = FigureCanvas(self._figure)

        self._layoutVertical = QtGui.QVBoxLayout(self)
        self._layoutVertical.addWidget(self._canvas)

    def figure(self):
        """
        Return matplotlib-figure of the widget.
        """
        return self._figure
    
    def clear(self):
        """
        Clear the chart.
        """
        # create an axis
        self._figure.clf()
        self._canvas.draw()

class PieChartWidget(MatplotlibWidget):
    """
    A widget to draw a pie chart from given data.
    """
    def __init__(self, parent=None):
        """
        Init function.

        Arguments:
            * parent -- parent element of this widget -- default = None
        """
        super(PieChartWidget, self).__init__(parent)

    @QtCore.pyqtSlot()
    def draw(self, data, title, percentage):
        """
        Draw pie chart from given data.

        Arguments:
            * data (array) -- values to draw
            * title (str) -- text shown over the chart
            * percentage (boolean) -- data shown as percentages?

        Signals:
            * drawPieChart(PyQt_PyObject) emited from PieChartTree.current_item_changed()
        """
        labels = []
        values = []
        for i in data:
            labels.append(i[0])
            values.append(float(i[1]) * 10)
        total = sum(values)

        # set format of output values
        if percentage:
            form = '%1.1f%%'
        else:
            form = lambda p: "{:.4f}".format(p * total / 100)
            
        # create an axis
        ax = self._figure.gca()
        ax.clear()

        # draw chart
        ax.pie(values, labels=labels,
               autopct=form, startangle=90,
               radius=0.25, center=(0, 0), frame=True)

        # set axis limit
        ax.set_axis_off()
        ax.set_xlim((-0.35, 0.35))
        ax.set_ylim((-0.35, 0.35))
        ax.set_title(title)

        # Set aspect ratio to be equal so that pie is drawn as a circle.
        ax.set_aspect('equal')

        # refresh canvas
        self._canvas.draw()

class ErrorbarChartWidget(MatplotlibWidget):
    """
     Draws a errorbar chart as Qt-Widget from data
    """
    def __init__(self, parent=None):
        """
        Init function.

        Arguments:
            * parent -- parent element of this widget -- default = None
        """
        super(ErrorbarChartWidget, self).__init__(parent)

    def draw(self, values, std_values=0, labels=[], xlabel="test nr.", ylabel="mean_value (in ms)",
             yscale="linear"):
        """
        Draw errorbar chart from given data.

        Arguments:
            * values (array) -- data values to draw
            * std_values (array) -- values of the errorbar
            * label (array) -- values to identify each graph
            * xlabel (text) -- text shown at x-axis
            * ylabel (text) -- text shown at y-axis
            * yscale (text) -- type of y-axis scale (linear/log)

        Signals:
            * drawErrorbarChart(PyQt_PyObject,PyQt_PyObject) emited from
                ErrorbarChartTree.current_item_changed()
        """

        # create an axis
        ax = self._figure.gca()
        ax.clear()

        # draw errorbar chart
        for i in range(len(values)):
            lbl = ''
            if len(labels) != 0:
                lbl = labels[i]

            x = np.arange(0.0, len(values[i]), 1.0)
            y = values[i]

            if std_values == 0:
                ax.errorbar(x, y, fmt='-o', label=lbl)
            else:
                ax.errorbar(x, y, yerr=std_values[i], fmt='-o', label=lbl)

        # add options to the chart
        # ax.set_title('variable, symmetric error')
        ax.set_xlabel(xlabel, fontsize=18)
        ax.set_ylabel(ylabel, fontsize=18)
        ax.set_yscale(yscale)
        ax.set_xticks(np.arange(min(x), max(x) + 1, np.ceil(len(values[0]) / 20.0)))
        ax.grid(True)
        if len(labels) != 0:
            ax.legend()

        # show graph
        self._canvas.draw()
        
class BarChartWidget(MatplotlibWidget):
    """
     Draws a errorbar chart as Qt-Widget from data
    """
    def __init__(self, parent=None):
        """
        Init function.

        Arguments:
            * parent -- parent element of this widget -- default = None
        """
        super(BarChartWidget, self).__init__(parent)

    def draw(self, data, title, percentage):
        """
        Draw pie chart from given data.

        Arguments:
            * data (array) -- values to draw
            * title (str) -- text shown over the chart
            * percentage (boolean) -- data shown as percentages?

        Signals:
            * drawPieChart(PyQt_PyObject) emited from PieChartTree.current_item_changed()
        """
        # create an axis
        ax = self._figure.gca()
        ax.clear()

        print("x")

        # show graph
        self._canvas.draw()