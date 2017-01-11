#==============================================================================
#
#     CodeGenerator.py
#
#     This file is part of ANNarchy.
#
#     Copyright (C) 2016-2019  Toni Freitag <tfreitag93@gmail.com>,
#     Helge Uelo Dinkelbach <helge.dinkelbach@gmail.com>
#
#     This program is free software: you can redistribute it and/or modify
#     it under the terms of the GNU General Public License as published by
#     the Free Software Foundation, either version 3 of the License, or
#     (at your option) any later version.
#
#     ANNarchy is distributed in the hope that it will be useful,
#     but WITHOUT ANY WARRANTY; without even the implied warranty of
#     MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#     GNU General Public License for more details.
#
#     You should have received a copy of the GNU General Public License
#     along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
#==============================================================================
from PyQt4 import QtGui, QtCore

from matplotlib.backends.backend_qt4agg import FigureCanvasQTAgg as FigureCanvas
import matplotlib.pyplot as plt

import numpy as np

class MatplotlibWidget(QtGui.QWidget):
    """
    Widget to draw matplotlib figures.
    """
    def __init__(self, parent=None):
        """
        Init function. Set layout of widget.
        """
        super(MatplotlibWidget, self).__init__(parent)

        self._figure = plt.figure(facecolor='white')
        self._canvas = FigureCanvas(self._figure)

        self.layoutVertical = QtGui.QVBoxLayout(self)
        self.layoutVertical.addWidget(self._canvas)

class PieChartWidget(MatplotlibWidget):
    """
     Draws a pie chart as Qt-Widget from data
    """
    def __init__(self, parent=None):
        """
        Init function.
        """
        super(PieChartWidget,self).__init__(parent)
    
    @QtCore.pyqtSlot()
    def draw(self, data, title, percentage):
        """
        Draw pie chart from given data.
        
        Signals:
            * drawPieChart(PyQt_PyObject) emited from PieChartTree.current_item_changed()
        """
        labels = []
        values = []
        for i in data:
            labels.append(i[0])
            values.append(float(i[1])*10)
        total = sum(values)
        
        if percentage:
            form = '%1.1f%%'
        else:
            form = lambda(p): '{:.4f}'.format(p * total / 100)
        
        # create an axis
        ax = self._figure.gca()
        ax.clear()

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
        super(ErrorbarChartWidget,self).__init__(parent)
        
    def draw(self, values, std_values):
        """
        Draw errorbar chart from given data.
        
        params:
            * values
            * std_values
        
        Signals:
            * drawErrorbarChart(PyQt_PyObject,PyQt_PyObject) emited from ErrorbarChartTree.current_item_changed()
        """
        x = np.arange(0.0, len(values), 1.0)
        y = values

        ax = self._figure.gca()
        ax.clear()

        ax.errorbar(x, y, yerr=std_values, fmt='-o')
        #ax.set_title('variable, symmetric error')
        ax.set_xlabel("test nr.", fontsize=18)
        ax.set_ylabel("mean value", fontsize=18)
        ax.set_xticks(np.arange(min(x), max(x)+1, 5.0))
        ax.grid(True)

        self._canvas.draw()