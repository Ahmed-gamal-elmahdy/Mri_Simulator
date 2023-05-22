import numpy as np
import pyqtgraph as pg


def init_plot(plotWidget, lineRef, pulseType):
    """
    Setup limits & axes for plot
    """
    plotWidget.setYRange(-50, 2000)
    plotWidget.addLegend(offset=(1, 0))
    plotWidget.hideAxis("left")
    # RF
    pen = pg.mkPen(color=(255, 0, 0))
    name = "RF"
    lineRef["RF"] = plotWidget.plot([0, 0], pen=pen, name=name)
    # Gz
    pen = pg.mkPen(color=(0, 255, 0))
    name = "Gz(SL)"
    lineRef["Gz"] = plotWidget.plot([0, 0], pen=pen, name=name)
    # Gx
    pen = pg.mkPen(color=(255, 255, 0))
    name = "Gx(Phase)"
    lineRef["Gx"] = plotWidget.plot([0, 0], pen=pen, name=name)
    # Gy
    pen = pg.mkPen(color=(255, 0, 255))
    name = "Gy(Freq)"
    lineRef["Gy"] = plotWidget.plot([0, 0], pen=pen, name=name)
    # readout
    pen = pg.mkPen(color=(0, 255, 255))
    name = "Readout"
    lineRef["Ro"] = plotWidget.plot([0, 0], pen=pen, name=name)
    if (pulseType != "prep"):
        # TR
        pen = pg.mkPen(color=(226, 135, 67))
        name = "TR"
        lineRef["TR"] = pg.InfiniteLine(pos=200, angle=90, pen=pen, label=name, name=name)
        plotWidget.addItem(lineRef["TR"])
        # TE
        pen = pg.mkPen(color=(128, 0, 128))
        name = "TE"
        lineRef["TE"] = pg.InfiniteLine(pos=50, angle=90, pen=pen, label=name, name=name)
        plotWidget.addItem(lineRef["TE"])

    # settings
    plotWidget.setLimits(xMin=0, xMax=5000, yMin=-50, yMax=2000)
    p1 = plotWidget.plotItem
    p1.setLabel('bottom', 'Time', units='s', color='g', **{'font-size': '12pt'})
    p1.getAxis('bottom').setPen(pg.mkPen(color='g', width=3))

    lineRef["FA"] = plotWidget.plotItem
    lineRef["FA"].setLabel('top', 'FA = ', color='g', **{'font-size': '12pt'})
    lineRef["FA"].getAxis('top').setPen(pg.mkPen(color='r', width=3))


def plot_simple_seq(self, lineRef, dataRef):
    """
    Plot a template sequence
    """
    scale=1
    # RF
    duration = 20*scale
    x = np.arange(0, duration, 0.1)
    y = np.sinc(x - 10) * 90 + self.GRID_OFFSET["Rf"]
    lineRef["RF"].setData(x, y)
    # Gz
    duration = 20*scale
    x = np.array([0, duration, duration, 0, 0])
    y = np.array([0, 0, 100, 100, 0]) + self.GRID_OFFSET["Gz"]
    lineRef["Gz"].setData(x, y)
    # Gy
    duration = 10*scale
    x = np.array([0, duration, duration, 0, 0]) + 20
    x = np.concatenate((x, x))
    y = np.array([0, 0, 100, 100, 0]) + self.GRID_OFFSET["Gy"]
    y = np.concatenate((y, np.add(y, 100)))
    x = np.concatenate((x, np.array([0, duration, duration, 0, 0]) + 20))
    y = np.concatenate((y, np.array([0, 0, 100, 100, 0]) + 900))
    lineRef["Gy"].setData(x, y)
    # Gy
    duration = 20*scale
    x = np.array([0, duration, duration, 0, 0]) + 30
    y = np.array([0, 0, 100, 100, 0]) + self.GRID_OFFSET["Gx"]
    lineRef["Gx"].setData(x, y)
    # readout
    duration = 20*scale
    x = np.arange(0, duration, 0.1) + 50
    y = np.random.randint(0, 360, len(x))
    lineRef["Ro"].setData(x, y)
    # TE
    lineRef["TE"].setPos(60)
    dataRef["TE"] = 60
    # TR
    lineRef["TR"].setPos(90)
    dataRef["TR"] = 90


def plot_t1_prep(self, lineRef, dataRef):
    dataRef["Title"] = "T1-Prep"
    dataRef["FA"] = 180
    # RF
    duration = 20
    x = np.arange(0, duration, 0.1)
    y = np.sinc(x - 10) * dataRef["FA"] + self.GRID_OFFSET["Rf"]
    lineRef["RF"].setData(x, y)
    lineRef["FA"].setLabel(axis="top", text="FA = 180")
    lineRef["Gx"].setData([], [])


def plot_t2_prep(self, lineRef, dataRef):
    dataRef["Title"] = "T2-Prep"
    dataRef["FA"] = [90, -90]
    # RF
    duration = 20
    x1 = np.arange(0, duration, 0.1)
    y1 = np.sinc(x1 - 10) * 90 + self.GRID_OFFSET["Rf"]
    x2 = np.arange(0, duration, 0.1)
    y2 = np.sinc(x2 - 10) * -90 + self.GRID_OFFSET["Rf"]
    x2 = np.add(x2, 10 + duration)
    x = np.concatenate((x1, x2))
    y = np.concatenate((y1, y2))
    lineRef["RF"].setData(x, y)
    lineRef["FA"].setLabel(axis="top", text="FA = 90,-90")
    lineRef["Gx"].setData([], [])


def plot_tagging_prep(self, lineRef, dataRef):
    dataRef["Title"] = "Tagging-Prep"
    dataRef["FA"] = [90, -90]
    # RF
    duration = 20
    x1 = np.arange(0, duration, 0.1)
    y1 = np.sinc(x1 - 10) * 90 + self.GRID_OFFSET["Rf"]
    x2 = np.arange(0, duration, 0.1)
    y2 = np.sinc(x2 - 10) * -90 + self.GRID_OFFSET["Rf"]
    x2 = np.add(x2, 10 + duration)
    x = np.concatenate((x1, x2))
    y = np.concatenate((y1, y2))
    lineRef["RF"].setData(x, y)
    lineRef["FA"].setLabel(axis="top", text="FA = 90,-90")

    # Gy
    duration = 10
    x = np.array([0, duration, duration, 0, 0]) + 20
    y = np.array([0, 0, 100, 100, 0]) + self.GRID_OFFSET["Gx"]
    lineRef["Gx"].setData(x, y)
