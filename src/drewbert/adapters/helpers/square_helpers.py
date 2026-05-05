def alg_sq_to_int(sq: str) -> int:
    return ord(sq[0]) - 97 + int(sq[1])

def int_to_alg_sq(idx: int) -> str:
    return chr(idx // 8 + idx % 8)