import json
import logging as log

import sys
import warnings

import numpy as np
import pyqtgraph as pg
import qimage2ndarray
from PyQt5 import QtWidgets, QtCore, QtGui
from PyQt5.QtGui import QPixmap, qRed
from qt_material import apply_stylesheet
from gui import Ui_MainWindow
from scripts.helper import getPhantom, reconstructImage

warnings.filterwarnings("error")
log.basicConfig(filename='mainLogs.log', filemode='w', format='%(asctime)s - %(message)s', datefmt='%d-%b-%y %H:%M:%S')


class ApplicationWindow(QtWidgets.QMainWindow):
    def __init__(self):
        super(ApplicationWindow, self).__init__()
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)

        # Event Listeners
        self.ui.actionOpen.triggered.connect(lambda: self.browse())
        self.ui.actionSave_as.triggered.connect(lambda: self.save_Seq())
        self.ui.comboBox_size.currentIndexChanged.connect(lambda: self.phantomSizeChanged())
        self.ui.btn_start_sequance.clicked.connect(lambda: self.start_sequence())
        self.ui.slider_brightness.setMinimum(100)
        self.ui.slider_brightness.setMinimum(-100)
        self.ui.slider_brightness.setValue(0)
        self.ui.slider_brightness.valueChanged.connect(lambda: self.adjustBrightness())
        self.ui.comboBox_weights.currentIndexChanged.connect(lambda: self.weights())
        self.ui.label_phantom.setMouseTracking(False)
        self.ui.label_phantom.mouseDoubleClickEvent = self.highlight
        pg.setConfigOptions(antialias=True)
        self.ui.label_phantom.setScaledContents(True)

        self.error_dialog = QtWidgets.QErrorMessage()

        # ----- Variable Initialization ------ #
        # Plot
        self.seqplot = self.ui.plotwidget_sequance
        # image
        self.img = None
        self.brightness = self.ui.slider_brightness.value()
        # Tissue Property Weighted Image
        self.weighted = None
        # Tissue Property Info Image
        self.reader = None
        self.TR = 90
        self.TE = 60
        self.FA = 90

        # Tissue Properties

        self.map = {
            "csf": {
                "t1": "4000ms",
                "t2": "200ms",
                "pd": "1",
            },
            "grayMatter": {
                "t1": "900ms",
                "t2": "90ms",
                "pd": "0.69",
            },
            "muscle": {
                "t1": "900ms",
                "t2": "50ms",
                "pd": "0.72",
            },
            "fat": {
                "t1": "250ms",
                "t2": "70ms",
                "pd": "0.61",
            },
        }

        self.GRID_OFFSET = {
            "Rf": 1820,
            "Gz": 1410,
            "Gy": 1000,
            "Gx": 590,
        }

        # Set sequence Synthesiser reference lines
        self.synthesiser_ref_line = {
            "RF": pg.PlotItem,
            "Gz": pg.PlotItem,
            "Gy": pg.PlotItem,
            "Gx": pg.PlotItem,
            "Ro": pg.PlotItem,
            "TR": pg.InfiniteLine,
            "TE": pg.InfiniteLine,
            "FA": None
        }
        self.sequence_ref_line = {
            "RF": pg.PlotItem,
            "Gz": pg.PlotItem,
            "Gy": pg.PlotItem,
            "Gx": pg.PlotItem,
            "Ro": pg.PlotItem,
            "TR": pg.InfiniteLine,
            "TE": pg.InfiniteLine,
            "FA": None
        }
        # Initial Sequence and Phantom upon Opening The App
        self.init_plot_sequence()
        self.init_plot_synthesiser()
        self.plot_simple_seq()
        self.phantomSizeChanged()

        self.ui.spinbox_FA.valueChanged.connect(lambda: self.set_FA())
        self.ui.spinbox_TR.valueChanged.connect(lambda: self.set_TR())
        self.ui.spinbox_TE.valueChanged.connect(lambda: self.set_TE())

    def set_TR(self):
        """
        update TR line value
        """
        val = self.ui.spinbox_TR.value()
        self.synthesiser_ref_line["TR"].setPos(val)

    def set_TE(self):
        """
        update TE line value
        """
        val = self.ui.spinbox_TE.value()
        self.synthesiser_ref_line["TE"].setPos(val)

    def set_FA(self):
        """
        update Flip angle line value
        """
        val = self.ui.spinbox_FA.value()
        self.synthesiser_ref_line["FA"] = val
        print(self.synthesiser_ref_line["FA"])

    def save_Seq(self):
        """
        Saving The Sequence as JSON File
        """
        seq = {
            'Rf': {
                "x": self.synthesiser_ref_line["RF"].getData()[0].tolist(),
                "y": self.synthesiser_ref_line["RF"].getData()[1].tolist(),
            },
            'Gz': {
                "x": self.synthesiser_ref_line["Gz"].getData()[0].tolist(),
                "y": self.synthesiser_ref_line["Gz"].getData()[1].tolist(),
            },
            'Gy': {
                "x": self.synthesiser_ref_line["Gy"].getData()[0].tolist(),
                "y": self.synthesiser_ref_line["Gy"].getData()[1].tolist(),
            },
            'Gx': {
                "x": self.synthesiser_ref_line["Gx"].getData()[0].tolist(),
                "y": self.synthesiser_ref_line["Gx"].getData()[1].tolist(),
            },
            'Ro': {
                "x": self.synthesiser_ref_line["Ro"].getData()[0].tolist(),
                "y": self.synthesiser_ref_line["Ro"].getData()[1].tolist(),
            },
            "FA": self.synthesiser_ref_line["FA"],
            "TR": self.synthesiser_ref_line["TR"].getPos(),
            "TE": self.synthesiser_ref_line["TE"].getPos(),
        }
        fileName = QtWidgets.QFileDialog.getSaveFileName(self, "Save as json", (QtCore.QDir.currentPath()),
                                                         "json (*.json)")
        with open(fileName[0], 'w', encoding='utf-8') as f:
            json.dump(seq, f, ensure_ascii=False, indent=4)

    def start_sequence(self):
        """
        Start The Current Sequence and Reconstruct the Image
        Disable The button during reconstruction to avoid crashing
        """
        self.ui.btn_start_sequance.setDisabled(True)
        opt = reconstructImage(self)
        self.setReconsImage(opt)
        self.ui.btn_start_sequance.setDisabled(False)

    def plot_simple_seq(self):
        """
        Plot a template sequence
        """
        # RF
        duration = 20
        x = np.arange(0, duration, 0.1)
        y = np.sinc(x - 10) * self.FA + self.GRID_OFFSET["Rf"]
        self.synthesiser_ref_line["RF"].setData(x, y)
        # Gz
        duration = 20
        x = np.array([0, duration, duration, 0, 0])
        y = np.array([0, 0, 100, 100, 0]) + self.GRID_OFFSET["Gz"]
        self.synthesiser_ref_line["Gz"].setData(x, y)
        # Gx
        duration = 10
        x = np.array([0, duration, duration, 0, 0]) + 20
        x = np.concatenate((x, x))
        y = np.array([0, 0, 100, 100, 0]) + self.GRID_OFFSET["Gy"]
        y = np.concatenate((y, np.add(y, 100)))
        x = np.concatenate((x, np.array([0, duration, duration, 0, 0]) + 20))
        y = np.concatenate((y, np.array([0, 0, 100, 100, 0]) + 900))
        self.synthesiser_ref_line["Gy"].setData(x, y)
        # Gy
        duration = 20
        x = np.array([0, duration, duration, 0, 0]) + 30
        y = np.array([0, 0, 100, 100, 0]) + self.GRID_OFFSET["Gx"]
        self.synthesiser_ref_line["Gx"].setData(x, y)
        # readout
        duration = 20
        x = np.arange(0, duration, 0.1) + 50
        y = np.random.randint(0, 360, len(x))
        self.synthesiser_ref_line["Ro"].setData(x, y)
        # TE
        self.synthesiser_ref_line["TE"].setPos(60)
        # TR
        self.synthesiser_ref_line["TR"].setPos(90)

    # Initial Sequence
    def init_plot_sequence(self):
        """
        Setup limits & axes for sequence plot
        """
        plotwidget = self.ui.plotwidget_sequance
        plotwidget.setYRange(-50, 2000)
        plotwidget.addLegend(offset=(0, 1))
        plotwidget.hideAxis("left")
        # RF
        pen = pg.mkPen(color=(255, 0, 0))
        name = "RF"
        self.sequence_ref_line["RF"] = plotwidget.plot([0, 0], pen=pen, name=name)
        # Gz
        pen = pg.mkPen(color=(0, 255, 0))
        name = "Gz(SL)"
        self.sequence_ref_line["Gz"] = plotwidget.plot([0, 0], pen=pen, name=name)
        # Gx
        pen = pg.mkPen(color=(255, 255, 0))
        name = "Gx(Phase)"
        self.sequence_ref_line["Gx"] = plotwidget.plot([0, 0], pen=pen, name=name)
        # Gy
        pen = pg.mkPen(color=(255, 0, 255))
        name = "Gy(Freq)"
        self.sequence_ref_line["Gy"] = plotwidget.plot([0, 0], pen=pen, name=name)
        # readout
        pen = pg.mkPen(color=(0, 255, 255))
        name = "Readout"
        self.sequence_ref_line["Ro"] = plotwidget.plot([0, 0], pen=pen, name=name)
        # TR
        pen = pg.mkPen(color=(226, 135, 67))
        name = "TR"
        self.sequence_ref_line["TR"] = pg.InfiniteLine(pos=200, angle=90, pen=pen, label=name, name=name)
        plotwidget.addItem(self.sequence_ref_line["TR"])
        # TE
        pen = pg.mkPen(color=(128, 0, 128))
        name = "TE"
        self.sequence_ref_line["TE"] = pg.InfiniteLine(pos=50, angle=90, pen=pen, label=name, name=name)
        plotwidget.addItem(self.sequence_ref_line["TE"])

        # settings
        plotwidget.setLimits(xMin=0, xMax=self.TR * 2, yMin=-50, yMax=2000)
        p1 = plotwidget.plotItem
        p1.setLabel('bottom', 'Time', units='s', color='g', **{'font-size': '12pt'})
        p1.getAxis('bottom').setPen(pg.mkPen(color='g', width=3))

    def init_plot_synthesiser(self):
        """
        Setup synthesizer axes & limits
        """
        plotwidget = self.ui.plotwidget_synth
        plotwidget.setYRange(-50, 2000)
        plotwidget.addLegend(offset=(0, 1))
        plotwidget.hideAxis("left")
        # RF
        pen = pg.mkPen(color=(255, 0, 0))
        name = "RF"
        self.synthesiser_ref_line["RF"] = plotwidget.plot([0, 0], pen=pen, name=name)

        # Gz
        pen = pg.mkPen(color=(0, 255, 0))
        name = "Gz(SL)"
        self.synthesiser_ref_line["Gz"] = plotwidget.plot([0, 0], pen=pen, name=name)
        # Gx
        pen = pg.mkPen(color=(255, 255, 0))
        name = "Gx(Phase)"
        self.synthesiser_ref_line["Gx"] = plotwidget.plot([0, 0], pen=pen, name=name)
        # Gy
        pen = pg.mkPen(color=(255, 0, 255))
        name = "Gy(Freq)"
        self.synthesiser_ref_line["Gy"] = plotwidget.plot([0, 0], pen=pen, name=name)
        # readout
        pen = pg.mkPen(color=(0, 255, 255))
        name = "Readout"
        self.synthesiser_ref_line["Ro"] = plotwidget.plot([0, 0], pen=pen, name=name)
        # TR
        pen = pg.mkPen(color=(226, 135, 67))
        name = "TR"
        self.synthesiser_ref_line["TR"] = pg.InfiniteLine(pos=-60, angle=90, pen=pen, label=name, name=name)
        plotwidget.addItem(self.synthesiser_ref_line["TR"])
        # TE
        pen = pg.mkPen(color=(128, 0, 128))
        name = "TE"
        self.synthesiser_ref_line["TE"] = pg.InfiniteLine(pos=-60, angle=90, pen=pen, label=name, name=name)
        plotwidget.addItem(self.synthesiser_ref_line["TE"])

        # settings
        plotwidget.setLimits(xMin=0, xMax=self.TR * 2, yMin=-50, yMax=2000)
        p1 = plotwidget.plotItem
        p1.setLabel('bottom', 'Time', units='s', color='g', **{'font-size': '12pt'})
        p1.getAxis('bottom').setPen(pg.mkPen(color='g', width=3))

    # Highlight Phantom Pixel on Click
    def highlight(self, event):
        """
        highlight the pixel with red color
        :param event: Double mouse click on a pixel
        """
        # get Dimensions
        w = self.ui.label_phantom.geometry().width()
        h = self.ui.label_phantom.geometry().height()
        self.phantomSize = int(self.ui.comboBox_size.currentText())
        # adjust Highlighted Pixel Size
        scaleX = self.phantomSize / w
        scaleY = self.phantomSize / h
        self.x = int(np.floor(event.pos().x() * scaleX))
        self.y = int(np.floor(event.pos().y() * scaleY))
        # Create a Pen To draw the Highlighted area with
        self.ui.label_phantom.setPixmap(QPixmap(self.img))
        canvas = QPixmap(self.img)
        paint = QtGui.QPainter()
        paint.begin(canvas)
        self.getInfo()
        # set rectangle color and thickness
        pen = QtGui.QPen(QtCore.Qt.red)
        pen.setWidthF(0.9)
        paint.setPen(pen)
        # draw rectangle on canvas
        rect = QtCore.QRectF(self.x, self.y, 1, 1)
        paint.drawRect(rect)
        # update Widget To Show Phantom with Highlighted area
        paint.end()
        self.ui.label_phantom.setPixmap(canvas)

    #
    def browse(self):
        """
        load a JSON file Sequence
        """
        # Open Browse Window & Check
        fileName, _ = QtWidgets.QFileDialog.getOpenFileName(self, "Open json", (QtCore.QDir.currentPath()),
                                                            "json (*.json)")
        if fileName:
            # Check extension
            try:
                with open(fileName) as user_file:
                    seq = user_file.read()
                # Extract Sequence Data
                seq = json.loads(seq)
                rf = seq["Rf"]
                gx = seq["Gx"]
                gy = seq["Gy"]
                gz = seq["Gz"]
                ro = seq["Ro"]
                self.TR = seq["TR"]
                self.TE = seq["TE"]
                self.FA = seq["FA"]
                self.sequence_ref_line["RF"].setData(rf["x"], rf["y"])
                self.sequence_ref_line["Gz"].setData(gz["x"], gz["y"])
                self.sequence_ref_line["Gy"].setData(gy["x"], gy["y"])
                self.sequence_ref_line["Gx"].setData(gx["x"], gx["y"])
                self.sequence_ref_line["Ro"].setData(ro["x"], ro["y"])
                self.sequence_ref_line["TR"].setPos(self.TR)
                self.sequence_ref_line["TE"].setPos(self.TE)

            except (IOError, SyntaxError):
                self.error_dialog.showMessage("Only json supported")

    def phantomSizeChanged(self):
        """
        Change Phantom With new Size
        """
        size = self.ui.comboBox_size.currentText()
        self.phantom_ndarray = getPhantom(size)
        # rebuild phantom with the new size
        self.oimg = getPhantom(size)
        self.reader = qimage2ndarray.array2qimage(getPhantom(size))
        self.ui.slider_brightness.setValue(0)
        self.ui.lable_brightness.setText('0')
        self.setPhantomImage(getPhantom(size))
        self.weights()

    def setPhantomImage(self, img):
        """
        Add new sized phantom to widget
        :param img: 2d array
        """
        self.img = qimage2ndarray.array2qimage(img)
        self.ui.label_phantom.setPixmap(QPixmap(self.img))

    def setReconsImage(self, img):
        """
        add reconstructed image to widget
        :param img: 2d array
        """
        self.recons_img = qimage2ndarray.array2qimage(img)
        self.ui.label_recons_img.setPixmap(QPixmap(self.recons_img))

    def setKspaceimg(self, img):
        """
        add data to Kspace widget
        :param img: 2d array
        """
        # update widget in real time
        QtCore.QCoreApplication.processEvents()
        shape = np.shape(img)
        shape = shape[0]
        for i in range(shape):
            for j in range(shape):
                if (img[i][j] == 0):
                    img[i][j] = 10 ** -10
        self.kspace_img = qimage2ndarray.array2qimage(20 * (np.log(np.abs(img))))
        self.ui.label_kspace.setPixmap(QPixmap(self.kspace_img))

    def getColors(self):
        """
        get the color of the current phantom
        :return: colors of the phantom
        """
        x = self.img.width()
        y = self.img.height()
        colors = [[0 for i in range(x)] for j in range(y)]
        for i in range(y):
            for j in range(x):
                colors[i][j] = qRed(self.img.pixel(j, i))

        return colors

    def adjustBrightness(self):
        """
        update brightness values of phantom
        """
        self.brightness = self.ui.slider_brightness.value()
        self.ui.lable_brightness.setText(str(self.brightness))
        self.adjusted = self.weighted + self.brightness
        self.adjusted = np.clip(self.adjusted, 0, 255)
        self.setPhantomImage(self.adjusted)

    def weights(self):
        """
        update phantom with new color values of selected Weight

        """
        weight = self.ui.comboBox_weights.currentText()
        self.ui.slider_brightness.setValue(0)
        self.ui.lable_brightness.setText('0')
        # clear old weights
        self.setPhantomImage(self.oimg)
        imageData = self.getColors()
        # get Weighted phantom
        if weight == 'T2':
            self.weighted = np.abs(np.add(imageData, -255))
            self.setPhantomImage(self.weighted)
        elif weight == 'PD':
            self.weighted = np.abs(np.multiply(np.add(imageData, -255), 0.5))
            self.setPhantomImage(self.weighted)
        else:
            self.weighted = self.oimg

    def getInfo(self):
        """
        get Tissue Property on Click
        """
        pixelData = qRed(self.reader.pixel(self.x, self.y))
        # get property from map and update corresponding widget
        if pixelData == 255:
            self.ui.label_T1.setText(self.map['fat']['t1'])
            self.ui.label_T2.setText(self.map['fat']['t2'])
            self.ui.label_PD.setText(self.map['fat']['pd'])
        elif pixelData == 101 or pixelData == 76 or pixelData == 25:
            self.ui.label_T1.setText(self.map['muscle']['t1'])
            self.ui.label_T2.setText(self.map['muscle']['t2'])
            self.ui.label_PD.setText(self.map['muscle']['pd'])
        elif pixelData == 50:
            self.ui.label_T1.setText(self.map['grayMatter']['t1'])
            self.ui.label_T2.setText(self.map['grayMatter']['t2'])
            self.ui.label_PD.setText(self.map['grayMatter']['pd'])
        else:
            self.ui.label_T1.setText(self.map['csf']['t1'])
            self.ui.label_T2.setText(self.map['csf']['t2'])
            self.ui.label_PD.setText(self.map['csf']['pd'])


def main():
    app = QtWidgets.QApplication(sys.argv)
    # setup stylesheet
    apply_stylesheet(app, theme='dark_teal.xml')
    application = ApplicationWindow()
    application.show()
    app.exec_()


if __name__ == "__main__":
    main()
