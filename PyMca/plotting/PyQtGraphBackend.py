#/*##########################################################################
# Copyright (C) 2004-2014 European Synchrotron Radiation Facility
#
# This file is part of the PyMca X-ray Fluorescence Toolkit developed at
# the ESRF by the Software group.
#
# This file is free software; you can redistribute it and/or modify it
# under the terms of the GNU Lesser General Public License as published by the Free
# Software Foundation; either version 2 of the License, or (at your option)
# any later version.
#
# This file is distributed in the hope that it will be useful, but WITHOUT ANY
# WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS
# FOR A PARTICULAR PURPOSE.  See the GNU Lesser General Public License for more
# details.
#
#############################################################################*/
__author__ = "V.A. Sole - ESRF Data Analysis"
__license__ = "LGPL"
__doc__ = """
This module implements a PyQtGraph plotting backend.
"""
import sys
if ("pyqtgraph" not in sys.modules):
    import pyqtgraph as pg
    pg.setConfigOption('background', 'w')
    pg.setConfigOption('foreground', 'k')
    pg.setConfigOption('leftButtonPan', False)
else:
    import pyqtgraph as pg
from pyqtgraph.Qt import QtCore, QtGui
import PlotBackend
_USE_ORIGINAL = False
DEBUG = 0

class CustomViewBox(pg.ViewBox):
    def __init__(self, *args, **kwds):
        pg.ViewBox.__init__(self, *args, **kwds)
        self.setMouseMode(self.RectMode)
        
    ## reimplement right-click to zoom out
    def mouseClickEvent(self, ev):
        if ev.button() == QtCore.Qt.RightButton:
            if len(self.axHistory) > 1:
                del self.axHistory[-1]
                self.setRange(self.axHistory[-1])
            else:
                self.autoRange()
            #setXRange
            #setYRange
            #setRange
            
    def mouseDragEvent(self, ev):
        if ev.button() == QtCore.Qt.RightButton:
            ev.ignore()
        else:
            pg.ViewBox.mouseDragEvent(self, ev)

    def autoRange(self):
        """
        Adjust scales and reset the zoom stack
        """
        self.axHistory = []
        pg.ViewBox.autoRange(self)

class InfiniteLine(pg.InfiniteLine):
    def mouseClickEvent(self, ev):
        if ev.button() == QtCore.Qt.LeftButton:
            if hasattr(self, "_plot1d_options"):
                if "selectable" in self._plot1d_options:
                    ev.accept()
                    self.moving = False
                    self.sigPositionChangeFinished.emit(self)
                    return
        pg.InfiniteLine.mouseClickEvent(self, ev)

    def mouseDragEvent(self, ev):
        if hasattr(self, "_plot1d_options"):
            if "selectable" in self._plot1d_options:
                ev.ignore()
                return
        pg.InfiniteLine.mouseDragEvent(self, ev)

    def setMouseHover(self, hover):
        if hasattr(self, "_plot1d_options"):
            if "selectable" in self._plot1d_options:
                if hover != self.mouseHovering:                    
                    if hover:
                        self._oldCursorShape = self.cursor().shape()
                        self.setCursor(QtGui.QCursor(QtCore.Qt.PointingHandCursor))
                    else:
                        self.setCursor(QtGui.QCursor(self._oldCursorShape))
            elif "draggable" in self._plot1d_options:
                oldShape = self.cursor().shape()
                if oldShape not in [QtCore.Qt.SizeHorCursor,
                                    QtCore.Qt.SizeVerCursor,
                                    QtCore.Qt.PointingHandCursor,
                                    QtCore.Qt.OpenHandCursor,
                                    QtCore.Qt.SizeAllCursor]:
                    self._originalCursorShape = oldShape
                if hover:
                    oldShape = self.cursor().shape()
                    if 'xmarker' in self._plot1d_options:
                        shape = QtCore.Qt.SizeHorCursor
                    elif 'ymarker' in self._plot1d_options:
                        shape = QtCore.Qt.SizeVerCursor
                    else:
                        shape = QtCore.Qt.OpenHandCursor
                    if oldShape != shape:
                        self.setCursor(QtGui.QCursor(shape))
                else:
                    self.setCursor(QtGui.QCursor(self._originalCursorShape))
        pg.InfiniteLine.setMouseHover(self, hover)

class PlotCurveItem(pg.PlotCurveItem):
    def mouseClickEvent(self, ev):
        if not self.clickable or ev.button() == QtCore.Qt.MiddleButton:
            return
        ev.accept()
        if ev.button() == QtCore.Qt.RightButton:
            button = "right"
        else:
            button = "left"
        ddict = {}
        if ev.double():
            ddict["event"] = "curveDoubleClicked"
        else:
            ddict["event"] = "curveClicked"
        ddict["type"] = "curve"
        ddict["button"] = button
        #print dir(ev)
        pos = ev.pos()
        ddict["x"] = pos.x()
        ddict["y"] = pos.y()
        pos = ev.screenPos()
        #pos = ev.scenePos()
        ddict["xpixel"] = pos.x()
        ddict["ypixel"] = pos.y()
        ddict["item"] = self
        ev.accept()
        self.sigClicked.emit(ddict)

class ScatterPlotItem(pg.ScatterPlotItem):
    def mouseClickEvent(self, ev):
        if ev.button() == QtCore.Qt.MiddleButton:
            ev.ignore()
            return
        if ev.button() == QtCore.Qt.RightButton:
            button = "right"
        else:
            button = "left"        
        if ev.button() == QtCore.Qt.LeftButton:
            pts = self.pointsAt(ev.pos())
            if len(pts) > 0:
                self.ptsClicked = pts
                ev.accept()
                ddict = {}
                if ev.double():
                    ddict["event"] = "curveDoubleClicked"
                else:
                    ddict["event"] = "curveClicked"
                #ddict["type"] = "scatterCurve"
                ddict["type"] = "scatter"
                ddict["button"] = button
                pos = ev.pos()
                ddict["x"] = pos.x()
                ddict["y"] = pos.y()
                pos = ev.screenPos()
                #pos = ev.scenePos()
                ddict["xpixel"] = pos.x()
                ddict["ypixel"] = pos.y()
                ddict["item"] = self
                ddict["xdata"] = [a.pos().x() for a in self.ptsClicked]
                ddict["ydata"] = [a.pos().y() for a in self.ptsClicked]
                self.sigClicked.emit(self, ddict)
            else:
                # should one ignore the event or say the number of points is 0?
                if DEBUG:
                    print("no spots")
                ev.ignore()
        else:
            ev.ignore()

class PlotDataItem(pg.PlotDataItem):
    def __init__(self, *args, **kargs):
        pg.PlotDataItem.__init__(self, *args, **kargs)
        self.curve.sigClicked.disconnect()
        self.scatter.sigClicked.disconnect()
        #self.removeItem(self.curve)
        #self.removeItem(self.scatter)
        self.clear()
        self.curve = PlotCurveItem()
        self.scatter = ScatterPlotItem()
        self.curve.setParentItem(self)
        self.scatter.setParentItem(self)
        self.curve.sigClicked.connect(self.curveClicked)
        self.scatter.sigClicked.connect(self.scatterClicked)
        if len(args):
            self.setData(*args, **kargs)

    def curveClicked(self, ddict=None):
        if self._plot1d_info['linewidth'] > 0:
            ddict["item"] = self
            self.sigClicked.emit(ddict)
        elif DEBUG:
            print("Ignoring due to linewidth")

    def scatterClicked(self, curve, ddict):
        ddict["item"] = self
        self.sigClicked.emit(ddict)

class PyQtGraphBackend(PlotBackend.PlotBackend, pg.PlotWidget):
    def __init__(self, parent=None, enableMenu=False, **kw):
        if 'viewBox' in kw:
            vb = kw['viewBox']
            del kw['viewBox']
        else:
           vb = CustomViewBox()
        pg.PlotWidget.__init__(self, parent, viewBox=vb,
                                   enableMenu=enableMenu, **kw)
        PlotBackend.PlotBackend.__init__(self, parent)

        self.setMouseTracking(True)

        #increase from default of 2
        self.scene().setClickRadius(5)

        # this only sends the position in pixel coordenates
        self.scene().sigMouseMoved.connect(self._mouseMoved)

        self._oldActiveCurve = None
        self._oldActiveCurveLegend = None
        self._logX = False
        self._logY = False
        self._imageItem = None
        if 0:
            import numpy
            x = numpy.arange(10000*200.)
            x.shape = 200, 10000
            self.invertY(True)
            self._imageItem = pg.ImageItem(image=x)
            self._imageItem.setZValue(0)
            #self._imageItem.setCompositionMode(QtGui.QPainter.CompositionMode_Multiply)
            self.addItem(self._imageItem)
        

    def _mouseMoved(self, pos):
        if self.sceneBoundingRect().contains(pos):
            mousePoint = self.getViewBox().mapSceneToView(pos)
            x = mousePoint.x()
            y = mousePoint.y()
            ddict = {}
            ddict["event"] = "MouseAt"
            ddict['x'] = x
            ddict['y'] = y
            ddict["xpixel"] = pos.x()
            ddict["ypixel"] = pos.y()
            self._callback(ddict)
                
    def addCurve(self, x, y, legend=None, info=None, replace=False, replot=True, **kw):
        """
        Add the 1D curve given by x an y to the graph.
        :param x: The data corresponding to the x axis
        :type x: list or numpy.ndarray
        :param y: The data corresponding to the y axis
        :type y: list or numpy.ndarray
        :param legend: The legend to be associated to the curve
        :type legend: string or None
        :param info: Dictionary of information associated to the curve
        :type info: dict or None
        :param replace: Flag to indicate if already existing curves are to be deleted
        :type replace: boolean default False
        :param replot: Flag to indicate plot is to be immediately updated
        :type replot: boolean default True
        :returns: The legend/handle used by the backend to univocally access it.
        """
        if info is None:
            info = {}
        color = info.get('plot_color', '#000000')
        symbol = info.get('plot_symbol', None)
        brush = color
        style = info.get('plot_line_style', '-')
        linewidth = 1
        """
        Better control instantiating a curve item and a scatter item
        because mouse coordenates are not emitted and right click is not
        handled.
        """
        if style in [None, " "]:
            #pen = QtCore.Qt.NoPen
            pen = QtGui.QPen(QtCore.Qt.NoPen)
            linewidth = 0
        elif style == "--":
            pen = QtGui.QPen(QtCore.Qt.DashLine)
            pen.setColor(QtGui.QColor(color))
            #pen.setWidth(linewidth)
        elif style in ["-.", ".-"]:
            pen = QtGui.QPen(QtCore.Qt.DashDotLine)
            pen.setColor(QtGui.QColor(color))
            #pen.setWidth(linewidth)
        elif style in ["-..", "..-"]:
            pen = QtGui.QPen(QtCore.Qt.DashDotDotLine)
            pen.setColor(QtGui.QColor(color))
            #pen.setWidth(linewidth)
        elif style in ["..", ":"]:
            pen = QtGui.QPen(QtCore.Qt.DotLine)
            pen.setColor(QtGui.QColor(color))
            #pen.setWidth(linewidth)
        else:
            pen = QtGui.QPen(QtCore.Qt.SolidLine)
            pen.setColor(QtGui.QColor(color))
            #pen.setWidth(linewidth)
        if _USE_ORIGINAL:
            item = self.plot(x, y, title=legend,
                             pen=pen,
                             symbol=symbol,
                             #symbolPen=color,
                             shadowPen=None,
                             symbolBrush=color,
                             clickable=True)
        else:
            item = PlotDataItem()
            item.setData(x, y, title=legend,
                         pen=pen,
                         symbol=symbol,
                         #symbolPen=color,
                         shadowPen=None,
                         symbolBrush=color,
                         clickable=True)
            self.addItem(item)
        if style in [None, " "]:
            item.curve.clickable = False
        else:
            item.curve.clickable = True
        item._plot1d_info = {'color':color,
                             'linewidth':linewidth,
                             'brush':brush,
                             'style':style,
                             'symbol':symbol,
                             'label':legend,
                             'type':'curve'}
        item.setZValue(10)
        item.curve.setClickable(True)
        item.sigClicked.connect(self._curveClicked)
        #both work, perhaps legend is safer?
        #return legend
        return item

    def addImage(self, data, legend=None, info=None,
                    replace=True, replot=True,
                    xScale=None, yScale=None, z=0, **kw):
        """
        :param data: (nrows, ncolumns) data or (nrows, ncolumns, RGBA) ubyte array 
        :type data: numpy.ndarray
        :param legend: The legend to be associated to the curve
        :type legend: string or None
        :param info: Dictionary of information associated to the image
        :type info: dict or None
        :param replace: Flag to indicate if already existing images are to be deleted
        :type replace: boolean default True
        :param replot: Flag to indicate plot is to be immediately updated
        :type replot: boolean default True
        :param xScale: Two floats defining the x scale
        :type xScale: list or numpy.ndarray
        :param yScale: Two floats defining the y scale
        :type yScale: list or numpy.ndarray
        :param z: level at which the image is to be located (to allow overlays).
        :type z: A number bigger than or equal to zero (default)  
        :returns: The legend/handle used by the backend to univocally access it.
        """
        item = pg.ImageItem(image=data)
        item.setZValue(z)
        #self._imageItem.setCompositionMode(QtGui.QPainter.CompositionMode_Multiply)
        if xScale is None:
            xScale = [0.0, 1.0]
        if yScale is None:
            yScale = [0.0, 1.0]
        item._plot1d_info = {'label':legend,
                             'type':'image',
                             'xScale':xScale,
                             'yScale':yScale,
                             'z':z}
        self.addItem(item)
        if replot:
            self.replot()

    def removeCurve(self, handle, replot=True):
        if hasattr(handle, '_plot1d_info'):
            actualHandle = handle
        else:
            # we have received a legend
            legend = handle
            actualHandle = None
            a = self.items()
            for item in a:
                if hasattr(item, '_plot1d_info'):
                    label = item._plot1d_info['label']
                    if label == legend:
                        actualHandle = item
                        break
        if actualHandle is not None:
            self.removeItem(actualHandle)
            if replot:
                self.replot()

    def setActiveCurve(self, legend, replot=True):
        if hasattr(legend, '_plot1d_info'):
            # we have received an actual item
            handle = legend
        else:
            # we have received a legend
            print("Received a legend")
            handle = None
            items = self.items()
            for item in items:
                if hasattr(item, '_plot1d_info'):
                    label = item._plot1d_info['label']
                    if label == legend:
                        handle = item
        #TODO: use setPen, setBrush, setSymbolPen, setSymbolBrush, setSymbol, ...
        if handle is not None:
            #print("handle found")
            color = '#000000'
            if handle._plot1d_info['linewidth'] > 0:
                handle.opts['pen'] = color
            handle.opts['symbolPen'] = color
            handle.opts['symbolBrush'] = color
            handle.updateItems()
        else:
            raise KeyError("Curve %s not found" % legend)
        if self._oldActiveCurve in self.items():
            #print("old still present")
            if self._oldActiveCurve._plot1d_info['label'] != legend:
                color = self._oldActiveCurve._plot1d_info['color']
            if self._oldActiveCurve._plot1d_info['linewidth'] > 0:
                self._oldActiveCurve.opts['pen'] = color
            self._oldActiveCurve.opts['symbolPen'] = color
            self._oldActiveCurve.opts['symbolBrush'] = color
            self._oldActiveCurve.updateItems()
        elif self._oldActiveCurveLegend is not None:
            #print("old legend", self._oldActiveCurveLegend)
            items = self.items()
            for item in items:
                if hasattr(item, '_plot1d_info'):
                    label = item._plot1d_info['label']
                    if label == self._oldActiveCurveLegend:
                        color = item._plot1d_info['color']
                        if item._plot1d_info['linewidth'] > 0:
                            item.opts['pen'] = color
                        item.opts['symbolPen'] = color
                        item.opts['symbolBrush'] = color
                        item.updateItems()
                        break
        self._oldActiveCurve = handle
        self._oldActiveCurveLegend = handle._plot1d_info['label']
        if replot:
            self.replot()

    def replot(self):
        """
        Update plot
        """
        pg.PlotWidget.update(self)
        return

    def clearCurves(self):
        """
        Clear all curves from the plot
        """
        #This removes also the markers
        #self.getPlotItem().clearPlots()
        itemList = self.items()
        for item in itemList:
            if hasattr(item, '_plot1d_info'):
                label = item._plot1d_info['label']
                if not label.startswith("__MARKER__"):
                    self.removeItem(item)

    def clear(self):
        """
        Clear all items from the plot
        """
        pg.PlotWidget.clearPlots()

    def resetZoom(self):
        """
        It should autoscale any axis that is in autoscale mode
        """
        xmin, xmax = self.getGraphXLimits()
        xAuto = self.isXAxisAutoScale() 
        yAuto = self.isYAxisAutoScale()
        if xAuto and yAuto:
            self.plotItem.autoRange()
        elif yAuto:
            xmin, xmax = self.getGraphXLimits()
            self.plotItem.autoRange()
            self.setGraphXLimits(xmin, xmax)
        elif xAuto:
            ymin, ymax = self.getGraphYLimits()
            self.plotItem.autoRange()
            self.setGraphYLimits(ymin, ymax)
        else:
            if DEBUG:
                print("Nothing to autoscale")
        self.replot()
        return

    #Graph related functions
    def setGraphTitle(self, title=""):
        self.setTitle(title)

    def setGraphXLabel(self, label="X"):
        self.setLabel('bottom', label)

    def setGraphYLabel(self, label="Y"):
        self.setLabel('left', label)
    
    def getGraphXLimits(self):
        """
        Get the graph X (bottom) limits.
        :return:  Minimum and maximum values of the X axis
        """
        rect = self.viewRect()
        return rect.left(), rect.right()

    def getGraphYLimits(self):
        """
        Get the graph Y (left) limits.
        :return:  Minimum and maximum values of the Y axis
        """
        rect = self.viewRect()
        return rect.bottom(), rect.top()

    def setGraphXLimits(self, xmin, xmax):
        self.setXRange(xmin, xmax, padding=0, update=False)

    def setGraphYLimits(self, ymin, ymax):
        self.setYRange(ymin, ymax, padding=0, update=False)

    def isXAxisAutoScale(self):
        if self._xAutoScale:
            return True
        else:
            return False

    def isYAxisAutoScale(self):
        if self._yAutoScale:
            return True
        else:
            return False

    def setXAxisAutoScale(self, flag=True):
        if flag:
            self._xAutoScale = True
        else:
            self._xAutoScale = False

    def setYAxisAutoScale(self, flag=True):
        if flag:
            self._yAutoScale = True
        else:
            self._yAutoScale = False

    def setXAxisLogarithmic(self, flag):
        if flag:
            self._logX = True
        else:
            self._logX = False
        self.setLogMode(self._logX, self._logY)

    def setYAxisLogarithmic(self, flag):
        if flag:
            self._logY = True
        else:
            self._logY = False
        self.setLogMode(self._logX, self._logY)

    def setLimits(self, xmin, xmax, ymin, ymax):
        self.setGraphXLimits(xmin, xmax)
        self.setGraphYLimits(ymin, ymax)

    # Marker handling
    def insertXMarker(self, x, label,
                      color='k', selectable=False, draggable=False,
                      **kw):
        """
        :param x: Horizontal position of the marker in graph coordenates
        :type x: float
        :param label: Legend associated to the marker
        :type label: string
        :param color: Color to be used for instance 'blue', 'b', '#FF0000'
        :type color: string, default 'k' (black)
        :param selectable: Flag to indicate if the marker can be selected
        :type selectable: boolean, default False
        :param draggable: Flag to indicate if the marker can be moved
        :type draggable: boolean, default False
        :return: Handle used by the backend to univocally access the marker
        """
        label = "__MARKER__" + label
        line = InfiniteLine(angle=90, movable=draggable)
        line.setPos(x)
        line.setY(1.)
        line._plot1d_info = {'label':label}
        line._plot1d_options = ["xmarker"]
        if selectable:
            line._plot1d_options.append('selectable')
        elif draggable:
            line._plot1d_options.append('draggable')
        if selectable or draggable:
            line.sigPositionChangeFinished.connect(self._xMarkerMoved)
        line.setZValue(10)
        self.addItem(line)
        return line
        
    def insertYMarker(self, y, label,
                      color='k', selectable=False, draggable=False,
                      **kw):
        """
        :param y: Vertical position of the marker in graph coordenates
        :type y: float
        :param label: Legend associated to the marker
        :type label: string
        :param color: Color to be used for instance 'blue', 'b', '#FF0000'
        :type color: string, default 'k' (black)
        :param selectable: Flag to indicate if the marker can be selected
        :type selectable: boolean, default False
        :param draggable: Flag to indicate if the marker can be moved
        :type draggable: boolean, default False
        :return: Handle used by the backend to univocally access the marker
        """
        label = "__MARKER__" + label
        line = InfiniteLine(angle=0, movable=draggable)
        line.setPos(y)
        line.setX(1.)
        line._plot1d_info = {'label':label}
        line._plot1d_options = ["ymarker"]
        if selectable:
            line._plot1d_options.append('selectable')
        elif draggable:
            line._plot1d_options.append('draggable')
        if selectable or draggable:
            line.sigPositionChangeFinished.connect(self._yMarkerMoved)
        line.setZValue(10)
        self.addItem(line)
        return line

    def insertMarker(self, x, y, label, **kw):
        print("Plot1DBackend insertMarker not implemented")

    def invertYAxis(self, flag=True):
        if flag:
            self.invertY(True)
        else:
            self.invertY(False)

    def _xMarkerMoved(self, item):
        label = item._plot1d_info['label']
        ddict = {}
        ddict['event'] = "markerMoved"
        ddict['label'] = item._plot1d_info['label'][10:]
        ddict['type'] = 'marker'
        if 'draggable' in item._plot1d_options:
            ddict['draggable'] = True
        else:
            ddict['draggable'] = False
        if 'selectable' in item._plot1d_options:
            ddict['selectable'] = True
            ddict['event'] = "markerSelected"
        else:
            ddict['selectable'] = False
        # use this and not the current mouse position because
        # it has to agree with the marker position
        ddict['x'] = item.getXPos()
        ddict['y'] = 1.0
        #ddict['xdata'] = artist.get_xdata()
        #ddict['ydata'] = artist.get_ydata()
        self._callback(ddict)

    def _yMarkerMoved(self, item):
        label = item._plot1d_info['label']
        ddict = {}
        ddict['event'] = "markerMoved"
        ddict['label'] = item._plot1d_info['label'][10:]
        ddict['type'] = 'marker'
        if 'draggable' in item._plot1d_options:
            ddict['draggable'] = True
        else:
            ddict['draggable'] = False
        if 'selectable' in item._plot1d_options:
            ddict['selectable'] = True
            ddict['event'] = "markerSelected"
        else:
            ddict['selectable'] = False
        # use this and not the current mouse position because
        # it has to agree with the marker position
        ddict['x'] = 1.0
        ddict['y'] = item.getYPos()
        #ddict['xdata'] = artist.get_xdata()
        #ddict['ydata'] = artist.get_ydata()
        self._callback(ddict)

    if _USE_ORIGINAL:
        def _curveClicked(self, item):
            label = item._plot1d_info['label']
            ddict = {}
            ddict['event'] = "curveClicked"
            ddict['button'] = 'left'
            ddict['label'] = label
            ddict['type'] = 'curve'
            self._callback(ddict)
    else:
        def _curveClicked(self, ddict0):
            item = ddict0['item']
            label = item._plot1d_info['label']
            ddict = {}
            ddict['event'] = "curveClicked"
            ddict['button'] = 'left'
            ddict['label'] = label
            ddict['type'] = 'curve'
            self._callback(ddict)
            

def main():
    import numpy
    x = numpy.arange(100.)
    y = x * x
    import Plot1D
    plot = Plot1D.Plot1D(backend=PyQtGraphBackend)
    plot.addCurve(x, y, "dummy")
    plot.addCurve(x + 100, -x * x)
    print("Active curve = ", plot.getActiveCurve())
    print("X Limits = ", plot.getGraphXLimits())
    print("Y Limits = ", plot.getGraphYLimits())
    print("All curves = ", plot.getAllCurves())
    plot.insertXMarker(50., draggable=True)
    data = numpy.arange(1000.*1000)
    data.shape = 1000,1000
    plot.addImage(data, "image")
    return plot

if __name__ == "__main__":
    import numpy
    app = QtGui.QApplication([])
    w = main()
    w.widget.show()
    #w.invertYAxis(True)
    #w.invertYAxis(False)
    app.exec_()
