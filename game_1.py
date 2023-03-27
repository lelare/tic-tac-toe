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
        self.turns = []
        self.symbols = {}
        self.leader = None

    def newPlayer(self, id: str) -> bool:
        if self.playerX is None:
            self.playerX = id
            self.turns.append(id)
            self.symbols[id] = Character.X
            return True
        if self.playerO is None:
            self.playerO = id
            self.turns.append(id)
            self.symbols[id] = Character.O
            return True
        return False

    def makeMove(self, id: str, point: Point) -> Character:
        character = self.symbols[id]
        if self.board[point.x][point.y] != Character.EMPTY:
            return Character.UNRECOGNIZED
        self.board[point.x][point.y] = character
        self.turns.pop(0)
        self.turns.append(id)
        return character

    def isFinished(self) -> bool:
        # check rows
        for i in range(3):
            if self.board[i][0] == self.board[i][1] == self.board[i][2] != Character.EMPTY:
                return True
        # check columns
        for i in range(3):
            if self.board[0][i] == self.board[1][i] == self.board[2][i] != Character.EMPTY:
                return True
        # check diagonals
        if self.board[0][0] == self.board[1][1] == self.board[2][2] != Character.EMPTY:
            return True
        if self.board[0][2] == self.board[1][1] == self.board[2][0] != Character.EMPTY:
            return True
        # check if board is full
        for aBoard in self.board:
            for j in range(len(self.board)):
                if aBoard[j] == Character.EMPTY:
                    return False
        return True

    def getWinner(self) -> Character:
        # check rows
        for i in range(3):
            if self.board[i][0] == self.board[i][1] == self.board[i][2] != Character.EMPTY:
                return self.board[i][0]
        # check columns
        for i in range(3):
            if self.board[0][i] == self.board[1][i] == self.board[2][i] != Character.EMPTY:
                return self.board[0][i]
        # check diagonals
        if self.board[0][0] == self.board[1][1] == self.board[2][2] != Character.EMPTY:
            return self.board[0][0]
        if self.board[0][2] == self.board[1][1] == self.board[2][0] != Character.EMPTY:
            return self.board[0][2]
        return Character.EMPTY

    
    def reset(self):
        self.board = [[Character.EMPTY for _ in range(3)] for _ in range(3)]
        self.playerO = None
        self.playerX = None
        self.turns = []
        self.symbols = {}
        self.leader = None

    def setLeader(self, leader_id: str):
        self.leader = leader_id

    def setTurnOrder(self, turns: List[str]):
        self.turns = turns

    def setPlayerSymbols(self, symbols: dict):
        self.symbols = symbols

    def getCurrentPlayer(self) -> str:
        return self.turns[0]

    def isTurn(self, id: str) -> bool:
        return id == self.turns[0]

    def getBoard(self) -> List[List[str]]:
        return self.board
