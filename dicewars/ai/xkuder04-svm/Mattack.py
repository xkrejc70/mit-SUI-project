from dicewars.client.game.board import Board
from dicewars.client.game.area import Area
from numpy import inf
from dicewars.ai.utils import save_state, probability_of_successful_attack, attack_succcess_probability
from .utils.utils import resonable_attacks_for_player, simulate_lossing_move, simulate_succesfull_move, evaluate_board
from .utils.models_util import load_model, models_dir_filepath
import time

class Mattack:
    def __init__(self, depth, players_order, players_ordered, player_index, min_time_left):
        self.depth = depth
        self.players_order = players_order
        self.players_ordered = players_ordered
        self.player_index = player_index
        self.min_time_left = min_time_left
        self.half_min_time_left = min_time_left/2
        self.clf = load_model(models_dir_filepath("eval_state_4_cf_svm.model"))

    # Return best move for given depth
    def best_result(self, board, time_left, start_turn_time):
        self.time_left = time_left
        self.start_turn_time = start_turn_time
        return self.best_result_for_given_depth(board, self.player_index, self.depth)

    # Uses Expectimax-n
    def best_result_for_given_depth(self, board, player_index, depth):
        reasonable_attacks = resonable_attacks_for_player(self.players_order[player_index], board, self.players_ordered, self.clf)
        # Do leaf part of search
        if x:= self.part_leaf(reasonable_attacks, depth, board): return x
        # Do recursive part of search
        if x:= self.part_recursive(reasonable_attacks, depth, board, player_index): return x

    # Return vector for leaf evaluation
    def part_leaf(self, reasonable_attacks, depth, board):
        time_spent = time.time() - self.start_turn_time
        is_no_time = (self.time_left - time_spent) < self.half_min_time_left
        if ((not reasonable_attacks) or (depth == 0)) or is_no_time:
            # Evaluation for each player
            evaluation_list = []
            for i in range(len(self.players_order)):
                evaluation_list.append(evaluate_board(board, self.players_order[i], self.players_ordered))
            return None, evaluation_list
        return None

    # Recursively generate tree of moves
    def part_recursive(self, reasonable_attacks, depth, board, player_index):
        max_evaluation = [-inf for i in range(len(self.players_order))]
        move = None
        for atack in reasonable_attacks:
            # Get porobabilities
            probability_of_win= probability_of_successful_attack(board, atack[0].get_name(), atack[1].get_name())
            probability_of_loss = 1 - probability_of_win

            board_win = simulate_succesfull_move(self.players_order[player_index], board, atack[0].get_name(), atack[1].get_name())

            # Evaluation values
            alfa = [0 for i in range(len(self.players_order))]

            # If probability of succesfull atack is greather then x, dont generate loss tree for quicker generation
            if probability_of_win > 0.95:
                _, result_win = self.best_result_for_given_depth(board_win, (player_index + 1) % len(self.players_order), depth - 1)

                for i in range(len(alfa)):
                    alfa[i] = alfa[i] + (result_win[i] * probability_of_win)
            else:
                # Generate loss move
                board_loss = simulate_lossing_move(board, atack[0].get_name(), atack[1].get_name())

                # Calculate joined evaluation
                _, result_win = self.best_result_for_given_depth(board_win, (player_index + 1) % len(self.players_order), depth - 1)
                for i in range(len(alfa)):
                    alfa[i] = alfa[i] + (result_win[i] * probability_of_win)

                _, result_loss = self.best_result_for_given_depth(board_loss, (player_index + 1) % len(self.players_order), depth - 1)
                for i in range(len(alfa)):
                    alfa[i] = alfa[i] + (result_loss[i] * probability_of_loss)

            # Store better value for current maximazer 
            if alfa[player_index] > max_evaluation[player_index]:
                max_evaluation = alfa
                move = atack

        return move, max_evaluation