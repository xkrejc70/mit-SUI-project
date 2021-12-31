from dicewars.ai.xkuder04.utils.models_util import model_data_dir_filepath

class DP_FLAG:
    UNKNOWN = 0
    START = 1
    TRANSFER = 2
    NEW_TURN = 3
    TRANSFER_VECTOR = 4
    ENDTURN_PART = 5
    STRATEGY = 6
    ATTACK = 7
    TRAIN_DATA = 8

# Show selected default prints
def debug_print(text, flag = DP_FLAG.UNKNOWN):
    allowed_flags = [
        #DP_FLAG.NEW_TURN,
        #DP_FLAG.TRANSFER,
        #DP_FLAG.TRANSFER_VECTOR,
        #DP_FLAG.ENDTURN_PART,
        #DP_FLAG.STRATEGY,
        #DP_FLAG.ATTACK, 
        #DP_FLAG.TRAIN_DATA
    ]
    allow_logs = True
    allow_logs = not allow_logs
    if allow_logs and flag in allowed_flags:
        if flag == DP_FLAG.TRAIN_DATA:
            with open(model_data_dir_filepath("eval_state_4.raw"), "a") as f:
                f.write(f"{text}\n")
        else:
            print(text)