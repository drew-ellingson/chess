def _add(tup1, tup2):
    return tuple(map(sum, zip(tup1, tup2)))

def _mult(scal, tup):
    return tuple(scal * x for x in tup)

def _sub(tup1, tup2):
    return _add(tup1, _mult(-1, tup2))

def sign(scal):
    return 1 if scal > 0 else 0 if scal == 0 else -1