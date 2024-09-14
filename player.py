from PySide2.QtCore import QThread
from playsound import playsound

class PlayMusicWithThread(QThread):
    def __init__(self,file):
        super().__init__()
        self.file=file

    def run(self):
        playsound(self.file)