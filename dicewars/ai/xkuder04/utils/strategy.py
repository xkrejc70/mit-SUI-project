from pickle import DEFAULT_PROTOCOL
from dicewars.ai.xkuder04.Mplayer import Mplayer

class STRATEGY:
    DEFAULT =       0
    FIRST_ATTACK =  1
    ATTACK =        2
    SUPPORT =       3
    FINAL_SUPPORT = 4

def select_strategy(self, board):
    return STRATEGY.DEFAULT # Remove after all TODOs done
    player = Mplayer(board, self.player_name)

    # Borders full -> attack
    if (player.n_border_dice == player.n_border_areas * 8) or (player.n_inner_areas == 0):
        return STRATEGY.FIRST_ATTACK

    return STRATEGY.SUPPORT