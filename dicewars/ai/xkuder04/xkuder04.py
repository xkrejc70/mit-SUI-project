import logging
import random
import copy
import numpy as np

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
        
        if nb_moves_this_turn == 0:
            self.evaluation_func(board)
            
        max_transfers = self.max_transfers
        player = Mplayer(board, self.player_name)

        if nb_transfers_this_turn < max_transfers:
            print(f"[{len(player.all_areas)}] all_areas: {[(a.get_name(), a.get_dice()) for a in player.all_areas]}")
            print(f"[{len(player.border_areas)}] border_areas: {[(a.get_name(), a.get_dice()) for a in player.border_areas]}")
            print(f"[{len(player.inner_areas)}] inner_areas: {[(a.get_name(), a.get_dice()) for a in player.inner_areas]}")

            #transfer = self.get_transfer_to_borders(player, board, 1)
            transfer = self.get_transfer_to_spec_border(player, board, player.border_areas[0], 1)
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

    # Generation of given depth of state space
    # Uses Expectimax-n
    # TODO try alfa/beta
    def best_result_for_given_depth(self, board, player_index ,depth):
        """
        function alphabeta(node, depth, α, β, maximizingPlayer) is
            if depth = 0 or node is a terminal node then
                return the heuristic value of node
            if maximizingPlayer then
                value := −∞
                for each child of node do
                    value := max(value, alphabeta(child, depth − 1, α, β, FALSE))
                    α := max(α, value)
                    if value ≥ β then
                        break (* β cutoff *)
                return value
            else
                value := +∞
                for each child of node do
                    value := min(value, alphabeta(child, depth − 1, α, β, TRUE))
                    β := min(β, value)
                    if value ≤ α then
                        break (* α cutoff *)
                return value

        function expectiminimax(node, depth)
            if node is a terminal node or depth = 0
                return the heuristic value of node
            if the adversary is to play at node
                // Return value of minimum-valued child node
                let α := +∞
                foreach child of node
                    α := min(α, expectiminimax(child, depth-1))
            else if we are to play at node
                // Return value of maximum-valued child node
                let α := -∞
                foreach child of node
                    α := max(α, expectiminimax(child, depth-1))
            else if random event at node
                // Return weighted average of all child nodes' values
                let α := 0
                foreach child of node
                    α := α + (Probability[child] × expectiminimax(child, depth-1))
            return α
        """
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

    # Get transfer from inner_area to border_area
    # TODO generate states, find best based on the number of transfers
    # TODO presouvat na zaklade moznych utokz na borders (n_dice, dulezitost udrzeni hranice), presun kostek mezi borders
    def get_transfer_to_borders(self, player, board: Board, n_transfers : int):
        if n_transfers == 1:
            # 1 transfer: move from the area with the most dice
            best_transfers = []

            for border in player.border_areas:
                if border.get_dice() == 8:
                    continue
                #print(f"*border: {border.get_name()}")
                
                best_transfer = self.get_best_transfer(player, board, border) #self.foo()? funguje ¯\_(ツ)_/¯
                if best_transfer: best_transfers.append(best_transfer)

            #print(f"best transfers: {best_transfers}")
            if best_transfers:
                max_index = np.array(best_transfers).argmax(axis=0)[0]
                return best_transfers[max_index][1], best_transfers[max_index][2]
            else:
                return None

        elif n_transfers == 2:
            pass
        return None

    # Get transfer from inner_area to specific border_area
    def get_transfer_to_spec_border(self, player, board: Board, border : Area, n_transfers : int): # border pripadne jen jmeno (int)
        if border.get_dice() == 8:
            print(f"Border {border.get_name()} already full")
            return None

        if n_transfers == 1:
            # 1 transfer: move from the area with the most dice
            best_transfer = AI.get_best_transfer(player, board, border)
            if best_transfer:
                return best_transfer[1], best_transfer[2]

        elif n_transfers == 2:
            pass
        return None

    # Get transfer from inner_area to border_area, as close as possible
    def get_transfer_near_the_border():
        pass

    # Get best transfer from neighbors
    def get_best_transfer(player, board, dst_area):
        inner_areas_names = [a.name for a in player.inner_areas]
        best_transfer = []
        max_dice = 1

        for neigh in dst_area.get_adjacent_areas_names():
            if neigh in inner_areas_names:
                #print(f"neigh: {neigh}")
                n_neigh_dice = board.get_area(neigh).get_dice()
                if n_neigh_dice > max_dice:
                    max_dice = n_neigh_dice
                    best_transfer = [n_neigh_dice, neigh, dst_area.get_name()] # [n_dice, src_area, dst_area]
                    #print(f"New best transfer: {neigh, n_neigh_dice} => {dst_area.get_name(), dst_area.get_dice()}")
        return best_transfer
    
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
        
# TODO put to new file
# List of resonable attacks for specified player
def resonable_attacks_for_player(player: int, board: Board) -> Iterator[Tuple[Area, Area]]:
    for area in board.get_player_border(player):
        if not area.can_attack():
            continue

        neighbours = area.get_adjacent_areas_names()

        for adj in neighbours:
            adjacent_area = board.get_area(adj)
            if adjacent_area.get_owner_name() != player:
                if probability_of_successful_attack(board, area.get_name(), adjacent_area.get_name()) >= 0.7:
                    yield (area, adjacent_area)

# Evaluate board score for player
# TODO make complexer evaluation
def evaluate_board(board: Board, player_name: int, players_ordered: List[int]) -> float:
    players = [Mplayer(board, player_name) for player_name in players_ordered]
    total_areas = sum(player.n_all_areas for player in players)
    total_dices = sum(player.n_dice for player in players)

    player = players[player_name - 1]

    up = player.n_all_areas + player.n_dice + player.n_border_dice + player.n_biggest_region_size
    down = total_areas + total_dices + player.n_border_areas
    score = player.is_alive*(up/down)
    return score

# Simulate winning move on board
def simulate_succesfull_move(player_name: int, board: Board, atk_from: int, atk_to: int) -> Board:
    edited_board = copy.deepcopy(board)

    area_from = edited_board.get_area(atk_from)
    area_to = edited_board.get_area(atk_to)

    area_to.set_dice(area_from.get_dice() - 1)
    area_to.set_owner(player_name)
    area_from.set_dice(1)

    return edited_board

# Simulate lossing move on board
def simulate_lossing_move(board: Board, atk_from: int, atk_to:int) -> Board:
    edited_board = copy.deepcopy(board)

    area_from = edited_board.get_area(atk_from)
    area_to = edited_board.get_area(atk_to)


    if area_from.get_dice() == 8:
        new_dice_count = area_to.get_dice() - 2
        if new_dice_count < 1:
            area_to.set_dice(1)
        else:
            area_to.set_dice(new_dice_count)

    elif area_from.get_dice() >= 4:
        new_dice_count = area_to.get_dice() - 1
        if new_dice_count < 1:
            area_to.set_dice(1)
        else:
            area_to.set_dice(new_dice_count)

    area_from.set_dice(1)

    return edited_board