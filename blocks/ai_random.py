import random as rnd

class AIRandom:
    def __init__(self):
        pass
    def find_move(self,position):
        count=0
        for i in range(11):
            for k in range(17):
                if position.valid_moves[i][k]:
                    count +=1
        val=rnd.randint(0,count-1)
        for i in range(11):
            for k in range(17):
                if position.valid_moves[i][k]:
                    val-=1
                    if val<0:
                        return (i,k)

        


