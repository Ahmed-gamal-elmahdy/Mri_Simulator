import codecs
import json
import logging as log
import os
import random
import sys
from io import BytesIO


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
from scripts import *
from scripts.helper import getPhantom


warnings.filterwarnings("error")
log.basicConfig(filename='mainLogs.log', filemode='w', format='%(asctime)s - %(message)s', datefmt='%d-%b-%y %H:%M:%S')




class ApplicationWindow(QtWidgets.QMainWindow):
    def __init__(self):
        super(ApplicationWindow, self).__init__()
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)
        self.ui.actionOpen.triggered.connect(lambda: self.browse())
        self.ui.actionSave_as.triggered.connect(lambda: self.save_Seq())
        self.ui.comboBox_size.currentIndexChanged.connect(lambda: self.phantomSizeChanged())

        self.ui.comboBox_size.addItems(["256", "512"])

        # Mouse Events
        self.ui.label_phantom.setMouseTracking(False)
        self.ui.label_phantom.mouseDoubleClickEvent = self.setColoredPixel

        # Enable antialiasing for prettier plots
        pg.setConfigOptions(antialias=True)
        self.ui.label_phantom.setScaledContents(True)
        ## Create image to display
        self.seqplot = self.ui.plotwidget_sequance

        self.img = None
        self.ui.btn_start_sequance.clicked.connect(lambda: self.updateFA())

        self.TR = 100
        self.TE = 50
        self.FA = 90


        #sequance plot
        self.seq_Data=None
        self.init_plot_seq()


    def save_Seq(self):
        seq = {
               'Rf': {
                   "x": self.Rf_line.getData()[0].tolist(),
                   "y": self.Rf_line.getData()[1].tolist(),
               },
               'Gz': {
                   "x": self.Gz_line.getData()[0].tolist(),
                   "y": self.Gz_line.getData()[1].tolist(),
               },
               'Gy': {
                   "x": self.Gy_line.getData()[0].tolist(),
                   "y": self.Gy_line.getData()[1].tolist(),
               },
               'Gx': {
                   "x": self.Gx_line.getData()[0].tolist(),
                   "y": self.Gx_line.getData()[1].tolist(),
               },
               'Ro': {
                   "x": self.Ro_line.getData()[0].tolist(),
                   "y": self.Ro_line.getData()[1].tolist(),
               },
               }
        fileName= QtWidgets.QFileDialog.getSaveFileName(self, "Open json", (QtCore.QDir.currentPath()), "json (*.json)")
        with open(fileName[0], 'w', encoding='utf-8') as f:
            json.dump(seq, f, ensure_ascii=False, indent=4)

    def plot_simple_seq(self):
        # RF
        duration = 20
        x = np.arange(0, duration, 0.1)
        y = np.sinc(x - 10) * self.FA + 1820
        self.Rf_line.setData(x, y)
        # Gz
        duration = 20
        x = np.array([0, duration, duration, 0, 0])
        y = np.array([0, 0, 100, 100, 0]) + 1410
        self.Gz_line.setData(x, y)
        # Gx
        duration = 10
        x = np.array([0, duration, duration, 0, 0]) + 20
        x = np.concatenate((x, x))
        y = np.array([0, 0, 100, 100, 0]) + 1000
        y = np.concatenate((y, np.add(y, 100)))
        x = np.concatenate((x, np.array([0, duration, duration, 0, 0]) + 20))
        y = np.concatenate((y, np.array([0, 0, 100, 100, 0]) + 900))
        self.Gx_line.setData(x, y)
        # Gy
        duration = 20
        x = np.array([0, duration, duration, 0, 0]) + 30
        y = np.array([0, 0, 100, 100, 0]) + 590
        self.Gy_line.setData(x, y)
        # readout
        duration = 20
        x = np.arange(0, duration, 0.1) + 50
        y = np.random.randint(0, 360, len(x))
        self.Ro_line.setData(x, y)

    def init_plot_seq(self):
        plotwidget = self.ui.plotwidget_sequance
        #plotwidget.setBackground("k")
        plotwidget.setYRange(-50,2000)
        plotwidget.addLegend(offset=(0,1))
        plotwidget.hideAxis("left")
        # RF
        pen = pg.mkPen(color=(255, 0, 0))
        name = "Rf,FA="+str(self.FA)
        self.Rf_line=plotwidget.plot([0,0],pen=pen,name=name)
        #Gz
        pen = pg.mkPen(color=(0, 255, 0))
        name = "Gz(SL)"
        self.Gz_line=plotwidget.plot([0,0],pen=pen,name=name)
        #Gx
        pen = pg.mkPen(color=(255, 255, 0))
        name = "Gx(Phase)"
        self.Gx_line=plotwidget.plot([0,0],pen=pen,name=name)
        #Gy
        pen = pg.mkPen(color=(255, 0, 255))
        name = "Gy(Freq)"
        self.Gy_line = plotwidget.plot([0,0],pen=pen,name=name)
        #readout
        pen = pg.mkPen(color=(0, 255, 255))
        name = "Readout"
        self.Ro_line = plotwidget.plot([0,0],pen=pen,name=name)
        plotwidget.setLimits(xMin=0, xMax=self.TR*2, yMin=-50, yMax=2000)
        p1=plotwidget.plotItem
        p1.setLabel('bottom', 'Time', units='s', color='g', **{'font-size': '12pt'})
        p1.getAxis('bottom').setPen(pg.mkPen(color='g', width=3))

    def updateFA(self):
        x = np.arange(0, 20, 0.1);
        y= np.sinc(x-10)*self.FA +1820
        self.Rf_line.setData(x,y)



    def setColoredPixel(self, event):
        w = self.ui.label_phantom.geometry().width()
        h = self.ui.label_phantom.geometry().height()
        self.phantomSize = int(self.ui.comboBox_size.currentText())
        scaleX = self.phantomSize / w
        scaleY = self.phantomSize / h
        self.x = int(np.floor(event.pos().x() * scaleX))
        self.y = int(np.floor(event.pos().y() * scaleY))
        self.ui.label_phantom.setPixmap(QPixmap(self.img))
        canvas = QPixmap(self.img)
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
        fileName, _ = QtWidgets.QFileDialog.getOpenFileName(self, "Open json", (QtCore.QDir.currentPath()), "json (*.json)")
        if fileName:
            # Check extension
            try:
                with open(fileName) as user_file:
                    seq = user_file.read()
                seq=json.loads(seq)
                rf=seq["Rf"]
                gx=seq["Gx"]
                gy=seq["Gy"]
                gz=seq["Gz"]
                ro=seq["Ro"]
                self.Rf_line.setData(rf["x"], rf["y"])
                self.Gz_line.setData(gz["x"], gz["y"])
                self.Gy_line.setData(gy["x"], gy["y"])
                self.Gx_line.setData(gx["x"], gx["y"])
                self.Ro_line.setData(ro["x"], ro["y"])
            except (IOError, SyntaxError):
                self.error('Check File Extension')

    def phantomSizeChanged(self):
        size = self.ui.comboBox_size.currentText()
        # rebuild phantom with the new size
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
