

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

        self.ks_castle_rights = {'W':True, 'B':True}
        self.qs_castle_rights = {'W':True, 'B':True}

        self.moves = []

class Move:
    def __init__(self, gs, sq_0, sq_1):
        self.r_0, self.c_0 = sq_0
        self.r_1, self.c_1 = sq_1
        self.gs = gs
        self.board = gs.board
        self.pc = self.board[self.r_0][self.c_0]
    
    def am_in_check(self):
        pass

    def is_other_persons_turn(self):
        return (self.gs.white_to_play and self.pc.startswith('B')) or (not self.gs.white_to_play and self.pc.startswith('W'))

    def has_illegal_collisions(self):
        # no landing on a piece of the same color
        if self.pc[0] == self.board[self.r_1][self.c_1][0]:
            return True
        
        # all knight moves legal as long as the above is True
        elif self.pc[-1] == 'N':
            return False
        
        # find intermediate squares, return whether or not there are pieces on any of them
        else:
            r_diff = self.r_1 - self.r_0 
            c_diff = self.c_1 - self.c_0
            max_diff = max(abs(r_diff), abs(c_diff))

            # covered by first case above
            if max_diff == 1:
                return False

            r_dir = 1 if r_diff > 0 else 0 if r_diff == 0 else -1
            c_dir = 1 if c_diff > 0 else 0 if c_diff == 0 else -1
    
            # exclude start and end squares
            intermediate_sqs = [(self.r_0 + r_dir * i, self.c_0 + c_dir * i) for i in range(1, max_diff)]

            return any(self.board[r][c] != '--' for (r,c) in intermediate_sqs)


    def is_legal(self):
        if self.is_other_persons_turn() or self.has_illegal_collisions():
            return False

        r_diff = self.r_1 - self.r_0 
        c_diff = self.c_1 - self.c_0

        legal = False
        if self.pc.endswith('R'):
            # same row or column
            if r_diff == 0 or c_diff == 0:
                legal = True 
        elif self.pc.endswith('N'):
            # L shapes, one diff is 1, one diff is 2
            if set([abs(r_diff), abs(c_diff)]) == set([1,2]):
                legal = True    
        elif self.pc.endswith('B'):
            # diagonals, diffs always equal
            if abs(r_diff) == abs(c_diff):
                legal = True
        elif self.pc.endswith('Q'):
            # rook or bishop union
            if abs(r_diff) == abs(c_diff) or r_diff == 0 or c_diff == 0:
                legal = True
        elif self.pc.endswith('K'):
            # one square in any direction, diagonals included
            if abs(self.c_0 - self.c_1) <= 1 and abs(self.r_0 - self.r_1) <= 1:
                legal = True

        # pawns can do a lot of garbage   
        elif self.pc.endswith('P'):
            # pawns can move 2 on the 2nd and 7th ranks only
            thresh = 2 if self.r_0 in [1,6] else 1

            # black pawns move up, white pawns move down
            orientation = 1 if self.pc.startswith('B') else -1

            if self.board[self.r_1][self.c_1] == '--' and self.c_0 == self.c_1 and 0 <= (orientation) * (self.r_1 - self.r_0) <= thresh:
                legal = True
            
            # pawns capture diagonally one square in front of them:
            # there needs to be an opponents piece there (not yours or empty)
            if abs(c_diff) == 1 and self.r_0 + orientation == self.r_1 and self.pc[0] not in ['--', self.board[self.r_1][self.c_1][0]]:
                legal = True

        return legal

    def execute(self):
        if self.is_legal():
            pc = self.board[self.r_0][self.c_0]
            self.board[self.r_0][self.c_0] = '--'
            self.board[self.r_1][self.c_1] = pc
            self.gs.white_to_play = not self.gs.white_to_play

            # revoke castling rights if king or rook moved
            if pc[-1] == 'K':
                self.gs.ks_castle_rights[pc] = False
                self.gs.qs_castle_rights[pc] = False

            if self.c_0 == 7 and pc[-1] == 'R':
                self.gs.ks_castle_rights[pc] = False
            if self.c_0 == 0 and pc[-1] == 'R':
                self.gs.qs_castle_rights[pc] = False
            
            self.gs.moves.append(self)