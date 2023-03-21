import logging
import time
import uuid
from grpc import RpcError
import grpc
import messages_pb2 as tictactoe_pb2
import messages_pb2_grpc as tictactoe_pb2_grpc
from messages_pb2 import ConnectionRequest, MoveRequest, Point, UpdateRequest
from messages_pb2_grpc import GameStub
from concurrent.futures import ThreadPoolExecutor
import threading

class GameComponent:
    def __init__(self):
        self.map = {i: ' ' for i in range(9)}
        channel = grpc.insecure_channel('localhost:50051')
        self.client = GameStub(channel=channel)
        self.user = str(uuid.uuid4())

        self.draw_board()

    def connect_to_server(self):
        try:
            resp = self.client.connect(ConnectionRequest(id=self.user))
            print(f"Connected to server; Count of players are: {resp.count_of_users}")
        except RpcError as e:
            logging.error(e)
        
    def handle_updates(self):
        def request_generator():
                yield UpdateRequest(id=self.user)

        for response in self.client.update(request_generator):
            self.update_map(response)
            self.draw_board()
            time.sleep(5)

    def update_map(self, response):
        point = response.point
        p = point.y + point.x + 2 * point.x
        print(f'{response.character} move to {p}')
        self.map[p] = response.character

    def draw_board(self):
        for i in range(9):
            if i % 3 == 0:
                print('---+---+---')
            print(f' {self.map[i]} ', end='|' if i % 3 < 2 else '\n')
        print('---+---+---')

    def run(self):
        self.connect_to_server()
        thread = threading.Thread(target=self.handle_updates, daemon=True)
        while True:
            point = int(input('Enter your move (0-8) or 10 to end the game: '))
            if point == 10: 
                thread.join()
                break
            x, y = divmod(point, 3)

            def request_generator():
                yield MoveRequest(point=Point(x=x, y=y), id=self.user)

            try:
                response = next(self.client.makeMove(request_generator()))
                if response.success:
                    print('Move successful')
                    self.update_map(response)
                    self.draw_board()
                else:
                    print('Move not allowed')
            except RpcError as e:
                logging.error(e)

if __name__ == '__main__':
    game = GameComponent()
    game.run()