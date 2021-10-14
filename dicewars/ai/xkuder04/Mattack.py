from dicewars.client.game.board import Board
from dicewars.client.game.area import Area

class Mattack:
    def __init__(self, board : Board, player_index, depth):
        self.board = board
        self.player_index = player_index
        self.depth = depth

    def find_best_for_given_depth(self):
        pass