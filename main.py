#!/usr/bin/python3

import sys
import random

import matplotlib

matplotlib.use("Qt5Agg")
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg
from matplotlib.figure import Figure

from PyQt5 import QtWidgets
from PyQt5 import QtCore
from PyQt5.QtGui import QIcon


class MplCanvas(FigureCanvasQTAgg):
    def __init__(self, parent=None, width=5, height=4, dpi=100):
        fig = Figure(figsize=(width, height), dpi=dpi)
        self.axes = fig.add_subplot(111)
        super(MplCanvas, self).__init__(fig)


class MainWindow(QtWidgets.QMainWindow):
    def __init__(self, *args, **kwargs):
        super(MainWindow, self).__init__(*args, **kwargs)

        self.initUI()

    def initUI(self):
        self.statusBar().showMessage("Initializing")
        self.setGeometry(300, 300, 250, 250)
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
        # Add exit action
        exitAction = QtWidgets.QAction(QIcon("exit.png"), "&Exit", self)
        exitAction.setShortcut("Ctrl+Q")
        exitAction.setStatusTip("Exit ANNarchy Profiler")
        exitAction.triggered.connect(QtWidgets.qApp.quit)
        fileMenu.addAction(exitAction)

        # Create the matplotlib FigureCanvas object,
        # wich defines a single set of axes as self.axes
        """
        sc = MplCanvas(self, width=5, height=4, dpi=100)
        sc.axes.plot(random.choices(range(5), k=5))
        self.setCentralWidget(sc)
        """
        self.statusBar().showMessage("Ready")

    def openFiles(self):
        options = QtWidgets.QFileDialog.Options()
        # options |= QtWidgets.QFileDialog.DontUseNativeDialog
        files, _ = QtWidgets.QFileDialog.getOpenFileNames(
            self,
            "QFileDialog.getOpenFileNames()",
            "",
            "Result files (*.xml);;All files (*)",
            options=options,
        )
        if files:
            print(files)


def main():
    app = QtWidgets.QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()