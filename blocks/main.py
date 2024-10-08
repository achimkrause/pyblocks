import sys
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame,
    QComboBox, QPushButton, QCheckBox
)
from PyQt6.QtCore import Qt, QTimer, pyqtSignal, QObject
from PyQt6.QtGui import QPainter, QColor
import numpy as np

from position import Position
from game import Game
from ai_random import AIRandomTemplate
from ai_mcts import AIMCTSTemplate
from ai import AIPlayerTemplate
from learning import Training

from pathlib import Path

from player import HumanPlayerTemplate

import argparse

movesColor = QColor(200,200,200)
playerColor = [QColor(75,75,75),QColor(227,225,161)]
textColor = QColor(0,0,255)

radius=5
click_radius=10

bar_width_proportion  = 0.6 #percentage of screen width
bar_height_proportion = 0.2 #percentage of grid size
bar_margin_proportion = 0.4 #percentage of grid size


class BoardGameArea(QWidget):
    move_click_signal0=pyqtSignal(int,int)
    move_click_signal1=pyqtSignal(int,int)
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumSize(600, 600)  # Set size of the board game area
        self.position = None
        self.active_player = 0
        self.move_click_signal=[self.move_click_signal0,self.move_click_signal1]
    def update_position(self,position):
        self.position = position
        if self.position.flipped:
            self.active_player = 1
        else:
            self.active_player = 0
        self.clear_additional_info()
    def paintEvent(self, event):
        self.update_dimensions()
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        self.draw_pieces(painter)
        self.draw_valid_moves(painter)
        if(hasattr(self,"additional_info") and self.additional_info != None):
            self.draw_additional_info(painter)
    def draw_pieces(self,painter):
        if self.position == None:
            return
        for i in range(11):
            for k in range(17):
                if self.position.pieces[0][i][k]:
                    self.draw_piece(i,k,playerColor[self.active_player],painter)
                if self.position.pieces[1][i][k]:
                    self.draw_piece(i,k,playerColor[1-self.active_player],painter)
    def draw_valid_moves(self,painter):
        if self.position == None:
            return
        for i in range(11):
            for k in range(17):
                if self.position.valid_moves[i][k]:
                    self.draw_valid_move(i,k,painter)
    def draw_additional_info(self,painter):
        for i in range(11):
            for k in range(17):
                if (i,k) in self.additional_info.children:
                    count = self.additional_info.children[(i,k)].visit_count
                    val = 1.0-(self.additional_info.children[(i,k)].value/count)
                    self.draw_info(i,k,"{},{:.2f}".format(count,val),painter)
        prior_value = self.additional_info.prior_value
        value = self.additional_info.action_value()
        self.draw_bars(prior_value,value,painter)
    def draw_bars(self,prior_value, value,painter):
        grid_size = self.grid_size
        bar_width = int(bar_width_proportion * self.width())
        bar_height = int(bar_height_proportion * grid_size)
        bar_margin = int(bar_margin_proportion * grid_size)
        posX = int((1-bar_width_proportion)/2*self.width())
        posY = self.game_area_originY + bar_margin
        cutX_value = int(value*bar_width)
        cutX_prior_value = int(prior_value*bar_width)

        painter.setBrush(playerColor[self.active_player])
        painter.setPen(QColor(0,0,0,0))
        painter.drawRect(posX, posY, cutX_value, bar_height)
        painter.drawRect(posX, posY+bar_height, cutX_prior_value, bar_height)
        painter.setBrush(playerColor[1-self.active_player])
        painter.drawRect(posX+cutX_value, posY, bar_width-cutX_value, bar_height)
        painter.drawRect(posX+cutX_prior_value, posY+bar_height, bar_width-cutX_prior_value, bar_height)
    def update_dimensions(self):
        grid_width = 11
        grid_height = 9 + bar_margin_proportion + 2*bar_height_proportion
        gridX=int(self.width() / grid_width)
        gridY=int(self.height() / grid_height)
        self.grid_size = min(gridX,gridY)
        self.game_area_originX = int((self.width() - grid_width * self.grid_size) / 2)
        self.game_area_originY = int((self.height() + grid_height * self.grid_size) / 2 - (bar_margin_proportion + 2*bar_height_proportion)*self.grid_size)
    def draw_valid_move(self,i,k,painter):
        grid_size=self.grid_size
        offX=self.game_area_originX
        offY=self.game_area_originY
        j = k//2
        horizontal = (k%2==0)
        if(horizontal):
            posX=offX + (1+i)*grid_size
            posY=offY - int((0.5+j)*grid_size)
        else:
            posX=offX + int((0.5+i)*grid_size)
            posY=offY - (1+j)*grid_size
        painter.setBrush(movesColor)
        painter.setPen(QColor(0,0,0,0))
        if horizontal:
            painter.drawRect(posX-2*radius, posY-radius, 4*radius, 2*radius)
        else:
            painter.drawRect(posX-radius, posY-2*radius, 2*radius, 4*radius)
    def draw_piece(self,i,k,c,painter):
        grid_size=self.grid_size
        offX=self.game_area_originX
        offY=self.game_area_originY
        j = k//2
        painter.setBrush(c)
        horizontal=(k%2==0)
        if(horizontal):
            painter.drawRect(offX+i*grid_size,offY-(j+1)*grid_size, 2*grid_size,grid_size)
        else:
            painter.drawRect(offX+i*grid_size,offY-(j+2)*grid_size, grid_size,2*grid_size)
    def draw_info(self,i,k,string,painter):
        grid_size=self.grid_size
        offX=self.game_area_originX
        offY=self.game_area_originY
        j = k//2
        horizontal = (k%2==0)
        if(horizontal):
            posX=offX + (1+i)*grid_size
            posY=offY - int((0.5+j)*grid_size) - int(1.5*radius)
        else:
            posX=offX + int((0.5+i)*grid_size)
            posY=offY - (1+j)*grid_size - int(2.5*radius)
        painter.setPen(textColor)
        painter.drawText(posX, posY, string)

    def mousePressEvent(self,event):
        grid_size=self.grid_size
        offX=self.game_area_originX
        offY=self.game_area_originY
        mouse_x = int(event.position().x())
        mouse_y = int(event.position().y())
        dot1 = ((mouse_x-offX) - (mouse_y-offY))//grid_size
        dot2 = (-(mouse_x-offX) - (mouse_y-offY))//grid_size
        k = dot1 + dot2
        i = (dot1 - dot2 - 1) // 2
        j = k//2
        horizontal = (k % 2 == 0)
        if(horizontal):
            posX=offX + (1+i)*grid_size
            posY=offY - int((0.5+j)*grid_size)
        else:
            posX=offX + int((0.5+i)*grid_size)
            posY=offY - (1+j)*grid_size
        if horizontal and abs(posX-mouse_x) <= 2*click_radius and abs(posY-mouse_y) <=click_radius:
            self.click_move_action(i,k)
        if not horizontal and abs(posX-mouse_x) <=click_radius and abs(posY-mouse_y) <= 2*click_radius:
            self.click_move_action(i,k)
    def click_move_action(self,i,k):
        if self.position == None:
            return
        if i<0 or i>10:
            return
        if k<0 or k>16:
            return
        if self.position.valid_moves[i][k]:
            self.move_click_signal[self.active_player].emit(i,k)
    def get_additional_info(self,info):
        #currently this is always the root of an MCTS tree
        self.additional_info = info
        self.update()
    def clear_additional_info(self):
        self.additional_info = None
        self.update()
        

class InfoArea(QWidget):
    player_template_changed_signal = pyqtSignal(int,object)
    restart_signal = pyqtSignal()

    def __init__(self, args, parent=None):
        super().__init__(parent)

        layout = QVBoxLayout()
        self.info_label = QLabel("", self)
        self.info_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.button = QPushButton("Restart",self)
        self.button.clicked.connect(self.restart)

        self.checkbox = QCheckBox("Autorestart")
        self.checkbox.stateChanged.connect(self.autorestart)

        self.combo_box = [QComboBox(self),QComboBox(self)]

        self.player_templates_options = [[],[]]


        self.over = False

        if(args.assistant):
            self.add_fixed_templates(None, None, args)
        elif(args.p0 == None and args.p1 == None):
            self.add_default_templates(args)
        else:
            self.add_fixed_templates(args.p0, args.p1,args)

        self.combo_box[0].currentTextChanged.connect(self.combo0changed)
        self.combo_box[1].currentTextChanged.connect(self.combo1changed)

        layout.addWidget(self.info_label)
        layout.addWidget(self.combo_box[0])
        layout.addWidget(self.combo_box[1])
        layout.addWidget(self.button)
        layout.addWidget(self.checkbox)
        self.setLayout(layout)
        self.setMinimumWidth(200)
        self.setMaximumWidth(200)
    def add_default_templates(self,args):
        self.combo_box[0].addItems(["Player", "AI (random)", "AI (MCTS)"])
        self.combo_box[1].addItems(["Player", "AI (random)", "AI (MCTS)"])
        mcts_steps = args.mcts_steps
        if mcts_steps == None:
            mcts_steps=500
        templates = [HumanPlayerTemplate(), AIPlayerTemplate(AIRandomTemplate()), AIPlayerTemplate(AIMCTSTemplate(mcts_steps=mcts_steps))]
        self.player_templates_options = [templates, templates]
    def add_fixed_templates(self,a0,a1,args):
        if(a0 == None):
            self.combo_box[0].addItems(["Player"])
            self.player_templates_options[0].append(HumanPlayerTemplate())
        else:
            mcts_steps = args.mcts_steps
            if mcts_steps == None:
                mcts_steps=500
            template = AIPlayerTemplate(AIMCTSTemplate(mcts_steps=mcts_steps,path=a0,initialize=args.initialize, training=args.train))
            self.combo_box[0].addItems(["AI {}".format(a0)])
            self.player_templates_options[0].append(template)
        if(a1 == None):
            self.combo_box[1].addItems(["Player"])
            self.player_templates_options[1].append(HumanPlayerTemplate())
        else:
            mcts_steps = args.mcts_steps
            if mcts_steps == None:
                mcts_steps=500
            template = AIPlayerTemplate(AIMCTSTemplate(mcts_steps=mcts_steps,path=a1,initialize=args.initialize, training=args.train))
            self.combo_box[1].addItems(["AI {}".format(a1)])
            self.player_templates_options[1].append(template)
        self.combo_box[0].setEnabled(False)
        self.combo_box[1].setEnabled(False)
    def combo0changed(self):
        self.combochanged(0)
    def combo1changed(self):
        self.combochanged(1)
    def combochanged(self,index):
        combo_index = self.combo_box[index].currentIndex()
        print("combo changed")
        self.player_template_changed_signal.emit(index, self.player_templates_options[index][combo_index])
    def get_player_templates(self):
        i0 = self.combo_box[0].currentIndex()
        t0 = self.player_templates_options[0][i0]
        i1 = self.combo_box[1].currentIndex()
        t1 = self.player_templates_options[1][i1]
        return [t0,t1]
    def restart(self):
        self.over = False
        self.info_label.setText("")
        self.restart_signal.emit()
    def autorestart(self):
        if(self.checkbox.isChecked() and self.over):
            self.restart()
    def show_result(self,winner):
        self.over = True
        if(winner==None):
            text="Draw!"
        else:
            color=["dark","light"]
            text="Player {} ({}) wins!".format(winner,color[winner])
        print(text)
        self.info_label.setText(text)
        self.autorestart()


class MainWindow(QMainWindow):
    def __init__(self,args):
        super().__init__()
        self.args = args

        self.setWindowTitle("Blocks")


        # Create the central widget and layout
        central_widget = QWidget()
        main_layout = QHBoxLayout(central_widget)

        # Board game area (left side)
        self.board_game_area = BoardGameArea()

        # Info area (right side)
        self.info_area = InfoArea(args)

        self.info_area.player_template_changed_signal.connect(self.change_player_template)
        self.info_area.restart_signal.connect(self.start_game)

        main_layout.addWidget(self.board_game_area)
        main_layout.addWidget(self.info_area)

        # Set the central widget for the main window
        self.setCentralWidget(central_widget)

        self.start_game()
    def start_game(self):
        player_templates = self.info_area.get_player_templates()
        players = [player_templates[0].new(), player_templates[1].new()]
        for i in range(2):
            players[i].additional_info_signal.connect(self.board_game_area.get_additional_info)
            if isinstance(player_templates[i],HumanPlayerTemplate):
                self.board_game_area.move_click_signal[i].connect(players[i].make_move)
        self.game = Game(players[0], players[1])
        self.game.update_signal.connect(self.board_game_area.update_position)
        self.game.end_signal.connect(self.info_area.show_result)
        if(self.args.assistant):
            ai_player = AIMCTSTemplate(mcts_steps=None,path=self.assistant,initialize=self.args.initialize, training=self.args.train).new()
            ai_player.additional_info_signal.connect(self.board_game_area.get_additional_info)
            #now we need to connect assistant to game
        self.game.update()
    def change_player_template(self,index,template):
        new_player = template.new()
        print("player changed")
        self.game.connect_player(index,new_player)
        new_player.additional_info_signal.connect(self.board_game_area.get_additional_info)
        if isinstance(template,HumanPlayerTemplate):
            self.board_game_area.move_click_signal[index].connect(new_player.make_move)
        

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--p0', type=str, help='Player 0 model path (leave empty for manual)')
    parser.add_argument('--p1', type=str, help='Player 1 model path (leave empty for manual)')
    parser.add_argument('--initialize', help='Initialize nonexistent filepaths.', action='store_true')
    parser.add_argument('--train', help='Store experience.', action='store_true') #should rename to practice
    parser.add_argument('--learn', help='Train a new model.', action='store_true')
    parser.add_argument('--i', type=str, help='Input model path.')
    parser.add_argument('--o', type=str, help='Output model path.')
    parser.add_argument('--overwrite', help='Override output model if existing.', action='store_true')
    parser.add_argument('--assistant', type=str, help='Manual play but with assisting model.')
    parser.add_argument('--mcts-steps', type=int, help='Number of steps in MCTS.')
    args = parser.parse_args()
    if(args.learn):
        train(args)
        exit()
    app = QApplication(sys.argv)
    window = MainWindow(args)
    window.show()
    sys.exit(app.exec())

def train(args):
    Training(Path(args.i), Path(args.o), overwrite=args.overwrite).run()

if __name__ == "__main__":
    main()

