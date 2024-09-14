from PySide2.QtWidgets import QApplication, QWidget, QPushButton,QLabel,QComboBox
from PySide2.QtCore import Signal
import struct


class settingScreen(QWidget):
    valueChanged = Signal(list)

    def __init__(self,x,y,w=300,h=400):
        super().__init__()
        # self.configFile="./app_files/config.inno"
        self.configFile = "./app_files/configBin.inno"
        params=self.read_binary_data(self.configFile)
        self.version="v1.2.8"
        self.w=w
        self.h=h
        self.x=x
        self.y=y
        self.tolerance=str(params[0])
        self.idletime=str(params[1])
        self.caltime=str(params[2])
        self.mousegap=str(params[3])
        self.scrolldist=str(params[4])
        if params[5]==1:
            self.activeLang="English"
        else:
            self.activeLang="Türkçe"
        self.clickSLevel=int(params[6])


        self.langPackageTR={"file":"Dosya","calibration":"Kalibrasyon","connect":"Görüntü","selCam":"Kamera Seç:","mLeft":"Sola Taşı","mRight":"Sağa Taşı",
                            "lClick": "Sol Tıklama","rClick":"Sağ Tıklama","dClick":"Çift Tıklama","fMove":"Serbest Gezin","sUp":"Yukarı Kaydır","sDown":"Aşağı Kaydır",
                            "otClick":"Tek Sefer Tıklama","ftClick":"Sürekli Tıklama","eCall":"Acil Durum Zili","vUp":"Ses Arttır","vDown":"Ses Azalt","oKB":"Klavye Aç","cKB":"Klavye Kapat",
                            "scNone":"SC:Yapılmadı","scOK":"SC:Tamamlandı","sett":"Ayarlar","ext":"Çıkış","calSc":"Ekran Kalibrasyonu","resetSc":"Kalibrasyonu Sıfırla","conCam":"Kameraya Bağlan","crop":"Görüntüyü Hizala",
                            "udCoeff":"Yukarı Aşağı Bakış Katsayısı:","idTime":"Tık İçin Bekleme Süresi (s):","calTime":"Kalibrasyon Süresi (s):","mGap":"Fare Boşluğu (px):",
                            "sDist":"Kaydırma Mesafesi (px):","aLang":"Aktif Dil:","rDef":"Varsayılanı Yükle","sSet":"Ayarları Kaydet\nve Uygula","sTitle":"Ayarlar","sClickS":"Klik Ses Seviyesi","openPDF":"Kullanım Kılavuzunu Aç",
                            "error":"Hata","pdfError":"PDF dosyası açılamadı."}

        self.langPackageENG={"file":"File","calibration":"Calibration","connect":"Image","selCam":"Select Cam:","mLeft":"Move Left","mRight":"Move Right",
                            "lClick": "Left Click","rClick":"Right Click","dClick":"Double Click","fMove":"Free Move","sUp":"Scroll Up","sDown":"Scroll Down",
                            "otClick":"One Time Click","ftClick":"Full Time Click","eCall":"Emergency Call","vUp":"Volume Up","vDown":"Volume Down","oKB":"Open KB","cKB":"Close KB",
                            "scNone":"SC:None","scOK":"SC:OK","sett":"Settings","ext":"Exit","calSc":"Screen Calibration","resetSc":"Reset Calibration","conCam":"Connect Camera","crop":"Align Image",
                            "udCoeff":"Up Down Look Coefficient:","idTime":"Idle Time for Click (s):","calTime":"Calibration Time (s):","mGap":"Mouse Gap (px):",
                            "sDist":"Scroll Distance (px):","aLang":"Active Language:","rDef":"Restore Default","sSet":"Save Settings\nand Apply","sTitle":"Settings","sClickS":"Click Volume Level","openPDF":"Open User Manual",
                             "error":"Error","pdfError":"Could not open PDF file."}

        if self.activeLang=="English":
            self.activeLangPack=self.langPackageENG
            self.clickSoundLevels=["Off","Low","Normal"]
        else:
            self.activeLangPack = self.langPackageTR
            self.clickSoundLevels = ["Kapalı", "Düşük", "Normal"]
        # self.setWindowFlags(Qt.WindowStaysOnTopHint | Qt.FramelessWindowHint)
        self.setFixedSize(self.w,self.h)
        self.setWindowTitle(self.activeLangPack["sTitle"])
        self.xx=(self.x-self.w)/2-self.w
        self.yy=(self.y-self.h)/2
        self.setGeometry(self.xx, self.yy, self.w, self.h)
        self.set_ui()


    def set_ui(self):
        self.toleranceLabel = QLabel(self.activeLangPack["udCoeff"], self)
        self.toleranceLabel.setGeometry(20, 30, 160, 20)
        self.toleranceCombo = QComboBox(self)
        self.toleranceCombo.setGeometry(180, 30, 100, 20)
        self.toleranceCombo.addItems(self.retList(1,3,1))
        self.toleranceCombo.setCurrentText(self.tolerance)

        self.idleTimeLabel = QLabel(self.activeLangPack["idTime"], self)
        self.idleTimeLabel.setGeometry(20, 60, 160, 20)
        self.idleTimeLabelCombo = QComboBox(self)
        self.idleTimeLabelCombo.setGeometry(180, 60, 100, 20)
        self.idleTimeLabelCombo.addItems(self.retList(1,5,1))
        self.idleTimeLabelCombo.setCurrentText(self.idletime)

        self.calTimeLabel = QLabel(self.activeLangPack["calTime"], self)
        self.calTimeLabel.setGeometry(20, 90, 160, 20)
        self.calTimeCombo = QComboBox(self)
        self.calTimeCombo.setGeometry(180, 90, 100, 20)
        self.calTimeCombo.addItems(self.retList(1,5,1))
        self.calTimeCombo.setCurrentText(self.caltime)

        self.mouseGapLabel = QLabel(self.activeLangPack["mGap"], self)
        self.mouseGapLabel.setGeometry(20, 120, 160, 20)
        self.mouseGapCombo = QComboBox(self)
        self.mouseGapCombo.setGeometry(180, 120, 100, 20)
        self.mouseGapCombo.addItems(self.retList(5,25,5))
        self.mouseGapCombo.setCurrentText(self.mousegap)

        self.scrolldistLabel = QLabel(self.activeLangPack["sDist"], self)
        self.scrolldistLabel.setGeometry(20, 150, 160, 20)
        self.scrolldistCombo = QComboBox(self)
        self.scrolldistCombo.setGeometry(180, 150, 100, 20)
        self.scrolldistCombo.addItems(self.retList(40,200,40))
        self.scrolldistCombo.setCurrentText(self.scrolldist)

        self.activeLangLabel = QLabel(self.activeLangPack["aLang"], self)
        self.activeLangLabel.setGeometry(20, 180, 160, 20)
        self.activeLangCombo = QComboBox(self)
        self.activeLangCombo.setGeometry(180, 180, 100, 20)
        self.activeLangCombo.addItems(["English","Türkçe"])
        self.activeLangCombo.setCurrentText(self.activeLang)

        self.clickSoundLabel = QLabel(self.activeLangPack["sClickS"], self)
        self.clickSoundLabel.setGeometry(20, 210, 160, 20)
        self.clickSoundCombo = QComboBox(self)
        self.clickSoundCombo.setGeometry(180, 210, 100, 20)
        self.clickSoundCombo.addItems(self.clickSoundLevels)
        self.clickSoundCombo.setCurrentIndex(self.clickSLevel)

        self.resetBtn = QPushButton(self)
        self.resetBtn.setGeometry(20, 250, 100, 50)
        self.resetBtn.setText(self.activeLangPack["rDef"])
        self.resetBtn.clicked.connect(self.restoreDefault)

        self.saveBtn = QPushButton(self)
        self.saveBtn.setGeometry(180, 250, 100, 50)
        self.saveBtn.setText(self.activeLangPack["sSet"])
        self.saveBtn.clicked.connect(self.saveSetting)

    def readParameters(self,file):
        with open(file, "r") as myFile:
            parameters = myFile.read().split(",")
            return parameters

    def retList(self,start,limit,step):
        lst=[]
        for i in range(start,limit+1,step):
            lst.append(str(i))
        return lst

    def restoreDefault(self):
        self.toleranceCombo.setCurrentText("2")
        self.idleTimeLabelCombo.setCurrentText("2")
        self.calTimeCombo.setCurrentText("3")
        self.mouseGapCombo.setCurrentText("10")
        self.scrolldistCombo.setCurrentText("40")
        self.activeLangCombo.setCurrentText("English")
        self.clickSoundCombo.setCurrentIndex(2)

    def saveSetting(self):

        self.tolerance=self.toleranceCombo.currentText()
        self.idletime=self.idleTimeLabelCombo.currentText()
        self.caltime=self.calTimeCombo.currentText()
        self.mousegap=self.mouseGapCombo.currentText()
        self.scrolldist=self.scrolldistCombo.currentText()
        self.activeLang=self.activeLangCombo.currentText()
        self.clickSLevel=self.clickSoundCombo.currentIndex()

        if self.activeLang=="English":
            self.activeLangNo = 1
            self.activeLangPack=self.langPackageENG
            self.clickSoundLevels=["Off","Low","Normal"]
        else:
            self.activeLangPack = self.langPackageTR
            self.activeLangNo = 2
            self.clickSoundLevels = ["Kapalı", "Düşük", "Normal"]

        self.setWindowTitle(self.activeLangPack["sTitle"])
        self.toleranceLabel.setText(self.activeLangPack["udCoeff"])
        self.idleTimeLabel.setText(self.activeLangPack["idTime"])
        self.calTimeLabel.setText(self.activeLangPack["calTime"])
        self.mouseGapLabel.setText(self.activeLangPack["mGap"])
        self.scrolldistLabel.setText(self.activeLangPack["sDist"])
        self.activeLangLabel.setText(self.activeLangPack["aLang"])
        self.clickSoundLabel.setText(self.activeLangPack["sClickS"])
        self.resetBtn.setText(self.activeLangPack["rDef"])
        self.saveBtn.setText(self.activeLangPack["sSet"])
        self.clickSoundCombo.clear()
        self.clickSoundCombo.addItems(self.clickSoundLevels)
        self.clickSoundCombo.setCurrentIndex(self.clickSLevel)


        self.valueChanged.emit([self.tolerance,self.idletime,self.caltime,self.mousegap,self.scrolldist,self.activeLangNo,self.clickSLevel])
        # tolerance,idletime,caltime,mousegap,scrolldist,activelanguage,clickSound
        parameters=[int(self.toleranceCombo.currentText()),
                                     int(self.idleTimeLabelCombo.currentText()),
                                     int(self.calTimeCombo.currentText()),
                                     int(self.mouseGapCombo.currentText()),
                                     int(self.scrolldistCombo.currentText()),
                                     int(self.activeLangNo),
                                    int(self.clickSoundCombo.currentIndex())]
        self.write_binary_data(parameters,self.configFile)

        self.close()

    def writeParameters(self,params, file):
        with open(file, "w") as myFile:
            myFile.write(",".join(params))

    def write_binary_data(self,data,filename):
        with open(filename, 'wb') as file:
            for item in data:
                file.write(struct.pack('I', item))

    def read_binary_data(self,filename):
        result = []
        with open(filename, 'rb') as file:
            while True:
                data = file.read(4)
                if not data:
                    break
                result.append(struct.unpack('I', data)[0])
        return result

