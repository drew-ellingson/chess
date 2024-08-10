from typing import List

import pygame as p
from engine import GameState, Move

WIDTH = HEIGHT = 512
DIMENSION = 8
SQ_SIZE = HEIGHT // DIMENSION
MAX_FPS = 15
PIECE_IMAGES = {}


def load_images() -> None:
    """load piece image pngs into PIECE_IMAGES global. run once during game setup"""

    pieces = ["bR", "bN", "bB", "bQ", "bK", "bp", "wR", "wN", "wB", "wQ", "wK", "wp"]
    for piece in pieces:
        PIECE_IMAGES[piece] = p.transform.scale(
            p.image.load("assets/images/pieces/" + piece + ".png"), (SQ_SIZE, SQ_SIZE)
        )


def main() -> None:
    """Initialize necessary pygame components and then enter main game loop"""

    p.init()
    screen = p.display.set_mode((WIDTH, HEIGHT))
    clock = p.time.Clock()
    screen.fill(p.Color("white"))
    gs = GameState()

    load_images()

    running = True

    # game loop

    sq_selected = ()  # (row, col) for last user-clicked sq
    player_clicks = []  # keep track of last two clicks for moves
    while running:
        for e in p.event.get():
            if e.type == p.QUIT:
                running = False

            elif e.type == p.MOUSEBUTTONDOWN:
                x, y = p.mouse.get_pos()
                col, row = x // SQ_SIZE, y // SQ_SIZE

                if sq_selected != (row, col):
                    sq_selected = (row, col)
                    player_clicks.append(sq_selected)
                else:
                    sq_selected = ()
                    player_clicks = []

                if len(player_clicks) == 2:
                    move = Move(player_clicks[0], player_clicks[1], gs.board)

                    if move in gs.gen_valid_moves():
                        gs.make_move(move)
                        print(move.notation)
                    sq_selected = ()
                    player_clicks = []

            elif e.type == p.KEYDOWN:
                if e.key == p.K_BACKSPACE:
                    gs.undo_move()
                if e.key == p.K_q:
                    for m in gs.gen_valid_moves():
                        print(m)

        draw_game_state(screen, gs)

        clock.tick(MAX_FPS)
        p.display.flip()


def draw_game_state(screen: p.Surface, gs: GameState) -> None:
    """single function to draw all game elements, including board, pieces,
    highlighting, etc"""

    draw_board(screen)
    draw_pieces(screen, gs.board)


def draw_board(screen: p.Surface) -> None:
    """draws the 8x8 board, alternating colors starting with light at the top left"""

    colors = [p.Color("white"), p.Color("grey")]
    for r in range(DIMENSION):
        for c in range(DIMENSION):
            sq_color = colors[(r + c) % 2]
            p.draw.rect(
                screen, sq_color, p.Rect(c * SQ_SIZE, r * SQ_SIZE, SQ_SIZE, SQ_SIZE)
            )


def draw_pieces(screen: p.Surface, board: List[List[str]]) -> None:
    """blits the pieces onto the board. ignores empty spaces"""

    for r in range(DIMENSION):
        for c in range(DIMENSION):
            piece = board[r][c]
            if piece != "--":
                screen.blit(
                    PIECE_IMAGES[piece],
                    p.Rect(c * SQ_SIZE, r * SQ_SIZE, SQ_SIZE, SQ_SIZE),
                )


if __name__ == "__main__":
    main()
