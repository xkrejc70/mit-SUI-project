import logging
import random
import copy
import numpy as np
import time

from .Mplayer import Mplayer
from .Mattack import Mattack
from .utils.utils import best_winning_attack, evaluate_board, print_start
from .utils.debug import DP_FLAG, debug_print
from .utils.transfer_utils import get_best_transfer_route, final_support, retreat_transfers

from numpy.lib.function_base import append
from dicewars.client.game import player

from dicewars.client.game.board import Board
from dicewars.client.game.area import Area
from typing import Iterator, List, Text, Tuple

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
        self.max_attacks_per_round = 10
        self.depth = 6
        self.mattack = Mattack(self.depth, self.players_order, self.players_ordered, self.player_index, self.min_time_left)
        self.transfer_route = []
        self.num_players = len(players_order)
        self.max_attacks = 15
        self.made_attack = 0
        
    def ai_turn(self, board, nb_moves_this_turn, nb_transfers_this_turn, nb_turns_this_game, time_left):
        self.start_turn_time = time.time()
        print_start(self, board, nb_moves_this_turn, nb_transfers_this_turn, time_left)

        if nb_transfers_this_turn == 0 and nb_moves_this_turn == 0:
            self.transfer_route = []
            self.made_attack = 0

        if x:= self.part_transfer_deep(board, nb_transfers_this_turn, nb_moves_this_turn): return x
        if x:= self.attack_n_times(board, time_left): return x
        if x:= self.retreat_forces(board, nb_transfers_this_turn): return x
        
        return EndTurnCommand()

    def retreat_forces(self, board, nb_transfers_this_turn):
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
                # Tree returned no attack
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

    # Final support, transfer dice close to borders Todelete
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
            # Tree returned no attack
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

    # First support Todelete
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

    # Final support Todelete
    def part_final_transfer_deep(self, board, start_depth, available_steps):
        player = Mplayer(board, self.player_name)
        if not self.transfer_route:
            self.transfer_route = get_best_transfer_route(player, board, start_depth, available_steps)
        if len(self.transfer_route) != 0:
            transfer = self.transfer_route.pop()
            debug_print(f"=> Transfer: {transfer[0], transfer[1]}", flag=DP_FLAG.TRANSFER)
            return TransferCommand(transfer[0], transfer[1])
        return None