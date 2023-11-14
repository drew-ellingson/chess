

class GameState:
    def __init__(self):
        self.board = [
            ['BR','BN','BB','BQ','BK','BB','BN','BR'],
            ['BP','BP','BP','BP','BP','BP','BP','BP'],
            ['--','--','--','--','--','--','--','--'],
            ['--','--','--','--','--','--','--','--'],
            ['--','--','--','--','--','--','--','--'],
            ['--','--','--','--','--','--','--','--'],
            ['WP','WP','WP','WP','WP','WP','WP','WP'],
            ['WR','WN','WB','WQ','WK','WB','WN','WR'],
        ]

        self.white_to_play = True
        self.game_over = False

        self.moves = []

class Move:
    def __init__(self, gs, sq_0, sq_1):
        self.r_0, self.c_0 = sq_0
        self.r_1, self.c_1 = sq_1
        self.gs = gs
        self.board = gs.board
        self.pc = self.board[self.r_0][self.c_0]
             
    def is_legal(self):

        if self.gs.white_to_play and self.pc.startswith('B') or not self.gs.white_to_play and self.pc.startswith('W'):
            return False

        r_diff = self.r_1 - self.r_0 
        c_diff = self.c_1 - self.c_0

        legal = False
        if self.pc.endswith('R'):
            if r_diff == 0 or c_diff == 0:
                legal = True 
        elif self.pc.endswith('N'):
            if set([abs(r_diff), abs(c_diff)]) == set([1,2]):
                legal = True    
        elif self.pc.endswith('B'):
            if abs(r_diff) == abs(c_diff):
                legal = True
        elif self.pc.endswith('Q'):
            if abs(r_diff) == abs(c_diff) or r_diff == 0 or c_diff == 0:
                legal = True
        elif self.pc.endswith('K'):
            if abs(self.c_0 - self.c_1) <= 1 and abs(self.r_0 - self.r_1) <= 1:
                legal = True
        elif self.pc.endswith('P'):
            thresh = 2 if self.r_0 in [1,6] else 1  # pawns can move 2 on the 2nd and 7th ranks only
            orientation = 1 if self.pc.startswith('B') else -1  # black pawns move up, white pawns move down
            if self.c_0 == self.c_1 and 0 <= (orientation) * (self.r_1 - self.r_0) <= thresh:
                legal = True
        return legal

    def execute(self):
        if self.is_legal():
            pc = self.board[self.r_0][self.c_0]
            self.board[self.r_0][self.c_0] = '--'
            self.board[self.r_1][self.c_1] = pc
            self.gs.white_to_play = not self.gs.white_to_play