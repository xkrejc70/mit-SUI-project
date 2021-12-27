import logging
import random
import copy
import numpy as np
import time

from .Mplayer import Mplayer
from .Mattack import Mattack
from .utils.utils import best_winning_attack, evaluate_board, is_endturn, print_start, best_possible_attack, retreat_transfers
from .utils.debug import DP_FLAG, debug_print
from .utils.transfer_utils import get_best_transfer_route, final_support
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
        #debug_print("", DP_FLAG.TRAIN_DATA)
        self.player_name = player_name
        self.players_order = players_order
        self.player_index = self.players_order.index(self.player_name)
        self.max_transfers = max_transfers
        self.players_ordered = sorted(players_order)
        self.logger = logging.getLogger('AI')
        self.min_time_left = 6
        self.max_attacks_per_round = 10
        self.strategy = STRATEGY.MULTI_TESTING
        #self.strategy = STRATEGY.SUPPORT
        self.ongoing_strategy = False
        self.depth = 4
        self.mattack = Mattack(self.depth, self.players_order, self.players_ordered, self.player_index, self.min_time_left)
        self.transfer_route = []
        self.num_players = len(players_order)
        self.max_attacks = 5

        self.made_attack = 0
        #print(f"player_name : {self.player_name}")
        
    def ai_turn(self, board, nb_moves_this_turn, nb_transfers_this_turn, nb_turns_this_game, time_left):
        self.start_turn_time = time.time()
        print_start(self, board, nb_moves_this_turn, nb_transfers_this_turn, time_left)

        if nb_transfers_this_turn == 0 and nb_moves_this_turn == 0:
            self.transfer_route = []
            self.made_attack = 0

        """
        self.unset_strategy(nb_moves_this_turn, nb_transfers_this_turn)

        if self.strategy != STRATEGY.FINAL_SUPPORT:
            if x:= self.part_endturn(nb_moves_this_turn, time_left, board, nb_transfers_this_turn): return x

        if (self.ongoing_strategy == False):
            self.set_ongoing_strategy(select_strategy(self, board))
        """

        debug_print(f"Strategy: {self.strategy}", flag=DP_FLAG.STRATEGY)
        debug_print(f"nb_transfers_this_turn: {nb_transfers_this_turn}", flag=DP_FLAG.TRANSFER)

        ##################### Strategies #####################

        if self.strategy == STRATEGY.DEFAULT: # TODO DELETE
            if x:= self.part_transfer_deep_test(board, nb_transfers_this_turn, nb_moves_this_turn): return x
            if x:= self.part_final_transfer(board, nb_transfers_this_turn): return x
            if x:= self.part_attack(board, time_left): return x

        elif self.strategy == STRATEGY.FIRST_ATTACK:
            if x:= self.part_attack(board, time_left): return x
            if x:= self.part_transfer_deep(board, nb_transfers_this_turn, nb_moves_this_turn): return x
            self.set_ongoing_strategy(STRATEGY.ATTACK)
            if x:= self.part_attack(board, time_left): return x
            self.set_ongoing_strategy(STRATEGY.FINAL_SUPPORT)
            if x:= self.part_final_transfer(board, nb_transfers_this_turn): return x

        elif self.strategy == STRATEGY.ATTACK:
            if x:= self.part_attack(board, time_left): return x
            self.set_ongoing_strategy(STRATEGY.FINAL_SUPPORT)
            if x:= self.part_final_transfer(board, nb_transfers_this_turn): return x

        elif self.strategy == STRATEGY.SUPPORT:
            if x:= self.part_transfer_deep(board, nb_transfers_this_turn, nb_moves_this_turn): return x
            self.set_ongoing_strategy(STRATEGY.ATTACK)
            if x:= self.part_attack(board, time_left): return x
            self.set_ongoing_strategy(STRATEGY.FINAL_SUPPORT)
            if x:= self.part_final_transfer(board, nb_transfers_this_turn): return x

        elif self.strategy == STRATEGY.FINAL_SUPPORT:
            if x:= self.part_final_transfer(board, nb_transfers_this_turn): return x

        elif self.strategy == STRATEGY.ACTUAL_BEST:
            if x:= self.part_transfer_deep(board, nb_transfers_this_turn, nb_moves_this_turn): return x
            if x:= self.attack_n_times(board, time_left): return x
            if x:= self.part_final_transfer(board, nb_transfers_this_turn): return x

        elif self.strategy == STRATEGY.MULTI_TESTING:
            if x:= self.part_transfer_deep(board, nb_transfers_this_turn, nb_moves_this_turn): return x
            if x:= self.attack_n_times(board, time_left): return x
            if x:= self.retreat_forces(board, nb_transfers_this_turn): return x

        return EndTurnCommand()

    # When time is low, end turn with final support
    def part_endturn(self, nb_moves_this_turn, time_left, board, nb_transfers_this_turn):
        if nb_moves_this_turn > 1:
            if is_endturn(time_left, self.min_time_left, nb_moves_this_turn, self.max_attacks_per_round):
                debug_print(f"End turn, time: {time.time() - self.start_turn_time}", DP_FLAG.ENDTURN_PART)
                self.set_ongoing_strategy(STRATEGY.FINAL_SUPPORT)
                if x:= self.part_final_transfer(board, nb_transfers_this_turn): return x
        return None

    def retreat_forces (self, board, nb_transfers_this_turn):
        # Continue with retreats
        list_of_reatreats = retreat_transfers(board, self.player_name)

        if nb_transfers_this_turn < self.max_transfers:
                if list_of_reatreats:
                    source, destination, _ = list_of_reatreats.pop(0)
          
                    debug_print(f"=> Retreat transfer: {source, destination}", flag=DP_FLAG.TRANSFER)
                    return TransferCommand(source, destination)

        return None


    def attack_n_times(self, board, time_left):
        move, evaluation = self.mattack.best_result(board, time_left, self.start_turn_time)
        debug_print(f"Best evaluation {evaluation}", flag=DP_FLAG.ATTACK)

        # Do number of attacks
        if self.made_attack <= self.max_attacks:
            self.made_attack += 1
            # Do provided attack
            if move:
                debug_print(f"Depth search attack {move[0].get_name()}->{move[1].get_name()}", flag=DP_FLAG.ATTACK)
                return BattleCommand(move[0].get_name(), move[1].get_name())
            else:
                ### Tree returned no attack
                # Try move with best chance of winning with probability
                move, win_prob = best_winning_attack(board, self.player_name)
                do_attack = random.random()

                # Do attack with good win probability
                if win_prob >= 0.6:
                    debug_print(f"Best value attack {move[0].get_name()}->{move[1].get_name()}", flag=DP_FLAG.ATTACK)
                    return BattleCommand(move[0].get_name(), move[1].get_name())
                else:
                    # Do worse attack with probability
                    if do_attack < 0.3:
                        # if move exists
                        if move:
                            debug_print(f"Worse attack with probability {move[0].get_name()}->{move[1].get_name()}", flag=DP_FLAG.ATTACK)
                            return BattleCommand(move[0].get_name(), move[1].get_name())  
                        else:
                            debug_print(f"No attack", flag=DP_FLAG.ATTACK)
        return None

    # Final support, transfer dice close to borders
    def part_final_transfer(self, board, nb_transfers_this_turn):
        player = Mplayer(board, self.player_name)
        if nb_transfers_this_turn < self.max_transfers:

            # Support borders
            if nb_transfers_this_turn < 2:
                if x:= self.part_final_transfer_deep(board, 0, 4): return x
            
            if nb_transfers_this_turn < 4:
                if x:= self.part_final_transfer_deep(board, 0, 2): return x

            transfer = final_support(player, board)
            if transfer:
                debug_print(f"=> Transfer: {transfer[0], transfer[1]}", flag=DP_FLAG.TRANSFER)
                return TransferCommand(transfer[0], transfer[1])

            else:
                # Support arrea in 2nd line
                if nb_transfers_this_turn < 2:
                    if x:= self.part_final_transfer_deep(board, 1, 4): return x

                if x:= self.part_final_transfer_deep(board, 1, 2): return x

        else:
            debug_print(f"Out of transfers ({nb_transfers_this_turn}/{self.max_transfers})", flag=DP_FLAG.TRANSFER)
            return EndTurnCommand()
        return None

    # Do attack provided by expectimaxn
    def part_attack(self, board, time_left):
        debug_print(f"Evaluate board: {evaluate_board(board, self.player_name, self.players_ordered, self.mattack.regr)}", flag=DP_FLAG.ATTACK)
        
        # Get result by expectimaxn
        move, evaluation = self.mattack.best_result(board, time_left, self.start_turn_time)
        debug_print(f"Best evaluation {evaluation}", flag=DP_FLAG.ATTACK)
        
        # Do provided attack
        if move:
            debug_print(f"Depth search attack {move[0].get_name()}->{move[1].get_name()}", flag=DP_FLAG.ATTACK)
            return BattleCommand(move[0].get_name(), move[1].get_name())
        else:
            ### Tree returned no attack
            # Try move with best chance of winning with probability
            move, win_prob = best_winning_attack(board, self.player_name)
            do_attack = random.random()

            # Do attack with good win probability
            if win_prob >= 0.6:
                debug_print(f"Best value attack {move[0].get_name()}->{move[1].get_name()}", flag=DP_FLAG.ATTACK)
                return BattleCommand(move[0].get_name(), move[1].get_name())
            else:
                # Do worse attack with probability
                if do_attack < 0.3:
                    # if move exists
                    if move:
                        debug_print(f"Worse attack with probability {move[0].get_name()}->{move[1].get_name()}", flag=DP_FLAG.ATTACK)
                        return BattleCommand(move[0].get_name(), move[1].get_name())  
                    else:
                        debug_print(f"No attack", flag=DP_FLAG.ATTACK)
        return None

    #TODO delete?
    def part_transfer_deep_old(self, board, nb_transfers_this_turn, nb_moves_this_turn):
        player = Mplayer(board, self.player_name)
        if nb_transfers_this_turn == 0 and nb_moves_this_turn == 0:
            self.transfer_route = get_best_transfer_route(player, board, 0, 6)
        if len(self.transfer_route) != 0:
            transfer = self.transfer_route.pop()
            return TransferCommand(transfer[0], transfer[1])
        return None

    # First support
    def part_transfer_deep(self, board, nb_transfers_this_turn, nb_moves_this_turn):
        player = Mplayer(board, self.player_name)
        available_steps = self.max_transfers - nb_transfers_this_turn

        if (nb_transfers_this_turn > 3 and not self.transfer_route) or (nb_transfers_this_turn == self.max_transfers):
            return None

        if not self.transfer_route:
            self.transfer_route = get_best_transfer_route(player, board, 0, available_steps)
        if len(self.transfer_route) != 0:
            transfer = self.transfer_route.pop()
            debug_print(f"=> Transfer: {transfer[0], transfer[1]}", flag=DP_FLAG.TRANSFER)
            return TransferCommand(transfer[0], transfer[1])
        return None

    # Final support
    def part_final_transfer_deep(self, board, start_depth, available_steps):
        player = Mplayer(board, self.player_name)
        if not self.transfer_route:
            self.transfer_route = get_best_transfer_route(player, board, start_depth, available_steps)
        if len(self.transfer_route) != 0:
            transfer = self.transfer_route.pop()
            debug_print(f"=> Transfer: {transfer[0], transfer[1]}", flag=DP_FLAG.TRANSFER)
            return TransferCommand(transfer[0], transfer[1])
        return None

    # Set if turn is strategy continuation
    def set_ongoing_strategy(self, strategy):
        self.ongoing_strategy = True
        self.strategy = strategy

    # Do if first turn
    def unset_strategy(self, nb_moves_this_turn, nb_transfers_this_turn):
        if (nb_moves_this_turn == 0) and (nb_transfers_this_turn == 0):
            self.ongoing_strategy = False