# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'TiHub.ui'
#
# Created by: PyQt5 UI code generator 5.9.2
#
# WARNING! All changes made in this file will be lost!

from PyQt5 import QtCore, QtGui, QtWidgets

class Ui_MainWindow(object):
    def setupUi(self, MainWindow):
        MainWindow.setObjectName("MainWindow")
        MainWindow.resize(418, 266)
        font = QtGui.QFont()
        font.setFamily("Times New Roman")
        MainWindow.setFont(font)
        self.centralwidget = QtWidgets.QWidget(MainWindow)
        self.centralwidget.setObjectName("centralwidget")
        self.SavePath = QtWidgets.QToolButton(self.centralwidget)
        self.SavePath.setGeometry(QtCore.QRect(30, 70, 81, 41))
        font = QtGui.QFont()
        font.setFamily("Times New Roman")
        self.SavePath.setFont(font)
        self.SavePath.setObjectName("SavePath")
        self.SaveFIlePath = QtWidgets.QTextBrowser(self.centralwidget)
        self.SaveFIlePath.setGeometry(QtCore.QRect(130, 70, 256, 31))
        self.SaveFIlePath.setObjectName("SaveFIlePath")
        self.Start = QtWidgets.QPushButton(self.centralwidget)
        self.Start.setGeometry(QtCore.QRect(30, 120, 81, 41))
        font = QtGui.QFont()
        font.setFamily("Times New Roman")
        self.Start.setFont(font)
        self.Start.setObjectName("Start")
        self.Rate = QtWidgets.QComboBox(self.centralwidget)
        self.Rate.setGeometry(QtCore.QRect(150, 30, 121, 20))
        self.Rate.setObjectName("Rate")
        self.State = QtWidgets.QTextBrowser(self.centralwidget)
        self.State.setGeometry(QtCore.QRect(130, 120, 256, 91))
        self.State.setObjectName("State")
        self.SamepleFrequency = QtWidgets.QLabel(self.centralwidget)
        self.SamepleFrequency.setGeometry(QtCore.QRect(30, 20, 101, 39))
        font = QtGui.QFont()
        font.setFamily("Times New Roman")
        self.SamepleFrequency.setFont(font)
        self.SamepleFrequency.setObjectName("SamepleFrequency")
        self.Stop = QtWidgets.QPushButton(self.centralwidget)
        self.Stop.setGeometry(QtCore.QRect(30, 170, 81, 41))
        font = QtGui.QFont()
        font.setFamily("Times New Roman")
        self.Stop.setFont(font)
        self.Stop.setObjectName("Stop")
        self.SetRegister = QtWidgets.QToolButton(self.centralwidget)
        self.SetRegister.setGeometry(QtCore.QRect(290, 20, 71, 41))
        font = QtGui.QFont()
        font.setFamily("Times New Roman")
        self.SetRegister.setFont(font)
        self.SetRegister.setObjectName("SetRegister")
        MainWindow.setCentralWidget(self.centralwidget)
        self.menubar = QtWidgets.QMenuBar(MainWindow)
        self.menubar.setGeometry(QtCore.QRect(0, 0, 418, 21))
        self.menubar.setObjectName("menubar")
        MainWindow.setMenuBar(self.menubar)
        self.statusbar = QtWidgets.QStatusBar(MainWindow)
        self.statusbar.setObjectName("statusbar")
        MainWindow.setStatusBar(self.statusbar)

        self.retranslateUi(MainWindow)
        QtCore.QMetaObject.connectSlotsByName(MainWindow)

    def retranslateUi(self, MainWindow):
        _translate = QtCore.QCoreApplication.translate
        MainWindow.setWindowTitle(_translate("MainWindow", "MainWindow"))
        self.SavePath.setText(_translate("MainWindow", "Save Path"))
        self.Start.setText(_translate("MainWindow", "Start"))
        self.SamepleFrequency.setText(_translate("MainWindow", "Sameple_Frequency"))
        self.Stop.setText(_translate("MainWindow", "Stop"))
        self.SetRegister.setText(_translate("MainWindow", "Set Register"))






