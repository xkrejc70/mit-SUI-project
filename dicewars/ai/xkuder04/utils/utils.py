import pickle
import torch
import numpy as np
from dicewars.client.game.board import Board
from typing import List
from dicewars.ai.xkuder04.Mplayer import Mplayer
from dicewars.ai.utils import probability_of_successful_attack, probability_of_holding_area, possible_attacks
from dicewars.ai.xkuder04.utils.debug import DP_FLAG, debug_print
from dicewars.ai.xkuder04.utils.transfer_utils import player_board2dist_dict, dist_dict2dist_counts, dist_counts2direction

def largest_region(board, player_name):
    players_regions = board.get_players_regions(player_name)
    max_region_size = max(len(region) for region in players_regions)
    return [region for region in players_regions if len(region) == max_region_size][0]

def area_predictor_features(current_area, target_area, player_name, board: Board, players_ordered):
    player = Mplayer(board, player_name)
    neighbours = [board.get_area(name) for name in target_area.get_adjacent_areas_names()]
    enemy_neighbours = [area for area in neighbours if area.get_owner_name() != player_name]
    border = player.border_areas
    #Pocet kostek ja na hranici
    border_dice_me = sum(area.get_dice() for area in border)
    #Pocet kostek ja na hranici prumer
    border_dice_me_avg = border_dice_me/len(border)
    #Pocet kostek policko ja
    current_dice = current_area.get_dice()
    #Pocet kostek policko nepritel
    target_dice = target_area.get_dice()
    #Pocet sousedu co nejsem ja
    n_enemy_neighbours = len(enemy_neighbours)
    #Pocet sousedu co jsem ja
    n_me_neighbours = len([area for area in neighbours if area.get_owner_name() == player_name])
    #am i in max area #NOT NOW
    is_in_largest_region = 1 if current_area.get_name() in largest_region(board, player_name) else 0
    #distribution_direction
    distribution_direction = get_distribution_direction(player, board)
    #player_count
    n_players = len(players_ordered)
    #moje area/areas
    areas_ration = player.n_all_areas / len(board.areas)
    #Pocet kostek soused na hranici prumer
    border_dice_enemy_avg = 0 if n_enemy_neighbours == 0 else sum(area.get_dice() for area in enemy_neighbours)/n_enemy_neighbours

    features = [
        border_dice_me,
        border_dice_me_avg,
        current_dice,
        target_dice,
        n_enemy_neighbours,
        n_me_neighbours,
        is_in_largest_region,
        distribution_direction,
        n_players,
        areas_ration,
        border_dice_enemy_avg
    ]
    return features
    
# List of resonable attacks for specified player
# Returns X moves that have good probability of success and have good chance to sorvive other AIs moves
def resonable_attacks_for_player(player: int, board: Board, players_ordered, clf):
    moves = []
    feature_list = []

    for area in board.get_player_border(player):
        if not area.can_attack():
            continue

        neighbours = area.get_adjacent_areas_names()

        for adj in neighbours:
            adjacent_area = board.get_area(adj)
            if adjacent_area.get_owner_name() != player:
                features = area_predictor_features(area, adjacent_area, player, board, players_ordered)
                #prob = probability_of_successful_attack_and_one_turn_hold(player, board, area, adjacent_area)
                #debug_print(features+[prob], flag=DP_FLAG.TRAIN_DATA)
                feature_list.append(features)
                moves.append((area, adjacent_area))
    
    if len(feature_list) == 0:
        return []

    list_of_attacks = []
    #results = clf.predict(feature_list)
    feature_list = torch.from_numpy(np.array(feature_list)).type(torch.FloatTensor)
    results = clf.predict(feature_list)
    for move, result in zip(moves, results):
        if bool(result):
            list_of_attacks.append(move)
    return list_of_attacks

# Calculates joined probability of succesfull atack and holding conquered area for another turn
def probability_of_successful_attack_and_one_turn_hold(player, board, area, adjacent_area):
    # Probability of successfull conguering
    attack_probability = probability_of_successful_attack(board, area.get_name(), adjacent_area.get_name())

    # Probability of holding that area to another turn
    move_board = simulate_succesfull_move(player, board, area.get_name(), adjacent_area.get_name())
    move_area = move_board.get_area(adjacent_area.get_name())
    hold_probability = probability_of_holding_area(move_board, move_area.get_name(), move_area.get_dice(), player)

    return attack_probability * hold_probability

# Return move with best actual attack and hold probability
def best_possible_attack(board, player_name):
    max_prob = 0
    move = None
    for attack in possible_attacks(board, player_name):
        prob = probability_of_successful_attack_and_one_turn_hold(player_name, board, attack[0], attack[1])
        if attack[0] in Mplayer(board, player_name).biggest_region:
            prob = prob * 2
        if prob > max_prob:
            max_prob = prob
            move = attack
    return move

# Return move with best actual attack prob
def best_winning_attack(board, player_name):
    max_prob = 0
    move = None
    for attack in possible_attacks(board, player_name):
        prob = probability_of_successful_attack(board, attack[0].get_name(), attack[1].get_name())
        if attack[0] in Mplayer(board, player_name).biggest_region:
            prob = prob * 2
        if prob > max_prob:
            max_prob = prob
            move = attack
    return move, max_prob

# Evaluate board score for player
def evaluate_board(board: Board, player_name: int, players_ordered: List[int]) -> float:
    players = [Mplayer(board, player_name) for player_name in players_ordered]
    total_areas = sum(player.n_all_areas for player in players)

    player = players[player_name - 1]

    # Owerall priorities
    priority_area = 1
    priority_max_area = 10
    priority_border_area = 4
    priority_layer_dice = 8
    sum_priority = priority_area + priority_max_area + priority_border_area + priority_layer_dice

    score = 0

    if player.n_all_areas == 0:
        return 0
    elif player.n_all_areas == total_areas:
        return 1
    else:
        ############### Maximaze me ####################
        # All in 0 - 1 inervals
        # Areas
        areas = player.n_all_areas/total_areas
        max_area = player.n_biggest_region_size / player.n_all_areas
        border = player.n_inner_areas / player.n_all_areas
        
        layers_dice_ratio = list()
        for i in range(player.n_layers):
            layers_dice_ratio.append(player.dice_in_layers[i] / (len(player.areas_in_layers[i])*8))

        # Distribute priority
        priorities_list = [1, 2/3, 4/7, 8/15, 16/31, 1/2]
        priority = priorities_list[-1]
        if player.n_layers < len(priorities_list):
            priority = priorities_list[player.n_layers-1]

        layer_priorities = list()
        for i in range(player.n_layers):
            layer_priorities.append(layers_dice_ratio[i]*pow(priority, i+1))

        layers = sum(layer_priorities)
        score_me = areas*priority_area + max_area*priority_max_area + border*priority_border_area + layers*priority_layer_dice
        score += score_me/sum_priority

    return score

def get_distribution_direction(player, board):
    dist_dict = player_board2dist_dict(player, board)
    dist_counts = dist_dict2dist_counts(dist_dict)
    dist_direction = dist_counts2direction(dist_counts)
    return dist_direction

def get_feature_vector(score, areas, max_area, border, layers, players, player, board):
    player_count = len([p for p in players if p.n_all_areas != 0])
    distribution_direction = get_distribution_direction(player, board)
    features = [
        areas,
        max_area, 
        border,
        layers,
        player_count,
        distribution_direction,
        score
    ]
    return features

# Simulate winning move on board
def simulate_succesfull_move(player_name: int, board: Board, atk_from: int, atk_to: int) -> Board:
    edited_board = pickle.loads(pickle.dumps(board))

    area_from = edited_board.get_area(atk_from)
    area_to = edited_board.get_area(atk_to)

    area_to.set_dice(area_from.get_dice() - 1)
    area_to.set_owner(player_name)
    area_from.set_dice(1)

    return edited_board

# Simulate lossing move on board
def simulate_lossing_move(board: Board, atk_from: int, atk_to:int) -> Board:
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

# Check if not enough time to continue
def is_endturn(time_left, min_time_left, nb_moves_this_turn, max_attacks_per_round):
    if time_left < min_time_left:
        return True
    if nb_moves_this_turn >= max_attacks_per_round:
        return True
    return False

def print_start(self, board, nb_moves_this_turn, nb_transfers_this_turn, time_left):
    if nb_moves_this_turn == 0 and nb_transfers_this_turn == 0:
        debug_print(f"\n####### NEW TURN #######", flag=DP_FLAG.NEW_TURN)
        debug_print(f"Time left = {time_left}", flag=DP_FLAG.NEW_TURN)
        debug_print(f"Player name = {self.player_name}", flag=DP_FLAG.NEW_TURN)
        debug_print(f"Player order = {self.players_order}", flag=DP_FLAG.NEW_TURN)