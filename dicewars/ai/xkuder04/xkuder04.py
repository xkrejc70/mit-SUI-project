import logging
import random
import copy
import numpy as np
import time

from .Mplayer import Mplayer
from .Mattack import Mattack
from .utils.utils import resonable_attacks_for_player, simulate_lossing_move, simulate_succesfull_move, evaluate_board, probability_of_successful_attack_and_one_turn_hold, is_endturn
from .utils.transfer_utils import get_transfer_to_borders, get_transfer_to_spec_border, get_transfer_near_the_border, get_best_transfer, from_largest_region

from numpy.lib.function_base import append
from dicewars.client.game import player

from dicewars.client.game.board import Board
from dicewars.client.game.area import Area
from typing import Iterator, List, Text, Tuple

from dicewars.ai.utils import possible_attacks, save_state, probability_of_successful_attack, attack_succcess_probability
from dicewars.ai.kb.xlogin42.utils import best_sdc_attack, is_acceptable_sdc_attack

from dicewars.client.ai_driver import BattleCommand, EndTurnCommand, TransferCommand


class AI:
    def __init__(self, player_name, board, players_order, max_transfers):
        self.player_name = player_name
        self.players_order = players_order
        self.player_index = self.players_order.index(self.player_name)
        self.max_transfers = max_transfers
        self.players_ordered = sorted(players_order)
        self.logger = logging.getLogger('AI')
        self.allow_logs = False
        self.min_time_left = 6
        self.max_attacks_per_round = 4
        self.depth = 4
        self.mattack = Mattack(self.depth, self.players_order, self.players_ordered, self.player_index)
        
    def ai_turn(self, board, nb_moves_this_turn, nb_transfers_this_turn, nb_turns_this_game, time_left):
        # TODO
        """
        Start evaluation tournament:  python3 ./scripts/dicewars-tournament.py -r -g 2 -n 50 --ai-under-test xkuder04.xkuder04 -b 101 -s 1337 -l logy
        Manage time for number of attacks
        """
        
        if nb_moves_this_turn == 0 and nb_transfers_this_turn == 0:
            self.turn_time = time.time()
            self.debug_print(f"####### NEW TURN #######")
            self.debug_print(f"Time left = {time_left}")
            self.debug_print(f"Player name = {self.player_name}")
            self.debug_print(f"Player order = {self.players_order}")
            self.debug_print(f"all_areas: {[(a.get_name(), a.get_dice()) for a in board.get_player_areas(self.player_name)]}")
            self.debug_print(f"border_areas: {[(a.get_name(), a.get_dice()) for a in board.get_player_border(self.player_name)]}")
            self.debug_print(f"inner_areas: {[(a.get_name(), a.get_dice()) for a in board.get_player_areas(self.player_name) if a not in board.get_player_border(self.player_name)]}")
        
        if nb_moves_this_turn > 1:
            # TODO manage time
            end = time.time()
            if is_endturn(time_left, self.min_time_left, nb_moves_this_turn, self.max_attacks_per_round):
                self.debug_print(f"End turn, time: {end - self.turn_time}")
                return EndTurnCommand()
        
        max_transfers = self.max_transfers
        player = Mplayer(board, self.player_name)

        if nb_transfers_this_turn < max_transfers:
            # 1) transfer dice close to the border (1st, 3rd and 5th transfer)
            # 2) transfer dice to the border (2, 4, 6)
            transfer = get_transfer_to_borders(player, board, 2 - nb_transfers_this_turn % 2)
            #transfer = self.get_transfer_to_spec_border(player, board, player.border_areas[0], 1)
            if transfer:
                self.debug_print(f"=> Transfer: {transfer[0], transfer[1]}")
                return TransferCommand(transfer[0], transfer[1])
            else:
                self.debug_print(f"No transfer (inner -> border) found")
        else:
            self.debug_print(f"Out of transfers ({nb_transfers_this_turn}/{self.max_transfers})")

        # For testing purpuses can be switched between testing AI and AI in construction
        # Testing of Expectiminimax
       
        self.debug_print(f"Evaluate board: {evaluate_board(board, self.player_name, self.players_ordered, self.mattack.regr)}")

        # TODO IF evaluation infinite then tranfer die
        # TODO for board with many possibilities is calc time bigger then 10s
        move, evaluation = self.mattack.best_result(board)
        #move, evaluation = self.best_result_for_given_depth(board, self.players_order.index(self.player_name), 4)

        self.debug_print(f"Best evaluation {evaluation}")
        if move:
            # Best move calculated by depth search
            self.debug_print(f"Depth search attack {move[0].get_name()}->{move[1].get_name()}")
            return BattleCommand(move[0].get_name(), move[1].get_name())
        else:
            # Try move with best chance of winning and holding arrea
            max_value = 0
            move = None
            for attack in possible_attacks(board, self.player_name):
                prob = probability_of_successful_attack_and_one_turn_hold(self.player_name, board, attack[0], attack[1])
                if prob > max_value:
                    max_value = prob
                    move = attack

            if move:
                self.debug_print(f"Best value attack {move[0].get_name()}->{move[1].get_name()}")
                return BattleCommand(move[0].get_name(), move[1].get_name())
            else:
                self.debug_print("No attack")
                end = time.time()
                self.debug_print(f"End turn, time: {end - self.turn_time}")
                return EndTurnCommand()

    # Debug logger
    def debug_print(self, text):
        if self.allow_logs:
            print(text)