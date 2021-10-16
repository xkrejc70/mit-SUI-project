import copy
from dicewars.client.game.board import Board
from dicewars.client.game.area import Area
from typing import Iterator, List, Tuple
from ..Mplayer import Mplayer
from dicewars.ai.utils import attack_succcess_probability, probability_of_successful_attack, probability_of_holding_area

# List of resonable attacks for specified player
# Returns moves that have good probability of success and have good chance to sorvive other AIs moves
# TODO make complexer moves selector
def resonable_attacks_for_player(player: int, board: Board):
    list_of_attacks = []
    for area in board.get_player_border(player):
        if not area.can_attack():
            continue

        neighbours = area.get_adjacent_areas_names()

        for adj in neighbours:
            adjacent_area = board.get_area(adj)
            if adjacent_area.get_owner_name() != player:
                joined_probability = probability_of_successful_attack_and_one_turn_hold(player, board, area, adjacent_area)
                if joined_probability >= 0.4:
                    list_of_attacks.append((area, adjacent_area))
                    

    return list_of_attacks

# Calculates joined probability of succesfull atack and holding conquered area for another turn
def probability_of_successful_attack_and_one_turn_hold(player, board, area, adjacent_area):
     # Probability of successfull conguering
    attack_probability = probability_of_successful_attack(board, area.get_name(), adjacent_area.get_name())

    # Probability of holding that area to another turn
    move_board = simulate_succesfull_move(player, board, area.get_name(), adjacent_area.get_name())
    move_arrea = move_board.get_area(adjacent_area.get_name())
    hold_probability = probability_of_holding_area(move_board, move_arrea.get_name(), move_arrea.get_dice(), player)

    return attack_probability * hold_probability


# Evaluate board score for player
# TODO make complexer evaluation
def evaluate_board(board: Board, player_name: int, players_ordered: List[int]) -> float:
    players = [Mplayer(board, player_name) for player_name in players_ordered]
    total_areas = sum(player.n_all_areas for player in players)
    total_dices = sum(player.n_dice for player in players)

    player = players[player_name - 1]

    up = player.n_all_areas + player.n_dice + player.n_border_dice + player.n_biggest_region_size
    down = total_areas + total_dices + player.n_border_areas
    score = player.is_alive*(up/down)
    return score

# Simulate winning move on board
def simulate_succesfull_move(player_name: int, board: Board, atk_from: int, atk_to: int) -> Board:
    edited_board = copy.deepcopy(board)

    area_from = edited_board.get_area(atk_from)
    area_to = edited_board.get_area(atk_to)

    area_to.set_dice(area_from.get_dice() - 1)
    area_to.set_owner(player_name)
    area_from.set_dice(1)

    return edited_board

# Simulate lossing move on board
def simulate_lossing_move(board: Board, atk_from: int, atk_to:int) -> Board:
    edited_board = copy.deepcopy(board)

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