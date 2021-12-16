import copy
import pickle
from dicewars.client.game.board import Board
from dicewars.client.game.area import Area
from typing import Iterator, List, Tuple
from ..Mplayer import Mplayer
from dicewars.ai.utils import attack_succcess_probability, probability_of_successful_attack, probability_of_holding_area, possible_attacks
from .models_util import load_model, models_dir_filepath
from .debug import DP_FLAG, debug_print
import time

# List of resonable attacks for specified player
# Returns X moves that have good probability of success and have good chance to sorvive other AIs moves
# TODO make complexer moves selector
def resonable_attacks_for_player(player: int, board: Board):
    min_joined_probability = 0.4
    max_attacks = 3
    list_of_attacks = []

    for area in board.get_player_border(player):
        if not area.can_attack():
            continue

        neighbours = area.get_adjacent_areas_names()

        for adj in neighbours:
            adjacent_area = board.get_area(adj)
            if adjacent_area.get_owner_name() != player:
                joined_probability = probability_of_successful_attack_and_one_turn_hold(player, board, area, adjacent_area)
                if joined_probability >= min_joined_probability:
                    list_of_attacks.append((area, adjacent_area, joined_probability))
                    
    return sorted(list_of_attacks, key= lambda x: x[2])[-max_attacks:]

# Calculates joined probability of succesfull atack and holding conquered area for another turn
def probability_of_successful_attack_and_one_turn_hold(player, board, area, adjacent_area):
    # Probability of successfull conguering
    attack_probability = probability_of_successful_attack(board, area.get_name(), adjacent_area.get_name())

    # Probability of holding that area to another turn
    move_board = simulate_succesfull_move(player, board, area.get_name(), adjacent_area.get_name())
    move_area = move_board.get_area(adjacent_area.get_name())
    hold_probability = probability_of_holding_area(move_board, move_area.get_name(), move_area.get_dice(), player)

    return attack_probability * hold_probability

def best_possible_attack(board, player_name):
    max_prob = 0
    move = None
    for attack in possible_attacks(board, player_name):
        prob = probability_of_successful_attack_and_one_turn_hold(player_name, board, attack[0], attack[1])
        if prob > max_prob:
            max_prob = prob
            move = attack
    return move

# Evaluate board score for player
# TODO make more complex evaluation
def evaluate_board(board: Board, player_name: int, players_ordered: List[int], regr) -> float:
    players = [Mplayer(board, player_name) for player_name in players_ordered]
    total_areas = sum(player.n_all_areas for player in players)
    total_dices = sum(player.n_dice for player in players)

    player = players[player_name - 1]

    up = player.n_all_areas + player.n_dice + player.n_border_dice + player.n_biggest_region_size
    down = total_areas + total_dices + player.n_border_areas
    score = player.is_alive*(up/down)

    features = [player.n_all_areas, player.n_dice, player.n_border_dice, player.n_biggest_region_size, total_areas, total_dices, player.n_border_areas]
    #regr = load_model(models_dir_filepath("eval_state_rf.model"))
    regr_result = regr.predict([features])[0]

    #print(f"Score: {score}, Rscore: {regr_result}")
    #diff = round(score-regr_result, 3)
    #print(diff)

    #return score
    return regr_result

#TODO delete
def evaluate_board_me(board: Board, player_name: int, players_ordered: List[int]) -> float:
    players = [Mplayer(board, player_name) for player_name in players_ordered]
    total_areas = sum(player.n_all_areas for player in players)
    total_dices = sum(player.n_dice for player in players)

    player = players[player_name - 1]

    up = player.n_all_areas + player.n_dice + player.n_border_dice + player.n_biggest_region_size
    down = total_areas + total_dices + player.n_border_areas
    score = player.is_alive*(up/down)
    #print([player.n_all_areas, player.n_dice, player.n_border_dice, player.n_biggest_region_size, total_areas, total_dices, player.n_border_areas, score])
    return score

# Simulate winning move on board
def simulate_succesfull_move(player_name: int, board: Board, atk_from: int, atk_to: int) -> Board:
    #edited_board = copy.deepcopy(board)
    edited_board = pickle.loads(pickle.dumps(board))

    area_from = edited_board.get_area(atk_from)
    area_to = edited_board.get_area(atk_to)

    area_to.set_dice(area_from.get_dice() - 1)
    area_to.set_owner(player_name)
    area_from.set_dice(1)

    return edited_board

# Simulate lossing move on board
def simulate_lossing_move(board: Board, atk_from: int, atk_to:int) -> Board:
    #edited_board = copy.deepcopy(board)
    edited_board = pickle.loads(pickle.dumps(board))

    area_from = edited_board.get_area(atk_from)
    area_to = edited_board.get_area(atk_to)

    if area_from.get_dice() == 8:
        new_dice_count = area_to.get_dice() - 2
        if new_dice_count < 1:
            area_to.set_dice(1)
        else:
            area_to.set_dice(new_dice_count)

    elif area_from.get_dice() >= 4:
        new_dice_count = area_to.get_dice() - 1
        if new_dice_count < 1:
            area_to.set_dice(1)
        else:
            area_to.set_dice(new_dice_count)

    area_from.set_dice(1)

    return edited_board

def is_endturn(time_left, min_time_left, nb_moves_this_turn, max_attacks_per_round):
    if time_left > min_time_left:
        return True
    if nb_moves_this_turn >= max_attacks_per_round:
        return True
    return False

#TODO delete
def print_start(self, board, nb_moves_this_turn, nb_transfers_this_turn, time_left):
    if nb_moves_this_turn == 0 and nb_transfers_this_turn == 0:
        self.turn_time = time.time()
        debug_print(f"\n####### NEW TURN #######", flag=DP_FLAG.NEW_TURN)
        debug_print(f"Time left = {time_left}", flag=DP_FLAG.NEW_TURN)
        debug_print(f"Player name = {self.player_name}", flag=DP_FLAG.NEW_TURN)
        debug_print(f"Player order = {self.players_order}", flag=DP_FLAG.NEW_TURN)
        #debug_print(f"all_areas: {[(a.get_name(), a.get_dice()) for a in board.get_player_areas(self.player_name)]}")
        #debug_print(f"border_areas: {[(a.get_name(), a.get_dice()) for a in board.get_player_border(self.player_name)]}")
        #debug_print(f"inner_areas: {[(a.get_name(), a.get_dice()) for a in board.get_player_areas(self.player_name) if a not in board.get_player_border(self.player_name)]}")