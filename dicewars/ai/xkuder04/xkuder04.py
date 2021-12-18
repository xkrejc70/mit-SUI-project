import logging
import random
import copy
import numpy as np
import time

from .Mplayer import Mplayer
from .Mattack import Mattack
from .utils.utils import evaluate_board, is_endturn, print_start, best_possible_attack
from .utils.debug import DP_FLAG, debug_print
from .utils.transfer_utils import get_transfer_to_borders, get_transfer_to_spec_border, get_best_transfer_route, get_own_area_info
from .utils.strategy import STRATEGY, select_strategy

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
        self.min_time_left = 6
        self.max_attacks_per_round = 4
        self.strategy = STRATEGY.DEFAULT
        self.depth = 4
        self.mattack = Mattack(self.depth, self.players_order, self.players_ordered, self.player_index, self.min_time_left)
        self.transfer_route = []
        
    def ai_turn(self, board, nb_moves_this_turn, nb_transfers_this_turn, nb_turns_this_game, time_left):
        self.start_turn_time = time.time()
        print_start(self, board, nb_moves_this_turn, nb_transfers_this_turn, time_left)

        if x:= self.part_endturn(nb_moves_this_turn, time_left): return x

        self.strategy = select_strategy(self, board)
        if self.strategy == STRATEGY.DEFAULT:
            self.strategy = "default"
            if x:= self.part_transfer_deep(board, nb_transfers_this_turn, nb_moves_this_turn): return x
            if x:= self.part_transfer(board, nb_transfers_this_turn): return x
            if x:= self.part_attack(board, time_left): return x
        elif self.strategy == STRATEGY.ATTACK:
            pass
        elif self.strategy == STRATEGY.SUPPORT_BORDERS:
            pass


        return EndTurnCommand()

    def part_endturn(self, nb_moves_this_turn, time_left):
        if nb_moves_this_turn > 1:
            # TODO manage time
            if is_endturn(time_left, self.min_time_left, nb_moves_this_turn, self.max_attacks_per_round):
                debug_print(f"End turn, time: {time.time() - self.start_turn_time}", DP_FLAG.ENDTURN_PART)
                return EndTurnCommand()
        return None

    def part_transfer(self, board, nb_transfers_this_turn):
        player = Mplayer(board, self.player_name)

        if nb_transfers_this_turn < self.max_transfers:
            # 1) transfer dice close to the border (1st, 3rd and 5th transfer)
            # 2) transfer dice to the border (2, 4, 6)
            transfer_depth = 2 - nb_transfers_this_turn % 2
            transfer = get_transfer_to_borders(player, board, transfer_depth)
            #transfer = self.get_transfer_to_spec_border(player, board, player.border_areas[0], 1)
            if transfer:
                debug_print(f"=> Transfer: {transfer[0], transfer[1]}", flag=DP_FLAG.TRANSFER)
                return TransferCommand(transfer[0], transfer[1])
            else:
                debug_print(f"No transfer (inner -> border) found", flag=DP_FLAG.TRANSFER)
        else:
            debug_print(f"Out of transfers ({nb_transfers_this_turn}/{self.max_transfers})", flag=DP_FLAG.TRANSFER)
        return None

    def part_attack(self, board, time_left):
        debug_print(f"Evaluate board: {evaluate_board(board, self.player_name, self.players_ordered, self.mattack.regr)}")
        # TODO IF evaluation infinite then tranfer die
        # TODO for board with many possibilities is calc time bigger then 10s
        move, evaluation = self.mattack.best_result(board, time_left, self.start_turn_time)

        debug_print(f"Best evaluation {evaluation}")
        if move: # ATTACK
            debug_print(f"Depth search attack {move[0].get_name()}->{move[1].get_name()}")
            return BattleCommand(move[0].get_name(), move[1].get_name())
        else:
            # Try move with best chance of winning and holding arrea
            move = best_possible_attack(board, self.player_name)

            if move is not None:
                debug_print(f"Best value attack {move[0].get_name()}->{move[1].get_name()}")
                return BattleCommand(move[0].get_name(), move[1].get_name())
            else:
                debug_print("No attack")
                return EndTurnCommand()
        return None

    def part_transfer_deep(self, board, nb_transfers_this_turn, nb_moves_this_turn):
        player = Mplayer(board, self.player_name)
        if nb_transfers_this_turn == 0 and nb_moves_this_turn == 0:
            self.transfer_route = get_best_transfer_route(player, board)
        if len(self.transfer_route) != 0:
            transfer = self.transfer_route.pop()
            return TransferCommand(transfer[0], transfer[1])
        return None