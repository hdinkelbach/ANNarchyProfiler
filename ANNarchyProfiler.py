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

from PyQt5.QtGui import QIcon
from PyQt5.Qt import Qt
from PyQt5 import QtCore, QtWidgets
from matplotlib.figure import Figure
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg
import marshal
import pathlib
import random
import sqlite3
import sys
from xml.etree import ElementTree

import matplotlib
import numpy as np

matplotlib.use("Qt5Agg")


class PlotCanvas(FigureCanvasQTAgg):
    def __init__(self, parent=None, width=5, height=4, dpi=100):
        self.parent = parent
        self.fig = Figure(figsize=(width, height), dpi=dpi)
        self.axes = self.fig.add_subplot(1, 1, 1)
        super(PlotCanvas, self).__init__(self.fig)


class ANNarchyProfiler(QtWidgets.QMainWindow):
    def __init__(self, *args, **kwargs):
        super(ANNarchyProfiler, self).__init__(*args, **kwargs)

        self.initUI()

    def initUI(self):
        # basic mainWidget settings
        self.statusBar().showMessage("Initializing")
        self.setGeometry(300, 300, 600, 400)
        self.setWindowTitle("ANNarchy Profiler")
        self.showMaximized()

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
        # Add save action
        saveAction = QtWidgets.QAction(QIcon("save.png"), "&Save", self)
        saveAction.setShortcut("Ctrl+S")
        saveAction.setStatusTip("Save Plot")
        saveAction.triggered.connect(self.savePlot)
        fileMenu.addAction(saveAction)
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
        fileMenu.addSeparator()
        fileMenu.addAction(exitAction)

        # Setup the tool bar
        self.toolbar = self.addToolBar("Tool Bar")
        # Add axis style button group
        self.axisStyleGroub = QtWidgets.QButtonGroup(self.toolbar)
        # Add basic option to button group
        self.basicAxisStyleButton = QtWidgets.QRadioButton("Basic")
        self.basicAxisStyleButton.setChecked(True)
        self.axisStyleGroub.addButton(self.basicAxisStyleButton)
        self.toolbar.addWidget(self.basicAxisStyleButton)
        # Add normalization option to button group
        self.normalizedAxisStyleButton = QtWidgets.QRadioButton("Normalize bars")
        self.axisStyleGroub.addButton(self.normalizedAxisStyleButton)
        self.toolbar.addWidget(self.normalizedAxisStyleButton)
        # Add logarithmic option to button group
        self.logarithmicAxisStyleButton = QtWidgets.QRadioButton("Logarithmic scale")
        self.axisStyleGroub.addButton(self.logarithmicAxisStyleButton)
        self.toolbar.addWidget(self.logarithmicAxisStyleButton)
        self.toolbar.addSeparator()
        # Add line plot style button group
        self.plotStyleGroup = QtWidgets.QButtonGroup(self.toolbar)
        # Add basic option to button group
        self.basicPlotStyleButton = QtWidgets.QRadioButton("Basic")
        self.basicPlotStyleButton.setChecked(True)
        self.plotStyleGroup.addButton(self.basicPlotStyleButton)
        self.toolbar.addWidget(self.basicPlotStyleButton)
        # Add speed up option to button group
        self.speedUpPlotStyleButton = QtWidgets.QRadioButton("Speed up")
        self.plotStyleGroup.addButton(self.speedUpPlotStyleButton)
        self.toolbar.addWidget(self.speedUpPlotStyleButton)
        # Add raw data option to button group
        self.rawDataPlotStyleButton = QtWidgets.QRadioButton("Raw data")
        self.plotStyleGroup.addButton(self.rawDataPlotStyleButton)
        self.toolbar.addWidget(self.rawDataPlotStyleButton)
        # Add minimum as lower bound for raw data slice
        self.minLabel = QtWidgets.QLabel("Min:")
        self.toolbar.addWidget(self.minLabel)
        self.minBox = QtWidgets.QSpinBox()
        # self.minBox.setEnabled(False)
        # self.minBox.setRange(0, 100)
        self.minBox.setMinimum(0)
        self.toolbar.addWidget(self.minBox)
        # Add maximum as upper bound for raw data slice
        self.maxLabel = QtWidgets.QLabel("Max:")
        self.toolbar.addWidget(self.maxLabel)
        self.maxBox = QtWidgets.QSpinBox()
        # self.maxBox.setEnabled(False)
        # self.maxBox.setRange(0, 100)
        self.maxBox.setMinimum(0)
        self.maxBox.setValue(2)
        self.toolbar.addWidget(self.maxBox)

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
                    data["raw_data"] = list(map(float, data["raw_data"].split()))
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
        # TODO: clean database entries (insert missing datasets) (SELECT ... EXCEPT SELECT ...)
        # select all the distinct object types from the database to create a property selection
        selection = self.dbCursor.execute("SELECT DISTINCT obj_type FROM datasets")
        objectTypes = list(selection)
        for objectType in objectTypes:
            # create a tree item
            item = QtWidgets.QTreeWidgetItem(self.objectsParent)
            # set text of the tree item to the object type
            item.setText(0, objectType[0])
            # select distinct object names for every object type
            if objectType[0] == "net":
                selection = self.dbCursor.execute(
                    "SELECT DISTINCT func FROM datasets WHERE obj_type=:objectName",
                    {"objectName": objectType[0]},
                )
            else:
                selection = self.dbCursor.execute(
                    "SELECT DISTINCT name FROM datasets WHERE obj_type=:objectName",
                    {"objectName": objectType[0]},
                )
            itemNames = list(selection)
            # add the objects as child of thier object type
            for itemName in itemNames:
                subItem = QtWidgets.QTreeWidgetItem(item)
                subItem.setText(0, itemName[0])
        # connect change actions to the drawing function
        self.tree.itemChanged.connect(self.redrawPlot)
        self.tree.itemSelectionChanged.connect(self.redrawPlot)
        self.basicAxisStyleButton.toggled.connect(self.redrawPlot)
        self.normalizedAxisStyleButton.toggled.connect(self.redrawPlot)
        self.logarithmicAxisStyleButton.toggled.connect(self.redrawPlot)
        self.basicPlotStyleButton.toggled.connect(self.redrawPlot)
        self.speedUpPlotStyleButton.toggled.connect(self.redrawPlot)
        self.rawDataPlotStyleButton.toggled.connect(self.redrawPlot)
        self.minBox.valueChanged.connect(self.redrawPlot)
        self.maxBox.valueChanged.connect(self.redrawPlot)

    def exportFiles(self):
        raise NotImplementedError("This function is not implemented yet")

    def savePlot(self):
        # get options for a file dialog to contol behavior and appearance
        options = QtWidgets.QFileDialog.Options()
        # get path and name of the file to save the plot into
        file_name, file_format = QtWidgets.QFileDialog.getSaveFileName(
            self,
            "Save Plot",
            "",
            "PNG Image (*.png);;JPG Image (*.jpg);;All files (*)",
            options=options,
        )
        print(file_name, file_format)
        self.plot.fig.savefig(file_name, format=file_format.split(".")[-1][:-1])

    def redrawPlot(self):
        # block all signals emitted by the item tree to prevent strange behavior
        self.tree.blockSignals(True)
        fileNames = list()
        objectName = str()
        base = list()
        plotValues = dict()
        label = "computation time per step [ms"
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
                if objectName == "net":
                    selection = self.dbCursor.execute(
                        "SELECT func, AVG(mean) FROM datasets WHERE file=:fileName AND obj_type=:objectName AND func!='step' GROUP BY func ORDER BY func",
                        {"fileName": fileName, "objectName": objectName},
                    )
                elif objectName == "proj":
                    selection = self.dbCursor.execute(
                        "SELECT name, AVG(mean) FROM datasets WHERE file=:fileName AND obj_type=:objectName GROUP BY name ORDER BY name",
                        {"fileName": fileName, "objectName": objectName},
                    )
                elif objectName == "pop":
                    selection = self.dbCursor.execute(
                        "SELECT name, AVG(mean) FROM datasets WHERE file=:fileName AND obj_type=:objectName GROUP BY name ORDER BY name",
                        {"fileName": fileName, "objectName": objectName},
                    )
                # FIXME: is there a more flexible way to build this list?
                elif (
                    objectName
                    in [
                        "global_op",
                        "neur_step",
                        "proj_step",
                        "psp",
                        "record",
                        "rng",
                        "step",
                    ]
                    and self.rawDataPlotStyleButton.isChecked()
                ):
                    selection = self.dbCursor.execute(
                        "SELECT func, raw_data FROM datasets WHERE file=:fileName AND func=:objectName",
                        {"fileName": fileName, "objectName": objectName},
                    )
                # FIXME: is there a more flexible way to build this list?
                elif (
                    objectName
                    in [
                        "global_op",
                        "neur_step",
                        "proj_step",
                        "psp",
                        "record",
                        "rng",
                        "step",
                    ]
                    and not self.rawDataPlotStyleButton.isChecked()
                ):
                    selection = self.dbCursor.execute(
                        "SELECT func, mean FROM datasets WHERE file=:fileName AND func=:objectName",
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
                if (
                    objectName
                    in [
                        "global_op",
                        "neur_step",
                        "proj_step",
                        "psp",
                        "record",
                        "rng",
                        "step",
                    ]
                    and self.rawDataPlotStyleButton.isChecked()
                ):
                    plotValues[fileName] = [marshal.loads(i) for _, i in funcValues]
                else:
                    plotValues[fileName] = [i for _, i in funcValues]
                # calculate overhead (this is only neccessary for the whole network)
                if objectName == "net":
                    selection = self.dbCursor.execute(
                        "SELECT func, AVG(mean) FROM datasets WHERE file=:fileName AND obj_type=:objectName AND func='step' GROUP BY func ORDER BY func",
                        {"fileName": fileName, "objectName": objectName},
                    )
                    funcValues = list(selection)
                    plotValues["func"].append("overhead")
                    # overhead is calculated as the difference between the step property and the sum of all other properties
                    plotValues[fileName].append(
                        funcValues[0][1] - sum(plotValues[fileName])
                    )
            if objectName in [
                "global_op",
                "neur_step",
                "proj_step",
                "psp",
                "record",
                "rng",
                "step",
            ]:
                self.plot.axes.grid(True, which="both", axis="both")
                for key, value in plotValues.items():
                    print(key, len(value))
                    if key == "func":
                        plotValues[key] = plotValues[key][0]
                    elif key != "func" and self.rawDataPlotStyleButton.isChecked():
                        [plotValues[key][0].extend(x) for x in plotValues[key][1:]]
                        plotValues[key] = plotValues[key][0]
                        # plotValues[key] = [np.mean(i) for i in zip(*(plotValues[key]))]
                        self.minBox.setMaximum(
                            max(len(plotValues[key]), self.minBox.maximum())
                        )
                        self.maxBox.setMaximum(
                            max(len(plotValues[key]), self.maxBox.maximum())
                        )
                        print(key, len(plotValues[key]))
                    else:
                        plotValues[key] = plotValues[key]
                if self.speedUpPlotStyleButton.isChecked():
                    base = list(plotValues.items())[1][1].copy()
                    for key, value in plotValues.items():
                        if key != "func":
                            curr = plotValues[key]
                            print("base", type(base), base[0])
                            print("curr", type(curr), curr[0])
                            for i in range(len(plotValues[key])):
                                plotValues[key][i] = base[i] / curr[i]
                    label = "computation time per step [speed up]"
                else:
                    label += "]"
                for key, value in plotValues.items():
                    if key != "func":
                        if self.rawDataPlotStyleButton.isChecked():
                            self.plot.axes.plot(
                                range(self.minBox.value(), self.maxBox.value() + 1),
                                value[self.minBox.value() : self.maxBox.value() + 1],
                                label=key,
                            )
                        else:
                            self.plot.axes.plot(value, label=key)
                if self.logarithmicAxisStyleButton.isChecked():
                    self.plot.axes.set_yscale("log")

                self.plot.axes.set_xlabel("Number of Measurements")
            else:
                self.plot.axes.grid(True, which="both", axis="y")
                # if the normalization box is checked normalize the values
                if self.normalizedAxisStyleButton.isChecked():
                    plotValues = self._normalize(plotValues)
                    label = "parts [percentages"
                print(plotValues)
                # if the logarithmic scale box is checked set y scale to log
                if self.logarithmicAxisStyleButton.isChecked():
                    self.plot.axes.set_yscale("log")
                    label += ", log-scale]"
                else:
                    label += "]"
                # plot the values as stacked bar chart
                # the bottom parameter starts out as a list of zeros and will grow with every plotted value
                for key, *value in zip(*(list(plotValues.values()))):
                    self.plot.axes.bar(fileNames, value, 0.35, label=key, bottom=base)
                    base = [i + j for i, j in zip(value, base)]
            # plot a legend
            self.plot.axes.legend()
            # set the y label
            self.plot.axes.set_ylabel(label)
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
