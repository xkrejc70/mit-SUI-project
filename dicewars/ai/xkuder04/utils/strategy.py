from pickle import DEFAULT_PROTOCOL
from dicewars.ai.xkuder04.Mplayer import Mplayer

# Strategy selector
class STRATEGY:
    SUPPORT =       0
    FIRST_ATTACK =  1
    RETREAT =       2

def select_strategy(self, board):
    player = Mplayer(board, self.player_name)

    # Borders full -> attack
    if (player.n_border_dice == player.n_border_areas * 8) or (player.n_inner_areas == 0):
        return STRATEGY.FIRST_ATTACK

    return STRATEGY.SUPPORT