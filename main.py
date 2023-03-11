
import logging as log
import os
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
import helper
import phantom

warnings.filterwarnings("error")
log.basicConfig(filename='mainLogs.log', filemode='w', format='%(asctime)s - %(message)s', datefmt='%d-%b-%y %H:%M:%S')

class ApplicationWindow(QtWidgets.QMainWindow):
    def __init__(self):
        super(ApplicationWindow, self).__init__()
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)
        self.ui.actionOpen.triggered.connect(lambda :browse())

        # Enable antialiasing for prettier plots
        pg.setConfigOptions(antialias=True)
        ## Create image to display
        v=self.ui.plotwidget_sequance
        img=sp.shepp_logan([512,512],dtype=np.float_)



        def browse():
            # Open Browse Window & Check
            fileName, _ = QtWidgets.QFileDialog.getOpenFileName(self, "Open img", (QtCore.QDir.homePath()),
                                                                "png (*.png)")
            if fileName:
                # Check extension
                try:
                    img = Image.open(fileName)
                    np_img = np.array(img)
                    setPhantomImage(np_img)



                except (IOError, SyntaxError):
                    self.error('Check File Extension')

        def setPhantomImage(input):

            img = qimage2ndarray.array2qimage(input)
            print("hi")
            self.ui.label_phantom.setPixmap(QPixmap(img))

        setPhantomImage(img)




def main():
    app = QtWidgets.QApplication(sys.argv)
    application = ApplicationWindow()
    application.show()
    app.exec_()


if __name__ == "__main__":
    main()
