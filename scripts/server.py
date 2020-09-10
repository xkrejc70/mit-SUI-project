#!/usr/bin/env python3

from argparse import ArgumentParser
import logging
import random

from itertools import cycle

from dicewars.server.board import Board
from dicewars.server.generator import BoardGenerator
from dicewars.server.game import Game


from utils import get_logging_level


def area_player_mapping(nb_players, nb_areas):
    assignment = {}
    unassigned_areas = list(range(1, nb_areas+1))
    player_cycle = cycle(range(1, nb_players+1))

    while unassigned_areas:
        player_no = next(player_cycle)
        area_no = random.choice(unassigned_areas)
        assignment[area_no] = player_no
        unassigned_areas.remove(area_no)

    return assignment


def players_areas(ownership, the_player):
    return [area for area, player in ownership.items() if player == the_player]


def assign_dice(board, nb_players, ownership):
    dice_total = 3 * board.get_number_of_areas() - random.randint(0, 5)
    players_processed = 0

    for player in range(1, nb_players+1):
        player_dice = int(round(dice_total / (nb_players - players_processed)))
        dice_total -= player_dice

        available_areas = [board.get_area_by_name(area_name) for area_name in players_areas(ownership, player)]

        # each area has to have at least one die
        for area in available_areas:
            area.set_dice(1)
            player_dice -= 1

        while player_dice and available_areas:
            area = random.choice(available_areas)
            if not area.add_die():  # adding a die to area failed means that area is full
                available_areas.remove(area)
            else:
                player_dice -= 1

        players_processed += 1


def main():
    """
    Server for Dice Wars
    """

    parser = ArgumentParser(prog='Dice_Wars-server')
    parser.add_argument('-n', '--number-of-players', help="Number of players", type=int, default=2)
    parser.add_argument('-p', '--port', help="Server port", type=int, default=5005)
    parser.add_argument('-a', '--address', help="Server address", default='127.0.0.1')
    parser.add_argument('-d', '--debug', help="Enable debug output", default='WARN')
    parser.add_argument('-b', '--board', help="Random seed to be used for board creating", type=int)
    parser.add_argument('-o', '--ownership', help="Random seed to be used for province assignment", type=int)
    parser.add_argument('-s', '--strength', help="Random seed to be used for dice assignment", type=int)
    parser.add_argument('-f', '--fixed', help="Random seed to be used for player order and dice rolls", type=int)
    parser.add_argument('-r', '--order', nargs='+',
                        help="Random seed to be used for dice assignment")
    args = parser.parse_args()
    log_level = get_logging_level(args)

    logging.basicConfig(level=log_level)
    logger = logging.getLogger('SERVER')
    logger.debug("Command line arguments: {0}".format(args))

    random.seed(args.board)
    generator = BoardGenerator()
    board = Board(generator.generate_board())

    random.seed(args.ownership)
    area_ownership = area_player_mapping(args.number_of_players, board.get_number_of_areas())

    random.seed(args.strength)
    assign_dice(board, args.number_of_players, area_ownership)

    random.seed(args.fixed)
    game = Game(board, area_ownership, args.number_of_players, args.address, args.port, args.order)
    game.run()


if __name__ == '__main__':
    main()
