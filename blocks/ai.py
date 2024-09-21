from PyQt6.QtCore import pyqtSignal, QObject, QTimer, QThread

class AIPlayer(QThread):
    move_signal = pyqtSignal(int,int) 
    additional_info_signal = pyqtSignal(object)

    def __init__(self,ai):
        super().__init__()
        self.ai=ai
        if(hasattr(ai,"additional_info_signal")):
           ai.additional_info_signal.connect(self.additional_info_signal.emit)

    def run(self):
        i,k=self.ai.find_move(self.position)
        self.move_signal.emit(i,k)

    def find_move(self,position):
        self.position = position
        self.start()

    def save_experience(self,game_name,value):
        if(hasattr(self.ai, "save_experience")):
            self.ai.save_experience(game_name,value)





