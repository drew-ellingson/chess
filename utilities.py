def _add(tup1, tup2):
    return tuple(map(sum, zip(tup1, tup2)))


def _mult(tup1, scal):
    return tuple(scal * i for i in tup1)


def is_valid_sq(tup):
    return all(0 <= i <= 7 for i in tup)
