from PyQt5.QtCore import Qt
from PyQt5.QtGui import QKeySequence, QColor
from PyQt5.QtWidgets import QFileDialog, QMessageBox
from binascii import hexlify
from datetime import datetime
import os, json, shutil

class Editor:
    def __init__(self):
        self.ui = None
        self.saveFilePath = ""
        self.currentItem = ""
        self.currentAddress = None
        self.changes = []
        with open("addresses.json") as jsonFile:
            self.addresses = json.load(jsonFile)
    
    def bindEvents(self, appUi):
        self.ui = appUi
        self.ui.actionWebsiteLink.triggered.connect(self.openHelpLink)
        self.ui.actionOpen.triggered.connect(self.openFile)
        self.ui.actionSave.triggered.connect(self.saveFile)
        self.ui.actionSaveCopy.triggered.connect(self.saveCopy)
        self.ui.lineEditSearch.textEdited.connect(self.populateList)
        self.ui.listWidget.clicked.connect(self.itemClicked)
        self.ui.lineEditNew.textEdited.connect(self.newEdited)
        
        #shortcuts
        self.ui.actionOpen.setShortcut(QKeySequence.Open)
        self.ui.actionSave.setShortcut(QKeySequence.Save)

    def populateList(self):
        self.ui.listWidget.clear()
        query = self.ui.lineEditSearch.text()
        for item in self.addresses:
            if query.lower() in item["name"].lower():
                self.ui.listWidget.addItem(item["name"])
                for change in self.changes:
                    if change["name"] == item["name"]:
                        self.ui.listWidget.findItems(item["name"], Qt.MatchExactly)[0].setForeground(QColor("red"))
                        break

    def itemClicked(self):
        if self.saveFilePath:
            self.currentItem = self.ui.listWidget.currentItem().text()
            self.ui.labelCurrentName.setText(self.currentItem)
            self.ui.lineEditNew.setText("")
            for i in self.addresses:
                if i["name"] == self.currentItem:
                    self.currentAddress = int(i["address"], base=16)
                    break
            for i in self.changes:
                if i["name"] == self.currentItem:
                    self.ui.lineEditNew.setText(i["newValue"])
                    break
            self.showValues()

    def showValues(self):
        try:
            with open(self.saveFilePath, "rb") as data:
                data.seek(self.currentAddress)
                self.ui.lineEditOld.setText(str(hexlify(data.read(1)), "utf-8"))
        except FileNotFoundError:
            msg = QMessageBox()
            msg.setIcon(QMessageBox.Information)
            msg.setText("Cannot read value from file. Make sure " + self.saveFilePath + " still exists.")
            msg.setWindowTitle("Attention")
            msg.setStandardButtons(QMessageBox.Ok)
            msg.exec_()
            
    def newEdited(self):
        if self.saveFilePath:
            for item in self.changes:
                if item["name"] == self.currentItem:
                    self.changes.remove(item)
            
            self.changes.append({"name":self.currentItem, "newValue":self.ui.lineEditNew.text()})
            self.populateList()

    def openHelpLink(self):
        os.system("start \"\" https://docs.epicmickey.wiki")
        
    def openFile(self):
        fname = QFileDialog.getOpenFileName(None, 'Open File', '',"Epic Mickey save files (*.dat)")
        try:
            with open(fname[0], "rb") as data:
                self.ui.lineEditNew.setReadOnly(False)
                self.saveFilePath = fname[0]
                self.ui.labelFile.setText((self.saveFilePath[:65] + '...') if len(self.saveFilePath) > 65 else self.saveFilePath)
                self.populateList()
        except FileNotFoundError:
            msg = QMessageBox()
            msg.setIcon(QMessageBox.Warning)
            msg.setText("Could not open file.")
            msg.setWindowTitle("Attention")
            msg.setStandardButtons(QMessageBox.Ok)
            msg.exec_()
    
    def saveCopy(self):
        if not self.saveFilePath:
            msg = QMessageBox()
            msg.setIcon(QMessageBox.Information)
            msg.setText("Please open a file first.")
            msg.setWindowTitle("Cannot Create Copy")
            msg.setStandardButtons(QMessageBox.Ok)
            msg.exec_()
        else:
            try:
                now = datetime.now()
                dest = self.saveFilePath + ".bak"
                shutil.copy(self.saveFilePath, dest)
                
                msg = QMessageBox()
                msg.setIcon(QMessageBox.Information)
                msg.setText("Backup copy saved to " + dest)
                msg.setWindowTitle("Success")
                msg.setStandardButtons(QMessageBox.Ok)
                msg.exec_()
            except:
                msg = QMessageBox()
                msg.setIcon(QMessageBox.Warning)
                msg.setText("An unknown error prevented a backup copy from being made.")
                msg.setWindowTitle("Attention")
                msg.setStandardButtons(QMessageBox.Ok)
                msg.exec_()
    
    def saveFile(self):
        errors = []
        try:
            with open(self.saveFilePath, "rb+") as data:
                for item in self.changes:
                    try:
                        newByte = bytes.fromhex(item["newValue"])
                        for address in self.addresses:
                            if address["name"] == item["name"]:
                                data.seek(int(address["address"], base=16))
                                data.write(newByte)
                                break
                    except:
                        errors.append(item["name"])
                self.changes = []
        except FileNotFoundError:
            msg = QMessageBox()
            msg.setIcon(QMessageBox.Warning)
            msg.setText("File could not be found. Make sure " + self.saveFilePath + " still exists.")
            msg.setWindowTitle("Attention")
            msg.setStandardButtons(QMessageBox.Ok)
            msg.exec_()
        
        self.populateList()
        
        if (len(errors) > 0):
            msg = QMessageBox()
            msg.setIcon(QMessageBox.Warning)
            msg.setText("One or more globals were not saved due to an invalid value.")
            msg.setWindowTitle("Attention")
            msg.setDetailedText("The following globals could not be saved:\n" + "\n".join(errors))
            msg.setStandardButtons(QMessageBox.Ok)
            msg.exec_()