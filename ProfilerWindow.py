# ==============================================================================
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
# ==============================================================================
import os

from PyQt5.QtCore import pyqtSlot, Qt
from PyQt5.QtWidgets import QErrorMessage, QFileDialog, QMainWindow, QMessageBox, QTreeWidgetItem
from PyQt5.uic import loadUi

from DataContainer import DataContainer
from RunDialog import RunDialog
from Charts import MatplotlibWidget


class ProfilerWindow(QMainWindow):
    """
    MainWindow of the application. Define all actions and hold the data to display.
    """
    def __init__(self):
        """
        Init the class variables, load the window and add actions to the menubar.
        """
        super(self.__class__, self).__init__()
        self.ui = loadUi("ProfilerWindow.ui")
        
        # actions menubar
        self.ui.btnLoadData.triggered.connect(self.load_data_dialog)
        self.ui.btnRunMeasurement.triggered.connect(self.load_run_dialog)
        self.ui.btnSave.triggered.connect(self.save_chart)
        
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
        self.ui.btnRawData.clicked.connect(self.click_raw_data)
        self.ui.btnRecalc.clicked.connect(self.click_recalc_errorbar)
        
        # set class variables 
        self._data = {}
    
    def show(self):
        """
        Display the widget.
        """
        self.ui.show()
        
    def add_data(self, data):
        """
        Add a new DataContainer instance to measurement-data.
        Ask for overwriting if a measurement with same number of threads exists.
        
        Arguments:
            * data (DataContainer) -- new data to hold in app
        """
        # Show warning if data for paradigm with same number of threads exists
        if data.key() in self._data:
            msg = QMessageBox()
            msg.setText(data.paradigm() + " with " + str(data.num_threads()) + " threads already exists. Want to overwrite?")
            msg.setIcon(QMessageBox.Warning)
            msg.setStandardButtons(QMessageBox.No | QMessageBox.Yes)
            msg.setDefaultButton(QMessageBox.Yes)
            if msg.exec_() != QMessageBox.Yes:
                return
        
        self._data[data.key()] = data
        self.update_cmb_thread()
        self.update_function_select()
        self.update_thread_select()
        
    def current_data(self):
        """
        Returns the data which is chosen over the combobox. If nothing chosen than it returns an empty DataContainer instance.
        """
        sel_idx = self.ui.cmbThread.itemData(self.ui.cmbThread.currentIndex())
        
        # Sanity check, if something is selected
        if sel_idx == None or sel_idx == '':
            return DataContainer()

        return self._data[sel_idx]

    # ==============================================================================
    # actions for the buttons in the menu bar
    # ==============================================================================

    @pyqtSlot()    
    def load_data_dialog(self):
        """
        Open file-dialog to choose multiple files. Add data to container and set it in application.
        
        Signals:
            * activated() emitted from btnLoadData in menubar
        """
        fnames, _ = QFileDialog.getOpenFileNames(self, 'Open data file', '.', '*.xml')

        for fname in fnames:
            # Process the file and store the date in a container
            data = DataContainer()
            if not data.load_data(fname):
                error = QErrorMessage()
                error.showMessage("Problem while importing data.")
            else:
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
        if self.current_data():
            self.update_piechart_tree()
            self.update_errorbarchart_tree()
            self.update_barchart_tree()
    
    def update_cmb_thread(self):
        """
        Update the items of the combobox from test data
        """
        self.ui.cmbThread.clear()
        for key in self._data:
            splitted = key.split("-")
            thread_count = splitted[1]
            paradigm = splitted[0]
            self.ui.cmbThread.addItem(paradigm + " - " + thread_count + " Threads ", key)
    
    
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
        
        current = current[0]
        
        # Check if child element is selected
        parentIdx = self.ui.FunctionSelectTree.invisibleRootItem().indexOfChild(current)
        if parentIdx == -1:
            parentIdx = current.parent().indexOfChild(current)
            parentIdx = self.ui.FunctionSelectTree.invisibleRootItem().indexOfChild(current.parent())
        
            if parentIdx == 0: obj_type = "net"
            elif parentIdx == 1: obj_type = "pop"
            elif parentIdx == 2: obj_type = "proj"
    
            root = self.ui.ThreadSelectTree.invisibleRootItem()
            idx = []
            for i in range(root.childCount()):
                if root.child(i).checkState(0) == Qt.Checked:
                    idx.append(str(self.ui.cmbThread.itemData(i)))
            
            if len(idx) == 0:
                return
            
            mean_values = []
            std_values = []
            labels = []
            
            obj = str(current.text(0)).split(" - ")
            for i in idx:
                mean_values.append(self._data[i].values_each_test(obj_type, obj[0], obj[1], "mean"))
                std_values.append(self._data[i].values_each_test(obj_type, obj[0], obj[1], "std"))
                labels.append(str(i) + " Threads")
            
            if self.ui.chkStdValues.isChecked():
                self.ui.MultiThreadChart.draw(mean_values, std_values, labels, yscale=str(self.ui.cmbScale.currentText()))
            else:
                self.ui.MultiThreadChart.draw(mean_values, labels=labels, yscale=str(self.ui.cmbScale.currentText()))
            
            ### Speedup-Graph ###
            
            mean_values = []
            mean_value = []
            labels = []
            
            for i in idx:
                paradigm, thread_count = i.split('-')
                paradigm_key = paradigm + '-1'
    
                if thread_count != '1' and paradigm_key in self._data:
                    mean_one_thread = self._data[paradigm_key].values_each_test(obj_type, obj[0], obj[1], "mean")
                    mean_value = self._data[i].values_each_test(obj_type, obj[0], obj[1], "mean")
                    for n in range(len(mean_value)):
                        mean_value[n] = mean_one_thread[n] / mean_value[n]
                        
                    mean_values.append(mean_value)
                    labels.append(str(i) + " Threads")
            
            if len(mean_values) != 0:  
                self.ui.SpeedupChart.draw(values=mean_values, labels=labels, ylabel="1 Thread / x Threads", yscale=str(self.ui.cmbScale.currentText()))
            
    def update_function_select(self):
        """
        Load no data in FunctionSelectTree if new file was added
        """
        l = []
        
        # names for network
        names = self.current_data().unique_function_names("net")
        item = QTreeWidgetItem(["Network"])
        for name in names:
            item.addChild(QTreeWidgetItem([name]))
        l.append(item)
        
        # names for population
        names = self.current_data().unique_function_names("pop")
        item = QTreeWidgetItem(["Population"])
        for name in names:
            item.addChild(QTreeWidgetItem([name]))
        l.append(item)
        
        # names for projection
        names = self.current_data().unique_function_names("proj")
        item = QTreeWidgetItem(["Projection"])
        for name in names:
            item.addChild(QTreeWidgetItem([name]))
        l.append(item)
        
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
    # actions for the TreeWidget of BarChart
    #==============================================================================
    
    @pyqtSlot(QTreeWidgetItem,QTreeWidgetItem)
    def change_barchart_tree(self, current, previous=0):
        """
        If selection changed then filter data and draw chart.
        
        Signals:
            * currentItemChanged(QTreeWidgetItem,QTreeWidgetItem) emitted from ErrorbarChartTree
        """
        pass

    def update_barchart_tree(self):
        """
        Fill TreeWidget with data from container.
        """
        pass
    
    #==============================================================================
    # actions for the TreeWidget of ErrorbarChart
    #==============================================================================
    
    @pyqtSlot(QTreeWidgetItem,QTreeWidgetItem)
    def change_errorbarchart_tree(self, current, previous=0):
        """
        If selection changed then filter data and draw chart.
        
        Signals:
            * currentItemChanged(QTreeWidgetItem,QTreeWidgetItem) emitted from ErrorbarChartTree
        """
        if current:
            idx = self.ui.ErrorbarChartTree.invisibleRootItem().indexOfChild(current)
            if idx == -1: # not top element?
                idx = current.parent().indexOfChild(current)
                parentIdx = self.ui.ErrorbarChartTree.invisibleRootItem().indexOfChild(current.parent())
            
                if parentIdx == 0: obj_type = "net"
                elif parentIdx == 1: obj_type = "pop"
                elif parentIdx == 2: obj_type = "proj"
                
                obj = str(current.text(0)).split(" - ")
                mean_values = [self.current_data().values_each_test(obj_type, obj[0], obj[1], "mean")]
                std_values = [self.current_data().values_each_test(obj_type, obj[0], obj[1], "std")]
            
                if self.ui.chkStdValues.isChecked():
                    self.ui.ErrorbarChart.draw(mean_values, std_values, yscale=str(self.ui.cmbScale.currentText()))
                else:
                    self.ui.ErrorbarChart.draw(mean_values, yscale=str(self.ui.cmbScale.currentText()))
            
                self.ui.cmbRawData.clear()
                for i in range(self.current_data().num_tests()):
                    self.ui.cmbRawData.addItem("Test " + str(i), i)
            
    def update_errorbarchart_tree(self):
        """
        Fill TreeWidget with data from container.
        """
        l = []
        
        # names for network
        names = self.current_data().unique_function_names("net")
        item = QTreeWidgetItem(["Network"])
        for name in names:
            item.addChild(QTreeWidgetItem([name]))
        l.append(item)
        
        # names for population
        names = self.current_data().unique_function_names("pop")
        item = QTreeWidgetItem(["Population"])
        for name in names:
            item.addChild(QTreeWidgetItem([name]))
        l.append(item)
        
        # names for projection
        names = self.current_data().unique_function_names("proj")
        item = QTreeWidgetItem(["Projection"])
        for name in names:
            item.addChild(QTreeWidgetItem([name]))
        l.append(item)
        
        self.ui.ErrorbarChartTree.clear()
        self.ui.ErrorbarChartTree.addTopLevelItems(l)
        
    def click_raw_data(self):
        """
        Loads raw data from given selection in errorbar-chart-widget.
        
        Signals:
            * clicked() emitted from btnRawData
        """
        if self.current_data() and self.ui.ErrorbarChartTree.selectedItems():
            
            current = self.ui.ErrorbarChartTree.selectedItems()[0]
            idx = self.ui.ErrorbarChartTree.invisibleRootItem().indexOfChild(current)
            if idx == -1: # not top element?
                idx = current.parent().indexOfChild(current)
                parentIdx = self.ui.ErrorbarChartTree.invisibleRootItem().indexOfChild(current.parent())
            
                if parentIdx == 0: obj_type = "net"
                elif parentIdx == 1: obj_type = "pop"
                elif parentIdx == 2: obj_type = "proj"
                
                obj = str(self.ui.ErrorbarChartTree.selectedItems()[0].text(0)).split(" - ")
                test_nr = self.ui.cmbRawData.itemData(self.ui.cmbRawData.currentIndex()).toInt()[0]
                raw_data = [self.current_data().values_each_test(obj_type, obj[0], obj[1], "raw")[test_nr]]
            
                self.ui.ErrorbarChart.draw(raw_data, yscale=str(self.ui.cmbScale.currentText()))
            
    def click_recalc_errorbar(self):
        """
        Recalc main values for given selection. Exclude values which are out of selected range.
        
        Signals:
            * clicked() emitted from btnRecalc
        """
        if self.current_data() and self.ui.ErrorbarChartTree.selectedItems():
            
            current = self.ui.ErrorbarChartTree.selectedItems()[0]
            idx = self.ui.ErrorbarChartTree.invisibleRootItem().indexOfChild(current)
            if idx == -1: # not top element?
                idx = current.parent().indexOfChild(current)
                parentIdx = self.ui.ErrorbarChartTree.invisibleRootItem().indexOfChild(current.parent())
            
                if parentIdx == 0: obj_type = "net"
                elif parentIdx == 1: obj_type = "pop"
                elif parentIdx == 2: obj_type = "proj"
        
                factor = float(self.ui.txtFactor.text())
                
                obj = str(self.ui.ErrorbarChartTree.selectedItems()[0].text(0)).split(" - ")
                mean_values, std_values = self.current_data().recalc_mean_values(obj_type, obj[0], obj[1], factor)

                if self.ui.chkStdValues.isChecked():
                    self.ui.ErrorbarChart.draw([mean_values], [std_values], yscale=str(self.ui.cmbScale.currentText()))
                else:
                    self.ui.ErrorbarChart.draw(mean_values, yscale=str(self.ui.cmbScale.currentText()))

    # ==============================================================================
    # actions for the TreeWidget of PieChart
    # ==============================================================================
    
    @pyqtSlot(QTreeWidgetItem,QTreeWidgetItem)
    def change_piechart_tree(self, current, previous):
        """
        If selection changed then filter data and draw chart.  
        
        Signals:
            * currentItemChanged(QTreeWidgetItem, QTreeWidgetItem) emitted from PieChartTree
        """
        if current:
            topIdx = self.ui.PieChartTree.invisibleRootItem().indexOfChild(current)
            if topIdx != -1: # top element? (Network)
                # TODO: what happens if multi-networks are measured ... ?
                values = self.current_data().values_by_type(topIdx, "net")

                #
                # This assignment is for clarity of the following code ...
                data_set = values[list(values.keys())[0]]

                # net-step = overhead + net-proj_step + net-psp + net-neur_step + rng + record
                # whereas some parts are optional ...
                overhead = data_set["step"]["mean"] - ( data_set["psp"]["mean"] + data_set["neur_step"]["mean"])

                #
                # Add mandatory operations
                data = [
                    ["psp\n(" + "%.4f" % data_set["psp"]["mean"] + ")", "%.4f" % data_set["psp"]["mean"]],
                    ["neur_step\n(" + "%.4f" % data_set["neur_step"]["mean"] + ")", "%.4f" % data_set["neur_step"]["mean"]],
                ]

                #
                # Check optional parts
                if "record" in data_set.keys():
                    overhead -= data_set["record"]["mean"]
                    data.append(["record\n(" + "%.4f" % data_set["record"]["mean"] + ")", "%.4f" % data_set["record"]["mean"]])

                if "proj_step" in data_set.keys():
                    overhead -= data_set["proj_step"]["mean"]
                    data.append(["proj_step\n(" + "%.4f" % data_set["proj_step"]["mean"] + ")", "%.4f" % data_set["proj_step"]["mean"]])
                
                if "rng" in data_set.keys():
                    overhead -= data_set["rng"]["mean"]
                    data.append(["Draw from RNG\n(" + "%.4f" % data_set["rng"]["mean"] + ")", "%.4f" % data_set["rng"]["mean"]])

                # Add overhead as last, its the time span which is obviously not measured ...
                data.append(["Overhead\n(" + "%.4f" % overhead + ")", "%.4f" % overhead])
                self.ui.PieChart.draw(data, current.text(0) + " (in ms)", True)
            else:
                childIdx = current.parent().indexOfChild(current)
                topIdx = self.ui.PieChartTree.invisibleRootItem().indexOfChild(current.parent())
                if topIdx != -1: # First child of Network?
                    try:
                        if childIdx == 0:
                            # Overhead = net_neur_step - sum(all pop_step)
                            neur_step = self.current_data().values_by_function(topIdx, "net", "neur_step")
                            neur_step = neur_step[list(neur_step.keys())[0]]
                            func_data = self.current_data().values_by_function(topIdx, "pop", "step")
        
                            overhead = neur_step["mean"]
                            values = []
                            for key,value in func_data.items():
        
                                overhead -= value["mean"]
                                values.append([str(key), "%.4f" % value["mean"]])
                            
                            values.append(["overhead", "%.4f" % overhead])
                            
                        if childIdx == 1:
                            proj_step = self.current_data().values_by_function(topIdx, "net", "proj_step")
                            proj_step = proj_step[list(proj_step.keys())[0]]
                            func_data = self.current_data().values_by_function(topIdx, "proj", "step")
        
                            overhead = proj_step["mean"]
                            values = []
                            for key,value in func_data.items():
        
                                overhead -= value["mean"]
                                values.append([str(key), "%.4f" % value["mean"]])
                            
                            values.append(["overhead", "%.4f" % overhead])
                            
                        if childIdx == 2:
                            net_psp = self.current_data().values_by_function(topIdx, "net", "psp")
                            net_psp = net_psp[list(net_psp.keys())[0]]
                            func_data = self.current_data().values_by_function(topIdx, "proj", "psp")
        
                            overhead = net_psp["mean"]
                            values = []
                            for key,value in func_data.items():
        
                                overhead -= value["mean"]
                                values.append([str(key), "%.4f" % value["mean"]])
                            
                            values.append(["overhead", "%.4f" % overhead])
                        
                        if childIdx == 3: # rng
                            net_rng = self.current_data().values_by_function(topIdx, "net", "rng")
                            net_rng = net_rng[list(net_rng.keys())[0]]
                            func_data = self.current_data().values_by_function(topIdx, "pop", "rng")

                            overhead = net_rng["mean"]
                            values = []
                            for key,value in func_data.items():
        
                                overhead -= value["mean"]
                                values.append([str(key), "%.4f" % value["mean"]])
                            
                            values.append(["overhead", "%.4f" % overhead])

                        self.ui.PieChart.draw(values, current.text(0) + " (in ms)", False)

                    except IndexError:
                        self.ui.PieChart.clear()
            
    def update_piechart_tree(self):
        """
        Fill TreeWidget with data from container.
        """
        top_lvl_obj = self.current_data().unique_function_names("net")

        wdg = self.ui.PieChartTree
        l = []
        for i in range(self.current_data().num_tests()):
            item = QTreeWidgetItem(["Measurement " + str(i)])
            item.addChild(QTreeWidgetItem(["pop - step"]))
            item.addChild(QTreeWidgetItem(["proj - step"]))
            item.addChild(QTreeWidgetItem(["proj - psp"]))
            if "network - rng" in top_lvl_obj:
                item.addChild(QTreeWidgetItem(["rng"]))
            if "network - record" in top_lvl_obj:
                #TODO: 
                # item.addChild(QTreeWidgetItem(["record"]))
                pass
                
            l.append(item)
        
        wdg.clear()
        wdg.addTopLevelItems(l)