from .models_util import create_cf_nn_model

#To collect data you need for model training follow these instructions.
#
#   1. Uncomment in xkuder04/utils/debug.py line 23.
#   2. Comment in xkuder04/utils/debug.py line 26.
#       These two steps will allow logs to be saved in the file eval_state_4.raw.
#   3. Uncomment in xkuder04/utils/utils.py line 75.
#   4. Uncomment in xkuder04/utils/utils.py line 76.
#   5. Let the bot play some games. Preferably some with 4 players in each game since those are the main thing for this project.
#   6. Uncomment in xkuder04/utils/debug.py line 26 for disabeling data collection.



#Creates model from training data
create_cf_nn_model("eval_state_4")