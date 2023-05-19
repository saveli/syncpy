# -*- coding: utf-8 -*-

### This file was generated for use with the Syncpy library.
### Copyright 2022, ISIR / Universite Pierre et Marie Curie (UPMC)
### syncpy@isir.upmc.fr
###
### Main contributor(s): Philippe Gauthier
###
### This software is a computer program whose for investigating
### synchrony in a fast and exhaustive way.
###
### This software is governed by the CeCILL-B license under French law
### and abiding by the rules of distribution of free software.  You
### can use, modify and/ or redistribute the software under the terms
### of the CeCILL-B license as circulated by CEA, CNRS and INRIA at the
### following URL "http://www.cecill.info".

### As a counterpart to the access to the source code and rights to
### copy, modify and redistribute granted by the license, users are
### provided only with a limited warranty and the software's author,
### the holder of the economic rights, and the successive licensors
### have only limited liability.
###
### In this respect, the user's attention is drawn to the risks
### associated with loading, using, modifying and/or developing or
### reproducing the software by the user in light of its specific
### status of free software, that may mean that it is complicated to
### manipulate, and that also therefore means that it is reserved for
### developers and experienced professionals having in-depth computer
### knowledge. Users are therefore encouraged to load and test the
### software's suitability as regards their requirements in conditions
### enabling the security of their systems and/or data to be ensured
### and, more generally, to use and operate it in the same conditions
### as regards security.
###
### The fact that you are presently reading this means that you have
### had knowledge of the CeCILL-B license and that you accept its terms.

import io
import json
import os
import subprocess
import sys
import time
import urllib.request, urllib.error, urllib.parse
from urllib.request import urlopen
import zipfile
import distutils.core
import shutil
import ssl
import requests
from PyQt5.QtGui import QIcon, QStandardItemModel, QStandardItem, QPixmap

sys.path.insert(0, '.')
sys.path.insert(0, 'Methods')

from PyQt5 import QtCore, QtGui, uic
from PyQt5.QtCore import pyqtSlot
from PyQt5.QtWidgets import QApplication, QStyle, QFileDialog, QMainWindow, QDialog, QDesktopWidget, QMessageBox, \
    QTableWidgetItem, QComboBox, QTreeWidgetItem, QProgressBar, QLabel, QMenu

#from src import Method
import matplotlib
matplotlib.use('Qt5Agg')
from ui.HeaderFileWizard import HeaderFileWizard
from ui.MethodWidget import MethodWidget
from ui.OutLog import OutLog
from ui.Tools import Tools
from ui.SyncpyAbout import SyncpyAbout

import matplotlib.pyplot as plot
import pandas as pd
import webbrowser
from scipy.io import loadmat
from collections import OrderedDict

import configparser

from Methods.utils.ExtractSignal import ExtractSignalFromCSV
from Methods.utils.ExtractSignal import ExtractSignalFromMAT

try:
    _fromUtf8 = QtCore.QString.fromUtf8
except AttributeError:
    def _fromUtf8(s):
        return s

try:
    _encoding = QApplication.UnicodeUTF8
    def _translate(context, text, disambig):
        return QApplication.translate(context, text, disambig, _encoding)
except AttributeError:
    def _translate(context, text, disambig):
        return QApplication.translate(context, text, disambig)


# Main Window Class
class SyncPy2(QMainWindow):
    COLOR_GREY = QtGui.QColor(200, 200, 200)

    def __init__(self):
        QDialog.__init__(self)
        geo = QDesktopWidget().availableGeometry()
        self.maxHeight = geo.height() - 100
        self.maxWidth = geo.width() - 50

        self.sessionHasBeenLoaded = False
        self.lastSavedSessionFilename = ""
        self.selectedDirectory = ""
        self.outputDirectory = ""
        self.methodUsed = ""
        self.columnSeparator = ","
        self.signalsHeader = []
        self.filesSelected = []
        self.nFilesSelected = 0
        self.signalsSelected = []
        self.nSignalsSelected = 0
        self.signalsRefreshed = False
        self.signals = []
        self.dataFiles = []
        self.recreateMethodList = False
        self.firstFile = ""
        self.filesHasHeaders = False
        self.outputBaseName = None


        self.syncpyplatform = ""
        self.plotImgPath = ""
        self.headerMap = OrderedDict()
        if sys.platform == 'darwin':
            os.system("export LC_ALL=en_US.UTF-8")
            os.system("export LANG=en_US.UTF-8")
            self.syncpyplatform = "m"
        elif sys.platform == 'win32':
            self.syncpyplatform = "w"
        elif sys.platform == 'linux2':
            self.syncpyplatform = "u"

        #load config file
        self.config = configparser.RawConfigParser()
        self.config.read('conf.ini')
        self.appVersion = self.getFromConfig('app.version')
        self.appName = self.getFromConfig('app.name')
        self.syncpyver = self.getFromConfig('sessionVersion')
        self.lastUpdate = self.getFromConfig('lastUpdate')

        self.plotImgPath = self.getFromConfig("plotImgPath")

        self.ui = uic.loadUi(self.getFromConfig("uiFile"), self)
        QtCore.QMetaObject.connectSlotsByName(self)

        table = self.ui.inputSignalsWidget
        table.setColumnCount(3)
        headers = []
        headers.append("Name")
        headers.append("Type")
        headers.append("Plot")
        table.setHorizontalHeaderLabels(headers)

        # --------- Add standards icons to main button ---------
        self.ui.startPushButton.setEnabled(False)
        self.ui.stopPushButton.setEnabled(False)
        self.ui.startPushButton.setIcon(self.style().standardIcon(QStyle.SP_CommandLink))
        self.ui.stopPushButton.setIcon(self.style().standardIcon(QStyle.SP_BrowserStop))
        self.ui.openOutputPushButton.setIcon(self.style().standardIcon(QStyle.SP_DirIcon))
        self.ui.headerWizardButton.setIcon(self.style().standardIcon(QStyle.SP_FileDialogContentsView))

        # --------- redirect outputs to log widget ---------
        sys.stdout = OutLog(self.ui.outputPrintEdit, sys.stdout)
        sys.stderr = OutLog(self.ui.outputPrintEdit, sys.stderr, QtCore.Qt.red)

        # --------- Add Method widget ---------
        self.ui.methodWidget = MethodWidget(self.ui.methodsArgsGroupBox)

        # --------- Events connections ---------
        self.ui.methodsTreeWidget.itemPressed.connect(self.treeItemSelected)
        self.ui.openOutputPushButton.clicked.connect(self.openOutputFolder)
        self.ui.plotSignalsButton.clicked.connect(self.plotSignals)
        self.ui.startPushButton.clicked.connect(self.computeBtnEvent)
        self.ui.stopPushButton.clicked.connect(self.ui.methodWidget.stopComputeProcess)
        self.ui.actionSaveSession.triggered.connect(self.saveSession)
        self.ui.actionGIT.triggered.connect(self.openGIT)
        self.ui.actionAbout.triggered.connect(self.openAbout)
        self.ui.actionUpdate.triggered.connect(self.checkUpdates)
        self.ui.actionSaveSessionOver.triggered.connect(self.resaveSession)
        self.ui.actionLoadSession.triggered.connect(self.loadSession)
        self.ui.clearLogPushButton.clicked.connect(self.clearLogBtnEvent)
        self.ui.inputFolderToolButton.clicked.connect(self.setInputFolder)
        self.ui.outputFolderToolButton.clicked.connect(self.outputFolderButtonEvent)
        self.ui.toolBox.currentChanged.connect(self.changeSelectedTab)
        self.ui.headerWizardButton.clicked.connect(self.headerWizardEvent)
        self.ui.exportSignalsButton.clicked.connect(self.exportSelectedSignals)

        self.ui.inputSignalsWidget.cellPressed.connect(self.checkSignalItemFromCellClick)
        # right click menu on toolbox
        self.ui.inputFileslistView.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
        self.ui.inputFileslistView.customContextMenuRequested.connect(self.openMenuToolbox)

        self.ui.inputSignalsWidget.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
        self.ui.inputSignalsWidget.customContextMenuRequested.connect(self.openMenuToolbox)


        self.ui.methodWidget.computationFinished.connect(self.enableButtons)

        self.ui.show()
        self.ui.toolBox.setCurrentIndex(0)
        self.warnForGoingBack(False)

        self.showStatus("{0} (v {1}) successfully loaded".format(self.appName, self.appVersion))

        #To-Do finish implementing Tools.plotSignals()
        self.ui.signalsStackedCheckBox.hide()

    def showStatus(self, msg):
        self.ui.statusbar.showMessage(msg)

    def getFromConfig(self, attribute):
        return self.config.get(self.__class__.__name__, attribute)

    def closeEvent(self, event):
        plot.close("all")
        event.accept()

    @pyqtSlot()
    def openGIT(self):
        webbrowser.open(self.getFromConfig('github'))

    @pyqtSlot()
    def openAbout(self):
        SyncpyAbout(self, self.config, self.__class__.__name__).open()

    @pyqtSlot()
    def openMenuToolbox(self, position):
        #if method tab, drop
        if self.ui.toolBox.currentIndex() == 2:
            return

        # Create a menu
        menu = QMenu("Menu", self)
        menu.addAction("Check All", self.selectAll)
        menu.addAction("Uncheck All", self.unselectAll)
        # Show the context menu.
        menu.exec_(self.ui.toolBox.mapToGlobal(position))

    @pyqtSlot(QTreeWidgetItem, int)
    def treeItemSelected(self, item, idx):
        fullPath = item.text(1)
        if fullPath != '':
            self.ui.methodWidget.clearArgumentList()
            self.methodUsed = fullPath
            self.ui.methodDescriptionTextEdit.setPlainText(self.ui.methodWidget.populateArguments(str(fullPath)))
            self.ui.startPushButton.setEnabled(True)

    @pyqtSlot()
    def computeBtnEvent(self):
        # load selected signals from selected files
        self.signals = []
        self.outputBaseName = None
        ismat = False
        dic = self.ui.methodWidget.getArgumentsAsDictionary()
        if not("ignoreInputSignals" in dic and dic["ignoreInputSignals"]):
            for f in self.filesSelected:
                if f.endswith('.mat'):
                    matfile = loadmat(f)
                    ismat = True
                for s in self.signalsSelected:
                    if not ismat:
                        if not self.filesHasHeaders:
                            self.signals.append(ExtractSignalFromCSV(str(f), separator=self.columnSeparator, unit='ms', columns=s, header=False, headerValues=self.signalsHeader))
                        else:
                            self.signals.append(ExtractSignalFromCSV(str(f), separator=self.columnSeparator, unit='ms', columns=[str(self.headerMap[s])]))
                    else:
                        ci = self.signalsHeader.index(s)
                        cn = str(self.signalsHeader[ci])
                        self.signals.append(ExtractSignalFromMAT(str(f), columns_index=ci, columns_wanted_names=[cn], matfile=matfile))

        self.ui.methodWidget.compute(self.signals, self.getOutputBasename())

        self.ui.stopPushButton.setEnabled(True)
        self.ui.startPushButton.setEnabled(False)
        self.ui.toolBox.setEnabled(False)

        self.showStatus("Computing...")

    def loadSignal(self, file, name):
        signal = None
        ismat = False
        if file.endswith('.mat'):
            matfile = loadmat(file)
            ismat = True

        if not ismat:
            if not self.filesHasHeaders:
                signal = ExtractSignalFromCSV(str(file), separator=self.columnSeparator, unit='ms', columns=name,
                                              header=False,
                                              headerValues=self.signalsHeader)
            else:
                signal = ExtractSignalFromCSV(str(file), separator=self.columnSeparator, unit='ms',
                                              columns=[str(self.headerMap[name])])
        else:
            ci = self.signalsHeader.index(name)
            cn = str(self.signalsHeader[ci])
            signal = ExtractSignalFromMAT(str(file), columns_index=ci, columns_wanted_names=[cn],
                                          matfile=matfile)
        return signal

    @pyqtSlot()
    def plotSignals(self):
        files = self.getSelectedFiles()
        names = self.getSignalsToPlot()
        if self.ui.signalsStackedCheckBox.isChecked():
            signals = []
            for f in self.getSelectedFiles():
                for name in names:
                    signal = self.loadSignal(f, name)
                    signals.append(signal)
            Tools.plotSignals(signals, files, names)
        else:
            for f in files:
                for s in names:
                    signal = self.loadSignal(f, s)
                    Tools.plotOneSignal(signal, s, f)

    @pyqtSlot()
    def clearLogBtnEvent(self):
        self.ui.outputPrintEdit.clear()

    @pyqtSlot()
    def enableButtons(self):
        self.ui.stopPushButton.setEnabled(False)
        self.ui.startPushButton.setEnabled(True)
        self.ui.toolBox.setEnabled(True)
        self.saveOutputsToFile()
        self.showStatus("")

    @pyqtSlot()
    def setSignalsRefreshed(self):
        self.signalsRefreshed = True

    @pyqtSlot()
    def headerWizardEvent(self):
        self.firstFile = None
        model = self.ui.inputFileslistView.model()
        if model is None:
            return
        for index in range(0, model.rowCount()):
            item = model.item(index)
            if item.checkState() == QtCore.Qt.Checked:
                self.firstFile = self.selectedDirectory + '/' + item.text()
                break

        if self.firstFile is None:
            return

        isHeaderInFile = self.filesHasHeaders
        headerWizardDialog = HeaderFileWizard(self, str(self.firstFile), self.config, self.signalsHeader, isHeaderInFile)
        if headerWizardDialog.exec_() == QDialog.Accepted:
            self.signalsHeader = headerWizardDialog.getHeaders()
            self.filesHasHeaders = headerWizardDialog.hasHeaders()

            if not headerWizardDialog.isMatFile:
                self.columnSeparator = headerWizardDialog.separator
                self.headerMap = headerWizardDialog.getHeaderMap()

            table = self.ui.inputSignalsWidget

            # timeFound = False
            # for h in self.signalsHeader:
            #     if "time" in h.lower():
            #         timeFound = True
            #
            # if not timeFound:
            #     print "Error: No Time data in input file"
            #     return
            #
            # table.setRowCount(len(self.signalsHeader)-1)
            table.setRowCount(len(self.signalsHeader))

            # add signals header to the view
            if len(self.signalsHeader) > 0:
                i = 0
                for h in self.signalsHeader:
                    self.setSignalItem(table, i, h, "", False, False)
                    i += 1
                self.showStatus("Signals loaded.")

    @pyqtSlot()
    def outputFolderButtonEvent(self):
        self.outputDirectory = os.path.relpath(str(QFileDialog.getExistingDirectory(self, "Select Output Directory")))
        self.ui.outputFolderText.setPlainText(self.outputDirectory)

    @pyqtSlot()
    def setInputFolder(self):
        # if load session, load data folder
        if self.sessionHasBeenLoaded:
            self.selectedDirectory = self.loadedSession["InputFolder"]
            self.outputDirectory = self.loadedSession["OutputDirectory"]
            self.columnSeparator = str(self.loadedSession["ColumnSeparator"])
        else:
            dir = QFileDialog.getExistingDirectory(self, "Select Directory")
            if dir:
                self.selectedDirectory = os.path.relpath(str(dir))

        if not self.selectedDirectory:
            return

        if not self.outputDirectory:
            self.outputDirectory = self.selectedDirectory

        self.ui.outputFolderText.setPlainText(self.outputDirectory)

        self.dataFiles = []
        self.dataFiles += [os.path.join(self.selectedDirectory, f)
                           for f in os.listdir(self.selectedDirectory)
                           if f.endswith('.csv') or f.endswith('.mat') or f.endswith('.tsv')]
        dataNames = []
        dataNames += [f for f in os.listdir(self.selectedDirectory) if f.endswith('.csv') or f.endswith('.mat') or f.endswith('.tsv')]
        model = QStandardItemModel(self.ui.inputFileslistView)
        for f in dataNames:
            item = QStandardItem(f)
            item.setCheckable(True)
            item.setEditable(False)
            model.appendRow(item)
        self.ui.inputFileslistView.setModel(model)

        # if load session check files used last time
        if self.sessionHasBeenLoaded:
            self.filesSelected = []
            for i in range(0,len(dataNames)):
                for lf in self.loadedSession["Files"]:
                    fname = os.path.basename(lf)
                    if dataNames[i] == fname:
                        item = model.item(i)
                        item.setCheckState(2)
                        self.filesSelected.append(self.dataFiles[i])

        self.clearSignals()
        self.sessionHasBeenLoaded = False

    @pyqtSlot()
    def openOutputFolder(self):
        if not self.outputDirectory:
            return

        outFolder = self.outputDirectory
        if self.syncpyplatform == "m":
            subprocess.call(['open', outFolder])
        elif self.syncpyplatform == "w":
            subprocess.call(['explorer', outFolder])
        else:
            subprocess.call(['xdg-open', outFolder])

    #0 unchecked, 2 checked
    def setItemsCheckState(self, state):
        if self.ui.toolBox.currentIndex() == 0:
            self.clearSignals()
            self.sessionHasBeenLoaded = False
            model = self.ui.inputFileslistView.model()
            if model is None:
                return
            for index in range(model.rowCount()):
                item = model.item(index)
                item.setCheckState(state)

        if self.ui.toolBox.currentIndex() == 1:
            table = self.ui.inputSignalsWidget
            col = table.currentColumn()
            for i in range(0, table.rowCount()):
                item = table.item(i, col)
                item.setCheckState(state)

    @pyqtSlot()
    def selectAll(self):
        self.setItemsCheckState(2)

    @pyqtSlot()
    def unselectAll(self):
        self.setItemsCheckState(0)

    @pyqtSlot(int, int)
    def checkSignalItemFromCellClick(self, row, col):
        if self.ui.toolBox.currentIndex() == 1:
            table = self.ui.inputSignalsWidget
            item = table.item(row, col)
            if item.background() != SyncPy2.COLOR_GREY:
                item.setCheckState(QtCore.Qt.Unchecked if item.checkState() == QtCore.Qt.Checked else QtCore.Qt.Checked)

    def warnForGoingBack(self, warn):
        self.ui.warningWidget.setVisible(warn)

    @pyqtSlot()
    def changeSelectedTab(self):
        if self.ui.toolBox.currentIndex() == 0:
            self.ui.startPushButton.setEnabled(False)
            self.ui.stopPushButton.setEnabled(False)

            oldNSignals = self.nSignalsSelected
            if oldNSignals == 0 and len(self.getSelectedSignals()) != 0:
                self.warnForGoingBack(True)
            elif len(self.getSelectedSignals()) == oldNSignals and len(self.getSelectedFiles()) > 0 and len(self.getSelectedSignals()) > 0:
                self.warnForGoingBack(True)
            else:
                self.warnForGoingBack(False)
                self.recreateMethodList = True

        # --------- populate signals ----------
        if self.ui.toolBox.currentIndex() == 1:
            if len(self.getSelectedFiles()) == 0:
                self.showStatus("Select at least one input file first")
            self.ui.startPushButton.setEnabled(False)
            self.ui.stopPushButton.setEnabled(False)

            #if self.methodUsed != "":
            oldNSignals = self.nSignalsSelected
            if len(self.getSelectedSignals()) == oldNSignals and len(self.getSelectedFiles()) > 0 and len(self.getSelectedSignals()) > 0:
                self.warnForGoingBack(True)
            else:
                self.warnForGoingBack(False)
                self.recreateMethodList = True

            if len(self.signalsHeader) == 0:
                self.headerWizardEvent()

        # --------- populate Methods ----------
        if self.ui.toolBox.currentIndex() == 2:

            oldNSignals = self.nSignalsSelected
            if self.signalsRefreshed or len(self.getSelectedSignals()) != oldNSignals \
                    or self.sessionHasBeenLoaded:
                self.recreateMethodList = True

            if self.nSignalsSelected == 0:
                self.showStatus("Select at least one signal first")
            self.warnForGoingBack(False)

            if self.recreateMethodList:
                self.ui.methodDescriptionTextEdit.setPlainText("")
                self.ui.methodWidget.clearArgumentList()
                self.ui.methodsTreeWidget.clear()
                self.createMethodList()
                self.recreateMethodList = False
                #self.methodUsed = fullPath
                #self.ui.methodDescriptionTextEdit.setPlainText(self.ui.methodWidget.populateArguments(str(fullPath)))
            else:
                self.selectMethodInTree()

            self.signalsRefreshed = False

        self.sessionHasBeenLoaded = False

    def selectMethodInTree(self):
        self.outputBaseName = None
        methodList = self.ui.methodsTreeWidget.findItems(os.path.basename(str(self.methodUsed)),
                                                         QtCore.Qt.MatchRecursive | QtCore.Qt.MatchExactly)
        for m in methodList:
            if m.text(1) == self.methodUsed:
                self.ui.methodsTreeWidget.scrollToItem(methodList[0])
                m.setSelected(True)
                self.treeItemSelected(m,0)

    def getSelectedFiles(self):
        # number of files selected
        self.nFilesSelected = 0
        model = self.ui.inputFileslistView.model()
        if model is None:
            return []
        self.filesSelected = []
        for index in range(model.rowCount()):
            item = model.item(index)
            if item.checkState() == QtCore.Qt.Checked:
                self.filesSelected.append(self.dataFiles[index])
                self.nFilesSelected += 1
        return self.filesSelected

    def getSelectedSignals(self):
        # number of signals selected
        self.nSignalsSelected = 0
        self.typeSum = 0
        table = self.ui.inputSignalsWidget
        self.signalsSelected = []
        for index in range(table.rowCount()):
            item = table.item(index, 0)
            if item.checkState() == QtCore.Qt.Checked:
                self.signalsSelected.append(str(item.text()))
                self.nSignalsSelected += 1
                type = table.cellWidget(index, 1).currentText()
                if str(type) == "categorical":
                    self.typeSum += 1
        return self.signalsSelected

    def getSignalsToPlot(self):
        # number of signals selected
        table = self.ui.inputSignalsWidget

        signalsToPlot = []
        for index in range(table.rowCount()):
            item = table.item(index, 2)
            if item.checkState() == QtCore.Qt.Checked:
                label = table.item(index, 0)
                signalsToPlot.append(str(label.text()))
        return signalsToPlot

    @pyqtSlot()
    def resaveSession(self):
        if self.lastSavedSessionFilename:
            self.saveSession(self.lastSavedSessionFilename)

    @pyqtSlot()
    def saveSession(self, fname=None):
        if fname == None:
            fname = QFileDialog.getSaveFileName(self, "Save Session File", ".", "Session Files (*.session)")
            if self.syncpyplatform == "u":
                fname += ".session"
        if not fname:
            return

        self.ui.actionSaveSessionOver.setText("Save over '" + os.path.basename(str(fname)) + "'")
        session = {}

        session["SyncPyVer"] = self.syncpyver
        session["SyncPyPlat"] = self.syncpyplatform

        session["FileContainsHeader"] = self.filesHasHeaders
        session["InputFolder"] = self.selectedDirectory
        session["OutputDirectory"] = self.outputDirectory

        session["Files"] = []
        for f in self.getSelectedFiles():
            session["Files"].append(f)

        # saving signals

        session["HeaderMap"] = self.headerMap

        session["Signals"] = []
        table = self.ui.inputSignalsWidget
        for i in range(0, table.rowCount()):
            item = table.item(i, 0)
            checkState = item.checkState()
            type = table.cellWidget(i, 1).currentText()
            plotState = table.item(i, 2).checkState()
            session["Signals"].append({'label': str(item.text()),
                                       'type': str(type),
                                       'plotState': plotState,
                                       'checkState': checkState})

        session["Method"] = str(self.methodUsed)
        session["ColumnSeparator"] = str(self.columnSeparator)
        session["MethodArgs"] = self.ui.methodWidget.getArgumentsAsDictionary()
        if session["MethodArgs"]:
            for arg in session["MethodArgs"]:
                if isinstance(session["MethodArgs"][arg], io.IOBase):
                    session["MethodArgs"][arg] = str(session["MethodArgs"][arg].name)
        session["ToolBoxIndex"] = self.ui.toolBox.currentIndex()

        with open(fname, 'w') as f:
            json.dump(session, f, indent=4)
            self.lastSavedSessionFilename = fname
            self.ui.actionSaveSessionOver.setEnabled(True)
            f.close()

    @pyqtSlot()
    def loadSession(self):
        self.loadedSession = {}
        fname = QFileDialog.getOpenFileName(self,"Open Session File", ".", "Session Files (*.session)")
        if fname:
            with open(fname, 'r') as f:
                self.loadedSession = json.load(f, object_pairs_hook=OrderedDict)
                self.lastSavedSessionFilename = fname
                self.sessionHasBeenLoaded = True
                self.ui.actionSaveSessionOver.setEnabled(True)
                f.close()
        if not self.loadedSession:
            return

        if self.loadedSession["SyncPyVer"] != self.syncpyver:
            print(("Unable to load session, SyncPy version mismatch (session " + self.loadedSession[
                "SyncPyVer"] + " vs current " + self.syncpyver+")"))
            return

        if self.loadedSession["SyncPyPlat"] != self.syncpyplatform:
            message = "Unable to load session, SyncPy platform mismatch (session created on "
            if self.loadedSession["SyncPyPlat"] == "u":
                message += "Linux "
            elif self.loadedSession["SyncPyPlat"] == "w":
                message += "Windows "
            elif self.loadedSession["SyncPyPlat"] == "m":
                message += "Mac "
            message += "and current platform is "

            if self.syncpyplatform == "u":
                message += "Linux"
            elif self.syncpyplatform == "w":
                message += "Windows"
            elif self.syncpyplatform == "m":
                message += "Mac"

            message += ")"

            print(message)
            return

        self.ui.actionSaveSessionOver.setText("Save over '" + os.path.basename(str(fname)) + "'")

        #populate file list
        try:
            self.setInputFolder()
        except:
            print("Error loading session: Unable to find input files")
            self.sessionHasBeenLoaded = False
            self.ui.actionSaveSessionOver.setEnabled(False)
            return

        self.filesHasHeaders = self.loadedSession["FileContainsHeader"]

        #populate signal list
        self.signalsSelected = []
        table = self.ui.inputSignalsWidget
        table.setRowCount(len(self.loadedSession["Signals"]))
        i = 0

        for sig in self.loadedSession["Signals"]:
            self.setSignalItem(table, i, sig["label"], sig["type"], sig["checkState"], sig["plotState"])
            i += 1

        #populate method list

        self.ui.toolBox.setCurrentIndex(int(self.loadedSession["ToolBoxIndex"]))

        self.ui.methodsTreeWidget.clear()
        self.createMethodList()
        self.methodUsed = self.loadedSession["Method"]
        self.selectMethodInTree()

        self.ui.methodWidget.setArgumentsWithDictionary(self.loadedSession["MethodArgs"])

        self.headerMap = self.loadedSession["HeaderMap"]

        for i in range(0, len(self.headerMap)):
            self.signalsHeader.append(list(self.headerMap.keys())[i])

    def setSignalItem(self, table, index, label, type, checked, plotted):
        item = QTableWidgetItem(label)
        isTime = "time" in label.lower()
        if not isTime:
            item.setCheckState(checked)
            item.setFlags(QtCore.Qt.ItemIsEnabled | QtCore.Qt.ItemIsUserCheckable)
        else:
            item.setBackground(SyncPy2.COLOR_GREY)
        table.setItem(index, 0, item)
        combo = QComboBox()
        combo.addItem("continuous")
        if not isTime:
            combo.addItem("categorical")
            combo.currentIndexChanged.connect(self.setSignalsRefreshed)
        if type and combo.findText(type):
            combo.setCurrentIndex(combo.findText(type))

        table.setCellWidget(index, 1, combo)
        icon = QIcon(QPixmap(self.plotImgPath))
        item = QTableWidgetItem(icon, "")
        if not isTime:
            item.setCheckState(plotted)
            item.setFlags(QtCore.Qt.ItemIsEnabled | QtCore.Qt.ItemIsUserCheckable)
        else:
            item.setBackground(SyncPy2.COLOR_GREY)
        table.setItem(index, 2, item)

    def clearSignals(self):
            self.warnForGoingBack(False)
            self.methodUsed = ""
            model = self.ui.inputSignalsWidget.model()
            if model is not None:
                while model.rowCount() > 0:
                    model.removeRow(0)
            self.signalsHeader = []
            plot.close("all")

    def getOutputBasename(self):
        if self.outputBaseName==None:
            methodName = str(self.methodUsed).rsplit('/', 1)[1].rsplit('.', 1)[0]
            currDay = time.strftime("%Y%m%d")
            currTime = time.strftime("%H%M%S")
            outDirName = self.outputDirectory + '/syncpy_out-' + currDay
            if not (os.path.exists(outDirName)):
                os.mkdir(outDirName)
            self.outputBaseName = outDirName + '/' + currTime + '-' + methodName
        return self.outputBaseName

    def saveOutputsToFile(self):
        baseName = self.getOutputBasename()
        outFile = open(baseName+'-log.txt', 'w')

        outFile.write("Data files used:\n")
        for f in self.filesSelected:
            outFile.write("\t"+f+"\n")

        outFile.write("\n\nSignals used:\n")
        for s in self.signalsSelected:
            outFile.write("\t"+s+"\n")

        outFile.write("\n\nMethod used:\n")
        outFile.write("\t"+self.methodUsed+"\n")
        outFile.write("\n\nResults:\n")

        res = self.ui.methodWidget.getResult()
        outFile.write("\t" + str(res) + "\n")
        outFile.close()

        try:
            for i in plot.get_fignums():
                f = plot.figure(i)
                filename = baseName+"-Figure"+str(i)+".png"
                f.savefig(os.path.abspath(filename))
        except Exception as ex:
            print(f"Exception while saving plot to '{filename}'\n{ex.message}")

    def createMethodList(self):
        rootFolder = "Methods"

        # number of files selected
        self.getSelectedFiles()
        if self.nFilesSelected == 0:
            return

        # number of signals selected
        self.getSelectedSignals()
        if self.nSignalsSelected == 0:
            return

        onlyUtils = False
        # populate root folder
        if self.nFilesSelected == 1:
            if self.nSignalsSelected == 1:
                print("Error: No method available for one signal only")
                return
            elif self.nSignalsSelected == 2:
                rootFolder += "/DataFrom2Persons/Univariate"
            elif self.nSignalsSelected > 2:
                #ici on propose toutes les methodes et l'utilisateur doit choisir si uni ou multivariate
                rootFolder += ""
        elif self.nFilesSelected == 2:
            if self.nSignalsSelected == 1:
                rootFolder += "/DataFrom2Persons/Univariate"
            elif self.nSignalsSelected > 1:
                rootFolder += "/DataFrom2Persons/Multivariate"
        elif self.nFilesSelected > 2:
            if self.nSignalsSelected == 1:
                rootFolder += "/DataFromManyPersons/Univariate"
            elif self.nSignalsSelected > 1:
                rootFolder += "/DataFromManyPersons/Multivariate"

        if rootFolder.count('/') > 1:
            if self.typeSum == 0:
                rootFolder += "/Continuous"
            elif self.typeSum == self.nSignalsSelected:
                rootFolder += "/Categorical"

        rootItem = QTreeWidgetItem(self.ui.methodsTreeWidget, [rootFolder])
        self.loadMethodsFromFolder(rootFolder, rootItem)

    def loadMethodsFromFolder(self, curPath, tree):
        folderIcon = self.style().standardIcon(QStyle.SP_DirIcon)
        methodIcon = self.style().standardIcon(QStyle.SP_MediaPlay)
        excluded_chars = ('_', '.')
        for (path, subdirs, files) in os.walk(curPath, topdown=True):
            if curPath == path:
                for directory in subdirs:
                    if curPath == "Methods" and not(directory.startswith("Data")) or directory[0] in excluded_chars:
                        continue
                    item = QTreeWidgetItem(tree, [directory])
                    item.setIcon(0, folderIcon)
                    self.loadMethodsFromFolder(path + '/' + directory, item)

                for name in files:
                    if (not name.startswith("__")) and name.endswith(".py"):
                        methodName = name
                        item = QTreeWidgetItem(tree, [methodName])
                        #storing full path hidden for convenience
                        item.setText(1, curPath+'/'+methodName)
                        item.setIcon(0, methodIcon)

    def exportSelectedSignals(self):
        table = self.ui.inputSignalsWidget
        selectedSignalsHeader = []
        # give filename
        self.getSelectedFiles()

        firstTime = True

        fileNumber = 1

        for index in range(table.rowCount()):
            item = table.item(index, 0)
            ismat = False
            for f in self.getSelectedFiles():
                if f.endswith('.mat'):
                    matfile = loadmat(f)
                    ismat = True
                if item.checkState() == QtCore.Qt.Checked:
                    s = str(item.text())
                    if not ismat:
                        if not self.filesHasHeaders:
                            signal = ExtractSignalFromCSV(str(f), separator=self.columnSeparator, unit='ms', columns=s, header=False,
                                                     headerValues=self.signalsHeader)
                        else:
                            signal = ExtractSignalFromCSV(str(f), separator=self.columnSeparator, unit='ms', columns=[str(self.headerMap[s])])
                    else:
                        ci = self.signalsHeader.index(s)
                        cn = str(self.signalsHeader[ci])
                        signal = ExtractSignalFromMAT(str(f), columns_index=ci, columns_wanted_names=[cn], matfile=matfile)


                    if firstTime:
                        seletedSignals = pd.DataFrame(index=signal.index)
                        firstTime = False

                    #seletedSignals.insert(col,s,signal)
                    #col += 1
                    seletedSignals[s+str(fileNumber)] = signal
                    fileNumber += 1

        fileName = ''

        fileName = QFileDialog.getSaveFileName(self)

        if not fileName:
            print("Error export signals: No filename provided")
            return
        else:
            if not fileName.endsWith('.csv'):
                fileName = fileName+'.csv'
            seletedSignals.to_csv(path_or_buf=fileName,header=True,sep=';')

    @pyqtSlot()
    def checkUpdates(self):
        # get  last commit number
        context = ssl._create_unverified_context()
        url = 'https://api.github.com/repos/syncpy/SyncPy/commits?per_page=1'
        try:
            response = urlopen(url, timeout=2, context=context).read()
        except (urllib.error.HTTPError, urllib.error.URLError):
            QMessageBox.information(self, 'SyncPy Updater','Unable to reach the server, check your internet connexion.')
            return
            
        data = json.loads(response.decode())
        # if difference, ask for update
        if data[0]["sha"] != self.lastUpdate:
            updateMsg = "New update available, do you want to update now?"
            reply = QMessageBox.question(self, 'SyncPy Updater',
                             updateMsg, QMessageBox.Yes, QMessageBox.No)

            # download last git archive
            # extract it
            # copy files
            # update last update number
            # ask for restart syncpy
            if reply == QMessageBox.Yes:
                updateWindow = QDialog(self)
                updateWindow.setWindowTitle("SyncPy Updater")
                updateWindow.setFixedSize(350,75)
                pb = QProgressBar(updateWindow)
                pb.setTextVisible(False)
                pb.setGeometry(0, 0, 350, 25)
                pb.setRange(0, 100)
                pb.setProperty("value", 0)
                lb = QLabel(updateWindow)
                lb.setGeometry(0, 30, 350, 25)
                lb.setText("Downloading update...")
                updateWindow.show()
                updateWindow.setWindowModality(QtCore.Qt.ApplicationModal)
                updateWindow.setModal(True)
                
                url = "https://github.com/syncpy/SyncPy/archive/master.zip"
                file_name = url.split('/')[-1]
                r = requests.get(url)
                file_size = len(r.content)
                file_size_dl = 0
                with open(file_name, 'wb') as f:
                    for chunk in r.iter_content(chunk_size=512): 
                        if chunk: # filter out keep-alive new chunks
                            file_size_dl += 512
                            pb.setValue(file_size_dl * 100. / file_size)
                            QApplication.processEvents()
                            f.write(chunk)
                    f.close()
                
                lb.setText("Installing update...")
                
                zip_ref = zipfile.ZipFile(file_name, 'r')
                zip_ref.extractall("update")
                zip_ref.close()
                
                time.sleep(1)
                
                distutils.dir_util.copy_tree("update/SyncPy-master", "../")
                shutil.rmtree("update")
                os.remove("master.zip")
                
                self.config = configparser.RawConfigParser()
                self.config.read('conf.ini')
                self.config.set('SyncPy2','lastUpdate',data[0]["sha"])
                self.lastUpdate = data[0]["sha"]
                with open('conf.ini', 'w') as configfile:
                    self.config.write(configfile)
                                
                updateWindow.close()  

                QMessageBox.information(self, 'SyncPy Updater','Update complete, restart SyncPy to apply changes.')
        else:
            QMessageBox.information(self, 'SyncPy Updater','No update found')


if __name__ == "__main__":
    import sys
    # on Linux set X11 windows thread safe or crash
    if sys.platform == 'linux2':
        QtCore.QCoreApplication.setAttribute(QtCore.Qt.AA_X11InitThreads)
    app = QApplication(sys.argv)
    ui = SyncPy2()
    sys.exit(app.exec_())
