from dicewars.client.game.board import Board
from dicewars.client.game.area import Area
import numpy as np

# Get transfer from inner_area to border_area
# TODO generate states, find best based on the number of transfers
# TODO presouvat na zaklade moznych utokz na borders (n_dice, dulezitost udrzeni hranice), presun kostek mezi borders
def get_transfer_to_borders(player, board: Board, depth : int):
    if depth == 1:
        # Get transfer from inner_area with the most dice
        best_transfers = []

        for border in player.border_areas:
            if border.get_dice() == 8:
                continue
            #print(f"*border: {border.get_name()}")
            
            best_transfer = get_best_transfer(player, board, border, [None]) #self.foo()? funguje ¯\_(ツ)_/¯ -nefunguje xD
            if best_transfer: best_transfers.append(best_transfer)

        #print(f"best transfers: {best_transfers}")
        if best_transfers:
            max_index = np.array(best_transfers).argmax(axis=0)[0]
            return best_transfers[max_index][1], best_transfers[max_index][2]
        else:
            return None

    elif depth == 2:
        # depth 2 ######################xx TORENAME
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
        #print(f"border_neighs: {border_neighs}")

        for border in player.border_areas:
            #print(f"*border: {border.get_name()}")
            
            for neigh in border.get_adjacent_areas_names():
                if neigh in inner_areas_names:
                    #print(f"neigh_1: {neigh}")
                    best_transfer = get_best_transfer(player, board, board.get_area(neigh), border_neighs)
                    if best_transfer: best_transfers.append(best_transfer)

        #print(f"best transfers: {best_transfers}")
        if best_transfers:
            max_index = np.array(best_transfers).argmax(axis=0)[0]
            return best_transfers[max_index][1], best_transfers[max_index][2]
        else:
            return None

    return None

# Get transfer from inner_area to specific border_area
def get_transfer_to_spec_border(player, board: Board, border : Area, n_transfers : int): # border pripadne jen jmeno (int)
    if border.get_dice() == 8:
        #print(f"Border {border.get_name()} already full")
        return None

    if n_transfers == 1:
        # 1 transfer: move from the area with the most dice
        best_transfer = get_best_transfer(player, board, border, [None])
        if best_transfer:
            return best_transfer[1], best_transfer[2]

    elif n_transfers == 2:
        pass
    return None

# Get transfer from inner_area to border_area, as close as possible
def get_transfer_near_the_border():
    pass

# Get best transfer from neighbors
def get_best_transfer(player, board, dst_area, illegal_areas):
    inner_areas_names = [a.name for a in player.inner_areas]
    best_transfer = []
    max_dice = 1

    for neigh in dst_area.get_adjacent_areas_names():
        if neigh in inner_areas_names and neigh not in illegal_areas:
            #print(f"neigh: {neigh}")
            n_neigh_dice = board.get_area(neigh).get_dice()
            if n_neigh_dice > max_dice:
                max_dice = n_neigh_dice
                best_transfer = [n_neigh_dice, neigh, dst_area.get_name()] # [n_dice, src_area, dst_area]
                #print(f"New best transfer: {neigh, n_neigh_dice} => {dst_area.get_name(), dst_area.get_dice()}")
    return best_transfer

def from_largest_region(logger, board, attacks, player_name):
    players_regions = board.get_players_regions(player_name)
    max_region_size = max(len(region) for region in players_regions)
    max_sized_regions = [region for region in players_regions if len(region) == max_region_size]
    
    the_largest_region = max_sized_regions[0]
    logger.debug('The largest region: {}'.format(the_largest_region))
    return [attack for attack in attacks if attack[0].get_name() in the_largest_region]