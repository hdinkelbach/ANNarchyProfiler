#!/usr/bin/python3

# ==============================================================================
#
#     ANNarchyProfiler.py
#
#     This file is part of ANNarchyProfiler.
#
#     Copyright (C) 2021  Max Linke <max.linke@live.de>
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
import random
from xml.etree import ElementTree
import pathlib
import sqlite3
import marshal
import numpy as np

import matplotlib

matplotlib.use("Qt5Agg")
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg
from matplotlib.figure import Figure

from PyQt5 import QtWidgets
from PyQt5 import QtCore
from PyQt5.Qt import Qt
from PyQt5.QtGui import QIcon


class PlotCanvas(FigureCanvasQTAgg):
    def __init__(self, parent=None, width=5, height=4, dpi=100):
        self.parent = parent
        fig = Figure(figsize=(width, height), dpi=dpi)
        self.axes = fig.add_subplot(1, 1, 1)
        super(PlotCanvas, self).__init__(fig)


class ANNarchyProfiler(QtWidgets.QMainWindow):
    def __init__(self, *args, **kwargs):
        super(ANNarchyProfiler, self).__init__(*args, **kwargs)

        self.initUI()

    def initUI(self):
        # basic mainWidget settings
        self.statusBar().showMessage("Initializing")
        self.setGeometry(300, 300, 600, 400)
        self.setWindowTitle("ANNarchy Profiler")

        # Setup the menu bar
        menubar = self.menuBar()
        fileMenu = menubar.addMenu("&File")
        settingsMenu = menubar.addMenu("&Settings")
        # Add open file action
        openAction = QtWidgets.QAction(QIcon("open.png"), "&Open", self)
        openAction.setShortcut("Ctrl+O")
        openAction.setStatusTip("Open files")
        openAction.triggered.connect(self.openFiles)
        fileMenu.addAction(openAction)
        # Add export action
        exportAction = QtWidgets.QAction(QIcon("export.png"), "&Export", self)
        exportAction.setShortcut("Ctrl+E")
        exportAction.setStatusTip("Export files")
        exportAction.triggered.connect(self.exportFiles)
        fileMenu.addAction(exportAction)
        # Add exit action
        exitAction = QtWidgets.QAction(QIcon("exit.png"), "&Exit", self)
        exitAction.setShortcut("Ctrl+Q")
        exitAction.setStatusTip("Exit ANNarchy Profiler")
        exitAction.triggered.connect(QtWidgets.qApp.quit)
        fileMenu.addAction(exitAction)

        # Setup the tool bar
        self.toolbar = self.addToolBar("Tool Bar")
        self.normBox = QtWidgets.QCheckBox("Normalize bars")
        self.toolbar.addWidget(self.normBox)

        # the widget to hold the application content
        self.mainWidget = QtWidgets.QWidget()
        self.mainWidget.setSizePolicy(
            QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding
        )
        # layout of boxes which stretch horizontally
        self.mainLayout = QtWidgets.QHBoxLayout(self.mainWidget)
        # tree widget do display properties in order
        self.tree = QtWidgets.QTreeWidget(self.mainWidget)
        self.tree.setSizePolicy(
            QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Minimum
        )
        self.tree.setHeaderLabels(["Data sources"])
        # self.tree.itemChanged.connect(self.redrawPlot)
        # self.tree.itemSelectionChanged.connect(self.redrawPlot)
        # I expose this item in this direct way so later we can access it more easily
        self.filesParent = QtWidgets.QTreeWidgetItem(self.tree)
        self.filesParent.setText(0, "Files")
        self.filesParent.setExpanded(True)
        self.filesParent.setFlags(
            self.filesParent.flags() | Qt.ItemIsTristate | Qt.ItemIsUserCheckable
        )
        self.filesParent.setToolTip(0, "The files providing the datasets")
        self.filesParent.setCheckState(0, Qt.Unchecked)
        self.objectsParent = QtWidgets.QTreeWidgetItem(self.tree)
        self.objectsParent.setText(0, "Objects")
        self.objectsParent.setExpanded(True)
        self.objectsParent.setFlags(self.objectsParent.flags())
        self.objectsParent.setToolTip(0, "The objects to analyse")
        # plot canvas to draw plots to
        self.plot = PlotCanvas(self.mainWidget)
        self.plot.setSizePolicy(
            QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding
        )
        self.plot.axes.plot(random.choices(range(5), k=5))
        self.mainLayout.setStretch(0, 1)
        self.mainLayout.setStretch(1, 4)
        self.mainLayout.addWidget(self.tree)
        self.mainLayout.addWidget(self.plot)
        self.setCentralWidget(self.mainWidget)

        # the database to store the datasets (in memory)
        self.dbConnection = sqlite3.connect(":memory:")
        self.dbCursor = self.dbConnection.cursor()
        self.dbCursor.execute(
            "CREATE TABLE datasets (id INTEGER PRIMARY KEY, file TEXT, paradigm TEXT, num_threads INTEGER, obj_type TEXT, name TEXT, func TEXT, label TEXT, mean REAL, std REAL, raw_data TEXT)"
        )
        self.dbConnection.commit()
        self.statusBar().showMessage("Ready")

    def openFiles(self):
        options = QtWidgets.QFileDialog.Options()
        files, _ = QtWidgets.QFileDialog.getOpenFileNames(
            self,
            "Open result files",
            "",
            "Result files (*.xml);;All files (*)",
            options=options,
        )

        for file in files:
            # TODO: Open, read and insert data
            print(file)
            name = pathlib.Path(file).name.split(".")[0]
            tree = ElementTree.parse(file)
            root = tree.getroot()
            parent = QtWidgets.QTreeWidgetItem(self.filesParent)
            parent.setText(0, name)
            parent.setFlags(parent.flags() | Qt.ItemIsUserCheckable)
            if config := root.find("config"):
                parent.setToolTip(
                    0,
                    "Paradigm: {}\nThreads: {}\nDatasets: {}".format(
                        config[0].text, config[1].text, len(root.findall("dataset"))
                    ),
                )
            parent.setCheckState(0, Qt.Checked)
            # load datasets into in memory database for better information retrieval
            if datasets := root.findall("dataset"):
                for dataset in datasets:
                    data = dict()
                    for i in dataset.iter():
                        data[i.tag] = i.text
                    self.dbCursor.execute(
                        "INSERT INTO datasets (file, paradigm, num_threads, obj_type, name, func, label, mean, std, raw_data) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                        [
                            name,
                            config[0].text,
                            config[1].text,
                            data.get("obj_type", None),
                            data.get("name", None),
                            data.get("func", None),
                            data.get("label", None),
                            data.get("mean", None),
                            data.get("std", None),
                            marshal.dumps(data.get("raw_data", None)),
                        ],
                    )
                    self.dbConnection.commit()
        self.filesParent.setCheckState(0, Qt.Checked)
        # TODO: Implement more sofisticated parameter selection
        objectTypes = self.dbCursor.execute("SELECT DISTINCT obj_type FROM datasets")
        for objectType in objectTypes.fetchall():
            item = QtWidgets.QTreeWidgetItem(self.objectsParent)
            item.setText(0, objectType[0])
            itemNames = self.dbCursor.execute(
                "SELECT DISTINCT name FROM datasets WHERE obj_type=:objectName",
                {"objectName": objectType[0]},
            )
            for itemName in itemNames.fetchall():
                subItem = QtWidgets.QTreeWidgetItem(item)
                subItem.setText(0, itemName[0])
        self.tree.itemChanged.connect(self.redrawPlot)
        self.tree.itemSelectionChanged.connect(self.redrawPlot)
        self.normBox.stateChanged.connect(self.redrawPlot)

    def exportFiles(self):
        raise NotImplementedError("This function is not implemented yet")

    def redrawPlot(self):
        # TODO: Implement parameter and data retrieval
        self.tree.blockSignals(True)
        fileNames = list()
        objectName = str()
        base = None
        plotValues = dict()
        print("Redraw the plot")
        for i in range(self.filesParent.childCount()):
            filesChild = self.filesParent.child(i)
            if filesChild.checkState(0):
                fileNames.append(filesChild.text(0))
        for i in range(self.objectsParent.childCount()):
            objectsChild = self.objectsParent.child(i)
            for j in range(objectsChild.childCount()):
                c = objectsChild.child(j)
                if c.isSelected():
                    objectName = c.text(0)
        print(fileNames)
        print(objectName)
        if objectName != "":
            self.plot.axes.clear()
            selection = self.dbCursor.execute(
                "SELECT DISTINCT func FROM datasets WHERE func!='step'"
            )
            funcNames = [v[0] for v in list(selection)]
            for funcName in funcNames:
                funcValues = list()
                for fileName in fileNames:
                    selection = self.dbCursor.execute(
                        "SELECT mean FROM datasets WHERE file=:fileName AND func=:funcName AND name=:objectName",
                        {
                            "fileName": fileName,
                            "funcName": funcName,
                            "objectName": objectName,
                        },
                    )
                    values = [v[0] for v in list(selection)]
                    print(
                        f"file: {fileName}; func: {funcName}; object: {objectName}; {values}"
                    )
                    if values != []:
                        funcValues.append(np.mean(values))
                if funcValues != []:
                    plotValues[funcName] = funcValues
            if self.normBox.isChecked():
                plotValues = self._normalize(plotValues)
            print(plotValues)
            for key, value in plotValues.items():
                self.plot.axes.bar(fileNames, value, 0.35, label=key, bottom=base)
                base = value
            self.plot.axes.legend()
            self.plot.draw()
        self.tree.blockSignals(False)

    def _normalize(self, data):
        d = data.copy()
        sums = [0.0] * len(list(data.values())[0])
        for key, value in data.items():
            for i, v in enumerate(value):
                sums[i] += v
        print(sums)
        for key, value in data.items():
            for i, v in enumerate(value):
                d[key][i] /= sums[i]
        return d
