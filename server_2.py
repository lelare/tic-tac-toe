from concurrent import futures
import logging
import random
import threading
import time
import grpc
import messages_pb2 as tictactoeserver_pb2
import messages_pb2_grpc as tictactoeserver_pb2_grpc

from game_1 import Game, Character, Point

class TicTacToeServer(tictactoeserver_pb2_grpc.GameServicer):

    def __init__(self, id, next_node_address, game_obj = Game()):
            self.id = id
            self.next_node_address = next_node_address
            self.leader_id = -1
            self.timestamp = None        
            self.turn_player = None
            self.game = game_obj
            self.observers = dict()
            self.updates = {}

    def Election(self, request, context):
        if request.id < self.id:
            return tictactoeserver_pb2.ElectionResponse(id=self.id)
        elif request.id == self.id:
            self.leader_id = self.id
            self.timestamp = time.time()
            return tictactoeserver_pb2.ElectionResponse(id=self.id)
        else:
            with grpc.insecure_channel(self.next_node_address) as channel:
                stub = tictactoeserver_pb2_grpc.GameStub(channel=channel)
                response = stub.Election(request)
            if response.id != self.id:
                self.leader_id = response.id
                self.timestamp = time.time()
            return response

    def TimeSync(self, request, context):
        if self.leader_id != -1 and self.timestamp is not None:
            return tictactoeserver_pb2.TimeSyncResponse(id=self.leader_id, time=self.timestamp)
        else:
            return tictactoeserver_pb2.TimeSyncResponse(id=-1, time=0)

    def start_election(self):
        with grpc.insecure_channel(self.next_node_address) as channel:
            stub = tictactoeserver_pb2_grpc.GameStub(channel=channel)
            response = stub.Election(tictactoeserver_pb2.ElectionRequest(id=self.id))

        if response.id != self.id:
            print(f"Node {self.id} lost election to node {response.id}")
            self.leader_id = response.id
            self.timestamp = time.time()


    def connect(self, request, context):
        if not self.game.newPlayer(request.id):
            context.set_details('Game already full')
            context.set_code(grpc.StatusCode.UNAVAILABLE)
            return tictactoeserver_pb2.PlayerResponse(count_of_users=self.game.numPlayers())

        if self.turn_player is None:
            self.turn_player = self.game.playerX

        user_id = request.id
        self.observers[user_id] = context
        logging.info(f"Connecting user: {request.id}")
        response = tictactoeserver_pb2.PlayerResponse()
        response.count_of_users = self.observers.keys().__len__()
        return response

    def fill(self, request, context):
        if request.id != self.turn_player:
            logging.warning(f"Not {request.id}'s turn")
            context.set_details('Not your turn')
            context.set_code(grpc.StatusCode.INVALID_ARGUMENT)
            return tictactoeserver_pb2.FillResponse(success=False)

        cell_id = request.cell_id
        row = (cell_id - 1) // 3
        col = (cell_id - 1) % 3

        if self.game.board[row][col] != Character.EMPTY:
            logging.warning(f"Cell {cell_id} is already occupied")
            context.set_details('Cell already occupied')
            context.set_code(grpc.StatusCode.INVALID_ARGUMENT)
            return tictactoeserver_pb2.FillResponse(success=False)

        timestamp = request.timestamp
        success = False
        while not success:
            character = self.game.makeMove(request.id, Point(row, col))
            if character == Character.UNRECOGNIZED:
                logging.warning(f"Wrong point for {row}, {col}")
                context.set_details('Invalid move')
                context.set_code(grpc.StatusCode.INVALID_ARGUMENT)
                return tictactoeserver_pb2.FillResponse(success=False)
            success = True

        self.turn_player = self.game.playerX if self.turn_player == self.game.playerO else self.game.playerO

        response = tictactoeserver_pb2.FillResponse(success=True)
        response.board.extend([''.join(row) for row in self.game.board])
        return response

    def makeMove(self, move_request, context):

        if move_request.id != self.turn_player:
            logging.warning(f"Not {move_request.id}'s turn")
            context.set_details('Not your turn')
            context.set_code(grpc.StatusCode.INVALID_ARGUMENT)
            return tictactoeserver_pb2.MoveResponse(success=False)

        point = move_request.point

        if self.game.board[point.x][point.y] != Character.EMPTY:
            logging.warning(f"Cell {point} is already occupied")
            context.set_details('Cell already occupied')
            context.set_code(grpc.StatusCode.INVALID_ARGUMENT)
            return tictactoeserver_pb2.MoveResponse(success=False)
        success = False
        while not success:
            character = self.game.makeMove(move_request.id, Point(point.x, point.y))
            if character == Character.UNRECOGNIZED:
                logging.warning(f"Wrong point for {point.x}, {point.y}")
                context.set_details('Invalid move')
                context.set_code(grpc.StatusCode.INVALID_ARGUMENT)
                return tictactoeserver_pb2.MoveResponse(success=False)
            success = True

        self.turn_player = self.game.playerX if self.turn_player == self.game.playerO else self.game.playerO
        
        self.update_value(move_request, character)           
        if self.game.isFinished():
            logging.info(f"Game finished")
            self.game.reset()
            return tictactoeserver_pb2.MoveResponse(success=False, message="Game finished")
        return tictactoeserver_pb2.MoveResponse(success=True, character=character, point=move_request.point)

    def update(self, request_iterator, context):
        for req in request_iterator: 
            logging.info(f"Update request from {req.id}")
            copy_updates = self.updates.copy()
            if req.id in self.updates.keys():
                self.updates.pop(req.id)
                for val, update in copy_updates.items():
                    if val == req.id:
                        yield update

    def update_value(self, move_request, character): 
        player_response = tictactoeserver_pb2.UpdateResponse()
        player_response.character = character
        player_response.point.x = move_request.point.x
        player_response.point.y = move_request.point.y
        player_response.changes = True
        for val in self.observers.keys():
            if val not in self.updates.keys():
                self.updates[val]=(player_response)

    def update_val(self, move_request, character):
        player_response = tictactoeserver_pb2.UpdateResponse()
        player_response.character = character
        player_response.point.x = move_request.point.x
        player_response.point.y = move_request.point.y
        player_response.changes = True    
        for val, observer in self.observers.items():

            observer.update(player_response)
        if self.game.isFinished():
            for val, observer in self.observers.items():
                observer.update(None)
            self.game.reset()

    def numPlayers(self):
        return self.game.numPlayers()


def election_task(node, interval):
    random.seed(time.time())
    time.sleep(interval + random.uniform(1, 3))  # Add random delay before starting the election
    node.start_election()
        
def serve(id, next_node_address, port, leader_election_interval, game_obj):
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    node = TicTacToeServer(id, next_node_address, game_obj)
    tictactoeserver_pb2_grpc.add_GameServicer_to_server(node, server)
    server.add_insecure_port(f'[::]:{port}')
    server.start()
    print(f"Node {id} running on port {port}")

    # Start a separate thread for running leader election periodically
    election_thread = threading.Thread(target=election_task, args=(node, leader_election_interval))
    election_thread.daemon = True
    election_thread.start()

    return node, server

def main():
    game = Game()
    leader_election_interval = 3  # Time in seconds between leader elections
    node1, server1 = serve(1, "localhost:50052", 50051, leader_election_interval, game)
    node2, server2 = serve(2, "localhost:50053", 50052, leader_election_interval, game)
    node3, server3 = serve(3, "localhost:50054", 50053, leader_election_interval, game)
    node4, server4 = serve(4, "localhost:50051", 50054, leader_election_interval, game)

    try:
        while True:
            time.sleep(60)
    except KeyboardInterrupt:
        server1.stop(0)
        server2.stop(0)
        server3.stop(0)
        server4.stop(0)


if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    main() 
