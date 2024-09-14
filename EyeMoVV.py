import sys
import config
from PySide2.QtCore import *
from PySide2.QtGui import *
from PySide2.QtWidgets import *

from win32event import CreateMutex
from win32api import CloseHandle, GetLastError
from winerror import ERROR_ALREADY_EXISTS

# Splash ekranı başlar
app = QApplication(sys.argv)
app.setStyle("Windows")
app.setStyleSheet("""
    QMenu:item:selected {
        color: #5c0a0a;
    }
    QWidget{
        background-color:"#faebd7";
        font-size:12px;
    }
    QPushButton:hover{
        color: #5c0a0a;
    }
""")

mutex = CreateMutex(None, False, config.SPLASHMUTEXNAME)
lasterror = GetLastError()
def alreadyrunning():
    return (lasterror == ERROR_ALREADY_EXISTS)

splash_pix = QPixmap(config.SPLASHLOGO)
splash = QSplashScreen(splash_pix, Qt.WindowStaysOnTopHint)

if alreadyrunning():
    sys.exit(1)
else:
    splash.show()
app.processEvents()
# Splash ekranı biter

import os
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '2'

import numpy as np
import threading
import platform
import time
import math
import pyautogui
import qimage2ndarray
from PySide2.QtMultimedia import QCameraInfo
import imutils
from playsound import playsound #1.2.2
import cv2

import calibration_anim
import setting
from mainMPFun import faceDetector
import clr
import player

pyautogui.PAUSE = 0

clr.AddReference("./app_files/dlls/WPFTabTip")

import WPFTabTip
klavye = WPFTabTip.TabTip

HEAD_POINT={"L":0,"R":0,"U":0,"D":0}
fDetector=faceDetector()

class MainApp(QMainWindow):
    def __init__(self):
        QMainWindow.__init__(self)

        self.mutexname = config.APPMUTEXNAME
        self.mutex = CreateMutex(None, False, self.mutexname)
        self.lasterror = GetLastError()

        desktop = QApplication.primaryScreen()
        screenRect = desktop.size()#desktop.availableGeometry()
        self.hs = screenRect.height()
        self.ws = screenRect.width()
        self.setWindowFlags(Qt.WindowStaysOnTopHint | Qt.FramelessWindowHint)
        self.cameraWidth=192#320 #220 192
        self.cameraHeight=256#240 #165 144
        self.windowWidth = 210
        self.windowHeight = 570+self.cameraHeight
        self.windowLeft=(self.ws-self.windowWidth)/2
        self.windowTop=(self.hs-self.windowHeight)/2
        self.cameraToleranceGap = 50
        self.cameraStartPoint = (0, 0)
        self.cameraEndPoint = (0, 0)
        self.windowTopDirection=200
        self.activeOpacity=1
        self.opacityFlag=False
        self.onHoverFlag = False
        self.mouseScreenToleranceLimit=8

        self.deactiveOpacity = 0.5
        self.setWindowOpacity(self.deactiveOpacity)

        self.setWindowTitle("EyeMo")
        self.animation = None
        self.baseHeight =self.windowHeight #330
        self.extendedHeight = self.windowHeight#600
        self.camera_list = []
        self.selectedCameraIndex = 0
        self.calibrationCount=0
        self.screenCount = 0
        self.setGeometry(self.windowLeft, self.windowTop, self.windowWidth, self.windowHeight)


        self.st=setting.settingScreen(self.ws,self.hs)
        self.tolerance=int(self.st.tolerance)
        self.idletime=int(self.st.idletime)
        self.caltime=int(self.st.caltime)
        self.mousegap=int(self.st.mousegap)
        self.scrolldist=int(self.st.scrolldist)
        self.activeLang=self.st.activeLang
        self.clickSoundLevel=self.st.clickSLevel
        tempCoeff=int(self.st.tolerance)
        self.st.valueChanged.connect(self.updateValuesFromSetting)
        if tempCoeff==1:
            self.upDownCoeff = 0.33
        elif tempCoeff==3:
            self.upDownCoeff = 0.66
        else:
            self.upDownCoeff=0.5


        self.leftRightCoeff = 0.5
        self.mouseBehavior=None
        self.leftEyeBlinkTime=0
        self.rightEyeBlinkTime = 0
        self.leftEyeBlinkFlag=False
        self.rightEyeBlinkFlag=False
        self.idled_time = [time.time()]
        self.idle_pos = [pyautogui.position()]
        self.reflexEyeBlinkFlag=False
        self.reflexEyeBlinkFlagNew = False
        self.reflexEyeBlinkTime=0
        self.earsOfEyes=[]
        self.triangelPointsAndDatasOfEyes = []
        self.cameraCropPoints=[]
        self.llooksrlooks=[]
        self.calibrationBreakThreshold=0.30
        self.calibrationBreakThresholdCount=0
        self.calibrationH=0
        self.lBlinkStatus=False
        self.rBlinkStatus = False
        self.keyboardAutoFlag=False
        self.keyboardManuelFlag = False
        self.headOutOfAreaFlag=False
        self.cropImageCommand=False
        self.musicThread = player.PlayMusicWithThread("./app_files/emergency_call.mp3")
        self.musicTimer = QTimer()
        self.capture=None

        self.lastAvgCnt=10
        self.xPupilL=0
        self.yPupilL=0
        self.xPupilR=0
        self.yPupilR=0
        self.screenPoint=[]
        self.screenBound={}
        self.leftLookThresholdPercentageL=0
        self.rightLookThresholdPercentageL=0
        self.leftLookThresholdPercentageR=0
        self.rightLookThresholdPercentageR=0
        self.upLookThreshold = 0
        self.leftBlinkThreshold=0
        self.rightBlinkThreshold = 0
        self.idleTimeForBlink = 1
        self.reflexTimeB = 0.3
        self.leftBlinkCalFlag=False
        self.rightBlinkCalFlag = False

        self.calCenter=None
        self.calLeft=None
        self.calTop=None
        self.calRight=None
        self.calBottom=None
        self.moveBound=10
        self.scCenter=None
        self.scLeft=None
        self.scTop=None
        self.scRight=None
        self.scBottom=None
        self.w = None
        self.wRet=None
        self.screenCalibrationFlag=False
        self.outCalibrationFlag = False
        self.setEyeCenterFlag=False
        self.screenCalibrationStatus=False
        self.activeHoverBtn=None
        self.oneTimeClickStatus=True

        self.main_layout = QVBoxLayout()
        self.setupMenu()
        self.setupUI()
        self.setLayout(self.main_layout)
        self.setMouseTracking(True)

    def setupUI(self):
        self.cameraListCombo = QComboBox(self)
        self.cameraListCombo.setGeometry(80, 30, 120, 20)
        self.cameraListCombo.setStyleSheet("QComboBox {font-size: 10px;}")
        self.addCameraToComboBox()

        self.selectLabel = QLabel(self.st.activeLangPack["selCam"], self)
        self.selectLabel.setGeometry(10, 30, 70, 20)

        self.video_size = QSize(self.cameraWidth, self.cameraHeight)
        self.image_label = QLabel(self)
        self.image_label.setFixedSize(self.video_size)
        self.image_label.move(10, 60)
        # self.image_label.enterEvent = lambda event: self.changeOpacity(self.activeOpacity)
        # self.main_layout.addWidget(self.image_label)

        self.moveLeftBtn = QPushButton(self)
        self.moveLeftBtn.setGeometry(10, 60+self.cameraHeight+10, 90, 50)
        self.moveLeftBtn.setText(self.st.activeLangPack["mLeft"])
        self.moveLeftBtn.installEventFilter(self)
        self.moveLeftBtn.clicked.connect(self.setupWindowLocLeft)

        self.moveRightBtn = QPushButton(self)
        self.moveRightBtn.setGeometry(110, 60+self.cameraHeight+10, 90, 50)
        self.moveRightBtn.setText(self.st.activeLangPack["mRight"])
        self.moveRightBtn.installEventFilter(self)
        self.moveRightBtn.clicked.connect(self.setupWindowLocRight)

        self.oneClickBtn = QPushButton(self)
        self.oneClickBtn.setGeometry(10, 60+self.cameraHeight+70, 90, 50)
        self.oneClickBtn.setText(self.st.activeLangPack["lClick"])
        self.oneClickBtn.installEventFilter(self)
        self.oneClickBtn.clicked.connect(self.setOneClick)
        self.oneClickBtn.setStyleSheet("QPushButton {background-color : lightblue;}")

        self.doubleClickBtn = QPushButton(self)
        self.doubleClickBtn.setGeometry(10, 60+self.cameraHeight+130, 90, 50)
        self.doubleClickBtn.setText(self.st.activeLangPack["dClick"])
        self.doubleClickBtn.installEventFilter(self)
        self.doubleClickBtn.clicked.connect(self.setDoubleClick)
        self.doubleClickBtn.setStyleSheet("QPushButton {background-color : lightblue;}")

        self.rightClickBtn = QPushButton(self)
        self.rightClickBtn.setGeometry(10, 60+self.cameraHeight+190, 90, 50)
        self.rightClickBtn.setText(self.st.activeLangPack["rClick"])
        self.rightClickBtn.installEventFilter(self)
        self.rightClickBtn.clicked.connect(self.setRightClick)
        self.rightClickBtn.setStyleSheet("QPushButton {background-color : lightblue;}")

        self.freeClickBtn = QPushButton(self)
        self.freeClickBtn.setGeometry(110, 60+self.cameraHeight+70, 90, 50)
        self.freeClickBtn.setText(self.st.activeLangPack["fMove"])
        self.freeClickBtn.installEventFilter(self)
        self.freeClickBtn.clicked.connect(self.setFreeClick)
        self.freeClickBtn.setStyleSheet("QPushButton {background-color : lightblue;}")

        self.mouseUpScrollBtn = QPushButton(self)
        self.mouseUpScrollBtn.setGeometry(110, 60+self.cameraHeight+130, 90, 50)
        self.mouseUpScrollBtn.setText(self.st.activeLangPack["sUp"])
        self.mouseUpScrollBtn.installEventFilter(self)
        self.mouseUpScrollBtn.clicked.connect(self.mouseUpScroll)
        self.mouseUpScrollBtn.setStyleSheet("QPushButton {background-color : lightblue;}")

        self.mouseDownScrollBtn = QPushButton(self)
        self.mouseDownScrollBtn.setGeometry(110, 60+self.cameraHeight+190, 90, 50)
        self.mouseDownScrollBtn.setText(self.st.activeLangPack["sDown"])
        self.mouseDownScrollBtn.installEventFilter(self)
        self.mouseDownScrollBtn.clicked.connect(self.mouseDownScroll)
        self.mouseDownScrollBtn.setStyleSheet("QPushButton {background-color : lightblue;}")

        self.oneTimeClickBtn = QPushButton(self)
        self.oneTimeClickBtn.setGeometry(10, 60+self.cameraHeight+250, 190, 30)
        self.oneTimeClickBtn.setText(self.st.activeLangPack["otClick"])
        self.oneTimeClickBtn.installEventFilter(self)
        self.oneTimeClickBtn.clicked.connect(self.setOneTimeClick)
        self.oneTimeClickBtn.setStyleSheet("QPushButton {background-color : lightblue;}")

        self.emergencyCallBtn = QPushButton(self)
        self.emergencyCallBtn.setGeometry(10, 60+self.cameraHeight+290, 190, 60)
        self.emergencyCallBtn.setText(self.st.activeLangPack["eCall"])
        self.emergencyCallBtn.installEventFilter(self)
        self.emergencyCallBtn.clicked.connect(self.runEmergencyCall)
        self.emergencyCallBtn.setStyleSheet("QPushButton {background-color : lightblue;}")

        self.volumeUpBtn = QPushButton(self)
        self.volumeUpBtn.setGeometry(110, 60+self.cameraHeight+360, 90, 50)
        self.volumeUpBtn.setText(self.st.activeLangPack["vUp"])
        self.volumeUpBtn.installEventFilter(self)
        self.volumeUpBtn.clicked.connect(self.setVolumeUp)
        self.volumeUpBtn.setStyleSheet("QPushButton {background-color : lightblue;}")

        self.volumeDownBtn = QPushButton(self)
        self.volumeDownBtn.setGeometry(10, 60+self.cameraHeight+360, 90, 50)
        self.volumeDownBtn.setText(self.st.activeLangPack["vDown"])
        self.volumeDownBtn.installEventFilter(self)
        self.volumeDownBtn.clicked.connect(self.setVolumeDown)
        self.volumeDownBtn.setStyleSheet("QPushButton {background-color : lightblue;}")

        self.keyboardOpenBtn = QPushButton(self)
        self.keyboardOpenBtn.setGeometry(10, 60+self.cameraHeight+420, 90, 50)
        self.keyboardOpenBtn.setText(self.st.activeLangPack["oKB"])
        self.keyboardOpenBtn.installEventFilter(self)
        self.keyboardOpenBtn.clicked.connect(self.keyboardOpen)
        self.keyboardOpenBtn.setStyleSheet("QPushButton {background-color : lightblue;}")

        self.keyboardCloseBtn = QPushButton(self)
        self.keyboardCloseBtn.setGeometry(110, 60+self.cameraHeight+420, 90, 50)
        self.keyboardCloseBtn.setText(self.st.activeLangPack["cKB"])
        self.keyboardCloseBtn.installEventFilter(self)
        self.keyboardCloseBtn.clicked.connect(self.keyboardClose)
        self.keyboardCloseBtn.setStyleSheet("QPushButton {background-color : lightblue;}")

    def updateValuesFromSetting(self, itemList):
        self.tolerance = int(itemList[0])
        self.idletime = int(itemList[1])
        self.caltime = int(itemList[2])
        self.mousegap = int(itemList[3])
        self.scrolldist = int(itemList[4])
        self.activeLang = itemList[5]
        self.clickSoundLevel =itemList[6]
        tempCoeff = int(itemList[0])
        if tempCoeff == 1:
            self.upDownCoeff = 0.33
        elif tempCoeff == 3:
            self.upDownCoeff = 0.66
        else:
            self.upDownCoeff = 0.5

        self.selectLabel.setText(self.st.activeLangPack["selCam"])
        self.moveLeftBtn.setText(self.st.activeLangPack["mLeft"])
        self.moveRightBtn.setText(self.st.activeLangPack["mRight"])
        self.oneClickBtn.setText(self.st.activeLangPack["lClick"])
        self.doubleClickBtn.setText(self.st.activeLangPack["dClick"])
        self.rightClickBtn.setText(self.st.activeLangPack["rClick"])
        self.freeClickBtn.setText(self.st.activeLangPack["fMove"])
        self.mouseUpScrollBtn.setText(self.st.activeLangPack["sUp"])
        self.mouseDownScrollBtn.setText(self.st.activeLangPack["sDown"])
        self.oneTimeClickBtn.setText(self.st.activeLangPack["otClick"])
        self.emergencyCallBtn.setText(self.st.activeLangPack["eCall"])
        self.volumeUpBtn.setText(self.st.activeLangPack["vUp"])
        self.volumeDownBtn.setText(self.st.activeLangPack["vDown"])
        self.keyboardOpenBtn.setText(self.st.activeLangPack["oKB"])
        self.keyboardCloseBtn.setText(self.st.activeLangPack["cKB"])
        self.oneTimeClickBtn.setText(self.st.activeLangPack["ftClick"])
        self.oneTimeClickBtn.setText(self.st.activeLangPack["otClick"])

        self.setting_action.setText(self.st.activeLangPack["sett"]+" "+self.st.version)
        self.pdf_action.setText(self.st.activeLangPack["openPDF"])
        self.exit_action.setText(self.st.activeLangPack["ext"])
        self.screenCal.setText(self.st.activeLangPack["calSc"])
        self.screenCalRst.setText(self.st.activeLangPack["resetSc"])
        self.connect_action.setText(self.st.activeLangPack["conCam"])
        self.crop_action.setText(self.st.activeLangPack["crop"])

        self.fileMenu.setTitle(self.st.activeLangPack["file"])
        self.calibrationMenu .setTitle(self.st.activeLangPack["calibration"])
        self.connectMenu.setTitle(self.st.activeLangPack["connect"])

        if self.screenCalibrationStatus == True:
            self.statusBarLabelSC.setText(self.st.activeLangPack["scOK"])
        else:
            self.statusBarLabelSC.setText(self.st.activeLangPack["scNone"])

    def setupMenu(self):
        menuBar = self.menuBar()

        self.fileMenu = menuBar.addMenu(self.st.activeLangPack["file"])
        self.setting_action = QAction(self.st.activeLangPack["sett"]+" "+self.st.version, self)
        self.setting_action.triggered.connect(self.settingApp)
        self.fileMenu.addAction(self.setting_action)
        self.pdf_action = QAction(self.st.activeLangPack["openPDF"], self)
        self.pdf_action.triggered.connect(self.openPDF)
        self.fileMenu.addAction(self.pdf_action)
        self.fileMenu.addSeparator()
        self.exit_action = QAction(self.st.activeLangPack["ext"], self)
        self.exit_action.triggered.connect(self.exitApp)
        self.fileMenu.addAction(self.exit_action)

        self.calibrationMenu = menuBar.addMenu(self.st.activeLangPack["calibration"])
        self.screenCalRst = QAction(self.st.activeLangPack["resetSc"], self)
        self.screenCalRst.setEnabled(False)
        self.screenCalRst.triggered.connect(self.resetScreenCalibration)
        self.calibrationMenu.addAction(self.screenCalRst)
        self.screenCal = QAction(self.st.activeLangPack["calSc"], self)
        self.screenCal.setEnabled(False)
        self.screenCal.triggered.connect(self.openScreenCalibration)
        self.calibrationMenu.addAction(self.screenCal)

        self.connectMenu = menuBar.addMenu(self.st.activeLangPack["connect"])
        self.connect_action = QAction(self.st.activeLangPack["conCam"], self)
        self.connect_action.triggered.connect(self.setupCamera)
        self.connectMenu.addAction(self.connect_action)
        self.crop_action = QAction(self.st.activeLangPack["crop"], self)
        self.crop_action.setEnabled(False)
        self.crop_action.triggered.connect(self.cropImage)
        self.connectMenu.addAction(self.crop_action)

        self.statusBarLabelSC = QLabel(self.st.activeLangPack["scNone"])
        self.statusBar().addWidget(self.statusBarLabelSC)

    def setupWindowLocLeft(self):
        self.windowLeft=0
        self.windowTop=0#self.windowTopDirection
        self.setGeometry(self.windowLeft, self.windowTop, self.windowWidth, self.windowHeight)
        self.moveLeftBtn.setStyleSheet("QPushButton {background-color : orange;}")
        self.moveRightBtn.setStyleSheet("")

    def setupWindowLocRight(self):
        self.windowLeft=self.ws-self.windowWidth
        self.windowTop=0#self.windowTopDirection
        self.setGeometry(self.windowLeft, self.windowTop, self.windowWidth, self.windowHeight)
        self.moveRightBtn.setStyleSheet("QPushButton {background-color : orange;}")
        self.moveLeftBtn.setStyleSheet("")

    def setupCamera(self):
        self.selectedCameraIndex = self.cameraListCombo.currentIndex()
        if (platform.system()=="Windows"):
            self.capture = cv2.VideoCapture(self.selectedCameraIndex, cv2.CAP_DSHOW)#cv2.CAP_MSMF
            self.capture.set(cv2.CAP_PROP_FOURCC, cv2.VideoWriter_fourcc('m', 'j', 'p', 'g'))
            self.capture.set(cv2.CAP_PROP_FOURCC, cv2.VideoWriter_fourcc('M', 'J', 'P','G'))
            self.capture.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)#1920
            self.capture.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)#1080

        elif (platform.system()=="Linux"):
            self.capture = cv2.VideoCapture(self.camera_list[self.selectedCameraIndex])
        else:#macos
            self.capture = cv2.VideoCapture(self.selectedCameraIndex)

        if self.capture.isOpened():
            self.crop_action.setEnabled(True)
            self.timer = QTimer()
            self.timer.timeout.connect(self.display_video_stream)
            self.timer.start(1)

    def addCameraToComboBox(self):
        for cam in QCameraInfo.availableCameras():
            self.cameraListCombo.addItem(cam.description(), cam)
            self.camera_list.append(cam.deviceName())

    def openPDF(self):
        pdf_path =config.USERMANUALPATH
        url = QUrl.fromLocalFile(pdf_path)
        if not QDesktopServices.openUrl(url):
            QMessageBox.warning(self, self.st.activeLangPack["error"], self.st.activeLangPack["pdfError"])

    def cleanUp(self):
        if self.capture!=None:
            if self.capture.isOpened():
                self.capture.release()
            cv2.destroyAllWindows()

    def exitApp(self):
        self.close()
        self.st.close()
        self.cleanUp()
        app = QApplication.instance()
        app.quit()

    def closeEvent(self, event):
        self.exitApp()

    def cropImage(self):
        self.cropImageCommand=True

    def settingApp(self):
        self.st.show()

    def enterEvent(self, event):
        self.setWindowOpacity(self.activeOpacity)
        self.opacityFlag=True
        self.onHoverFlag = True

    def leaveEvent(self, event):
        self.setWindowOpacity(self.deactiveOpacity)
        self.opacityFlag = False
        self.onHoverFlag = False

    def runEmergencyCall(self):
        pyautogui.press("volumeup", presses=50)
        self.emergencyCallBtn.setEnabled(False)
        if self.musicThread.isRunning():
            self.musicThread.terminate()
        self.musicThread = player.PlayMusicWithThread("./app_files/emergency_call.mp3")
        self.musicThread.start()

        self.musicTimer.timeout.connect(self.checkMusicStatus)
        self.musicTimer.start(1000)

    def checkMusicStatus(self):
        if not self.musicThread.isRunning():
            self.emergencyCallBtn.setEnabled(True)
            self.musicTimer.stop()
            pyautogui.press("volumedown", presses=50)
            pyautogui.press("volumeup", presses=25)

    def setVolumeUp(self):
        pyautogui.press("volumeup",presses=2)

    def setVolumeDown(self):
        pyautogui.press("volumedown",presses=2)

    def keyboardOpen(self):
        klavye.Close()
        klavye.Open()

    def keyboardClose(self):
        klavye.Close()

    def setOneTimeClick(self):
        if self.oneTimeClickStatus==True:
            self.oneTimeClickBtn.setText(self.st.activeLangPack["ftClick"])
            self.oneTimeClickBtn.setStyleSheet("QPushButton {background-color : lightgreen;}")
            self.oneTimeClickStatus=False
        else:
            self.oneTimeClickBtn.setText(self.st.activeLangPack["otClick"])
            self.oneTimeClickBtn.setStyleSheet("QPushButton {background-color : lightblue;}")
            self.oneTimeClickStatus=True

    def setFreeClick(self):
        self.mouseBehavior=None
        self.freeClickBtn.setStyleSheet("QPushButton {background-color : lightgreen;}")
        self.oneClickBtn.setStyleSheet("QPushButton {background-color : lightblue;}")
        self.doubleClickBtn.setStyleSheet("QPushButton {background-color : lightblue;}")
        self.rightClickBtn.setStyleSheet("QPushButton {background-color : lightblue;}")
        self.mouseUpScrollBtn.setStyleSheet("QPushButton {background-color : lightblue;}")
        self.mouseDownScrollBtn.setStyleSheet("QPushButton {background-color : lightblue;}")

    def setOneClick(self):
        if self.mouseBehavior!=1:
            self.mouseBehavior = 1
            self.oneClickBtn.setStyleSheet("QPushButton {background-color : lightgreen;}")
            self.freeClickBtn.setStyleSheet("QPushButton {background-color : lightblue;}")
            self.doubleClickBtn.setStyleSheet("QPushButton {background-color : lightblue;}")
            self.rightClickBtn.setStyleSheet("QPushButton {background-color : lightblue;}")
            self.mouseUpScrollBtn.setStyleSheet("QPushButton {background-color : lightblue;}")
            self.mouseDownScrollBtn.setStyleSheet("QPushButton {background-color : lightblue;}")
        elif self.mouseBehavior==1:
            self.oneClickBtn.setStyleSheet("QPushButton {background-color : lightblue;}")
            self.mouseBehavior=None

    def setDoubleClick(self):
        if self.mouseBehavior != 2:
            self.mouseBehavior = 2
            self.doubleClickBtn.setStyleSheet("QPushButton {background-color : lightgreen;}")
            self.oneClickBtn.setStyleSheet("QPushButton {background-color : lightblue;}")
            self.freeClickBtn.setStyleSheet("QPushButton {background-color : lightblue;}")
            self.rightClickBtn.setStyleSheet("QPushButton {background-color : lightblue;}")
            self.mouseUpScrollBtn.setStyleSheet("QPushButton {background-color : lightblue;}")
            self.mouseDownScrollBtn.setStyleSheet("QPushButton {background-color : lightblue;}")
        elif self.mouseBehavior == 2:
            self.doubleClickBtn.setStyleSheet("QPushButton {background-color : lightblue;}")
            self.mouseBehavior = None

    def setRightClick(self):
        if self.mouseBehavior != 3:
            self.mouseBehavior = 3
            self.rightClickBtn.setStyleSheet("QPushButton {background-color : lightgreen;}")
            self.freeClickBtn.setStyleSheet("QPushButton {background-color : lightblue;}")
            self.oneClickBtn.setStyleSheet("QPushButton {background-color : lightblue;}")
            self.doubleClickBtn.setStyleSheet("QPushButton {background-color : lightblue;}")
            self.mouseUpScrollBtn.setStyleSheet("QPushButton {background-color : lightblue;}")
            self.mouseDownScrollBtn.setStyleSheet("QPushButton {background-color : lightblue;}")
        elif self.mouseBehavior == 3:
            self.rightClickBtn.setStyleSheet("QPushButton {background-color : lightblue;}")
            self.mouseBehavior = None

    def mouseUpScroll(self):
        if self.mouseBehavior != 4:
            self.mouseBehavior = 4
            self.mouseUpScrollBtn.setStyleSheet("QPushButton {background-color : lightgreen;}")
            self.freeClickBtn.setStyleSheet("QPushButton {background-color : lightblue;}")
            self.oneClickBtn.setStyleSheet("QPushButton {background-color : lightblue;}")
            self.doubleClickBtn.setStyleSheet("QPushButton {background-color : lightblue;}")
            self.rightClickBtn.setStyleSheet("QPushButton {background-color : lightblue;}")
            self.mouseDownScrollBtn.setStyleSheet("QPushButton {background-color : lightblue;}")
        elif self.mouseBehavior == 4:
            self.mouseUpScrollBtn.setStyleSheet("QPushButton {background-color : lightblue;}")
            self.mouseBehavior = None

    def mouseDownScroll(self):
        if self.mouseBehavior != 5:
            self.mouseBehavior = 5
            self.mouseDownScrollBtn.setStyleSheet("QPushButton {background-color : lightgreen;}")
            self.freeClickBtn.setStyleSheet("QPushButton {background-color : lightblue;}")
            self.oneClickBtn.setStyleSheet("QPushButton {background-color : lightblue;}")
            self.doubleClickBtn.setStyleSheet("QPushButton {background-color : lightblue;}")
            self.rightClickBtn.setStyleSheet("QPushButton {background-color : lightblue;}")
            self.mouseUpScrollBtn.setStyleSheet("QPushButton {background-color : lightblue;}")
        elif self.mouseBehavior == 5:
            self.mouseDownScrollBtn.setStyleSheet("QPushButton {background-color : lightblue;}")
            self.mouseBehavior = None

    def resetScreenCalibration(self):
        self.cropImageCommand=False
        self.cameraStartPoint = (0, 0)
        self.cameraEndPoint = (0, 0)
        self.leftBlinkThreshold=0
        self.rightBlinkThreshold = 0
        self.screenCalibrationFlag=False
        self.screenCalibrationStatus=False
        self.screenCalRst.setEnabled(False)
        self.screenCal.setEnabled(True)

    def openScreenCalibration(self):
        self.screenCalibrationFlag=True
        self.screenCalibrationStatus=False
        self.screenCount=0
        self.screenPoint.clear()
        self.screenBound.clear()
        self.earsOfEyes.clear()
        self.triangelPointsAndDatasOfEyes.clear()
        self.cameraCropPoints.clear()
        self.llooksrlooks.clear()
        self.leftBlinkThreshold=0
        self.rightBlinkThreshold = 0

    def resetBtnStyle(self):
        self.freeClickBtn.setStyleSheet("QPushButton {background-color : lightblue;}")
        self.oneClickBtn.setStyleSheet("QPushButton {background-color : lightblue;}")
        self.doubleClickBtn.setStyleSheet("QPushButton {background-color : lightblue;}")
        self.rightClickBtn.setStyleSheet("QPushButton {background-color : lightblue;}")
        self.mouseDownScrollBtn.setStyleSheet("QPushButton {background-color : lightblue;}")
        self.mouseUpScrollBtn.setStyleSheet("QPushButton {background-color : lightblue;}")

    def eventFilter(self, source, event):
        if event.type() == QEvent.Enter and source == self.moveLeftBtn:
            self.activeHoverBtn="L"
        elif event.type() == QEvent.Enter and source == self.moveRightBtn:
            self.activeHoverBtn = "R"
        elif event.type() == QEvent.Enter and source == self.oneClickBtn:
            self.activeHoverBtn=1
        elif event.type() == QEvent.Enter and source == self.doubleClickBtn:
            self.activeHoverBtn=2
        elif event.type() == QEvent.Enter and source == self.rightClickBtn:
            self.activeHoverBtn=3
        elif event.type() == QEvent.Enter and source == self.mouseUpScrollBtn:
            self.activeHoverBtn=4
        elif event.type() == QEvent.Enter and source == self.mouseDownScrollBtn:
            self.activeHoverBtn=5
        elif event.type() == QEvent.Enter and source == self.freeClickBtn:
            self.activeHoverBtn=6
        elif event.type() == QEvent.Enter and source == self.oneTimeClickBtn:
            self.activeHoverBtn=7
        elif event.type() == QEvent.Enter and source == self.emergencyCallBtn:
            self.activeHoverBtn=8
        elif event.type() == QEvent.Enter and source == self.volumeUpBtn:
            self.activeHoverBtn=9
        elif event.type() == QEvent.Enter and source == self.volumeDownBtn:
            self.activeHoverBtn=10
        elif event.type() == QEvent.Enter and source == self.keyboardOpenBtn:
            self.activeHoverBtn=11
        elif event.type() == QEvent.Enter and source == self.keyboardCloseBtn:
            self.activeHoverBtn=12
        elif event.type() == QEvent.Leave:
            self.activeHoverBtn = None

        return super().eventFilter(source, event)

    def leaveEvent(self, e):
        self.changeOpacity(self.deactiveOpacity)  # <---
        self.opacityFlag = False
        self.onHoverFlag = False

    def changeOpacity(self,opacity):
        self.setWindowOpacity(opacity)

    def updateIdle(self):
        self.idled_time.append(time.time())
        self.idle_pos.append(pyautogui.position())

    def mouseIdleTimeAndUpdate(self):
        cnt=0
        for i in range(len(self.idle_pos)-1):
            del self.idle_pos[0]
        for i in range(len(self.idled_time)-1):
            del self.idled_time[0]
        current_pos = pyautogui.position()
        if current_pos!=self.idle_pos[0]:
            self.updateIdle()
        elif time.time()-self.idled_time[0]>self.idletime:
            if self.activeHoverBtn is not None:
                cnt=1
                self.playSoundWithTrigger(1)
                if self.activeHoverBtn=="L":
                    self.setupWindowLocLeft()
                elif self.activeHoverBtn=="R":
                    self.setupWindowLocRight()
                elif self.activeHoverBtn == 1:
                    self.setOneClick()
                elif self.activeHoverBtn == 2:
                    self.setDoubleClick()
                elif self.activeHoverBtn == 3:
                    self.setRightClick()
                elif self.activeHoverBtn == 4:
                    self.mouseUpScroll()
                elif self.activeHoverBtn == 5:
                    self.mouseDownScroll()
                elif self.activeHoverBtn == 6:
                    self.setFreeClick()
                elif self.activeHoverBtn == 7:
                    self.setOneTimeClick()
                elif self.activeHoverBtn == 8:
                    self.runEmergencyCall()
                elif self.activeHoverBtn == 9:
                    self.setVolumeUp()
                elif self.activeHoverBtn == 10:
                    self.setVolumeDown()
                elif self.activeHoverBtn == 11:
                    self.keyboardOpen()
                elif self.activeHoverBtn == 12:
                    self.keyboardClose()

            if cnt==0:
                self.mouseTriggerEye()
            self.updateIdle()

    def display_video_stream(self):
        _, frame = self.capture.read()
        self.mouseIdleTimeAndUpdate()

        returnedParameters=self.imageProcessingStage(frame)

        if (len(returnedParameters))==8:
            retImage, l4, headPoints, lPupilG, rPupilG, nosePG, llookG, rlookG = returnedParameters
            h, ll, rr, _ = self.getNormalLenAndPointV2(lPupilG, rPupilG, nosePG)
            if self.screenCalibrationStatus == True:
                self.screenCalRst.setEnabled(True)
                self.screenCal.setEnabled(False)
                if self.headOutOfAreaFlag == False:
                    yonUD = self.upDownDirectionSet(l4, h, ll, rr, llookG, rlookG)
                    self.mouseMoverV2(yonUD)
                if self.setEyeCenterFlag == True:
                    self.setupWindowLocLeft()
                    self.setEyeCenterFlag = False
            else:
                self.screenCalRst.setEnabled(False)
                self.screenCal.setEnabled(True)

            if self.screenCalibrationFlag == True and self.screenCount <= 11:
                if self.w is None:
                    x, y = self.screenCalibrationPoints()
                    self.playSoundWithTriggerSelect(1, self.screenCount)
                    if self.screenCount < 5:
                        self.w = calibration_anim.ScreenCalibration(x, y, t=self.caltime, screen="in")
                    elif self.screenCount > 4 and self.screenCount < 9:
                        self.w = calibration_anim.ScreenCalibration(x, y, t=self.caltime, screen="out")
                    else:
                        self.w = calibration_anim.ScreenCalibration(x, y, t=self.caltime, screen="blink")
                    self.w.show()
                    self.screenCount += 1

                if (self.w.isVisible() == False) and self.w is not None:
                    print(self.screenCount)
                    self.earsOfEyes.append(l4)
                    self.cameraCropPoints.append(headPoints)
                    self.triangelPointsAndDatasOfEyes.append([h, ll, rr])
                    self.llooksrlooks.append([llookG, rlookG])
                    self.screenPoint.append(l4)
                    self.w = None
        else:
            retImage,value=returnedParameters

        retImage = imutils.resize(retImage, width=self.cameraWidth)
        image = qimage2ndarray.array2qimage(retImage)
        self.image_label.setPixmap(QPixmap.fromImage(image))

        if len(self.screenPoint) == 11 and self.screenCalibrationFlag == True:
            self.leftLookThresholdPercentageL=round((self.llooksrlooks[1][0]+self.llooksrlooks[5][0])/2,2)
            self.leftLookThresholdPercentageR=round((self.llooksrlooks[1][1]+self.llooksrlooks[5][1])/2,2)
            self.rightLookThresholdPercentageL=round((self.llooksrlooks[3][0]+self.llooksrlooks[7][0])/2,2)
            self.rightLookThresholdPercentageR=round((self.llooksrlooks[3][1]+self.llooksrlooks[7][1])/2,2)

            uF1=self.triangelPointsAndDatasOfEyes[6][0]-self.triangelPointsAndDatasOfEyes[2][0]
            self.upLookThreshold=self.triangelPointsAndDatasOfEyes[2][0]+round(uF1*self.upDownCoeff)

            lB=self.earsOfEyes[4][0]-self.earsOfEyes[8][0]
            lB=math.floor(lB*self.upDownCoeff* 100)/100.0
            lB=lB+self.earsOfEyes[9][0]

            rB=self.earsOfEyes[4][1]-self.earsOfEyes[8][1]
            rB=math.floor(rB*self.upDownCoeff* 100)/100.0
            rB=rB+self.earsOfEyes[10][1]

            if lB>=self.earsOfEyes[10][0] and rB<self.earsOfEyes[9][1]:
                self.rightBlinkThreshold = rB
                self.leftBlinkThreshold =round((self.earsOfEyes[8][0]+self.earsOfEyes[9][0])*self.upDownCoeff,2)
                self.rightBlinkCalFlag=True
                self.playSoundWithTriggerSelect(1,21)
            elif rB>=self.earsOfEyes[9][1] and lB<self.earsOfEyes[10][0]:
                self.leftBlinkThreshold = lB
                self.rightBlinkThreshold =round((self.earsOfEyes[8][1]+self.earsOfEyes[10][1])*self.upDownCoeff,2)
                self.leftBlinkCalFlag = True
                self.playSoundWithTriggerSelect(1,22)
            elif rB>=self.earsOfEyes[9][1] and lB>=self.earsOfEyes[10][0]:
                self.rightBlinkThreshold =round((self.earsOfEyes[8][1]+self.earsOfEyes[10][1])*self.upDownCoeff,2)
                self.leftBlinkThreshold =round((self.earsOfEyes[8][0]+self.earsOfEyes[9][0])*self.upDownCoeff,2)
                self.playSoundWithTriggerSelect(1,23)
            else:
                self.leftBlinkThreshold = lB
                self.rightBlinkThreshold = rB
                self.rightBlinkCalFlag = True
                self.leftBlinkCalFlag = True
                self.playSoundWithTriggerSelect(1,20)
            # for tt in self.llooksrlooks:
            #     #pass
            #     print(tt)

            p1TopX = 0
            p2TopX = 0
            p3TopX = 0
            p4TopX = 0
            p1TopY = 0
            p2TopY = 0
            p3TopY = 0
            p4TopY = 0
            for l in self.cameraCropPoints:
                p1TopX += l[0][0]
                p2TopX += l[1][0]
                p3TopX += l[2][0]
                p4TopX += l[3][0]
                p1TopY += l[0][1]
                p2TopY += l[1][1]
                p3TopY += l[2][1]
                p4TopY += l[3][1]


            HEAD_POINT["L"] = np.array([int(p1TopX / len(self.cameraCropPoints)),int(p1TopY / len(self.cameraCropPoints))])
            HEAD_POINT["R"] = np.array([int(p2TopX / len(self.cameraCropPoints)),int(p2TopY / len(self.cameraCropPoints))])
            HEAD_POINT["U"] = np.array([int(p3TopX / len(self.cameraCropPoints)),int(p3TopY / len(self.cameraCropPoints))])
            HEAD_POINT["D"] = np.array([int(p4TopX / len(self.cameraCropPoints)),int(p4TopY / len(self.cameraCropPoints))])
            self.calibrationH=round((self.triangelPointsAndDatasOfEyes[0][0]+self.triangelPointsAndDatasOfEyes[1][0]+self.triangelPointsAndDatasOfEyes[3][0])/3)

            print(self.upLookThreshold, "****")
            print(self.leftBlinkThreshold, "****")
            print(self.rightBlinkThreshold, "****")
            print(self.calibrationH,"****")
            print(self.leftLookThresholdPercentageL, "****")
            print(self.leftLookThresholdPercentageR, "****")
            print(self.rightLookThresholdPercentageL, "****")
            print(self.rightLookThresholdPercentageR,"****")
            #print(HEAD_POINT)
            self.statusBarLabelSC.setText(self.st.activeLangPack["scOK"])
            self.screenCalibrationFlag=False
            self.screenCalibrationStatus = True

    def screenCalibrationPoints(self,w=100,h=100):
        i=self.screenCount
        hs = self.hs
        ws = self.ws
        x=0
        y=0
        if i==0:
            x = (ws / 2) - (w / 2)
            y = (hs / 2) - (h / 2)
        elif i==1:
            x=0
            y=hs/2 - (h / 2)
        elif i==2:
            x=ws/2 - (w / 2)
            y=0
        elif i==3:
            x=ws - w
            y=hs/2 - (h / 2)
        elif i==4:
            x=ws/2 - (w / 2)
            y=hs - h
        elif i==5:
            x=0
            y=hs/2 - (h / 2)
        elif i==6:
            x=ws/2 - (w / 2)
            y=0
        elif i==7:
            x=ws - w
            y=hs/2 - (h / 2)
        elif i==8:
            x=ws/2 - (w / 2)
            y=hs - h
        elif i==9:
            x = ws / 2 - (w / 2)
            y = 0
        elif i==10:
            x = ws / 2 - (w / 2)
            y = 0
        return x,y

    def upDownDirectionSet(self, l4,h,ll,rr,llook,rlook):
        earl=l4[0]
        earr=l4[1]
        if self.lBlinkStatus==False and self.rBlinkStatus==False:
            if h>self.upLookThreshold:
                yon="U"
            elif earl < self.leftBlinkThreshold and earr < self.rightBlinkThreshold:
                yon="D"
            elif llook<self.leftLookThresholdPercentageL and rlook>self.leftLookThresholdPercentageR:
                yon="L"
            elif llook>self.rightLookThresholdPercentageL and rlook<self.rightLookThresholdPercentageR:
                yon="R"
            else:
                yon="M"
        else:
            yon = "M"
        return yon

    def mouseMoverV2(self,directionUD):
        mx,my=pyautogui.position()
        toleranceLimit=self.mouseScreenToleranceLimit
        toleranceLimitLU=2
        if directionUD=="L":
            if mx-self.mousegap>toleranceLimitLU:
                pyautogui.moveTo(mx-self.mousegap,my)#go left
            else:
                pyautogui.moveTo(toleranceLimitLU,my)#go left
        if directionUD=="R":
            if mx+self.mousegap<self.ws-toleranceLimit:
                pyautogui.moveTo(mx+self.mousegap,my)#go left
            else:
                pyautogui.moveTo(self.ws-toleranceLimit, my)
        if directionUD=="D":
            if my+self.mousegap<self.hs-toleranceLimit:
                pyautogui.moveTo(mx,my+self.mousegap)#go down
            else:
                pyautogui.moveTo(mx,self.hs-toleranceLimit)
        if directionUD=="U":
            pyautogui.moveTo(mx,my-self.mousegap)#go up

    def mouseTriggerEye(self):
       # if self.mouseBehavior!=None:
        #    self.playSoundWithTrigger(1)
        if self.mouseBehavior==1:
            pyautogui.click()
            self.playSoundWithTrigger(1)
        elif self.mouseBehavior==0:
            self.mouseBehavior=None
        elif self.mouseBehavior==2:
            pyautogui.doubleClick()
            self.playSoundWithTrigger(1)
        elif self.mouseBehavior==3:
            pyautogui.rightClick()
            self.playSoundWithTrigger(1)
        elif self.mouseBehavior==4:
            pyautogui.scroll(-self.scrolldist)
        elif self.mouseBehavior==5:
            pyautogui.scroll(self.scrolldist)

        if self.oneTimeClickStatus==True:
            self.mouseBehavior=None
            self.resetBtnStyle()

    def playSoundWithTrigger(self,selection):
        if selection==1:
            if self.clickSoundLevel==1:
                play = threading.Thread(target=playsound, args=("./app_files/process_soundL.mp3",))
                play.start()
            elif self.clickSoundLevel==2:
                play = threading.Thread(target=playsound, args=("./app_files/process_sound.mp3",))
                play.start()

    def playSoundWithTriggerSelect(self,selection,fileNo):
        if self.activeLang=="Türkçe":
            lr="tr"
        else:
            lr="en"
        if selection==1:
            play = threading.Thread(target=playsound, args=("./app_files/"+str(fileNo)+"_"+lr+".mp3",))
            play.start()

    def distance(self,point_1, point_2):
        dist = sum([(i - j) ** 2 for i, j in zip(point_1, point_2)]) ** 0.5
        return dist

    def eu_distance(self,p1, p2):
        x1, y1 = p1.ravel()
        x2, y2 = p2.ravel()
        distance = ((x1 - x2) ** 2 + (y1 - y2) ** 2)**0.5
        return distance

    def getNormalLenAndPointV2(self,p1, p2, p3):
        # p1 left eye, p2 right eye, p3 nose
        c = math.sqrt((p2[0] - p3[0]) ** 2 + (p2[1] - p3[1]) ** 2)
        b = math.sqrt((p1[0] - p3[0]) ** 2 + (p1[1] - p3[1]) ** 2)
        a = math.sqrt((p1[0] - p2[0]) ** 2 + (p1[1] - p2[1]) ** 2)
        cos_C = (a ** 2 + b ** 2 - c ** 2) / (2 * a * b)
        C_radyan = math.acos(cos_C)
        shortLine = b * math.cos(C_radyan)
        longLine = b * math.sin(C_radyan)
        if (p2[0] - p1[0]) != 0:
            slope = math.atan((p2[1] - p1[1]) / (p2[0] - p1[0]))
        else:
            slope = math.pi / 2
        x_end = p1[0] + shortLine * math.cos(slope)
        y_end = p1[1] + shortLine * math.sin(slope)

        distL = self.eu_distance(np.array([p1[0],p1[1]]), np.array([round(x_end), round(y_end)]))
        distR = self.eu_distance(np.array([p2[0],p2[1]]), np.array([round(x_end), round(y_end)]))
        return round(longLine), round(distL), round(distR), [round(x_end), round(y_end)]

    def imageProcessingStage(self,image):
        image = cv2.flip(image, 1)
        image_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        rows, cols, _ = image_rgb.shape
        image = cv2.cvtColor(image_rgb, cv2.COLOR_BGR2GRAY)
        img_h, img_w = image.shape[:2]
        results = fDetector.findFace(image_rgb)

        if results.multi_face_landmarks:
            mesh_points = np.array(
                [np.multiply([p.x, p.y], [img_w, img_h]).astype(int) for p in results.multi_face_landmarks[0].landmark])
            (l_cx, l_cy), l_radius = cv2.minEnclosingCircle(mesh_points[config.LEFT_IRIS])
            (r_cx, r_cy), r_radius = cv2.minEnclosingCircle(mesh_points[config.RIGHT_IRIS])
            center_left = np.array([l_cx, l_cy], dtype=np.int32)
            center_right = np.array([r_cx, r_cy], dtype=np.int32)

            #göz bebekleri turkuaz olarak işaretlenir
            cv2.circle(image_rgb, center_left, int(l_radius), (0, 255, 255), 1, cv2.LINE_AA)
            cv2.circle(image_rgb, center_right, int(r_radius), (0, 255, 255), 1, cv2.LINE_AA)

            ldist1=self.eu_distance(center_left,mesh_points[config.L_H_LEFT][0])
            ldist2 = self.eu_distance(center_left, mesh_points[config.L_H_RIGHT][0])
            rdist1 = self.eu_distance(center_right, mesh_points[config.R_H_LEFT][0])
            rdist2 = self.eu_distance(center_right, mesh_points[config.R_H_RIGHT][0])
            llook=round(ldist1/ldist2,2)
            rlook=round(rdist2/rdist1,2)


            self.xPupilL=int(center_left[0])
            self.yPupilL=int(center_left[1])
            self.xPupilR=int(center_right[0])
            self.yPupilR=int(center_right[1])
            self.nosePoint=mesh_points[1]
            lPupil=[int(center_left[0]),int(center_left[1])]
            rPupil=[int(center_right[0]),int(center_right[1])]
            noseP=mesh_points[1]

            P2_P6l = self.distance(mesh_points[config.chosen_left_eye_idxs][1], mesh_points[config.chosen_left_eye_idxs][5])
            P3_P5l = self.distance(mesh_points[config.chosen_left_eye_idxs][2], mesh_points[config.chosen_left_eye_idxs][4])
            P1_P4l = self.distance(mesh_points[config.chosen_left_eye_idxs][0], mesh_points[config.chosen_left_eye_idxs][3])

            P2_P6r = self.distance(mesh_points[config.chosen_right_eye_idxs][1], mesh_points[config.chosen_right_eye_idxs][5])
            P3_P5r = self.distance(mesh_points[config.chosen_right_eye_idxs][2], mesh_points[config.chosen_right_eye_idxs][4])
            P1_P4r = self.distance(mesh_points[config.chosen_right_eye_idxs][0], mesh_points[config.chosen_right_eye_idxs][3])

            earl = (P2_P6l + P3_P5l) / (2.0 * P1_P4l)
            earr = (P2_P6r + P3_P5r) / (2.0 * P1_P4r)
            l4 = [round(earl,2), round(earr,2)]


            if earl<self.leftBlinkThreshold and earr<self.rightBlinkThreshold and self.reflexEyeBlinkFlag==False:
                self.reflexEyeBlinkFlag=True
                self.reflexEyeBlinkTime=time.time()
            if earl<self.leftBlinkThreshold and earr<self.rightBlinkThreshold and self.reflexEyeBlinkFlag==True:
                if time.time()-self.reflexEyeBlinkTime>self.reflexTimeB:
                    self.reflexEyeBlinkFlagNew=True
            else:
                self.reflexEyeBlinkFlagNew=False
                self.reflexEyeBlinkTime = time.time()
                self.reflexEyeBlinkFlag = False

            if earl<self.leftBlinkThreshold and earr>self.rightBlinkThreshold and self.reflexEyeBlinkFlagNew==False and self.leftBlinkCalFlag==True:
               # print("sol gözle ilgili yerdeyiz")
                self.lBlinkStatus=True
                if self.leftEyeBlinkFlag==False:
                    self.leftEyeBlinkTime=time.time()
                    self.leftEyeBlinkFlag=True
                elif self.leftEyeBlinkFlag == True and time.time() - self.leftEyeBlinkTime > self.idleTimeForBlink:
                    self.leftEyeBlinkFlag = False
                    self.leftEyeBlinkTime = time.time()
                    self.playSoundWithTrigger(1)
                    pyautogui.click()
            else:
                self.leftEyeBlinkFlag = False
                self.leftEyeBlinkTime = time.time()
                self.lBlinkStatus = False

            if earl>self.leftBlinkThreshold and earr<self.rightBlinkThreshold and self.reflexEyeBlinkFlagNew==False and self.rightBlinkCalFlag==True:
                #print("sağ gözle ilgili yerdeyiz")
                self.rBlinkStatus = True
                if self.rightEyeBlinkFlag==False:
                    self.rightEyeBlinkTime=time.time()
                    self.rightEyeBlinkFlag=True

                elif self.rightEyeBlinkFlag == True and time.time() - self.rightEyeBlinkTime > self.idleTimeForBlink:
                    #print(self.rightEyeBlinkFlag, time.time() - self.rightEyeBlinkTime)
                    self.rightEyeBlinkFlag = False
                    self.rightEyeBlinkTime = time.time()
                    self.playSoundWithTrigger(1)
                    pyautogui.doubleClick()#rightClick()
            else:
                self.rightEyeBlinkFlag = False
                self.rightEyeBlinkTime = time.time()
                self.rBlinkStatus = False


            if self.cameraStartPoint[0] == 0 and self.cameraStartPoint[1] == 0:
                HEAD_POINT["L"] = mesh_points[config.HEAD_H][0]
                HEAD_POINT["R"] = mesh_points[config.HEAD_H][1]
                HEAD_POINT["U"] = mesh_points[config.HEAD_V][0]
                HEAD_POINT["D"] = mesh_points[config.HEAD_V][1]
                #print(HEAD_POINT)


            headPointsList=[mesh_points[config.HEAD_H][0],mesh_points[config.HEAD_H][1],mesh_points[config.HEAD_V][0],mesh_points[config.HEAD_V][1]]

            #yüzdeki kırmızı ve beyaz noktalar işaretlenir
            cv2.circle(image_rgb, mesh_points[config.HEAD_H][0], 10, (255, 255, 255), -1, cv2.LINE_AA)
            cv2.circle(image_rgb, mesh_points[config.HEAD_H][1], 10, (255, 255, 255), -1, cv2.LINE_AA)
            cv2.circle(image_rgb, mesh_points[config.HEAD_V][0], 10, (255, 255, 255), -1, cv2.LINE_AA)
            cv2.circle(image_rgb, mesh_points[config.HEAD_V][1], 10, (255, 255, 255), -1, cv2.LINE_AA)

            cv2.circle(image_rgb, HEAD_POINT["L"], 8, (255, 0, 0), -1, cv2.LINE_AA)
            cv2.circle(image_rgb, HEAD_POINT["R"], 8, (255, 0, 0), -1, cv2.LINE_AA)
            cv2.circle(image_rgb, HEAD_POINT["U"], 8, (255, 0, 0), -1, cv2.LINE_AA)
            cv2.circle(image_rgb, HEAD_POINT["D"], 8, (255, 0, 0), -1, cv2.LINE_AA)

            if self.cropImageCommand==True:
                self.cameraStartPoint = (
                HEAD_POINT["L"][0] - self.cameraToleranceGap, HEAD_POINT["U"][1] - self.cameraToleranceGap)
                self.cameraEndPoint = (
                HEAD_POINT["R"][0] + self.cameraToleranceGap, HEAD_POINT["D"][1] + self.cameraToleranceGap)
                color = (0, 255, 0)
                thickness = 2
                image_rgb = cv2.rectangle(image_rgb, self.cameraStartPoint, self.cameraEndPoint, color, thickness)

                cropped_image = image_rgb[
                                self.cameraStartPoint[1] - self.cameraToleranceGap:self.cameraStartPoint[1] + (self.cameraEndPoint[1] - self.cameraStartPoint[1]) + self.cameraToleranceGap,
                                self.cameraStartPoint[0] - self.cameraToleranceGap:self.cameraStartPoint[0] + (self.cameraEndPoint[0] - self.cameraStartPoint[0]) + self.cameraToleranceGap]

                labeled_img = cropped_image
            else:
                labeled_img = image_rgb  # cropped_image

            if self.screenCalibrationStatus==True:

                d1 = self.eu_distance(HEAD_POINT["L"], mesh_points[config.HEAD_H][0])
                d2 = self.eu_distance(HEAD_POINT["R"], mesh_points[config.HEAD_H][1])
                d3 = self.eu_distance(HEAD_POINT["U"], mesh_points[config.HEAD_V][0])
                d4 = self.eu_distance(HEAD_POINT["D"], mesh_points[config.HEAD_V][1])
                lDist = [round(d1,2), round(d2,2), round(d3,2), round(d4,2)]
                #print(self.opacityFlag,self.onHoverFlag)
                if self.calibrationH>0 and max(lDist)/self.calibrationH>self.calibrationBreakThreshold:
                    self.headOutOfAreaFlag = True
                    self.calibrationBreakThresholdCount+=1
                    if self.calibrationBreakThresholdCount>20:
                        #print(round(self.eu_distance(mesh_points[HEAD_H][0],mesh_points[HEAD_H][1]),2),lDist, max(lDist))
                        if self.clickSoundLevel == 1:
                            self.playSoundWithTriggerSelect(1, "31L")
                        elif self.clickSoundLevel == 2:
                            self.playSoundWithTriggerSelect(1, 31)

                        self.calibrationBreakThresholdCount =0
                        if self.opacityFlag==False and self.onHoverFlag ==False:
                            self.setWindowOpacity(self.activeOpacity)
                            self.opacityFlag=True
                else:
                    self.headOutOfAreaFlag=False
                    if self.opacityFlag == True and self.onHoverFlag == False:
                        self.setWindowOpacity(self.deactiveOpacity)
                        self.opacityFlag=False
                    #print("calibrasyon noktan bozuluyor düzelt")
                #print(self.reflexEyeBlinkFlag,self.reflexEyeBlinkFlagNew)

                if  self.reflexEyeBlinkFlagNew==True:
                    return labeled_img,l4,headPointsList,lPupil,rPupil,noseP,llook,rlook
                else:
                    return labeled_img, [1,1],headPointsList,lPupil,rPupil,noseP,llook,rlook
            else:
                #return labeled_img, int(center_left[0]), int(center_left[1]), int(0)
                #print("burasi calisti")
                return labeled_img,l4,headPointsList,lPupil,rPupil,noseP,llook,rlook
        else:
            overlay_png = cv2.imread('./app_files/nohead.png', -1)
            alpha = cv2.resize(overlay_png[:, :, 3], (image_rgb.shape[1], image_rgb.shape[0]))
            combined = cv2.bitwise_and(overlay_png[:, :, 0:3], overlay_png[:, :, 0:3], mask=alpha)
            background = cv2.bitwise_and(image_rgb, image_rgb, mask=cv2.bitwise_not(alpha))
            result = cv2.add(combined, background)

            return result,0

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Escape:
            # self.close()
            pass

    def abs_distance(self,p1,p2):
        distance=abs(p1[1]-p2[1])
        return distance

    def alreadyrunning(self):
        return (self.lasterror == ERROR_ALREADY_EXISTS)

    def __del__(self):
        if self.mutex:
            CloseHandle(self.mutex)

    def showRuntimeError(self):
        button = QMessageBox.critical(self, "Error", "Another copy of the application is running. Make sure the other application is closed and try again.", buttons=QMessageBox.Ok)
        return button

win = MainApp()
splash.finish(win)
if win.alreadyrunning():
    sys.exit(1)
else:
    win.show()
sys.exit(app.exec_())