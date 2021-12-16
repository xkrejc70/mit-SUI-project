class DP_FLAG:
    UNKNOWN = 0
    START = 1
    TRANSFER = 2
    NEW_TURN = 3
    TRANSFER_VECTOR = 4

def debug_print(text, flag = DP_FLAG.UNKNOWN):
    allowed_flags = [DP_FLAG.NEW_TURN, DP_FLAG.TRANSFER_VECTOR]
    allow_logs = True
    #allow_logs = False
    if allow_logs and flag in allowed_flags:
        print(text)