
from numpy.lib.function_base import piecewise


class Mplayer:
    def __init__(self, board, player_name : int):
        self.player_name = player_name
        self.n_dice = board.get_player_dice(self.player_name)
        self.all_areas = board.get_player_areas(self.player_name)
        self.border_areas = board.get_player_border(self.player_name)
        self.inner_areas = [a for a in self.all_areas if a not in self.border_areas]
        self.n_biggest_region_size = max(len(region) for region in board.get_players_regions(self.player_name))
        self.n_all_areas = len(self.all_areas)
        self.n_border_areas = len(self.border_areas)
        self.n_inner_areas = len(self.inner_areas)
        self.n_border_dice = sum(a.get_dice() for a in self.border_areas)
        self.is_alive = bool(self.n_all_areas)

        ######### Calculate layers from border and dice in them #############
        if self.n_all_areas != 0:
            # Inicialize areas to layers
            area_layer = [256 for i in range(self.n_all_areas)]
            for i in range(self.n_all_areas):
                if self.all_areas[i] in self.border_areas:
                    area_layer[i] = 1

            # Calculate layer number form border
            areas_to_cover = list(self.border_areas)
            finished_areas = list()
            while areas_to_cover:
                area = areas_to_cover.pop(0)
                layer = area_layer[self.all_areas.index(area)]

                for neighbour_index in area.get_adjacent_areas_names():
                    neighbour_area = board.get_area(neighbour_index)
                    if neighbour_area.get_owner_name() != player_name:
                        continue
                    
                    if area_layer[self.all_areas.index(neighbour_area)] > layer + 1:
                        area_layer[self.all_areas.index(neighbour_area)] = layer + 1

                    if neighbour_area not in finished_areas:
                        areas_to_cover.append(neighbour_area)
                        finished_areas.append(neighbour_area)

            # Create list of layers with arreas
            areas_in_layers = [list() for i in range(max(area_layer))]
            for i in range(self.n_all_areas):
                layer = area_layer[i]
                areas_in_layers[layer-1].append(self.all_areas[i])
                
            # Calculate number of dice in layers
            dice_in_layers = [0 for i in range(max(area_layer))]
            for i in range(len(dice_in_layers)):
                for area in areas_in_layers[i]:
                    dice_in_layers[i] += area.get_dice()

            self.areas_in_layers = areas_in_layers
            self.dice_in_layers = dice_in_layers
            self.n_layers = len(self.areas_in_layers)

    #TODO delete
    """def print_F(self):
        print(f"player_name : {self.player_name}")
        print(f"n_dice : {self.n_dice}")
        print(f"all_areas : {[(a.get_name(), a.get_dice()) for a in self.all_areas]}")
        print(f"border_areas : {[(a.get_name(), a.get_dice()) for a in self.border_areas]}")
        print(f"inner_areas : {[(a.get_name(), a.get_dice()) for a in self.inner_areas]}")
        print(f"n_all_areas : {self.n_all_areas}")
        print(f"n_border_areas : {self.n_border_areas}")
        print(f"is_alive : {self.is_alive}")
        print()"""