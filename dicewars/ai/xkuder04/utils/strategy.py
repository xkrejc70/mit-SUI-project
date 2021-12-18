from pickle import DEFAULT_PROTOCOL
from dicewars.ai.xkuder04.Mplayer import Mplayer

class STRATEGY:
    DEFAULT =           0
    SUPPORT_BORDERS =   1
    ATTACK =            2
    SUPPORT_2ND_LINE =  3
    SUPPORT_2ND_LINE =  4
    END_TURN =          5

def select_strategy(self, board):
    return STRATEGY.DEFAULT
    player = Mplayer(board, self.player_name)

    # Borders full
    if player.n_border_dice == player.n_border_areas * 8:
        print("full borders")
        return STRATEGY.SUPPORT_2ND_LINE

    print("b_a")
    for b_a in player.border_areas:
        print(b_a.dice)
    

    
    
    #vector = get_own_area_info(player, board)
    #print(vector)

    return STRATEGY.DEFAULT