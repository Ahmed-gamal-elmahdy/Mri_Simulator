import logging as log
import os
import sys
from io import BytesIO

import sigpy
from PyQt5 import QtWidgets
from PyQt5.QtGui import QPixmap
from PyQt5.QtWidgets import QFileDialog, QMessageBox
import warnings
import matplotlib.image as mpimg
from matplotlib import pyplot as plt

from PyQt5 import QtWidgets, QtCore, QtGui
from PyQt5.QtGui import QPixmap
from PyQt5.QtWidgets import QMessageBox
import numpy as np
import qimage2ndarray
import sys
import math
import threading
import pyqtgraph as pg
from PyQt5.QtWidgets import QFileDialog
from math import sin, cos, pi
import csv
import cv2
import numpy as np
from PIL import Image
from gui import Ui_MainWindow
from scripts.helper import *

warnings.filterwarnings("error")
log.basicConfig(filename='mainLogs.log', filemode='w', format='%(asctime)s - %(message)s', datefmt='%d-%b-%y %H:%M:%S')


class ApplicationWindow(QtWidgets.QMainWindow):
    def __init__(self):
        super(ApplicationWindow, self).__init__()
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)
        self.ui.actionOpen.triggered.connect(lambda: self.browse())
        self.ui.comboBox_size.currentIndexChanged.connect(lambda: self.phantomSizeChanged())


        self.ui.comboBox_size.addItems(["256","512"])

        # Mouse Events
        self.ui.label_phantom.setMouseTracking(False)
        self.ui.label_phantom.mouseDoubleClickEvent=self.setColoredPixel

        # Enable antialiasing for prettier plots
        pg.setConfigOptions(antialias=True)
        self.ui.label_phantom.setScaledContents(True)
        ## Create image to display
        v = self.ui.plotwidget_sequance
        self.img = None

    def setColoredPixel(self, event):
        w=self.ui.label_phantom.geometry().width()
        h=self.ui.label_phantom.geometry().height()
        self.phantomSize = int(self.ui.comboBox_size.currentText())
        scaleX=self.phantomSize / w
        scaleY=self.phantomSize / h
        self.x = np.floor(event.pos().x() * scaleX)
        self.y = np.floor(event.pos().y() * scaleY)
        #self.x = np.floor(x)
        #self.y = np.floor(y)
        print(self.x)
        print(self.y)
        self.ui.label_phantom.setPixmap(QPixmap(self.img))
        canvas = QPixmap(self.img)
        print(canvas.size())
        paint = QtGui.QPainter()
        paint.begin(canvas)
        # set rectangle color and thickness
        pen = QtGui.QPen(QtCore.Qt.red)
        pen.setWidthF(0.9)
        paint.setPen(pen)
        # draw rectangle on painter
        rect = QtCore.QRectF(self.x, self.y, 1, 1)
        paint.drawRect(rect)
        # set pixmap onto the label widget
        paint.end()
        self.ui.label_phantom.setPixmap(canvas)


    def browse(self):
        # Open Browse Window & Check
        fileName, _ = QtWidgets.QFileDialog.getOpenFileName(self, "Open img", (QtCore.QDir.homePath()),
                                                            "png (*.png)")
        if fileName:
            # Check extension
            try:
                print("hi")
            except (IOError, SyntaxError):
                self.error('Check File Extension')

    def phantomSizeChanged(self):
        size = self.ui.comboBox_size.currentText()
        #rebuild phantom with the new size
        self.setPhantomImage(getPhantom(size))

    def setPhantomImage(self, img):
        # no need to resize set scaled content fill the img
        # img = cv2.resize(img, (512, 512))
        self.img = qimage2ndarray.array2qimage(img)
        self.ui.label_phantom.setPixmap(QPixmap(self.img))


def main():
    app = QtWidgets.QApplication(sys.argv)
    application = ApplicationWindow()
    application.show()
    app.exec_()


if __name__ == "__main__":
    main()
