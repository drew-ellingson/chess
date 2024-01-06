import pygame as p
import chess_engine as ce

# BOARD GLOBALS

WIDTH, HEIGHT = 1024, 1024
SQ_COUNT = 8  # in a row or column
SQ_SIZE = WIDTH // SQ_COUNT

# SCREEN GLOBALS

MAX_FPS = 30

# CHESS GLOBALS / ASSETS

PIECES = ['BR', 'BN', 'BB', 'BQ', 'BK','BP', 'WR', 'WN', 'WB', 'WQ', 'WK', 'WP']
IMAGES = {}

def load_images():
    for pc in PIECES:
        IMAGES[pc] = p.transform.scale(p.image.load('assets/images/piece_sets/standard/'+pc+'.png'), (SQ_SIZE, SQ_SIZE))

def main():
    p.init()
    screen = p.display.set_mode((WIDTH, HEIGHT))
    clock = p.time.Clock()
    screen.fill(p.Color('white'))
    gs = ce.GameState()
    
    load_images()
    player_clicks = []
    curr_sq = ()
    
    running = True
    while running:
        for e in p.event.get():
            if e.type == p.QUIT:
                running = False

            if e.type == p.MOUSEBUTTONDOWN:
                loc = p.mouse.get_pos()
                c, r = loc[0]//SQ_SIZE, loc[1]//SQ_SIZE

                if curr_sq == (r, c):
                    curr_sq = ()
                    player_clicks.pop()

                elif curr_sq == () and gs.board[r][c] == '--':
                    continue
                else:
                    curr_sq = (r, c)
                    player_clicks.append((r, c))
                
                if len(player_clicks) == 2:
                    move = ce.Move(gs, player_clicks[0], player_clicks[1])
                    valid_moves = ce.GameState.gen_valid_pc_moves(gs, player_clicks[0])

                    print(move)
                    print(valid_moves)

                    move.execute()
                    player_clicks.clear()
                    curr_sq = ()          

        draw_game_state(screen, gs, curr_sq)
        clock.tick(MAX_FPS)
        p.display.flip()

def draw_game_state(screen, gs, curr_sq):
    draw_board(screen, curr_sq)
    draw_pieces(screen, gs.board)

def draw_board(screen, curr_sq):
    colors = [p.Color('white'), p.Color('dark grey')]
    highlight_color = p.Color('yellow')

    for r in range(SQ_COUNT):
        for c in range(SQ_COUNT):
             color = highlight_color if (r,c) == curr_sq else colors[(r+c)% 2]
             p.draw.rect(screen, color, p.Rect(c * SQ_SIZE, r * SQ_SIZE, SQ_SIZE, SQ_SIZE))
                 

def draw_pieces(screen, board):
    for r in range(SQ_COUNT):
        for c in range(SQ_COUNT):
            if board[r][c] == '--':
                continue
            else: 
                screen.blit(IMAGES[board[r][c]], p.Rect(c * SQ_SIZE, r * SQ_SIZE, SQ_SIZE, SQ_SIZE))
        
if __name__ == '__main__':
    main()