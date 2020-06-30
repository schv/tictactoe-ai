from copy import deepcopy
from random import randint
from typing import Tuple, List, Dict
from enum import Enum
from itertools import cycle
from functools import reduce


class Difficulty(Enum):
    EASY = "easy"
    MEDIUM = "medium"
    HARD = "hard"


class GameStatus(Enum):
    NOT_STARTED = "Not started"
    NOT_FINISHED = "Game not finished"
    X_WINS = "X wins"
    O_WINS = "O wins"
    DRAW = "Draw"


class Turn(Enum):
    X = "X"
    O = "O"

    def flipped(self):
        return Turn.X if self is Turn.O else Turn.O

    def won(self):
        if self is Turn.X:
            return GameStatus.X_WINS
        if self is Turn.O:
            return GameStatus.O_WINS

    def opt(self):
        return max if self is Turn.X else min

    def points(self):
        if self is Turn.X:
            return 5
        if self is Turn.O:
            return -5


class Player:
    def validate_input(self, game, column: int, row: int) -> bool:
        return game.cell_available(column, row)

    def make_move(self, game) -> Tuple[int, int]:
        while True:
            column, row = self.get_input(game)
            if self.validate_input(game, column, row):
                game.make_move(column, row)
                return column, row


    def get_input(self, game) -> Tuple[int, int]:
        pass

    @staticmethod
    def spawn(turn: Turn, kind: str):
        if kind == "user":
            return Human(turn)
        elif kind in ["easy", "medium", "hard"]:
            return AI(turn, Difficulty(kind))
        else:
            raise ValueError


class AI(Player):
    def __init__(self, turn: Turn, difficulty: Difficulty = Difficulty.EASY):
        self.turn = turn
        self.difficulty = difficulty
        self.move_calculator = {
            Difficulty.EASY: self.easy_move,
            Difficulty.MEDIUM: self.medium_move,
            Difficulty.HARD: self.hard_move,
        }[self.difficulty]

    def next_turn_victory(self, field_copy, turn):
        for i, row in enumerate(field_copy.state):
            for j, cell in enumerate(row):
                if cell == Field.empty_cell:
                    field_copy.set_cell(i, j, turn.value)
                    if field_copy.check_field() is turn.won():
                        return Game.idx_to_coord(i, j)
                    else:
                        field_copy.set_cell(i, j, Field.empty_cell)

    def easy_move(self, game):
        column = randint(1, 3)
        row = randint(1, 3)
        return column, row

    def medium_move(self, game):
        field_copy = deepcopy(game.field)
        # print(field_copy)
        return self.next_turn_victory(field_copy, self.turn) \
            or self.next_turn_victory(field_copy, self.turn.flipped()) \
            or self.easy_move(game)

    def hard_move(self, game):
        field_copy = deepcopy(game.field)
        # print(field_copy)
        return self.next_turn_victory(field_copy, self.turn) \
            or self.next_turn_victory(field_copy, self.turn.flipped()) \
            or Strategy.optimal_move(game)

    def get_input(self, game) -> Tuple[int, int]:
        column, row = self.move_calculator(game)
        return column, row

    def make_move(self, game) -> Tuple[int, int]:
        print(f'Making move level "{self.difficulty.value}"')
        return super(AI, self).make_move(game)


class Human(Player):
    def __init__(self, turn: Turn):
        self.turn = turn

    def validate_input(self, game, column: int, row: int) -> bool:
        if not (column in range(1, 4) and row in range(1, 4)):
            print("Coordinates should be from 1 to 3!")
            return False
        elif not game.cell_available(column, row):
            print("This cell is occupied! Choose another one!")
            return False
        else:
            return True

    def get_input(self, game) -> Tuple[int, int]:
        while True:
            user_input = input("Enter the coordinates: ").strip()
            try:
                column, row = [int(x) for x in user_input.split()]
                return column, row
            except (TypeError, ValueError):
                print("You should enter numbers!")


class Field:
    empty_cell = "_"

    def __init__(self):
        self.state = [[self.empty_cell for _ in range(3)] for _ in range(3)]
        self.empty = 9

    def set_cell(self, r, c, val):
        if self.state[r][c] != Field.empty_cell and val == Field.empty_cell:
            self.empty += 1
        elif self.state[r][c] == Field.empty_cell and val != Field.empty_cell:
            self.empty -= 1

        assert self.empty >= 0

        self.state[r][c] = val

    def decode_field(self, seq: str):
        iter_seq = iter(seq)
        self.state = [[next(iter_seq) for _ in range(3)] for _ in range(3)]


    def check_field(self) -> GameStatus:
        field = self.state

        vs = (
            d1 := field[0][0] == field[1][1] == field[2][2] != Field.empty_cell and field[0][0],
            d2 := field[0][2] == field[1][1] == field[2][0] != Field.empty_cell and field[0][2],

            h1 := field[0][0] == field[0][1] == field[0][2] != Field.empty_cell and field[0][0],
            h2 := field[1][0] == field[1][1] == field[1][2] != Field.empty_cell and field[1][0],
            h3 := field[2][0] == field[2][1] == field[2][2] != Field.empty_cell and field[2][0],

            v1 := field[0][0] == field[1][0] == field[2][0] != Field.empty_cell and field[0][0],
            v2 := field[0][1] == field[1][1] == field[2][1] != Field.empty_cell and field[0][1],
            v3 := field[0][2] == field[1][2] == field[2][2] != Field.empty_cell and field[0][2],
        )

        trs = list(filter(lambda x: x != False and x != Field.empty_cell, vs))
        assert 0 <= len(trs) <= 2, self

        if cell := reduce(lambda x, y: x or y, vs):
            assert len(set(trs)) <= 1, cell
            return GameStatus(f"{cell} wins")

        if self.empty == 0:
            return GameStatus.DRAW
        else:
            return GameStatus.NOT_FINISHED



    def __str__(self):
        return f"""
---------
| {" ".join(self.state[0])} |
| {" ".join(self.state[1])} |
| {" ".join(self.state[2])} |
---------"""


class Game:
    status = GameStatus.NOT_STARTED
    empty_cell = "_"
    # turns_left = 9
    draw_points = -3


    def __init__(self, current_player: Player, pending_player: Player):
        self.current_player = current_player
        self.pending_player = pending_player
        self.players = (current_player, pending_player)
        self.field = Field()
        self.status = GameStatus.NOT_FINISHED
        self.turns = cycle(Turn)
        self.history = []
        # turn = "X"
        self.current_turn = next(self.turns)

    def load_from_save(self, seq: str):
        xs = seq.count('X')
        os = seq.count('O')

        # self.turns_left -= xs + os
        self.current_turn = Turn('X' if xs == os else 'O')
        del self.turns
        self.field.decode_field(seq)

    def next_turn(self):
        # self.turn = 'O' if self.turn == 'X' else 'X'
        self.current_turn = next(self.turns)
        self.current_player, self.pending_player = self.pending_player, self.current_player

    def cell_available(self, column: int, row: int) -> bool:
        i, j = self.coord_to_idx(column, row)
        return self.field.state[i][j] == Field.empty_cell

    def make_move(self, column: int, row: int):
        i, j = self.coord_to_idx(column, row)
        self.field.set_cell(i, j, self.current_turn.value)
        self.history.append((i, j))
        self.next_turn()
        # print(self.field.empty)

    @staticmethod
    def coord_to_idx(column: int, row: int) -> Tuple[int, int]:
        return 3 - row, column - 1

    @staticmethod
    def idx_to_coord(i: int, j: int) -> Tuple[int, int]:
        return j + 1, 3 - i

    def check_field(self) -> GameStatus:
        self.status = self.field.check_field()
        return self.status

# strats = generate_strats(Field(), Turn.X)

def generate_strats(field, turn: Turn) -> Dict:
        strats = {}
        for r, row in enumerate(field.state):
            for c, cell in enumerate(row):
                if cell == Field.empty_cell:
                    key = (r, c)
                    field.set_cell(r, c, turn.value)
                    res = field.check_field()

                    if res is turn.won():
                        strats[key] = {
                                'next': None,
                                'points': turn.points(),
                        }

                    if res is GameStatus.DRAW:
                        strats[key] = {
                                'next': None,
                                'points': Game.draw_points,
                        }

                    if res is GameStatus.NOT_FINISHED:
                        nxt = generate_strats(field, turn.flipped())
                        ps = sum(x['points'] for x in nxt.values())
                        strats[key] = {
                            'next': nxt,
                            'points': ps,
                        }

                    field.set_cell(r, c, Field.empty_cell)

        return strats

class Strategy():
    strat = generate_strats(Field(), Turn.X)

    @staticmethod
    def optimal_move(game) -> Tuple[int, int]:
        cur = Strategy.strat
        for move in game.history:
            cur = cur[move]['next']

        # print(cur.keys())
        # print(game.history)
        opt = game.current_turn.opt()(cur.items(), key=lambda x: x[1]['points'])
        # print(opt[0])
        return Game.idx_to_coord(*opt[0])


def main():
    while True:
        user_input = input("Input command: ").strip()
        if user_input == "exit":
            return
        try:
            start, x_player_kind, o_player_kind = user_input.split()
            if start != "start":
                raise ValueError
            if x_player_kind not in ["user", "easy", "medium", "hard"] or o_player_kind not in ["user", "easy", "medium", "hard"]:
                raise ValueError
            break

        except ValueError:
            print(("Bad parameters"))

    x_player = Player.spawn(Turn("X"), x_player_kind)
    o_player = Player.spawn(Turn("O"), o_player_kind)

    # human = Human(Turn("X"))
    # ai = AI(Turn("O"), Difficulty("easy"))

    game = Game(x_player, o_player)
    print(game.field)

    while game.status is GameStatus.NOT_FINISHED:
        game.current_player.make_move(game)
        game.check_field()
        print(game.field)

    print(game.status.value)

def check_strats():
    with open('C:\\Users\\evgen\\Documents\\docs\\stepik\\strats2.txt', 'w') as f:
        field = Field()
        strats = generate_strats(field, Turn.X)

        # json.dump(strats, f)
        print("Success", len(strats))
        print([(idx, strat['points']) for idx, strat in strats.items()])
        print(field)
        ps = iter(strats.values())
        nf = Field()
        for i, row in enumerate(nf.state):
            for j, cell in enumerate(row):
                row[j] = str(next(ps)['points'])
        print(nf)

if __name__ == '__main__':
    main()
    # check_strats()
