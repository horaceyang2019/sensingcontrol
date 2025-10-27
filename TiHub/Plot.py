# -*- coding: utf-8 -*-
"""
Created on Fri Aug 12 13:32:25 2022

@author: user
"""

import sys
import random
import matplotlib
matplotlib.use('Qt5Agg')
from PyQt5 import QtCore, QtWidgets
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
from PyQt5.QtGui import QIcon

# In[] set figure 
class MplCanvas(FigureCanvas):

    def __init__(self, parent = None, width = 10, height = 8, dpi = 80):        
        fig = Figure(figsize = (width, height), dpi = dpi)
        self.axes_x = fig.add_subplot(311)
        self.axes_y = fig.add_subplot(312)
        self.axes_z = fig.add_subplot(313)
        self.axes_x.set_ylabel('X_G')
        self.axes_y.set_ylabel('Y_G')
        self.axes_z.set_ylabel('Z_G')
        
        super(MplCanvas, self).__init__(fig)
        
# In[]
class PlotMainWindow(QtWidgets.QMainWindow):

    def __init__(self, *args, **kwargs):
        super(PlotMainWindow, self).__init__(*args, **kwargs)
        
        self.canvas = MplCanvas(self, width = 10, height = 8, dpi = 80)
        self.setCentralWidget(self.canvas)
        self.setWindowTitle('Real Time Graphics')
        self.setWindowIcon(QIcon('./Logo/NKUST.png'))  
        
        n_data = 160
        self.xdata = list(range(n_data))
        self.ydata = [random.randint(0, 16) for i in range(n_data)]

        self.x_plot_ref = None
        self.y_plot_ref = None
        self.z_plot_ref = None
        
        self.Update_Plot()
        self.show()

        self.timer = QtCore.QTimer()
        self.timer.setInterval(100)
        self.timer.timeout.connect(self.Update_Plot)
        self.timer.start()
        
    def Update_Plot(self):
        # Drop off the first y element, append a new one.
        self.ydata = self.ydata[1:] + [random.randint(0, 16)]

        # Note: we no longer need to clear the axis.
        if self.x_plot_ref is None:
            x_plot_refs = self.canvas.axes_x.plot(self.xdata, self.ydata, 'b')
            y_plot_refs = self.canvas.axes_y.plot(self.xdata, self.ydata, 'b')
            z_plot_refs = self.canvas.axes_z.plot(self.xdata, self.ydata, 'b')
            
            self.x_plot_ref = x_plot_refs[0]
            self.y_plot_ref = y_plot_refs[0]
            self.z_plot_ref = z_plot_refs[0]
            
        else:
            self.x_plot_ref.set_ydata(self.ydata)
            self.y_plot_ref.set_ydata(self.ydata)
            self.z_plot_ref.set_ydata(self.ydata)

        # Trigger the canvas to update and redraw.
        self.canvas.draw()
    
    def closeEvent(self, close_event):
        reply = QtWidgets.QMessageBox.question(self, 'Warning', "Do you want to close the window？",
                                               QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No,
                                               QtWidgets.QMessageBox.No)
        if reply == QtWidgets.QMessageBox.Yes:
            close_event.accept()
        else:
            close_event.ignore() 

# In[]        
if __name__ == "__main__":
  
    app = QtWidgets.QApplication(sys.argv)
    w = PlotMainWindow()
    w.show()



        