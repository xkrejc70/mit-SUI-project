from dicewars.client.game.board import Board
from dicewars.client.game.area import Area
from dicewars.ai.xkuder04.Mplayer import Mplayer
from dicewars.ai.xkuder04.utils.utils import probability_of_successful_attack
import numpy as np
import time
from .debug import debug_print, DP_FLAG
from .transfer_tree import transfer_tree

def get_best_transfer_route(player, board: Board, start_depth, available_steps):
    dist_dict = player_board2dist_dict(player, board)
    dist_counts = dist_dict2dist_counts(dist_dict)
    dist_direction = dist_counts2direction(dist_counts)
    tt = transfer_tree(dist_dict)
    route = tt.find_best_transfer(start_depth, available_steps)
    debug_print(f"Route: {route}", DP_FLAG.TRANSFER_VECTOR)
    return route

# Get tranfer to support with the least number of dice
def final_support(self, board):
    player = Mplayer(board, self.player_name)

    # Support border with the least number of dice
    transfer_depth = 1
    sorted_border_areas = sorted(player.border_areas, key=lambda border: border.dice)

    for border_to_support in sorted_border_areas:
        debug_print(f"min: {border_to_support.get_dice()}", DP_FLAG.TRANSFER)
        if border_to_support.get_dice() != 8:
            transfer = get_transfer_to_spec_border(player, board, border_to_support, transfer_depth)
            if transfer:
                return transfer
        else:
            break
    
    debug_print(f"No transfer (inner -> border) found", flag=DP_FLAG.TRANSFER)
    return None


# Get transfer from inner_area to border_area
def get_transfer_to_borders(player, board: Board, depth : int):
    if depth == 1:
        # Get transfer from inner_area with the most dice
        best_transfers = []

        for border in player.border_areas:
            if border.get_dice() == 8:
                continue
            
            best_transfer = get_best_transfer(player, board, border, [None])
            if best_transfer: best_transfers.append(best_transfer)

        if best_transfers:
            max_index = np.array(best_transfers).argmax(axis=0)[0]
            return best_transfers[max_index][1], best_transfers[max_index][2]
        else:
            return None

    elif depth == 2:
        # depth 2
        best_transfers = []
        inner_areas_names = [a.name for a in player.inner_areas]

        # Get areas that are adjacent to the borders
        border_neighs = []
        for border in player.border_areas:
            for areas in border.get_adjacent_areas_names():
                if isinstance(areas, int):
                    if areas in inner_areas_names: border_neighs.append(areas)
                else:
                    border_neighs.append([a for a in areas if a in inner_areas_names])
            
            for neigh in border.get_adjacent_areas_names():
                if neigh in inner_areas_names:
                    best_transfer = get_best_transfer(player, board, board.get_area(neigh), border_neighs)
                    if best_transfer: best_transfers.append(best_transfer)

        if best_transfers:
            max_index = np.array(best_transfers).argmax(axis=0)[0]
            return best_transfers[max_index][1], best_transfers[max_index][2]
        else:
            return None

    return None

# Get transfer from inner_area to specific border_area
def get_transfer_to_spec_border(player, board: Board, border : Area, n_transfers : int): # border pripadne jen jmeno (int)
    if border.get_dice() == 8:
        return None

    if n_transfers == 1:
        # 1 transfer: move from the area with the most dice
        best_transfer = get_best_transfer(player, board, border, [None])
        if best_transfer:
            return best_transfer[1], best_transfer[2]

    elif n_transfers == 2:
        pass
    return None

def get_transfer_to_spec_area():
    pass

# Get best transfer from neighbors
def get_best_transfer(player, board, dst_area, illegal_areas):
    inner_areas_names = [a.name for a in player.inner_areas]
    best_transfer = []
    max_dice = 1

    for neigh in dst_area.get_adjacent_areas_names():
        if neigh in inner_areas_names and neigh not in illegal_areas:
            n_neigh_dice = board.get_area(neigh).get_dice()
            if n_neigh_dice > max_dice:
                max_dice = n_neigh_dice
                best_transfer = [n_neigh_dice, neigh, dst_area.get_name()] # [n_dice, src_area, dst_area]
    return best_transfer

def from_largest_region(logger, board, attacks, player_name):
    players_regions = board.get_players_regions(player_name)
    max_region_size = max(len(region) for region in players_regions)
    max_sized_regions = [region for region in players_regions if len(region) == max_region_size]
    
    the_largest_region = max_sized_regions[0]
    logger.debug('The largest region: {}'.format(the_largest_region))
    return [attack for attack in attacks if attack[0].get_name() in the_largest_region]

def board2dist_dict_recursive(dist, dist_dict, dist_dict_set, area_names, board):
    dist_dict[dist] = []
    for b_a in dist_dict[dist-1]:
        for nb_a_name in b_a.get_adjacent_areas_names():
            if nb_a_name not in dist_dict_set and nb_a_name in area_names:
                dist_dict[dist].append(board.get_area(nb_a_name))
                dist_dict_set.add(nb_a_name)
    if len(dist_dict[dist]) != 0:
        board2dist_dict_recursive(dist+1, dist_dict, dist_dict_set, area_names, board)
    else:
        del dist_dict[dist]

def player_board2dist_dict(player, board: Board):
    area_names = [a.name for a in player.all_areas]
    dist_dict_set = set()
    dist_dict = {}
    dist = 0
    dist_dict[dist] = []
    for b_a in player.border_areas:
        dist_dict[dist].append(b_a)
        dist_dict_set.add(b_a.name)
    board2dist_dict_recursive(dist+1, dist_dict, dist_dict_set, area_names, board)
    return dist_dict

def dist_dict2dist_counts(dist_dict):
    dist_counts = {}
    for distance in dist_dict.keys():
        dist_counts[distance] = 0
        for area in dist_dict[distance]:
            dist_counts[distance] += area.dice
    return dist_counts

def dist_counts2direction(dist_counts):
    y = (sum(k for k in dist_counts.keys()))
    x = (sum(i for i in dist_counts.values()))
    if y == 0:
        return 1
    vector = (x,y)
    direction = vector[1] / vector[0]
    return direction

# Return transfers from endangered bord areas
def retreat_transfers(board, player_name):
    list_of_retreats = []
    border_areas = board.get_player_border(player_name)

    for area in border_areas:
        transfer_area_dice = area.get_dice()
        if transfer_area_dice < 2:
            continue

        neighbour_names = area.get_adjacent_areas_names()
        neighbour_areas = [board.get_area(adj) for adj in neighbour_names]

        # Make list of owned and enemy adnacent areas to calculate danger level
        owned_adjacent_areas = []
        enemy_adjacent_areas = []
        for neighbour_area in neighbour_areas:
            if neighbour_area.get_owner_name() != player_name:
                enemy_adjacent_areas.append(neighbour_area)
            else:
                owned_adjacent_areas. append(neighbour_area)

        # TODO test only max
        # Caclulate average conquer probability of area
        average_conguer_prob = 0
        n_possible_attackers = 0
        for enemy_area in enemy_adjacent_areas:
            if not enemy_area.can_attack():
                continue
            
            n_possible_attackers += 1
            average_conguer_prob += probability_of_successful_attack(board, enemy_area.get_name(), area.get_name())

        if n_possible_attackers == 0:
            average_conguer_prob = 0
        else:
            average_conguer_prob /= n_possible_attackers
        
        # Calculate best area to transfer to.
        transfer_area_dice = area.get_dice()
        for owned_area in owned_adjacent_areas:
            owned_area_dice = owned_area.get_dice()
            new_dice_count = transfer_area_dice + owned_area_dice
            if new_dice_count <= 8 and not(owned_area in border_areas):
                #print(area.get_name(), owned_area.get_name(), average_conguer_prob*new_dice_count)
                list_of_retreats.append((area.get_name(), owned_area.get_name(), average_conguer_prob*new_dice_count))

    return sorted(list_of_retreats, key= lambda x: x[2], reverse=True)
