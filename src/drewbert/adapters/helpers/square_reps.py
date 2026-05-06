def alg_sq_to_int(sq: str) -> int:
    return 8 * (int(sq[1]) - 1)  + (ord(sq[0]) - 97)


def int_to_alg_sq(idx: int) -> str:
    return chr(idx % 8 + 97) + str(idx // 8 + 1)


if __name__ == '__main__':
    print(alg_sq_to_int('a1'))
    print(alg_sq_to_int('a2'))
    print(alg_sq_to_int('b1'))    
    print(alg_sq_to_int('d6'))

    print(int_to_alg_sq(0))
    print(int_to_alg_sq(8))
    print(int_to_alg_sq(1))
    print(int_to_alg_sq(43))

    