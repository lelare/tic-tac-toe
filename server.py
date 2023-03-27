from concurrent import futures
import logging
import grpc
import messages_pb2 as tictactoeserver_pb2
import messages_pb2_grpc as tictactoeserver_pb2_grpc

from game import Game

class TicTacToeServer(tictactoeserver_pb2_grpc.GameServicer):

    def __init__(self):
        self.game = Game()
        self.observers = dict()
        self.updates = {}

    def connect(self, request, context):
        user_id = request.id
        self.observers[user_id] = context
        logging.info(f"Connecting user: {request.id}")
        self.game.newPlayer(request.id)
        response = tictactoeserver_pb2.PlayerResponse()
        response.count_of_users = self.observers.keys().__len__()
        return response

    def makeMove(self, request_iterator, context):
        for move_request in request_iterator:
            character = self.game.makeMove(move_request.id, move_request.point)
            if character == tictactoeserver_pb2.Character.Value('UNRECOGNIZED'):
                logging.warning(f"Wrong point for {move_request.point}")
                context.set_details('Invalid move')
                context.set_code(grpc.StatusCode.INVALID_ARGUMENT)
                yield tictactoeserver_pb2.MoveResponse(success=False)
            self.update_value(move_request, character)           
            if self.game.isFinished():
                logging.info(f"Game finished")
                yield tictactoeserver_pb2.MoveResponse(success=False, message="Game finished")
                self.game.reset()
            yield tictactoeserver_pb2.MoveResponse(success=True, character=character, point=move_request.point)

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
        player_response.character = character
        player_response.point.x = move_request.point.x
        player_response.point.y = move_request.point.y
        print(self.observers.keys())
        print(self.updates.keys())
        for val in self.observers.keys():
            if val not in self.updates.keys():
                self.updates[val] = player_response

    def update_val(self, move_request, character):
        player_response = tictactoeserver_pb2.PlayerResponse()
        player_response.char = character
        player_response.point.x = move_request.point.x
        player_response.point.y = move_request.point.y
            
        for val, observer in self.observers.items():
            observer.send(player_response)
        if self.game.isFinished():
            for val, observer in self.observers.items():
                observer.send(None)
            self.game.reset()

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