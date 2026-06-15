from drewbert.core.position import Position
from drewbert.search import minimax
from drewbert.eval import material

SEARCHES = {
    minimax: 
}
def main(search_fn: searchFn, eval_fn: PositionEvalFn, depth: int = 3) -> None
    position = Position.startpos()
    pass 

if __name__ == "__main__":
    args = parse_args() #- --search minimax --eval material --depth 3
    main(SEARCHES[args.search], EVALS[args.evals], args.depth)
