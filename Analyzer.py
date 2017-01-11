#==============================================================================
#
#     Analyzer.py
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
#==============================================================================
from PyQt4 import QtGui, QtCore
from DataContainer import DataContainer

try:
    _fromUtf8 = QtCore.QString.fromUtf8
except AttributeError:
    def _fromUtf8(s):
        return s

class Analyzer(QtGui.QTabWidget):
    """
    Main widget. Choose between pie and error chart.
    Hold data from loaded xml-file.
    """
    def __init__(self, parent):
        """
        Init function. Create empty data-container.
        """
        QtGui.QTabWidget.__init__(self, parent)
        self._data_container = DataContainer()
        
    @QtCore.pyqtSlot()
    def load_data(self):
        """
        Open file-dialog and import data into container.
        Set data in all tabs.
        """
        fname = QtGui.QFileDialog.getOpenFileName(self, 'Open data file', '.', '*.xml')

        if fname:
            self.set_data(fname)
            
    def set_data(self, fname):
        self._data_container.load_data(fname)

        self.emit(QtCore.SIGNAL(_fromUtf8("setPieChartTree(PyQt_PyObject)")), self._data_container)
        self.emit(QtCore.SIGNAL(_fromUtf8("setErrorbarChartTree(PyQt_PyObject)")), self._data_container)
        
     
    @QtCore.pyqtSlot()
    def load_pie_chart(self):
        """
        Send data-container to PieChartTree to change Chart.
        """
        self.emit(QtCore.SIGNAL(_fromUtf8("setPieChart(PyQt_PyObject)")), self._data_container)
    
    @QtCore.pyqtSlot()
    def load_errorbar_chart(self):
        """
        Send data-container to ErrorbarChartTree to change Chart.
        """
        self.emit(QtCore.SIGNAL(_fromUtf8("setErrorbarChart(PyQt_PyObject)")), self._data_container)
            
class PieChartTree(QtGui.QTreeWidget):
    """
    Choose a function of a network out of the tests
    """
    def __init__(self, parent):
        """
        Init function.
        """
        QtGui.QTreeView.__init__(self, parent)
    
    @QtCore.pyqtSlot(object)
    def load_data(self, data):
        """
        Save data-container and fill TreeWidget.
        
        Signals
            * setPieChartTree(PyQt_PyObject) emitted from Analyzer.load_data()
        """
        self._data = data
        
        l = []
        for i in xrange(self._data.num_tests()):
            item = QtGui.QTreeWidgetItem(["Measurement " + str(i)])
            item.addChild(QtGui.QTreeWidgetItem(["pop - step"]))
            item.addChild(QtGui.QTreeWidgetItem(["proj - step"]))
            item.addChild(QtGui.QTreeWidgetItem(["proj - psp"]))
            l.append(item)
        
        self.clear()
        self.addTopLevelItems(l)
    
    @QtCore.pyqtSlot(QtGui.QTreeWidgetItem,QtGui.QTreeWidgetItem)    
    def current_item_changed(self, current, previous):
        """
        If selection changed then filter data and draw chart.
            
        Signals:
            * currentItemChanged(QTreeWidgetItem, QTreeWidgetItem) emited from PieChartTree
        """
        topIdx = self.invisibleRootItem().indexOfChild(current)
        if topIdx != -1: # top element? (Network)
            values = self._data.values_by_type(topIdx, "net")
            
            # net-step = overhead + net-proj_step + net-psp + net-neur_step
            overhead = values["step"]["mean"] - (values["proj_step"]["mean"] + values["psp"]["mean"] + values["neur_step"]["mean"])
                
            data = [
                    ["Overhead\n(" + "%.4f" % overhead + ")", "%.4f" % overhead],
                    ["proj_step\n(" + "%.4f" % values["proj_step"]["mean"] + ")", "%.4f" % values["proj_step"]["mean"]],
                    ["psp\n(" + "%.4f" % values["psp"]["mean"] + ")", "%.4f" % values["psp"]["mean"]],
                    ["neur_step\n(" + "%.4f" % values["neur_step"]["mean"] + ")", "%.4f" % values["neur_step"]["mean"]]
                ]
            self.emit(QtCore.SIGNAL(_fromUtf8("drawPieChart(PyQt_PyObject,PyQt_PyObject,PyQt_PyObject)")), data, current.text(0) + " (in ms)", True)
        else:
            childIdx = current.parent().indexOfChild(current)
            topIdx = self.invisibleRootItem().indexOfChild(current.parent())
            if topIdx != -1: # First child of Network?
                
                if childIdx == 0:
                    neur_step = self._data.values_by_function(topIdx, "net", "neur_step")
                    func_data = self._data.values_by_function(topIdx, "pop", "step")

                    overhead = neur_step["mean"]
                    values = []
                    for key,value in func_data.items():

                        overhead -= value["mean"]
                        values.append(["pop" + str(key), "%.4f" % value["mean"]])
                    
                    values.append(["overhead", "%.4f" % overhead])
                    
                if childIdx == 1:
                    proj_step = self._data.values_by_function(topIdx, "net", "proj_step")
                    func_data = self._data.values_by_function(topIdx, "proj", "step")

                    overhead = proj_step["mean"]
                    values = []
                    for key,value in func_data.items():

                        overhead -= value["mean"]
                        values.append(["proj" + str(key), "%.4f" % value["mean"]])
                    
                    values.append(["overhead", "%.4f" % overhead])
                    
                if childIdx == 2:
                    net_psp = self._data.values_by_function(topIdx, "net", "psp")
                    func_data = self._data.values_by_function(topIdx, "proj", "psp")

                    overhead = net_psp["mean"]
                    values = []
                    for key,value in func_data.items():

                        overhead -= value["mean"]
                        values.append(["proj" + str(key), "%.4f" % value["mean"]])
                    
                    values.append(["overhead", "%.4f" % overhead])
                #values = self._data.values_by_function(topIdx, current.text(0))
                
                # calc overhead
                #overhead = values[0][1]
                #for i in xrange(1, len(values)):
                    #overhead -= values[i][1]
                #values[0] = ["overhead", "%.4f" % overhead]
                
                self.emit(QtCore.SIGNAL(_fromUtf8("drawPieChart(PyQt_PyObject,PyQt_PyObject,PyQt_PyObject)")), values, current.text(0) + " (in ms)", False)
            
            
class ErrorbarChartTree(QtGui.QTreeWidget):
    """
    Choose a function out of the tests
    """
    def __init__(self, parent):
        """
        Init function.
        """
        QtGui.QTreeView.__init__(self, parent)
    
    @QtCore.pyqtSlot(object)  
    def load_data(self, data):
        """
        Save data-container and fill TreeWidget.
        
        Signals
            * setErrorbarChartTree(PyQt_PyObject) emited from Analyzer.load_data()
        """
        self._data = data
        names = self._data.unique_function_names()
        l = []
        for name in names:
            l.append(QtGui.QTreeWidgetItem([name]))
        
        self.clear()
        self.addTopLevelItems(l)
        
    @QtCore.pyqtSlot(QtGui.QTreeWidgetItem,QtGui.QTreeWidgetItem)    
    def current_item_changed(self, current, previous):
        """
        If selection changed then filter data and draw chart.
        
        Signals:
            * currentItemChanged(QTreeWidgetItem, QTreeWidgetItem) emited from ErrorbarChartTree
        """
        obj = str(current.text(0)).split(" - ")
        mean_values = self._data.values_each_test(obj[0], obj[1], "mean")
        std_values = self._data.values_each_test(obj[0], obj[1], "std")
        
        self.emit(QtCore.SIGNAL(_fromUtf8("drawErrorbarChart(PyQt_PyObject, PyQt_PyObject)")), mean_values, std_values)