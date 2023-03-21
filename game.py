from typing import List

class Character:
    EMPTY = '-'
    X = 'X'
    O = 'O'
    UNRECOGNIZED = 'U'

class Point:
    def __init__(self, x: int, y: int):
        self.x = x
        self.y = y

class Game:
    def __init__(self):
        self.playerX = None
        self.playerO = None
        self.board = [[Character.EMPTY for _ in range(3)] for _ in range(3)]

    def newPlayer(self, id: str) -> bool:
        if self.playerX is None:
            self.playerX = id
            return True
        if self.playerO is None:
            self.playerO = id
            return True
        return False

    def makeMove(self, id: str, point: Point) -> Character:
        character = Character.UNRECOGNIZED
        if self.board[point.x][point.y] != Character.EMPTY:
            return Character.UNRECOGNIZED
        if id == self.playerX:
            character = Character.X
        if id == self.playerO:
            character = Character.O
        self.board[point.x][point.y] = character
        return character

    def isFinished(self) -> bool:
        for aBoard in self.board:
            for j in range(len(self.board)):
                if aBoard[j] == Character.EMPTY:
                    return False
        return True

    def reset(self):
        for aBoard in self.board:
            for j in range(len(self.board)):
                aBoard[j] = Character.EMPTY
        self.playerO = None
        self.playerX = None
