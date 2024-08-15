from typing import List, Tuple

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

    sq_selected: Tuple[int, int] = ()  # (row, col) for last user-clicked sq
    player_clicks: List[Tuple[int, int]] = []  # keep track of last two clicks for moves

    new_game = True
    while running:
        new_clicks = False
        for e in p.event.get():
            if e.type == p.QUIT:
                running = False

            elif e.type == p.MOUSEBUTTONDOWN:
                new_clicks = True
                x, y = p.mouse.get_pos()
                col, row = x // SQ_SIZE, y // SQ_SIZE

                if sq_selected != (row, col):
                    sq_selected = (row, col)

                    # only want to allow selecting piece of current player color as the
                    # first click
                    if (
                        len(player_clicks) == 1
                        or gs.board[row][col][0] == gs.current_player_color()
                    ):
                        player_clicks.append(sq_selected)
                else:
                    sq_selected = ()
                    player_clicks = []

                if len(player_clicks) == 2:
                    move = Move(player_clicks[0], player_clicks[1], gs.board)

                    if move in gs.gen_valid_moves(gs.current_player_color()):
                        gs.make_move(move)
                        print(move.notation)
                    sq_selected = ()
                    player_clicks = []

            elif e.type == p.KEYDOWN:
                if e.key == p.K_BACKSPACE:
                    gs.undo_move()
                if e.key == p.K_q:
                    print(
                        f"Current player valid moves: \
                            {gs.gen_valid_moves(gs.current_player_color())}"
                    )
                    print(
                        f"Other player valid moves: \
                        {gs.gen_valid_moves(gs.other_player_color())}"
                    )
                if e.key == p.K_d:
                    print(f"Debug Details:\n\t{gs}")

        if new_clicks or new_game:
            draw_game_state(screen, gs, player_clicks)
            new_clicks = False
            new_game = False

        clock.tick(MAX_FPS)
        p.display.flip()


def draw_game_state(
    screen: p.Surface, gs: GameState, player_clicks: List[Tuple[int, int]]
) -> None:
    """single function to draw all game elements, including board, pieces,
    highlighting, etc"""

    draw_board(screen)
    draw_highlight(screen, gs, player_clicks)
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


def draw_highlight(
    screen: p.Surface, gs: GameState, player_clicks: List[Tuple[int, int]]
) -> None:
    """
    Highlight currently selected square + all legal moves starting from that
    square
    """
    if len(player_clicks) == 1:
        sq = player_clicks[0]
        if gs.board[sq[0]][sq[1]][0] == gs.current_player_color():
            color = p.Color("yellow")
            p.draw.rect(
                screen,
                color,
                p.Rect(
                    sq[1] * SQ_SIZE,
                    sq[0] * SQ_SIZE,
                    SQ_SIZE,
                    SQ_SIZE,
                ),
            )

        legal_moves = [
            m
            for m in gs.gen_valid_moves(gs.current_player_color())
            if m.x_0 == sq[0] and m.y_0 == sq[1]
        ]

        for m in legal_moves:
            color = p.Color("green")
            p.draw.rect(
                screen,
                color,
                p.Rect(
                    m.y_1 * SQ_SIZE,
                    m.x_1 * SQ_SIZE,
                    SQ_SIZE,
                    SQ_SIZE,
                ),
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
