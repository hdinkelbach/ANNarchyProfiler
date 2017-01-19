#==============================================================================
#
#     ProfilerWindow.py
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

from PyQt4.QtCore import pyqtSlot, Qt, SIGNAL
from PyQt4.QtGui import QFileDialog, QMainWindow, QMessageBox, QTreeWidgetItem
from PyQt4.uic import loadUi

from DataContainer import DataContainer
from RunDialog import RunDialog

class ProfilerWindow(QMainWindow):
    """
    MainWindow of the application. Define all actions and hold the data for display.
    """
    def __init__(self):
        """
        Init the class variables, load the window and add actions to the menubar.
        """
        super(self.__class__, self).__init__()
        self.ui = loadUi("ProfilerWindow.ui")
        
        # actions menubar
        self.ui.btnLoadData.activated.connect(self.load_data_dialog)
        self.ui.btnRunMeasurement.activated.connect(self.load_run_dialog)
        self.ui.btnSave.activated.connect(self.save_chart)
        
        # action combobox
        self.ui.cmbThread.currentIndexChanged.connect(self.change_cmb_thread)
        self.ui.cmbScale.currentIndexChanged.connect(self.change_std_state)
        
        # action TreeWidgets
        self.ui.PieChartTree.currentItemChanged.connect(self.change_piechart_tree)
        self.ui.ErrorbarChartTree.currentItemChanged.connect(self.change_errorbarchart_tree)
        self.ui.FunctionSelectTree.itemSelectionChanged.connect(self.change_multithread_selection)
        self.ui.ThreadSelectTree.itemChanged.connect(self.change_multithread_selection)
        
        # action checkbox
        self.ui.chkStdValues.stateChanged.connect(self.change_std_state)
        
        # action button
        self.ui.btnRawData.clicked.connect(self.load_raw_data)
        
        # set class variables 
        self._data = {}
    
    def show(self):
        self.ui.show()
        
    def add_data(self, data):
        """
        Add a DataContainer instance to measurement-data.
        Ask for overwriting if a measurement with same number of threads exists.
        """
        if self._data.has_key(data.num_threads()):
            msg = QMessageBox()
            msg.setText("Data from the same number of threads is set. Want to overwrite?")
            msg.setIcon(QMessageBox.Warning)
            msg.setStandardButtons(QMessageBox.No | QMessageBox.Yes)
            msg.setDefaultButton(QMessageBox.Yes)
            if msg.exec_() != QMessageBox.Yes:
                return
        
        self._data[data.num_threads()] = data
        self.update_cmb_thread()
        self.update_function_select()
        self.update_thread_select()
        
    def current_data(self):
        if self.ui.cmbThread.itemData(self.ui.cmbThread.currentIndex()).toInt()[0] == 0: return False
        return self._data[self.ui.cmbThread.itemData(self.ui.cmbThread.currentIndex()).toInt()[0]]
        
    
    #==============================================================================
    # actions for the buttons in the menubar
    #==============================================================================
    
    @pyqtSlot()    
    def load_data_dialog(self):
        """
        Open file-dialog to choose multiple files. Add data to container and set it in application.
        
        Signals:
            * activated() emitted from btnLoadData in menubar
        """
        fnames = QFileDialog.getOpenFileNames(self, 'Open data file', '.', '*.xml')

        for fname in fnames:
            data = DataContainer()
            data.load_data(fname)
            self.add_data(data)
        
    @pyqtSlot()
    def load_run_dialog(self):
        """
        Shows a dialog to enter data for a ANNarchy profile run.
        Measurement data will be load into the application.
        
        Signals:
            * activated() emitted from btnRunMeasurement in menubar
        """
        diag = RunDialog()
        script, path, args = diag.get_data()
        
        if(script != ""):
            os.system("cd " + str(path))
            os.system("python " + str(script) + " --profile --profile_out=" + str(path) + "/measurement.xml " + str(args))
            
            data = DataContainer()
            data.load_data(str(path) + "/measurement.xml")
            self.add_data(data)
    
    @pyqtSlot()
    def save_chart(self):
        """
        Saves the current shown chart as a file.
        
        Signals:
            * activated() emitted from btnSave in menubar
        """
        
        # tab "Standardabweichung" selected
        if self.ui.AnalyzerWidget.currentIndex() == 0:
            figure = self.ui.ErrorbarChart.figure()
            
        # tab "Torte" selected
        elif self.ui.AnalyzerWidget.currentIndex() == 1:
            figure = self.ui.PieChart.figure()
        
        # tab "Multi-Thread" selected
        elif self.ui.AnalyzerWidget.currentIndex() == 2:
            figure = self.ui.MultiThreadChart.figure()
        
        # tab "Speedup" selected
        elif self.ui.AnalyzerWidget.currentIndex() == 3:
            figure = self.ui.SpeedupChart.figure()
                
        if figure != 0:
            fname = QFileDialog.getSaveFileName(self, 'Save chart file', './chart.png', 'Image file (*.png *.jpg);;PDF file (*.pdf)')
            if fname:
                figure.savefig(str(fname))
    
    #==============================================================================
    # actions for the show std values
    #==============================================================================
    
    @pyqtSlot()
    def change_std_state(self):
        """
        Update ErrorbarChart and MultiThread Chart if state of std state checkbox changed
        
        Signals:
            * stateChanged(int) emitted from chkStdState
            * currentIndexChanged(int) emitted from cmbScale
        """
        if len(self.ui.ErrorbarChartTree.selectedItems()) != 0:
            self.change_errorbarchart_tree(self.ui.ErrorbarChartTree.selectedItems()[0])
            
        self.change_multithread_selection()

    
    #==============================================================================
    # actions for the combobox for choosing test-data
    #==============================================================================
    
    @pyqtSlot()
    def change_cmb_thread(self):
        """
        Update TreeViews if combobox changed.
        
        Signals:
            * currentIndexChanged(int) emitted from cmbThread
        """
        if self.ui.cmbThread.itemData(self.ui.cmbThread.currentIndex()).toInt()[1]:
            self.update_piechart_tree()
            self.update_errorbarchart_tree()
    
    def update_cmb_thread(self):
        """
        Update the items of the combobox from test data
        """
        self.ui.cmbThread.clear()
        for key in self._data:
            self.ui.cmbThread.addItem(str(key) + " Threads ", key)
    
    
    #==============================================================================
    # actions for the MultiThreadTab
    #==============================================================================
    
    def change_multithread_selection(self):
        """
        Change the errorbar chart in the multi thread tab and speedup tab if some selection changed.
        
        Signals:
            * itemSelectionChanged() emitted from FunctionSelectTree
            * itemChanged() emitted from ThreadSelectionTree
        """
        current = self.ui.FunctionSelectTree.selectedItems()
        
        if len(current) == 0:
            return
        
        root = self.ui.ThreadSelectTree.invisibleRootItem()
        idx = []
        for i in range(root.childCount()):
            if root.child(i).checkState(0) == Qt.Checked:
                idx.append(self.ui.cmbThread.itemData(i).toInt()[0])
        
        if len(idx) == 0:
            return
        
        mean_values = []
        std_values = []
        labels = []
        
        obj = str(current[0].text(0)).split(" - ")
        for i in idx:
            mean_values.append(self._data[i].values_each_test(obj[0], obj[1], "mean"))
            std_values.append(self._data[i].values_each_test(obj[0], obj[1], "std"))
            labels.append(str(i) + " Threads")
        
        if self.ui.chkStdValues.isChecked():
            self.ui.MultiThreadChart.draw(mean_values, std_values, labels, yscale=str(self.ui.cmbScale.currentText()))
        else:
            self.ui.MultiThreadChart.draw(mean_values, labels=labels, yscale=str(self.ui.cmbScale.currentText()))
        
        # if no data with 1 thread than exit
        if self._data.has_key(1) == False:
            return
        
        mean_values = []
        mean_value = []
        labels = []
        mean_one_thread = self._data[1].values_each_test(obj[0], obj[1], "mean")
        
        for i in idx:
            if i != 1:
                mean_value = self._data[i].values_each_test(obj[0], obj[1], "mean")
                for n in range(len(mean_value)):
                    mean_value[n] = mean_one_thread[n] / mean_value[n]
                    
                mean_values.append(mean_value)
                labels.append(str(i) + " Threads")
            
        self.ui.SpeedupChart.draw(values=mean_values, labels=labels, ylabel="1 Thread / x Threads", yscale=str(self.ui.cmbScale.currentText()))
        
    def update_function_select(self):
        """
        Load no data in FunctionSelectTree if new file was added
        """
        names = self.current_data().unique_function_names()
        l = []
        for name in names:
            l.append(QTreeWidgetItem([name]))
        
        self.ui.FunctionSelectTree.clear()
        self.ui.FunctionSelectTree.addTopLevelItems(l)
        self.ui.FunctionSelectTree.setCurrentItem(l[0])
    
    def update_thread_select(self):
        """
        Load no data in ThreadSelectTree if new file was added
        """
        
        l = []
        for key in self._data:
            item = QTreeWidgetItem([str(key) + " Threads"])
            item.setFlags(Qt.ItemIsEnabled | Qt.ItemIsUserCheckable)
            item.setCheckState(0, Qt.Unchecked) 
            l.append(item)
        
        self.ui.ThreadSelectTree.clear()
        self.ui.ThreadSelectTree.addTopLevelItems(l)
         
    
    #==============================================================================
    # actions for the TreeWidget of ErrorbarChart
    #==============================================================================
    
    @pyqtSlot(QTreeWidgetItem,QTreeWidgetItem)
    def change_errorbarchart_tree(self, current, previous=0):
        """
        If selection changed then filter data and draw chart.
        """
        if current:
            obj = str(current.text(0)).split(" - ")
            mean_values = [self.current_data().values_each_test(obj[0], obj[1], "mean")]
            std_values = [self.current_data().values_each_test(obj[0], obj[1], "std")]
            
            if self.ui.chkStdValues.isChecked():
                self.ui.ErrorbarChart.draw(mean_values, std_values, yscale=str(self.ui.cmbScale.currentText()))
            else:
                self.ui.ErrorbarChart.draw(mean_values, yscale=str(self.ui.cmbScale.currentText()))
            
            self.ui.cmbRawData.clear()
            for i in xrange(self.current_data().num_tests()):
                self.ui.cmbRawData.addItem("Test " + str(i), i)
            
    def update_errorbarchart_tree(self):
        """
        Fill TreeWidget with data from cointainer.
        """
        names = self.current_data().unique_function_names()
        l = []
        for name in names:
            l.append(QTreeWidgetItem([name]))
        
        self.ui.ErrorbarChartTree.clear()
        self.ui.ErrorbarChartTree.addTopLevelItems(l)
        
    def load_raw_data(self):
        if self.current_data() and self.ui.ErrorbarChartTree.selectedItems():
            obj = str(self.ui.ErrorbarChartTree.selectedItems()[0].text(0)).split(" - ")
            test_nr = self.ui.cmbRawData.itemData(self.ui.cmbRawData.currentIndex()).toInt()[0]
            raw_data = [self.current_data().values_each_test(obj[0], obj[1], "raw")[test_nr]]
            
            self.ui.ErrorbarChart.draw(raw_data, yscale=str(self.ui.cmbScale.currentText()))
            
    
    #==============================================================================
    # actions for the TreeWidget of PieChart
    #==============================================================================
    
    @pyqtSlot(QTreeWidgetItem,QTreeWidgetItem)
    def change_piechart_tree(self, current, previous):
        """
        If selection changed then filter data and draw chart.    
        """
        if current:
            topIdx = self.ui.PieChartTree.invisibleRootItem().indexOfChild(current)
            if topIdx != -1: # top element? (Network)
                values = self.current_data().values_by_type(topIdx, "net")
                
                # net-step = overhead + net-proj_step + net-psp + net-neur_step
                overhead = values["step"]["mean"] - (values["proj_step"]["mean"] + values["psp"]["mean"] + values["neur_step"]["mean"])
                    
                data = [
                        ["Overhead\n(" + "%.4f" % overhead + ")", "%.4f" % overhead],
                        ["proj_step\n(" + "%.4f" % values["proj_step"]["mean"] + ")", "%.4f" % values["proj_step"]["mean"]],
                        ["psp\n(" + "%.4f" % values["psp"]["mean"] + ")", "%.4f" % values["psp"]["mean"]],
                        ["neur_step\n(" + "%.4f" % values["neur_step"]["mean"] + ")", "%.4f" % values["neur_step"]["mean"]]
                    ]
                self.ui.PieChart.draw(data, current.text(0) + " (in ms)", True)
            else:
                childIdx = current.parent().indexOfChild(current)
                topIdx = self.ui.PieChartTree.invisibleRootItem().indexOfChild(current.parent())
                if topIdx != -1: # First child of Network?
                    
                    if childIdx == 0:
                        neur_step = self.current_data().values_by_function(topIdx, "net", "neur_step")
                        func_data = self.current_data().values_by_function(topIdx, "pop", "step")
    
                        overhead = neur_step["mean"]
                        values = []
                        for key,value in func_data.items():
    
                            overhead -= value["mean"]
                            values.append(["pop" + str(key), "%.4f" % value["mean"]])
                        
                        values.append(["overhead", "%.4f" % overhead])
                        
                    if childIdx == 1:
                        proj_step = self.current_data().values_by_function(topIdx, "net", "proj_step")
                        func_data = self.current_data().values_by_function(topIdx, "proj", "step")
    
                        overhead = proj_step["mean"]
                        values = []
                        for key,value in func_data.items():
    
                            overhead -= value["mean"]
                            values.append(["proj" + str(key), "%.4f" % value["mean"]])
                        
                        values.append(["overhead", "%.4f" % overhead])
                        
                    if childIdx == 2:
                        net_psp = self.current_data().values_by_function(topIdx, "net", "psp")
                        func_data = self.current_data().values_by_function(topIdx, "proj", "psp")
    
                        overhead = net_psp["mean"]
                        values = []
                        for key,value in func_data.items():
    
                            overhead -= value["mean"]
                            values.append(["proj" + str(key), "%.4f" % value["mean"]])
                        
                        values.append(["overhead", "%.4f" % overhead])
                    
                    self.ui.PieChart.draw(values, current.text(0) + " (in ms)", False)
            
    def update_piechart_tree(self):
        """
        Fill TreeWidget with data from cointainer.
        """
        wdg = self.ui.PieChartTree
        l = []
        for i in xrange(self.current_data().num_tests()):
            item = QTreeWidgetItem(["Measurement " + str(i)])
            item.addChild(QTreeWidgetItem(["pop - step"]))
            item.addChild(QTreeWidgetItem(["proj - step"]))
            item.addChild(QTreeWidgetItem(["proj - psp"]))
            l.append(item)
        
        wdg.clear()
        wdg.addTopLevelItems(l)