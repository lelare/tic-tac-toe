from concurrent import futures
import logging
import grpc
import messages_pb2 as tictactoeserver_pb2
import messages_pb2_grpc as tictactoeserver_pb2_grpc

from game import Game, Character, Point

class TicTacToeServer(tictactoeserver_pb2_grpc.GameServicer):

    def __init__(self):
        self.game = Game()
        self.observers = dict()
        self.updates = {}

    def connect(self, request, context):
        user_id = request.id
        self.observers[user_id] = context
        logging.info(f"Connecting user: {request.id}")
        if not self.game.newPlayer(request.id):
            context.set_details('Game is full')
            context.set_code(grpc.StatusCode.UNAVAILABLE)
            return tictactoeserver_pb2.PlayerResponse(count_of_users=self.observers.keys().__len__())
        symbols = {self.game.playerX: Character.X, self.game.playerO: Character.O}
        self.game.setPlayerSymbols(symbols)
        self.game.setLeader(self.game.playerX)
        self.game.setTurnOrder([self.game.playerX, self.game.playerO])
        response = tictactoeserver_pb2.PlayerResponse(count_of_users=self.observers.keys().__len__())
        return response

    def makeMove(self, request_iterator, context):
        for move_request in request_iterator:
            if not self.game.isTurn(move_request.id):
                logging.warning(f"Not {move_request.id}'s turn")
                context.set_details('Not your turn')
                context.set_code(grpc.StatusCode.UNAVAILABLE)
                yield tictactoeserver_pb2.MoveResponse(success=False)
            character = self.game.makeMove(move_request.id, Point(move_request.point.x, move_request.point.y))
            if character == Character.UNRECOGNIZED:
                logging.warning(f"Wrong point for {move_request.point}")
                context.set_details('Invalid move')
                context.set_code(grpc.StatusCode.INVALID_ARGUMENT)
                yield tictactoeserver_pb2.MoveResponse(success=False)
            else:
                self.update_value(move_request, character)
                if self.game.isFinished():
                    winner = self.game.getWinner()
                    logging.info(f"Game finished. Winner: {winner}")
                    yield tictactoeserver_pb2.MoveResponse(success=True, message="Game finished", char=winner, point=None, is_turn=False)
                    self.game.reset()
                else:
                    yield tictactoeserver_pb2.MoveResponse(success=True, char=character, point=move_request.point, is_turn=True)

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
        player_response = tictactoeserver_pb2.UpdateResponce()
        player_response.char = character
        player_response.point.x = move_request.point.x
        player_response.point.y = move_request.point.y
        for val in self.observers.keys():
            if val not in self.updates.keys():
                self.updates[val] = []
            self.updates[val].append(player_response)

def serve():
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    tictactoeserver_pb2_grpc.add_GameServicer_to_server(TicTacToeServer(), server)
    server.add_insecure_port('[::]:50051')
    server.start()
    logging.info("Server started, listening on port 50051")
    server.wait_for_termination()

if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    serve() 
