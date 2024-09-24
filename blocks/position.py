import numpy as np

class Position:
    def __init__(self):
        #the blocks are stored in an 11x17 array.
        #[i][2j] represents the block consisting of (i,j) and (i+1,j)
        #[i][2j+1] represents the block consisting of (i,j) and (i,j+1)
        self.empty = True
        self.over = False
        self.result = None
        self.flipped = False
        self.pieces = [np.zeros(shape=(11,17),dtype=np.int8), np.zeros(shape=(11,17),dtype=np.int8)]
        self.valid_moves = np.zeros(shape=(11,17),dtype=np.int8)
        self.occupied_mask = [np.zeros(shape=(11,9),dtype=np.int8), np.zeros(shape=(11,9),dtype=np.int8)]
        self._update_valid_moves()
    def copy(self):
        copy=Position()
        copy.empty = self.empty
        copy.over = self.over
        copy.result = self.result
        copy.pieces[0] = self.pieces[0].copy()
        copy.pieces[1] = self.pieces[1].copy()
        copy.occupied_mask[0] = self.occupied_mask[0].copy()
        copy.occupied_mask[1] = self.occupied_mask[1].copy()
        copy.valid_moves = self.valid_moves.copy()
        return copy

    def _update_occupied_mask(self,index):
        for i in range(11):
            for j in range(9):
                #(i,j) is touched by [i][2j],[i-1][2j],[i][2j+1],[i][2j-1]
                ps=self.pieces[index]
                touch=ps[i][2*j]
                if(j<=7):
                    touch+=ps[i][2*j+1]
                if(i>=1):
                    touch+=ps[i-1][2*j]
                if(j>=1):
                    touch+=ps[i][2*j-1]
                if(touch>0):
                    self.occupied_mask[index][i][j]=1
                else:
                    self.occupied_mask[index][i][j]=0

    def _update_valid_moves(self):
        for i in range(11):
            for k in range(17):
                self.valid_moves[i][k]=1
                j=k//2
                horizontal = (k%2==0)

                if self.over:
                    self.valid_moves[i][k]=0
                    continue

                #because of symmetry, we may restrict the first two moves to horizontal or vertical in the middle of the board
                if self.empty:
                    if i==5 and (k==0 or k==1):
                        self.valid_moves[i][k]=1
                    else:
                        self.valid_moves[i][k]=0
                    continue

                #at the right edge, we don't have horizontal pieces
                if horizontal and i==10:
                    self.valid_moves[i][k]=0
                    continue

                #rule: pieces may not overlap
                if horizontal:
                    msk=self.occupied_mask
                    touch=msk[0][i][j]+msk[0][i+1][j]+msk[1][i+1][j]+msk[1][i][j]
                    if(touch>0):
                        self.valid_moves[i][k]=0
                        continue
                else:
                    msk=self.occupied_mask
                    touch=msk[0][i][j]+msk[0][i][j+1]+msk[1][i][j]+msk[1][i][j+1]
                    if(touch>0):
                        self.valid_moves[i][k]=0
                        continue

                #rule: pieces may only be placed on "solid ground"
                if horizontal and j>0:
                    msk=self.occupied_mask
                    below_left=msk[0][i][j-1]+msk[1][i][j-1]
                    below_right=msk[0][i+1][j-1]+msk[1][i+1][j-1]
                    if(below_left != 1 or below_right != 1):
                        self.valid_moves[i][k]=0
                        continue
                if not horizontal and j>0:
                    msk=self.occupied_mask
                    below=msk[0][i][j-1]+msk[1][i][j-1]
                    if(below != 1):
                        self.valid_moves[i][k]=0
                        continue
                #rule: pieces may not touch short ends if of same color:
                if horizontal and ((i>=2 and self.pieces[0][i-2][k]) or (i<=7 and self.pieces[0][i+2][k])):
                    self.valid_moves[i][k]=0
                    continue
                if not horizontal and ((k>=5 and self.pieces[0][i][k-4]) or (k<=11 and self.pieces[0][i][k+4])):
                    self.valid_moves[i][k]=0
                    continue
                
                #rule: wall must be connected:
                if horizontal and j==0 and not self.empty:
                    msk=self.occupied_mask
                    sides=0
                    if i>=1 and msk[0][i-1][j]+msk[1][i-1][j] == 1:
                        sides += 1
                    if i<=7 and msk[0][i+2][j]+msk[1][i+2][j] == 1:
                        sides += 1
                    if sides == 0:
                        self.valid_moves[i][k]=0
                if not horizontal and j==0 and not self.empty:
                    msk=self.occupied_mask
                    sides=0
                    if i>=1 and msk[0][i-1][j]+msk[1][i-1][j] == 1:
                        sides += 1
                    if i<=8 and msk[0][i+1][j]+msk[1][i+1][j] == 1:
                        sides += 1
                    if sides == 0:
                        self.valid_moves[i][k]=0
                #rule: not more than 9 wide occupied:
                if j==0:
                    count=self._count_row0()
                    if horizontal and count >= 8:
                        self.valid_moves[i][k]=0
                    if not horizontal and count >= 9:
                        self.valid_moves[i][k]=0

    def _count_row0(self):
        result=0
        msk=self.occupied_mask
        for i in range(11):
            result += msk[0][i][0] + msk[1][i][0]
        return result
    def _left_edge(self):
        if(self.empty):
            raise ValueError("called _left_edge on empty position")
        msk=self.occupied_mask
        for i in range(11):
            if msk[0][i][0] + msk[1][i][0] > 0:
                return i

    def move(self,i,k):
        if(self.valid_moves[i][k]==0):
            return False
        self.pieces[0][i][k]=1
        self.empty=False
        self._update_occupied_mask(0)
        self._update_occupied_mask(1)
        self._normalize()
        self._swap()
        self._update_valid_moves()
        self._check_over()
        if(self.over):
            self.valid_moves = np.zeros(shape=(11,17),dtype=np.int8)
        return True

    def _swap(self):
        self.flipped = not self.flipped
        ps=self.pieces[0]
        self.pieces[0]=self.pieces[1]
        self.pieces[1]=ps
        msk=self.occupied_mask[0]
        self.occupied_mask[0]=self.occupied_mask[1]
        self.occupied_mask[1]=msk

    def _normalize(self):
        count = self._count_row0()
        left_edge = self._left_edge()
        #left_edge *should* be (11 - count) // 2
        shift = (11-count)//2 - left_edge
        #shift arrays
        self.pieces[0] = np.roll(self.pieces[0], shift, 0)
        self.pieces[1] = np.roll(self.pieces[1], shift, 0)
        self.occupied_mask[0] = np.roll(self.occupied_mask[0], shift, 0)
        self.occupied_mask[1] = np.roll(self.occupied_mask[1], shift, 0)

    def _check_over(self):
        no_moves_left=True
        for i in range(11):
            for k in range(17):
                if self.valid_moves[i][k]:
                    no_moves_left=False
        if no_moves_left:
            self.over=True
            count_stones=0
            for i in range(11):
                for j in range(9):
                    if self.occupied_mask[0][i][j]:
                        count_stones += 1
            if(count_stones < 40):
                self.result=0.0
                return
            else:
                self.result=0.5
                return

        #horizontal
        for i in range(11-4):
            for j in range(9):
                if self.occupied_mask[0][i][j]:
                    player=0
                elif self.occupied_mask[1][i][j]:
                    player=1
                else:
                    continue
                won=True
                for d in range(1,5): 
                    won &= self.occupied_mask[player][i+d][j]
                if won:
                    self.over=True
                    self.result=0.0
                    return
        #vertical
        for i in range(11):
            for j in range(9-4):
                if self.occupied_mask[0][i][j]:
                    player=0
                elif self.occupied_mask[1][i][j]:
                    player=1
                else:
                    continue
                won=True
                for d in range(1,5): 
                    won &= self.occupied_mask[player][i][j+d]
                if won:
                    self.over=True
                    self.result=0.0
                    return
        #diagonal
        for i in range(11-4):
            for j in range(9-4):
                if self.occupied_mask[0][i][j]:
                    player=0
                elif self.occupied_mask[1][i][j]:
                    player=1
                else:
                    continue
                won=True
                for d in range(1,5): 
                    won &= self.occupied_mask[player][i+d][j+d]
                if won:
                    self.over=True
                    self.result=0.0
                    return
        #codiagonal
        for i in range(11-4):
            for j in range(4,9):
                if self.occupied_mask[0][i][j]:
                    player=0
                elif self.occupied_mask[1][i][j]:
                    player=1
                else:
                    continue
                won=True
                for d in range(1,5): 
                    won &= self.occupied_mask[player][i+d][j-d]
                if won:
                    self.over=True
                    self.result=0.0
                    return



