import logging
import random

from dicewars.ai.utils import possible_attacks, save_state
from dicewars.ai.kb.xlogin42.utils import best_sdc_attack, is_acceptable_sdc_attack

from dicewars.client.ai_driver import BattleCommand, EndTurnCommand, TransferCommand


class AI:
    def __init__(self, player_name, board, players_order, max_transfers):
        self.player_name = player_name
        self.players_order = players_order
        self.max_transfers = max_transfers
        self.players_ordered = sorted(players_order)
        self.logger = logging.getLogger('AI')
        

    def ai_turn(self, board, nb_moves_this_turn, nb_transfers_this_turn, nb_turns_this_game, time_left):
        
        if nb_moves_this_turn == 0 and nb_transfers_this_turn == 0:
            print(f"####### NEW TURN #######")
        
        if nb_moves_this_turn == 0:
            self.evaluation_func(board)

        max_transfers = self.max_transfers  #6

        if nb_transfers_this_turn < max_transfers:
            transfer = self.get_transfer_to_borders(board)
            if transfer:
                    return TransferCommand(transfer[0], transfer[1])
            else:
                print(f"No transfer (inner -> border) found")
        else:
            print(f"Out of transfers ({nb_transfers_this_turn}/{self.max_transfers})")

        if nb_turns_this_game < 3:
            self.logger.debug("Doing a random move")
            attack_filter = lambda x: x
            attack_selector = random.choice
            attack_acceptor = lambda x: True

            with open('debug.save', 'wb') as f:
                save_state(f, board, self.player_name, self.players_order)

        else:
            self.logger.debug("Doing a serious move")
            attack_filter = lambda x: self.from_largest_region(board, x)
            attack_selector = best_sdc_attack
            attack_acceptor = lambda x: is_acceptable_sdc_attack(x)

            with open('debug.save', 'wb') as f:
                save_state(f, board, self.player_name, self.players_order)

        all_moves = list(possible_attacks(board, self.player_name))
        if not all_moves:
            self.logger.debug("There are no moves possible at all")
            return EndTurnCommand()

        moves_of_interest = attack_filter(all_moves)
        if not moves_of_interest:
            self.logger.debug("There are no moves of interest")
            return EndTurnCommand()

        the_move = attack_selector(moves_of_interest)

        if attack_acceptor(the_move):
            return EndTurnCommand()
            #return BattleCommand(the_move[0].get_name(), the_move[1].get_name())
        else:
            self.logger.debug("The move {} is not acceptable, ending turn".format(the_move))
            return EndTurnCommand()

    
    def get_transfer_to_borders(self, board):
        # transfer dice from inner_area to border_area (do 1st possible transfer)
        player = Mplayer(board, self.player_name)
        print(f"[{len(player.all_areas)}] all_areas: {[(a.get_name(), a.get_dice()) for a in player.all_areas]}")
        print(f"[{len(player.border_areas)}] border_areas: {[(a.get_name(), a.get_dice()) for a in player.border_areas]}")
        print(f"[{len(player.inner_areas)}] inner_areas: {[(a.get_name(), a.get_dice()) for a in player.inner_areas]}")
        border_areas_names = [a.name for a in player.border_areas]

        for area in player.inner_areas:
            if area.get_dice() < 2:
                continue
            for neigh in area.get_adjacent_areas_names():
                if neigh in border_areas_names and board.get_area(neigh).get_dice() < 8:
                    print(f"=> Transfer: {area.get_name(), area.get_dice()} => {neigh, board.get_area(neigh).get_dice()}")
                    return area.get_name(), neigh
        return None
    
    def from_largest_region(self, board, attacks):
        players_regions = board.get_players_regions(self.player_name)
        max_region_size = max(len(region) for region in players_regions)
        max_sized_regions = [region for region in players_regions if len(region) == max_region_size]
        
        the_largest_region = max_sized_regions[0]
        self.logger.debug('The largest region: {}'.format(the_largest_region))
        return [attack for attack in attacks if attack[0].get_name() in the_largest_region]

    def evaluation_func(self, board):
        max_score = 1000
        #print(f"Total players: {len(self.players_order)}, Players alive: {board.nb_players_alive()}")
        #print(f"AI PLayer_name: {self.player_name}")
        players = [Mplayer(board, player_name) for player_name in self.players_ordered]
        total_areas = sum(player.n_all_areas for player in players)
        total_dices = sum(player.n_dice for player in players)
        for player in players:
            up = player.n_all_areas + player.n_dice + player.n_border_dice + player.n_biggest_region_size   #primo umerne
            down = total_areas + total_dices + player.n_border_areas    #neprimo umerne
            score = player.is_alive*(up/down)   #if dead tak *0 -> score == 0, jinak je to *1 -> score == 1*score #zatim je to useless radek
            score = int(round(score*max_score))
            #print(f"Player_name: {player.player_name}; score: {score}")
        #print(f"#################################")

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
        #self.print_F()

    def print_F(self):
        print(f"player_name : {self.player_name}")
        print(f"n_dice : {self.n_dice}")
        print(f"all_areas : {[(a.get_name(), a.get_dice()) for a in self.all_areas]}")
        print(f"border_areas : {[(a.get_name(), a.get_dice()) for a in self.border_areas]}")
        print(f"inner_areas : {[(a.get_name(), a.get_dice()) for a in self.inner_areas]}")
        print(f"n_all_areas : {self.n_all_areas}")
        print(f"n_border_areas : {self.n_border_areas}")
        print(f"is_alive : {self.is_alive}")
        print()
        
