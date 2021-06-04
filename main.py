from PyQt5.QtWidgets import *
from PyQt5.QtCore import Qt
from datetime import datetime

import os
import sys
import requests
import json


class TideTimeWindow(QMainWindow):
	def __init__(self, locationId, parent=None):
		super(TideTimeWindow, self).__init__(parent)
		self.setGeometry(600, 600, 300, 300)
		self.tideData = self.getTideData(locationId)
		self.mainTable = QTableWidget()
		self.formatTable()
		self.show()

	def formatTable(self):
		self.mainTable.setRowCount(28)
		self.mainTable.setColumnCount(2)
		self.mainTable.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeToContents)
		self.mainTable.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeToContents)
		self.mainTable.setHorizontalHeaderLabels(["High/Low Water", "Time (24h)"])

		for i, dp in enumerate(self.tideData):
			self.mainTable.setItem(i, 0, QTableWidgetItem("High" if dp["EventType"] == "HighWater" else "Low"))
			try:
				time = datetime.fromisoformat(dp["DateTime"].split(".")[0])
				self.mainTable.setItem(i, 1, QTableWidgetItem(time.strftime("%a %d - %H:%M")))
			except KeyError:
				self.mainTable.setItem(i, 1, QTableWidgetItem("???"))

		self.setCentralWidget(self.mainTable)

	@staticmethod
	def getTideData(id):
		return json.loads(requests.get(f"https://admiraltyapi.azure-api.net/uktidalapi/api/V1/Stations/{id}/TidalEvents", headers={"Ocp-Apim-Subscription-Key": os.environ["API_KEY"]}).text)


class MainWindow(QMainWindow):
	def __init__(self, *args, **kwargs):
		super().__init__()
		self.initUI()

	def initUI(self):
		self.setGeometry(400, 400, 400, 400)
		self.tableData = self.getTableData()
		self.mainLayout = QVBoxLayout()

		self.inputBoxLayout = QHBoxLayout()

		self.locationInputBox = QLineEdit()
		self.locationInputBox.textChanged.connect(self.updateTableData)
		self.locationInputBox.returnPressed.connect(self.locationSelected)
		self.inputBoxLayout.addWidget(self.locationInputBox)

		self.submitButton = QPushButton("Submit")
		self.submitButton.clicked.connect(self.locationSelected)
		self.inputBoxLayout.addWidget(self.submitButton)

		self.inputBoxWidget = QWidget()
		self.inputBoxWidget.setLayout(self.inputBoxLayout)
		self.mainLayout.addWidget(self.inputBoxWidget)

		self.locationChoiceTable = QTableWidget()
		self.locationChoiceTable.cellDoubleClicked.connect(self.selectItemFromTable)
		self.mainLayout.addWidget(self.locationChoiceTable)

		self.mainWidget = QWidget()
		self.mainWidget.setLayout(self.mainLayout)
		self.setCentralWidget(self.mainWidget)
		self.show()

	@staticmethod
	def getTableData():
		return json.loads(requests.get("https://admiraltyapi.azure-api.net/uktidalapi/api/V1/Stations", headers={"Ocp-Apim-Subscription-Key": os.environ["API_KEY"]}).text)

	def updateTableData(self, text):
		self.currentTableData = self.tableData["features"]
		text = text.lower()
		keepList = []
		for dp in self.currentTableData:
			try:
				if dp["properties"]["Name"].lower().startswith(text):
					keepList.append(dp)
			except KeyError:
				pass
		self.locationChoiceTable.clear()
		self.locationChoiceTable.setRowCount(len(keepList))
		self.locationChoiceTable.setColumnCount(1)
		self.locationChoiceTable.setColumnWidth(0, 200)
		for i, dp in enumerate(keepList):
			currentItem = QTableWidgetItem(dp["properties"]["Name"])
			self.locationChoiceTable.setItem(0, i, currentItem)

	def selectItemFromTable(self, row, col):
		self.locationInputBox.setText(self.locationChoiceTable.itemAt(row, col).text())

	def locationSelected(self):
		self.tideTimeWidget = TideTimeWindow(self.getIdFromName(self.locationInputBox.text(), self.currentTableData))

	@staticmethod
	def getIdFromName(name, data):
		for dp in data:
			try:
				if dp["properties"]["Name"].lower() == name.lower():
					return dp["properties"]["Id"]
			except KeyError:
				pass

		return "0001"


def main(args):
	app = QApplication(args)
	_ = MainWindow()
	sys.exit(app.exec_())


if __name__ == '__main__':
	main(sys.argv)
