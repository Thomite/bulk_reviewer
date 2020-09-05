import sys
import os 

from PyQt5 import QtGui, QtCore
from PyQt5.QtCore import pyqtSlot, Qt
from PyQt5.QtGui import QIcon, QPixmap
from PyQt5.QtWidgets import QApplication, QMainWindow, QMenu, QVBoxLayout, QSizePolicy, QMessageBox, QWidget, QPushButton
from PyQt5.QtWidgets import QHBoxLayout, QGroupBox, QDialog, QGridLayout, QLabel, QProgressBar

import glob
import random

import pandas as pd

import argparse

def initialise_review_dataset(directory):

	fn = directory + "/reviews.csv"

	if os.path.exists(fn):
		return pd.read_csv(fn)

	else:

		filenames = glob.glob(directory + "/*.*")

		dset = pd.DataFrame()

		dset["filename"] = filenames
		dset["reviewed"] = False
		dset["score"] = 0

	return dset

def get_unreviewed(dset, N=10):

    unreviewed = dset.query("reviewed == False").head(N)
    return unreviewed

def update_reviews(original_dset, updated_dset):
    
    original_dset.update(updated_dset)

class ClickableLabel(QLabel):

	def __init__(self, ID, filename, parent):
		super().__init__()
		self.setAcceptDrops(True)

		pixmap = QPixmap(filename)
		pixmap = pixmap.scaled(200, 200, QtCore.Qt.KeepAspectRatio)

		self.setPixmap(pixmap)
		self.clicked = False
		self.setStyleSheet("QLabel {padding: 5px}")

		self.ID = ID 
		self.filename = filename
		self.mainwindow_parent = parent

	def toggle(self):

		if self.clicked == False:

			self.clicked = True
			self.mainwindow_parent.set_review(self.ID, -1)
			self.setStyleSheet("QLabel {padding: 5px; background-color: #F10000}")

		else:
			self.clicked = False
			self.mainwindow_parent.set_review(self.ID, 1)
			self.setStyleSheet("QLabel {padding: 5px; background-color: #0000F1}")

	def mousePressEvent(self, event):
        
		if event.buttons() & QtCore.Qt.LeftButton:

			print(f"Clicked {self.ID}")
			self.toggle()


class App(QMainWindow):

	def __init__(self):
		super().__init__()
		self.left = 50
		self.top = 50
		self.title = 'Bulk reviewer'
		self.width = 640
		self.height = 640

		self.num_rows = 2
		self.num_cols = 2

		self.directory = "D:/Projects/Sit/"
		self.reviews = initialise_review_dataset(self.directory)

		self.initUI()

	def initUI(self):

		self.setWindowTitle(self.title)
		self.setGeometry(self.left, self.top, self.width, self.height)

		self.central_widget = QWidget()
		self.setCentralWidget(self.central_widget)

		self.central_widget_layout = QGridLayout()
		self.central_widget.setLayout(self.central_widget_layout)

		# -- Create stuff
		self.create_montage_panel()
		self.create_progress_panel()


		# -- Place stuff
		self.central_widget_layout.addWidget(self.montage_panel, 0, 0)
		self.central_widget_layout.addWidget(self.progress_panel, 1, 0)
		# --

		self.update_montage_panel()
		self.update_progress_panel()
		self.show()

	def create_montage_panel(self):
		self.montage_panel = QWidget()
		self.montage_panel_layout = QGridLayout()
		self.montage_panel.setLayout(self.montage_panel_layout)

	def create_progress_panel(self):

		self.progress_panel = QWidget()
		self.progress_panel_layout = QGridLayout()
		self.progress_panel.setLayout(self.progress_panel_layout)

		self.progress_bar = QProgressBar()
		self.label_progress = QLabel(self.progress_panel)

		self.progress_panel_layout.addWidget(self.progress_bar, 0, 0)
		self.progress_panel_layout.addWidget(self.label_progress, 0, 1)

	def clear_montage_panel(self):
		for i in reversed(range(self.montage_panel_layout.count())): 
			self.montage_panel_layout.itemAt(i).widget().deleteLater()

	def update_progress_panel(self):

		num_reviewed = sum(self.reviews["reviewed"] == True)
		num_remaining = sum(self.reviews["reviewed"] == False)
		total = len(self.reviews)

		percent_done = (num_reviewed / total) * 100

		description = f"({num_reviewed} of {total})"

		self.progress_bar.setValue(percent_done)
		self.label_progress.setText(description)

	def update_montage_panel(self):
		
		self.clear_montage_panel()

		N = int(self.num_rows * self.num_cols)

		self.currently_showing_images = get_unreviewed(self.reviews, N=N)
		
		filenames = list(self.currently_showing_images["filename"])

		n = 0

		for r in range(self.num_rows):
			for c in range(self.num_cols):

				if n < len(self.currently_showing_images):
					index = self.currently_showing_images.index[n]
					filename = self.currently_showing_images.loc[index, "filename"]
					l = ClickableLabel(index, filename, self)
					self.montage_panel_layout.addWidget(l, r, c)
					n += 1


	def set_review(self, index, score):
		
		self.currently_showing_images.loc[index, "reviewed"] = True
		self.currently_showing_images.loc[index, "score"] = score

	def commit_reviews(self):

		remaining = self.currently_showing_images["reviewed"] == False
		self.currently_showing_images.loc[remaining, "reviewed"] = True
		self.currently_showing_images.loc[remaining, "score"] = 1

		update_reviews(self.reviews, self.currently_showing_images)

	def keyPressEvent(self, event):

		key = event.key()

		if key == Qt.Key_Escape:
			self.close_window()

		elif key == Qt.Key_Right:

			print("NEXT")
			self.commit_reviews()
			self.update_montage_panel()
			self.update_progress_panel()

		elif key == Qt.Key_P:
			print("Printing reviews")
			self.print_reviews()


	def print_reviews(self):

		try:
			self.reviews.to_csv(self.directory + "/reviews.csv")

		except:
			print("Couldn't print to reviews.csv")

	def close_window(self):

		
		self.close()

	def closeEvent(self, event):#
		self.print_reviews()
		self.deleteLater()

if __name__ == '__main__':
	app = QApplication(sys.argv)
	ex = App()
	sys.exit(app.exec_())