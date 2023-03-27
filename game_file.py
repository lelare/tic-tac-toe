import logging
import time
import uuid
from grpc import RpcError
import grpc
from messages_pb2 import ConnectionRequest, MoveRequest, Point, UpdateRequest, TimeSyncRequest, TimeSyncResponse, ElectionRequest, ElectionResponse
from messages_pb2_grpc import GameStub
from concurrent.futures import ThreadPoolExecutor
import threading

class GameComponent:
    def __init__(self, client):
        self.map = {i: ' ' for i in range(9)}
        self.client = client
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
            try:
                response = self.client.makeMove(MoveRequest(point=Point(x=x, y=y), id=self.user))
                if response.success:
                    print('Move successful')
                    self.update_map(response)
                    self.draw_board()
                else:
                    print('Move not allowed')
            except RpcError as e:
                logging.error(e)

def query_node(address):
    with grpc.insecure_channel(address) as channel:
        stub = GameStub(channel)
        response = stub.TimeSync(TimeSyncRequest())
        print(f"response: {response}")
    if response.id != -1:
        return response.id, response.time, address
    else:
        return None, None, None

def main():
    node_addresses = ['localhost:50052', 'localhost:50051', 'localhost:50053', "localhost:50054"]
    leader_id, leader_time, address = None, None, None
    while True:
        for address in node_addresses:
            print(f"Querying node at {address}...")
            leader_id, leader_time, address = query_node(address)
            if leader_id is not None:                
                break

        if leader_id is not None:
                print(f"Node at {address} reports leader: Node {leader_id} with timestamp {leader_time}")
                break
        else:
            print(f"Node at {address} reports no leader elected yet.")
        time.sleep(5)
    channel = grpc.insecure_channel(address)
    game = GameComponent(GameStub(channel))
    game.run()


if __name__ == '__main__':
    main()