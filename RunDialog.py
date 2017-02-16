#==============================================================================
#
#     RunDialog.py
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
from PyQt4.QtCore import SIGNAL
from PyQt4.QtGui import QDialog, QFileDialog
from PyQt4.uic import loadUi

class RunDialog(QDialog):
    """
    This is a modified Qt-Component. It opens a dialog where your can choose the script to analyse,
    the path where the scipt will be executete und the data files saved and add some arguments for
    execution of the script.
    """
    def __init__(self):
        """
        Load design of the dialog window from ui-file and connect buttons with functions.
        """
        super(self.__class__, self).__init__()
        self.ui = loadUi("RunDialog.ui")
        
        self.ui.btnPath.clicked.connect(self.select_path)
        self.ui.btnScript.clicked.connect(self.select_script)

        
    def get_data(self):
        """
        Return the input-values of the dialog if submit-button was clicked.
        """
        self.ui.exec_()
        if(self.result() == self.Accepted):
            return self.ui.txtScript.text(), self.ui.txtPath.text(), self.ui.txtArgs.text()
        else:
            return '', '', ''
    
    def select_path(self):
        """
        Open a FileDialog to choose the execution directory.
        """
        self.ui.txtPath.setText(QFileDialog.getExistingDirectory(self, 'Select working directory', '.'))
        
    def select_script(self):
        """
        Open a FileDialog to choose the script to execute. If a working directory path is set then
        by default this path will be opened else the path of the profiler.
        """
        if(self.ui.txtPath.text() != ""):
            path = self.ui.txtPath.text()
        else:
            path = "."
        self.ui.txtScript.setText(QFileDialog.getOpenFileName(self, 'Select script file', path, '*.py'))