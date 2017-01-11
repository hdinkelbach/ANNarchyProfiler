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
from PyQt4.QtCore import pyqtSlot, SIGNAL
from PyQt4.QtGui import QApplication, QDialog, QFileDialog, QMainWindow
from PyQt4.uic import loadUi

import sys, os

class ANNarchyProfilerWindow(QMainWindow):
    def __init__(self):
        super(self.__class__, self).__init__()
        self.ui = loadUi("ANNarchyProfiler.ui")
        
        # actions menubar
        self.ui.connect(self.ui.btnRunMeasurement, SIGNAL("activated()"), self.load_run_dialog)
        self.ui.connect(self.ui.btnSave, SIGNAL("activated()"), self.save_chart)
    
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
        
class ANNarchyRunDialog(QDialog):
    def __init__(self):
        super(self.__class__, self).__init__()
        self.ui = loadUi("ANNarchyRunDialog.ui")
        
        self.ui.connect(self.ui.btnPath, SIGNAL("clicked()"), self.select_path)
        self.ui.connect(self.ui.btnScript, SIGNAL("clicked()"), self.select_script)

        
    def get_data(self):
        self.ui.exec_()
        if(self.result() == self.Accepted):
            return self.ui.txtScript.text(), self.ui.txtPath.text(), self.ui.txtArgs.text()
        else:
            return '', '', ''
    
    def select_path(self):
        self.ui.txtPath.setText(QFileDialog.getExistingDirectory(self, 'Select working directory', '.'))
        
    def select_script(self):
        if(self.ui.txtPath.text() != ""):
            path = self.ui.txtPath.text()
        else:
            path = "."
        self.ui.txtScript.setText(QFileDialog.getOpenFileName(self, 'Select script file', path, '*.py'))

if __name__ == '__main__': 
    app = QApplication(sys.argv)
    window = ANNarchyProfilerWindow()
    window.show()
    app.exec_() 