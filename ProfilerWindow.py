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
from PyQt4.QtCore import pyqtSlot, SIGNAL
from PyQt4.QtGui import QFileDialog, QMainWindow, QMessageBox
from PyQt4.uic import loadUi

from DataContainer import DataContainer

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
        self.ui.connect(self.ui.btnLoadData, SIGNAL('activated()'), self.load_data_dialog)
        self.ui.connect(self.ui.btnRunMeasurement, SIGNAL('activated()'), self.load_run_dialog)
        self.ui.connect(self.ui.btnSave, SIGNAL('activated()'), self.save_chart)
        
        # action combobox
        self.ui.connect(self.ui.cmbThread, SIGNAL('currentIndexChanged(int)'), self.change_combobox)
        
        # set class variables 
        self._data = {}
    
    def show(self):
        self.ui.show()
        
    def add_data(self, data):
        """
        Add a DataContainer instance to test-data.
        Ask for overwriting if a test with same number of threads exists.
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
        self.update_combobox()
        
        
    #==============================================================================
    # actions for the combobox for choosing test-data
    #==============================================================================
    
    @pyqtSlot()
    def change_combobox(self, idx):
        """
        Update TreeViews if combobox changed.
        
        Signals:
            * currentIndexChanged(int) emitted from cmbThread
        """
        if self.ui.cmbThread.itemData(idx).toInt()[1]:
            key = self.ui.cmbThread.itemData(idx).toInt()[0]
            self.ui.PieChartTree.load_data(self._data[key])
            self.ui.ErrorbarChartTree.load_data(self._data[key])
    
    def update_combobox(self):
        """
        Update the items of the combobox from test data
        """
        self.ui.cmbThread.clear()
        for key in self._data:
            self.ui.cmbThread.addItem(str(key) + " Threads ", key)
    
    
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
        diag = ANNarchyRunDialog()
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
        if(self.ui.AnalyzerWidget.currentIndex() == 0):
            figure = self.ui.ErrorbarChart.figure()
            
        # tab "Torte" selected
        elif(self.ui.AnalyzerWidget.currentIndex() == 1):
            figure = self.ui.PieChart.figure()
        
        if(figure != 0):
            fname = QFileDialog.getSaveFileName(self, 'Save chart file', './chart.png', 'Image file (*.png *.jpg);;PDF file (*.pdf)')
            if(fname):
                figure.savefig(str(fname))
    