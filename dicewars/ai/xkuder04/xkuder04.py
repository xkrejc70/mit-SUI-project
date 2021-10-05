import logging
import random

from dicewars.ai.utils import possible_attacks, save_state
from dicewars.ai.kb.xlogin42.utils import best_sdc_attack, is_acceptable_sdc_attack

from dicewars.client.ai_driver import BattleCommand, EndTurnCommand


class AI:
    def __init__(self, player_name, board, players_order, max_transfers):
        self.player_name = player_name
        self.players_order = players_order
        self.logger = logging.getLogger('AI')

    def ai_turn(self, board, nb_moves_this_turn, nb_transfers_this_turn, nb_turns_this_game, time_left):
        self.evaluation_func(board)

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
            return BattleCommand(the_move[0].get_name(), the_move[1].get_name())
        else:
            self.logger.debug("The move {} is not acceptable, ending turn".format(the_move))
            return EndTurnCommand()

    def from_largest_region(self, board, attacks):
        players_regions = board.get_players_regions(self.player_name)
        max_region_size = max(len(region) for region in players_regions)
        max_sized_regions = [region for region in players_regions if len(region) == max_region_size]
        
        the_largest_region = max_sized_regions[0]
        self.logger.debug('The largest region: {}'.format(the_largest_region))
        return [attack for attack in attacks if attack[0].get_name() in the_largest_region]

    def evaluation_func(self, board):
        print(f"Total players: {len(self.players_order)}, Players alive: {board.nb_players_alive()}")
        players = [Mplayer(board, player_name) for player_name in self.players_order]
        print(f"#################################")
        score = 42
        return score

class Mplayer:
    def __init__(self, board, player_name : int):
        self.player_name = player_name
        self.n_dice = board.get_player_dice(self.player_name)
        self.all_areas = board.get_player_areas(self.player_name)
        self.border_areas = board.get_player_border(self.player_name)
        self.n_all_areas = len(self.all_areas)
        self.n_border_areas = len(self.border_areas)
        self.is_alive = bool(self.n_all_areas)
        self.print_F()

    def print_F(self):
        print(f"player_name : {self.player_name}")
        print(f"n_dice : {self.n_dice}")
        print(f"all_areas : {[(a.get_name(), a.get_dice()) for a in self.all_areas]}")
        print(f"border_areas : {[(a.get_name(), a.get_dice()) for a in self.border_areas]}")
        print(f"n_all_areas : {self.n_all_areas}")
        print(f"n_border_areas : {self.n_border_areas}")
        print(f"is_alive : {self.is_alive}")
        print()
        