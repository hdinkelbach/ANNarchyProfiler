# ==============================================================================
#
#     main.py
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
import sys

from PyQt5.QtWidgets import QApplication

from ProfilerWindow import ProfilerWindow

"""
ANNarchyProfiler is an extension for neuron simulator ANNarchy. This tool help to analyze
the rim of a script. The data of the profiler will be shown in graph. So it is possible to
compare different measurements and measurements with different thread count.

Start the tool with following command:

    $ python main.py

This tool is on github: https://github.com/hdinkelbach/ANNarchyProfiler
"""
if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = ProfilerWindow()
    window.show()
    app.exec_()
