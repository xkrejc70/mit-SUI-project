from ..utils import possible_attacks, probability_of_holding_area


def get_sdc_attack(board, player_name):
    attacks = []
    for source, target in possible_attacks(board, player_name):
        area_dice = source.get_dice()
        strength_difference = area_dice - target.get_dice()
        attack = [source.get_name(), target.get_name(), strength_difference]
        attacks.append(attack)

    attacks = sorted(attacks, key=lambda attack: attack[2], reverse=True)

    if attacks and attacks[0][2] >= 0:
        return attacks[0]
    else:
        return None


def get_transfer_to_border(board, player_name):
    border_names = [a.name for a in board.get_player_border(player_name)]
    all_areas = board.get_player_areas(player_name)
    inner = [a for a in all_areas if a.name not in border_names]

    for area in inner:
        if area.get_dice() < 2:
            continue

        for neigh in area.get_adjacent_areas_names():
            if neigh in border_names and board.get_area(neigh).get_dice() < 8:
                return area.get_name(), neigh

    return None


def get_transfer_from_endangered(board, player_name):
    border_names = [a.name for a in board.get_player_border(player_name)]
    all_areas = board.get_player_areas(player_name)
    inner = [a.name for a in all_areas if a.name not in border_names]

    retreats = []

    for area in border_names:
        area = board.get_area(area)
        if area.get_dice() < 2:
            continue

        p_loss = probability_of_holding_area(board, area.get_name(), area.get_dice(), player_name)
        retreats.append((area, p_loss * area.get_dice()))

    retreats = sorted(retreats, key=lambda x: x[1], reverse=True)

    for retreating in retreats:
        area = retreating[0]
        for neigh in area.get_adjacent_areas_names():
            if neigh in inner and board.get_area(neigh).get_dice() < 8:
                return area.get_name(), neigh

    return None
