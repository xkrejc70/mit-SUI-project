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