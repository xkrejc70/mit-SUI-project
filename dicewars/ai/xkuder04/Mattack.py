from dicewars.client.game.board import Board
from dicewars.client.game.area import Area
from numpy import inf
from dicewars.ai.utils import save_state, probability_of_successful_attack, attack_succcess_probability
from .utils.utils import resonable_attacks_for_player, simulate_lossing_move, simulate_succesfull_move, evaluate_board, evaluate_board_me
from .utils.models_util import load_model, models_dir_filepath

class Mattack:
    def __init__(self, depth, players_order, players_ordered, player_index):
        self.depth = depth
        self.players_order = players_order
        self.players_ordered = players_ordered
        self.player_index = player_index
        self.regr = load_model(models_dir_filepath("eval_state_rf.model"))

    def best_result(self, board):
        evaluate_board_me(board, self.players_order[self.player_index], self.players_ordered)
        return self.best_result_for_given_depth(board, self.player_index, self.depth)

    # Uses Expectimax-n
    def best_result_for_given_depth(self, board, player_index, depth):
        # Maximal depth of searching
        if ((not resonable_attacks_for_player(self.players_order[player_index], board)) or (depth == 0)):
            # Evaluation for each player
            evaluation_list = []
            for i in range(len(self.players_order)):
                evaluation_list.append(evaluate_board(board, self.players_order[i], self.players_ordered, self.regr))
            return None, evaluation_list

        # Get best move from all moves of player i 
        # Each move consist of success and loss with respective probabilities
        max_evaluation = [-inf for i in range(len(self.players_order))]
        move = None
        for atack in resonable_attacks_for_player(self.players_order[player_index], board):
            # Get porobabilities
            probability_of_win= probability_of_successful_attack(board, atack[0].get_name(), atack[1].get_name())
            probability_of_loss = 1 - probability_of_win

            # Generate win move
            board_win = simulate_succesfull_move(self.players_order[player_index], board, atack[0].get_name(), atack[1].get_name())

            # Evaluation values
            alfa = [0 for i in range(len(self.players_order))]

            # If probability of succesfull atack is greather then x, dont generate loss tree for quicker generation
            # TODO x = 0.95
            if probability_of_win > 0.95:
                _, result_win = self.best_result_for_given_depth(board_win, (player_index + 1) % len(self.players_order), depth - 1)

                alfa = result_win
            else:
                # Generate loss move
                board_loss = simulate_lossing_move(board, atack[0].get_name(), atack[1].get_name())

                # Calculate joined evaluation
                alfa = [0 for i in range(len(self.players_order))]
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