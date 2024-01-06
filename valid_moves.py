from itertools import product 

pos_range = list(range(1, 8))
neg_range = list(range(-1, -8, -1))
zeroes = [0] * 7

knight_moves = [x for x in product([1,2,-1,-2], [1,2,-1,-2]) if sum(abs(i) for i in x) == 3]

diags = list(zip(pos_range, pos_range)) + list(zip(pos_range, neg_range)) + list(zip(neg_range, pos_range)) + list(zip(neg_range, neg_range))
rows_cols = list(zip(pos_range, zeroes)) + list(zip(neg_range, zeroes)) + list(zip(zeroes, pos_range)) + list(zip(zeroes, neg_range))

immediate_surrounding = [x for x in product([-1,0,1], [-1, 0, 1]) if x != (0,0)]

DIFFS = {
    'R': rows_cols,
    'N': knight_moves,
    'B': diags,
    'Q': diags + rows_cols,
    'K': immediate_surrounding,
    'P': [(1,0), (2,0), (1,1), (1,-1), (-1,0), (-2, 0), (-1, 1), (-1, -1)] # all valid pawn moves for either side
}
