class DP_FLAG:
    UNKNOWN = 0
    START = 1
    TRANSFER = 2
    NEW_TURN = 3

def debug_print(text, flag = DP_FLAG.UNKNOWN):
    allowed_flags = [DP_FLAG.NEW_TURN, DP_FLAG.TRANSFER]
    allow_logs = True
    #allow_logs = False
    if allow_logs and flag in allowed_flags:
        print(text)