import json
import logging as log
import sys
import warnings

import qimage2ndarray
from PyQt5 import QtWidgets, QtCore, QtGui
from PyQt5.QtGui import QPixmap, qRed
from qt_material import apply_stylesheet

from gui import Ui_MainWindow
from scripts.helper import getPhantom, reconstructImage
from scripts.plot import *

warnings.filterwarnings("error")
log.basicConfig(filename='mainLogs.log', filemode='w', format='%(asctime)s - %(message)s', datefmt='%d-%b-%y %H:%M:%S')


class ApplicationWindow(QtWidgets.QMainWindow):
    def __init__(self):
        super(ApplicationWindow, self).__init__()
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)

        # Event Listeners
        self.ui.comboBox_seq_pulse.currentTextChanged.connect(lambda: self.sequance_changed())
        self.ui.comboBox_prep_pulse.currentTextChanged.connect(lambda: self.prep_changed())

        self.ui.actionOpen.triggered.connect(lambda: self.browse())
        self.ui.actionSave_as.triggered.connect(lambda: self.save_Seq())
        self.ui.comboBox_size.currentIndexChanged.connect(lambda: self.phantomSizeChanged())
        self.ui.btn_start_sequance.clicked.connect(lambda: self.start_sequence())
        self.ui.comboBox_weights.currentIndexChanged.connect(lambda: self.weights())
        self.ui.label_phantom.setMouseTracking(False)
        self.ui.label_phantom.mouseDoubleClickEvent = self.highlight
        self.ui.label_phantom.mouseMoveEvent = self.adjustContrastAndBrightness
        self.ui.spinbox_FA.setValue(10)
        self.ui.spinbox_TE.setValue(10)
        self.ui.spinbox_TR.setValue(1000)
        self.ui.spinbox_FA.setMaximum(180)
        self.ui.spinbox_FA.setSingleStep(10)
        self.ui.spinbox_TE.setSingleStep(5)
        self.ui.spinbox_TR.setSingleStep(50)
        pg.setConfigOptions(antialias=True)
        self.ui.label_phantom.setScaledContents(True)

        self.error_dialog = QtWidgets.QErrorMessage()

        # ----- Variable Initialization ------ #
        # Plot
        self.seqplot = self.ui.plotwidget_sequance
        # image
        self.img = None
        self.brightness = 1
        self.contrast = 1.0
        self.oldY = None
        self.oldX = None
        # Tissue Property Weighted Image
        self.weighted = None
        # Tissue Property Info Image
        self.reader = None

        self.TR = 1000
        self.TE = 10
        self.FA = 10


        # Tissue Properties

        self.map = {
            "csf": {
                "t1": "4000",
                "t2": "200",
                "pd": "1",
            },
            "grayMatter": {
                "t1": "900",
                "t2": "90",
                "pd": "0.69",
            },
            "muscle": {
                "t1": "900",
                "t2": "50",
                "pd": "0.72",
            },
            "fat": {
                "t1": "250",
                "t2": "70",
                "pd": "0.61",
            },
        }

        self.GRID_OFFSET = {
            "Rf": 1820,
            "Gz": 1410,
            "Gy": 1000,
            "Gx": 590,
        }

        # Set Data Ref

        self.seqDataRef = {
            "FA": 90,
            "TR": 100,
            "TE": 30
        }
        self.prepDataRef = {
            "Title": "T1-Prep",
            "FA": 180,
        }
        self.synthDataRef = {
            "FA": 90,
            "TR": 100,
            "TE": 30
        }
        self.customLoaded = {
            "FA": 0,
            "TR": 0,
            "TE": 0
        }
        # Set sequence Synthesiser reference lines
        self.synthLineRef = {
            "RF": pg.PlotItem,
            "Gz": pg.PlotItem,
            "Gy": pg.PlotItem,
            "Gx": pg.PlotItem,
            "Ro": pg.PlotItem,
            "TR": pg.InfiniteLine,
            "TE": pg.InfiniteLine,
            "FA": None
        }
        self.seqLineRef = {
            "RF": pg.PlotItem,
            "Gz": pg.PlotItem,
            "Gy": pg.PlotItem,
            "Gx": pg.PlotItem,
            "Ro": pg.PlotItem,
            "TR": pg.InfiniteLine,
            "TE": pg.InfiniteLine,
            "FA": None
        }
        self.prepLineRef = {
            "RF": pg.PlotItem,
            "Gz": pg.PlotItem,
            "Gy": pg.PlotItem,
            "Gx": pg.PlotItem,
            "Ro": pg.PlotItem,
            "TR": pg.InfiniteLine,
            "TE": pg.InfiniteLine,
            "FA": None
        }

        # initialize plot widgets

        init_plot(self.ui.plotwidget_sequance, self.seqLineRef, "seq")
        init_plot(self.ui.plotwidget_prep, self.prepLineRef, "prep")
        init_plot(self.ui.plotwidget_synth, self.synthLineRef, "seq")
        #
        plot_simple_seq(self, self.seqLineRef, self.seqDataRef)
        plot_simple_seq(self, self.synthLineRef, self.synthDataRef)
        #

        plot_t1_prep(self, self.prepLineRef, self.prepDataRef)

        #
        self.phantomSizeChanged()

        self.ui.spinbox_FA.valueChanged.connect(lambda: self.set_FA())
        self.ui.spinbox_TR.valueChanged.connect(lambda: self.set_TR())
        self.ui.spinbox_TE.valueChanged.connect(lambda: self.set_TE())

    def prep_changed(self):
        sequance = self.ui.comboBox_prep_pulse.currentText()
        if sequance == "T1 Prep.":
            plot_t1_prep(self, self.prepLineRef, self.prepDataRef)
        elif sequance == "T2 Prep.":
            plot_t2_prep(self, self.prepLineRef, self.prepDataRef)
        elif sequance == "Tagging":
            plot_tagging_prep(self, self.prepLineRef, self.prepDataRef)

    def set_TR(self):
        """
        update TR line value
        """
        val = self.ui.spinbox_TR.value()

        self.synthDataRef["TR"] = val
        self.synthLineRef["TR"].setPos(val)


    def set_TE(self):
        """
        update TE line value
        """
        val = self.ui.spinbox_TE.value()

        self.synthDataRef["TE"] = val
        self.synthLineRef["TE"].setPos(val)


    def set_FA(self):
        """
        update Flip angle line value
        """
        val = self.ui.spinbox_FA.value()

        self.synthDataRef["FA"] = val
        self.synthLineRef["FA"].setLabel(axis="top", text=f"FA = {val}")


    def save_Seq(self):
        """
        Saving The Sequence as JSON File
        """
        seq = {
            "FA": self.synthDataRef["FA"],
            "TR": self.synthDataRef["TR"],
            "TE": self.synthDataRef["TE"],
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

    def sequance_changed(self):
        sequance = self.ui.comboBox_seq_pulse.currentText()
        if (sequance == "FA:90, TR: 100, TE:70"):
            self.seqDataRef["TR"] = 100
            self.seqDataRef["TE"] = 70
            self.seqDataRef["FA"] = 90
            self.seqLineRef["TR"].setPos(100)
            self.seqLineRef["TE"].setPos(70)
            self.seqLineRef["FA"].setLabel(axis="top", text=f"FA = {90}")
        elif (sequance == "FA:180, TR: 100, TE:70"):
            self.seqDataRef["TR"] = 100
            self.seqDataRef["TE"] = 70
            self.seqDataRef["FA"] = 180
            self.seqLineRef["TR"].setPos(100)
            self.seqLineRef["TE"].setPos(70)
            self.seqLineRef["FA"].setLabel(axis="top", text=f"FA = {180}")
        elif (sequance == "FA:120, TR: 100, TE:70"):
            self.seqDataRef["TR"] = 100
            self.seqDataRef["TE"] = 70
            self.seqDataRef["FA"] = 120
            self.seqLineRef["TR"].setPos(100)
            self.seqLineRef["TE"].setPos(70)
            self.seqLineRef["FA"].setLabel(axis="top", text=f"FA = {120}")
        elif (sequance == "Custom"):

            self.seqDataRef["TR"] = self.customLoaded["TR"]
            self.seqDataRef["TE"] = self.customLoaded["TE"]
            self.seqDataRef["FA"] = self.customLoaded["FA"]
            self.seqLineRef["TR"].setPos(self.customLoaded["TR"])
            self.seqLineRef["TE"].setPos(self.customLoaded["TE"])
            self.seqLineRef["FA"].setLabel(axis="top", text=f"FA = {self.customLoaded['TE']}")

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
                self.customLoaded = json.loads(seq)
                self.ui.comboBox_seq_pulse.setCurrentIndex(3)
            except (IOError, SyntaxError):
                self.error_dialog.showMessage("Only json supported")

    def phantomSizeChanged(self):
        """
        Change Phantom With new Size
        """
        size = int(self.ui.comboBox_size.currentText())
        self.T1 = np.zeros((size, size))
        self.T2 = np.zeros((size, size))
        self.setPhantomImage(getPhantom(size))
        self.getProperties()
        self.phantom_ndarray = getPhantom(size)
        # rebuild phantom with the new size
        self.oimg = getPhantom(size)
        self.reader = qimage2ndarray.array2qimage(getPhantom(size))

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
        if self.ui.comboBox_viewer.currentIndex() == 0:
            self.ui.label_img1.setPixmap(QPixmap(self.recons_img))
        else:
            self.ui.label_img2.setPixmap(QPixmap(self.recons_img))

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

        if self.ui.comboBox_viewer.currentIndex() == 0:
            self.ui.label_kspace1.setPixmap(QPixmap(self.kspace_img))
        else:
            self.ui.label_kspace2.setPixmap(QPixmap(self.kspace_img))

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

    def adjustContrastAndBrightness(self, event):
        maxContrast = 2
        minContrast = 0.1
        maxBrightness = 100
        minBrightness = -100
        displacement = 10

        if self.oldX is None:
            self.oldX = event.pos().x()
        if self.oldY is None:
            self.oldY = event.pos().y()
            return

        newX = event.pos().x()
        if newX - displacement > self.oldX:
            self.contrast += 0.05
        elif newX < self.oldX - displacement:
            self.contrast -= 0.05

        newY = event.pos().y()
        if newY - displacement > self.oldY:
            self.brightness += 5
        elif newY < self.oldY - displacement:
            self.brightness -= 5

        # Check for Limits
        if self.contrast > maxContrast:
            self.contrast = maxContrast
        elif self.contrast < minContrast:
            self.contrast = minContrast
        if self.brightness > maxBrightness:
            self.brightness = maxBrightness
        elif self.brightness < minBrightness:
            self.brightness = minBrightness

        self.adjusted = np.add(self.weighted, -127)
        self.adjusted = np.multiply(self.adjusted, self.contrast)
        self.adjusted = np.add(self.adjusted, 127)
        self.adjusted = np.clip(self.adjusted, 0, 255)

        self.adjusted = self.adjusted + self.brightness
        self.adjusted = np.clip(self.adjusted, 0, 255)

        np.round(self.adjusted)
        self.setPhantomImage(self.adjusted)

        self.oldY = newY
        self.oldX = newX

    def weights(self):
        """
        update phantom with new color values of selected Weight

        """
        weight = self.ui.comboBox_weights.currentText()
        # clear old weights
        self.setPhantomImage(self.oimg)
        imageData = self.getColors()
        # get Weighted phantom
        if weight == 'T2':
            self.FA = 12
            self.ui.spinbox_FA.setValue(12)
            self.weighted = np.abs(np.add(imageData, -255))
            self.setPhantomImage(self.weighted)
        elif weight == 'PD':
            self.ui.spinbox_FA.setValue(12)
            self.FA = 12
            self.weighted = np.abs(np.multiply(np.add(imageData, -255), 0.5))
            self.setPhantomImage(self.weighted)
        else:
            self.ui.spinbox_FA.setValue(28)
            self.FA = 28
            self.weighted = self.oimg

    def getInfo(self):
        """
        get Tissue Property on Click
        """
        pixelData = qRed(self.reader.pixel(self.x, self.y))
        # get property from map and update corresponding widget
        if pixelData == 255:
            self.ui.label_T1.setText(self.map['fat']['t1'] + "ms")
            self.ui.label_T2.setText(self.map['fat']['t2'] + "ms")
            self.ui.label_PD.setText(self.map['fat']['pd'])
        elif pixelData == 101 or pixelData == 76 or pixelData == 25:
            self.ui.label_T1.setText(self.map['muscle']['t1'] + "ms")
            self.ui.label_T2.setText(self.map['muscle']['t2'] + "ms")
            self.ui.label_PD.setText(self.map['muscle']['pd'])
        elif pixelData == 50:
            self.ui.label_T1.setText(self.map['grayMatter']['t1'] + "ms")
            self.ui.label_T2.setText(self.map['grayMatter']['t2'] + "ms")
            self.ui.label_PD.setText(self.map['grayMatter']['pd'])
        else:
            self.ui.label_T1.setText(self.map['csf']['t1'] + "ms")
            self.ui.label_T2.setText(self.map['csf']['t2'] + "ms")
            self.ui.label_PD.setText(self.map['csf']['pd'])

    def getProperties(self):
        pixelData = self.getColors()
        for i in range(len(pixelData)):
            for j in range(len(pixelData)):
                if pixelData[i][j] == 255:
                    self.T1[i][j] = self.map['fat']['t1']
                    self.T2[i][j] = self.map['fat']['t2']
                elif pixelData[i][j] == 101 or pixelData == 76 or pixelData == 25:
                    self.T1[i][j] = self.map['muscle']['t1']
                    self.T2[i][j] = self.map['muscle']['t2']
                elif pixelData[i][j] == 50:
                    self.T1[i][j] = self.map['grayMatter']['t1']
                    self.T2[i][j] = self.map['grayMatter']['t2']
                else:
                    self.T1[i][j] = self.map['csf']['t1']
                    self.T2[i][j] = self.map['csf']['t2']


def main():
    app = QtWidgets.QApplication(sys.argv)
    # setup stylesheet
    apply_stylesheet(app, theme='dark_teal.xml')
    application = ApplicationWindow()
    application.show()
    app.exec_()


if __name__ == "__main__":
    main()
