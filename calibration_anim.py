import sys
from PySide2.QtWidgets import QApplication, QWidget, QPushButton, QFrame, \
    QHBoxLayout, QVBoxLayout,QGraphicsEllipseItem
from PySide2.QtCore import *
from PySide2.QtGui import QBrush, QPen


class ScreenCalibration(QWidget):
    def __init__(self,x,y,w=100,h=100,t=3,screen="in",outDir=0):
        super().__init__()

        self.w=w
        self.h=h
        self.x=x
        self.y=y
        self.t=t*1000

        QTimer.singleShot(self.t, self.close)
        self.setWindowFlags(Qt.WindowStaysOnTopHint | Qt.FramelessWindowHint)
        self.setFixedSize(self.w,self.h)

        self.setGeometry(self.x, self.y, self.w, self.h)
        self.frame = QFrame(self)
        if screen=="in":
            self.frame.setStyleSheet('background-color: darkGreen;')
        elif screen=="out":
            self.frame.setStyleSheet('background-color: Red;')
        else:
            self.frame.setStyleSheet('background-color: Blue;')
        self.frame.setFrameStyle(QFrame.Panel | QFrame.Raised)
        #self.setStyleSheet(".QFrame {background-image: url('./app_files/greenarrow.png')}")
        self.frame.resize(self.w,self.h)
        self.animation(screen)

    def animation(self,screen):
        self.animation = QPropertyAnimation(self.frame, b'geometry')
        self.animation.setDuration(self.t)  # mm seconds
        if screen=="in":
            self.animation.setStartValue(QRectF(self.w//2,self.h//2, 0, 0))
            self.animation.setEndValue(QRectF(0, 0, self.w,self.h))
        else:
            self.animation.setStartValue(QRectF(self.w//2,self.h//2, 0, 0))
            self.animation.setEndValue(QRectF(0, 0, self.w,self.h))
        self.animation.start()
        self.animation.finished.connect(self.finishMethod)

    def finishMethod(self):
        return True

    def changePos(self,x,y):
        self.setGeometry(x, y, self.w, self.h)
        self.animation()
