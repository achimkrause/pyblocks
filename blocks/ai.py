from PyQt6.QtCore import pyqtSignal, QObject, QTimer, QThread

from player import Player, PlayerTemplate

class AIThread(QThread):
    result_signal = pyqtSignal(int,int)
    def __init__(self,ai,position):
        super().__init__()
        self.ai=ai
        self.position=position
    def run(self):
        i,k=self.ai.find_move(self.position)
        self.result_signal.emit(i,k)

class AIPlayerTemplate(PlayerTemplate):
    def __init__(self,ai_template):
        super().__init__()
        self.ai_template = ai_template
    def new(self):
        ai = self.ai_template.new()
        return AIPlayer(ai)

class AIPlayer(Player):
    def __init__(self,ai):
        super().__init__()
        self.ai = ai
        ai.additional_info_signal.connect(self.additional_info_signal.emit)
    def find_move(self,position):
        self.thread = AIThread(self.ai,position)
        self.thread.result_signal.connect(self.move_signal.emit)
        self.thread.start()
    def game_end(self,game_name,value):
        self.ai.train(game_name,value)

#abstract
class AITemplate:
    def __init__(self):
        pass
    def new(self):
        return AI()

#abstract
class AI(QObject):
    additional_info_signal = pyqtSignal(object)
    def __init__(self):
        super().__init__()
    def find_move(self,position):
        pass
    def train(self,value):
        pass
