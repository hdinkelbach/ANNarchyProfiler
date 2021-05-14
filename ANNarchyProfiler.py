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

import marshal
import pathlib
import random
import sqlite3
import sys
from xml.etree import ElementTree

import matplotlib
import numpy as np

matplotlib.use("Qt5Agg")
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg
from matplotlib.figure import Figure
from PyQt5 import QtCore, QtWidgets
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
        # I expose this items in this direct way so later we can access them more easily
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

        self.statusBar().showMessage("Ready")

    def openFiles(self):
        # drop database if it exists so we don't have redundant data
        self.dbCursor.execute("DROP TABLE IF EXISTS datasets")
        # create database as it can't exist at this point
        self.dbCursor.execute(
            "CREATE TABLE datasets (id INTEGER PRIMARY KEY, file TEXT, paradigm TEXT, num_threads INTEGER, obj_type TEXT, name TEXT, func TEXT, label TEXT, mean REAL, std REAL, raw_data TEXT)"
        )
        # commit changes to the database
        self.dbConnection.commit()
        # remove tree children as we would have redundant entries otherwise
        while self.filesParent.childCount() != 0:
            self.filesParent.removeChild(self.filesParent.child(0))
        while self.objectsParent.childCount() != 0:
            self.objectsParent.removeChild(self.objectsParent.child(0))
        # get options for a file dialog to contol behavior and appearance
        options = QtWidgets.QFileDialog.Options()
        # get files from file dialog (as default only directories and .xml files are shown)
        files, _ = QtWidgets.QFileDialog.getOpenFileNames(
            self,
            "Open result files",
            "",
            "Result files (*.xml);;All files (*)",
            options=options,
        )

        # iterate over the files, load the datasets and store them to the database
        for file in files:
            print(file)
            # get the name of the file without extension
            name = pathlib.Path(file).name.split(".")[0]
            # parse the xml tree structure of the file
            tree = ElementTree.parse(file)
            # get the entry point of the xml tree
            root = tree.getroot()
            # create a new item for the selection tree
            parent = QtWidgets.QTreeWidgetItem(self.filesParent)
            # set the name of the tree item to the file name
            parent.setText(0, name)
            # add the Qt.ItemIsUserCheckable flag to the standard flags
            parent.setFlags(parent.flags() | Qt.ItemIsUserCheckable)
            # if the file contains a "config" section, read information and set them as tool tip
            if config := root.find("config"):
                parent.setToolTip(
                    0,
                    "Paradigm: {}\nThreads: {}\nDatasets: {}".format(
                        config[0].text, config[1].text, len(root.findall("dataset"))
                    ),
                )
            # set the tree item to be checked by default
            parent.setCheckState(0, Qt.Checked)
            # find all the "dataset" tags (if there are none we have no data to store)
            if datasets := root.findall("dataset"):
                for dataset in datasets:
                    data = dict()
                    # save dataset in more accessable data format
                    for i in dataset.iter():
                        data[i.tag] = i.text
                    # insert dataset into database (not existing data will be None)
                    # the "raw_data" property is stored as a byte text serialized with marshal
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
                    # commit the changes to the database to make sure the data is stored properly
                    self.dbConnection.commit()
        # set the tree parent item to be checked by default to avoid check state inconsistencies
        self.filesParent.setCheckState(0, Qt.Checked)
        # select all the distinct object types from the database to create a property selection
        objectTypes = self.dbCursor.execute("SELECT DISTINCT obj_type FROM datasets")
        for objectType in objectTypes.fetchall():
            # create a tree item
            item = QtWidgets.QTreeWidgetItem(self.objectsParent)
            # set text of the tree item to the object type
            item.setText(0, objectType[0])
            # select distinct object names for every object type
            itemNames = self.dbCursor.execute(
                "SELECT DISTINCT name FROM datasets WHERE obj_type=:objectName",
                {"objectName": objectType[0]},
            )
            # add the objects as child of thier object type
            for itemName in itemNames.fetchall():
                subItem = QtWidgets.QTreeWidgetItem(item)
                subItem.setText(0, itemName[0])
        # connect change actions to the drawing function
        self.tree.itemChanged.connect(self.redrawPlot)
        self.tree.itemSelectionChanged.connect(self.redrawPlot)
        self.normBox.stateChanged.connect(self.redrawPlot)

    def exportFiles(self):
        raise NotImplementedError("This function is not implemented yet")

    def redrawPlot(self):
        # block all signals emitted by the item tree to prevent strange behavior
        self.tree.blockSignals(True)
        fileNames = list()
        objectName = str()
        base = list()
        plotValues = dict()
        print("Redraw the plot")
        # find all checked data sources by iterating through the structure
        for i in range(self.filesParent.childCount()):
            filesChild = self.filesParent.child(i)
            if filesChild.checkState(0):
                fileNames.append(filesChild.text(0))
        # find the selected property by iterating through the structure
        for i in range(self.objectsParent.childCount()):
            objectsChild = self.objectsParent.child(i)
            if objectsChild.isSelected():
                objectName = objectsChild.text(0)
            else:
                for j in range(objectsChild.childCount()):
                    c = objectsChild.child(j)
                    if c.isSelected():
                        objectName = c.text(0)
        print(fileNames)
        base = [0.0] * len(fileNames)
        print(objectName)

        # catch the case of unselected property as it can cause errors
        if objectName != "":
            # clear the plotting canvas
            self.plot.axes.clear()
            for fileName in fileNames:
                # fetch values from database
                if objectName == "network":
                    selection = self.dbCursor.execute(
                        "SELECT func, AVG(mean) FROM datasets WHERE file=:fileName AND name=:objectName AND func!='step' GROUP BY func ORDER BY func",
                        {"fileName": fileName, "objectName": objectName},
                    )
                elif objectName == "proj":
                    selection = self.dbCursor.execute(
                        "SELECT name, AVG(mean) FROM datasets WHERE file=:fileName AND obj_type=:objectName GROUP BY name ORDER BY name",
                        {"fileName": fileName, "objectName": objectName},
                    )
                else:
                    selection = self.dbCursor.execute(
                        "SELECT func, AVG(mean) FROM datasets WHERE file=:fileName AND name=:objectName GROUP BY func ORDER BY func",
                        {"fileName": fileName, "objectName": objectName},
                    )
                # gather fetched values in dict to plot them later
                funcValues = list(selection)
                plotValues["func"] = [i for i, _ in funcValues]
                plotValues[fileName] = [i for _, i in funcValues]
                # calculate overhead (this is only neccessary for the whole network)
                if objectName == "network":
                    selection = self.dbCursor.execute(
                        "SELECT func, AVG(mean) FROM datasets WHERE file=:fileName AND name=:objectName AND func='step' GROUP BY func ORDER BY func",
                        {"fileName": fileName, "objectName": objectName},
                    )
                    funcValues = list(selection)
                    plotValues["func"].append("overhead")
                    # overhead is calculated as the difference between the step property and the sum of all other properties
                    plotValues[fileName].append(
                        funcValues[0][1] - sum(plotValues[fileName])
                    )
            # if the normalization box is checked normalize the values
            if self.normBox.isChecked():
                plotValues = self._normalize(plotValues)
            print(plotValues)
            # plot the values as stacked bar chart
            # the bottom parameter starts out as a list of zeros and will grow with every plotted value
            for key, *value in zip(*(list(plotValues.values()))):
                self.plot.axes.bar(fileNames, value, 0.35, label=key, bottom=base)
                base = [i + j for i, j in zip(value, base)]
            # plot a legend
            self.plot.axes.legend()
            # draw the plot to the canvas
            self.plot.draw()
        # release the signal blockade
        self.tree.blockSignals(False)

    def _normalize(self, data):
        # normalize the values for relative plotting
        # normalization is achived by deviding every value by the sum of all values
        d = data.copy()
        for key, value in data.items():
            if key == "func":
                continue
            else:
                s = sum(value)
                d[key] = [i / s for i in data[key]]
        return d
