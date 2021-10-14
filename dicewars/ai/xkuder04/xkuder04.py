import logging
import random
import copy
import numpy as np

from .Mplayer import Mplayer
from .utils.utils import resonable_attacks_for_player, simulate_lossing_move, simulate_succesfull_move, evaluate_board
from .utils.transfer_utils import get_transfer_to_borders, get_transfer_to_spec_border, get_transfer_near_the_border, get_best_transfer, from_largest_region

from numpy import inf
from numpy.lib.function_base import append
from dicewars.client.game import player

from dicewars.client.game.board import Board
from dicewars.client.game.area import Area
from typing import Iterator, List, Tuple

from dicewars.ai.utils import possible_attacks, save_state, probability_of_successful_attack, attack_succcess_probability
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
        
        max_transfers = self.max_transfers
        player = Mplayer(board, self.player_name)

        if nb_transfers_this_turn < max_transfers:
            #print(f"[{len(player.all_areas)}] all_areas: {[(a.get_name(), a.get_dice()) for a in player.all_areas]}")
            #print(f"[{len(player.border_areas)}] border_areas: {[(a.get_name(), a.get_dice()) for a in player.border_areas]}")
            #print(f"[{len(player.inner_areas)}] inner_areas: {[(a.get_name(), a.get_dice()) for a in player.inner_areas]}")

            # 1) transfer dice close to the border (1st, 3rd and 5th transfer)
            # 2) transfer dice to the border (2, 4, 6)
            transfer = get_transfer_to_borders(player, board, 2 - nb_transfers_this_turn % 2)
            #transfer = self.get_transfer_to_spec_border(player, board, player.border_areas[0], 1)
            if transfer:
                print(f"=> Transfer: {transfer[0], transfer[1]}")
                return TransferCommand(transfer[0], transfer[1])
            else:
                print(f"No transfer (inner -> border) found")
        else:
            print(f"Out of transfers ({nb_transfers_this_turn}/{self.max_transfers})")

        # For testing purpuses can be switched between testing AI and AI in construction
        # Testing of Expectiminimax
       
        print(f"Evaluate board: {evaluate_board(board, self.player_name, self.players_ordered)}")

        """
        # Try posible atack and evaluate score
        for atk in list(resonable_attacks_for_player(self.player_name, board)):
            print(f"Atack {atk[0].get_name()}->{atk[1].get_name()}, chance {probability_of_successful_attack(board, atk[0].get_name(), atk[1].get_name())}")
            new_board = simulate_succesfull_move(self.player_name, board, atk[0], atk[1])
            print(f"New board: {evaluate_board(new_board, self.player_name, self.players_ordered)}")
        """


        print(f"Player name = {self.player_name}")
        print(f"Player order = {self.players_order}")

       
        production_strategy = True
        if production_strategy:
            # TODO IF evaluation infinite then do do move
            # TODO for board with many possibilities is calc time bigger then 10s
            move, evaluation = self.best_result_for_given_depth(board, self.players_order.index(self.player_name), 4)

            print(f"Best evaluation {evaluation}")
            if move:
                print(f"Move {move[0].get_name()}->{move[1].get_name()}")
                return BattleCommand(move[0].get_name(), move[1].get_name())

            return EndTurnCommand()

        else:
            # AI for testing 
            if nb_turns_this_game < 3:
                self.logger.debug("Doing a random move")
                attack_filter = lambda x: x
                attack_selector = random.choice
                attack_acceptor = lambda x: True

                with open('debug.save', 'wb') as f:
                    save_state(f, board, self.player_name, self.players_order)

            else:
                self.logger.debug("Doing a serious move")
                attack_filter = lambda x: from_largest_region(self.logger, board, x, self.player_name)
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

    # Generation of given depth of state space
    # Uses Expectimax-n
    # TODO try alfa/beta
    def best_result_for_given_depth(self, board, player_index ,depth):
        # Next player is calculated from equatin: (player_order + 1) mod len(self.player_prder())

        # Maximal depth of searching
        if ((not list(possible_attacks(board, self.players_order[player_index]))) or (depth == 0)):
            # Evaluation for each player
            evaluation_list = []
            for i in range(len(self.players_order)):
                evaluation_list.append(evaluate_board(board, self.players_order[i], self.players_ordered))

            return None, evaluation_list

        # Get best move from all moves of player i 
        # Each move consist of success and loss with respective probabilities
        max_evaluation = [-inf for i in range(len(self.players_order))]
        move = None
        for atack in resonable_attacks_for_player(self.players_order[player_index], board):
            # Get porobabilities
            probability_of_win= probability_of_successful_attack(board, atack[0].get_name(), atack[1].get_name())
            probability_of_loss = 1 - probability_of_win

            # Generate board for each scenario
            board_win = simulate_succesfull_move(self.players_order[player_index], board, atack[0].get_name(), atack[1].get_name())
            board_loss = simulate_lossing_move(board, atack[0].get_name(), atack[1].get_name())

            # Calculate joined evaluation
            alfa = [0 for i in range(len(self.players_order))]
            _, result_win = self.best_result_for_given_depth(board_win, (player_index + 1) % len(self.players_order), depth - 1)
            for i in range(len(alfa)):
                alfa[i] = alfa[i] + (result_win[i] * probability_of_win)

            _, result_loss = self.best_result_for_given_depth(board_loss, (player_index + 1) % len(self.players_order), depth - 1)
            for i in range(len(alfa)):
                alfa[i] = alfa[i] + (result_loss[i] * probability_of_loss)

            # Store better value for current maximazer 
            if alfa[player_index] > max_evaluation[player_index]:
                max_evaluation = alfa
                move = atack

        return move, max_evaluation