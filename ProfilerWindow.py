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
from PyQt4.QtGui import QMainWindow
from PyQt4.uic import loadUi

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
        self.ui.connect(self.ui.btnRunMeasurement, SIGNAL("activated()"), self.load_run_dialog)
        self.ui.connect(self.ui.btnSave, SIGNAL("activated()"), self.save_chart)
        
        # set class variables 
        self._data = {}
    
    @pyqtSlot()
    def load_run_dialog(self):
        """
        Shows a dialog to enter data for a ANNarchy profile run.
        
        Signals:
            * activated() emitted from btnRunMeasurement in menubar
        """
        diag = ANNarchyRunDialog()
        script, path, args = diag.get_data()
        
        if(script != ""):
            os.system("cd " + str(path))
            os.system("python " + str(script) + " --profile --profile_out=" + str(path) + "/measurement.xml " + str(args))
            self.ui.AnalyzerWidget.set_data(str(path) + "/measurement.xml")
    
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
    
    def show(self):
        self.ui.show()