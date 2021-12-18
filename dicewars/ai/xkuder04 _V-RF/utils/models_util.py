import pickle
from os.path import join, dirname, realpath
from sklearn.ensemble import RandomForestRegressor
from ast import literal_eval

def model_data_dir_filepath(filename):
    return join(dirname(realpath(__file__)), "model_data", filename)

def models_dir_filepath(filename):
    return join(dirname(dirname(realpath(__file__))), "models", filename)

def file2lines(filepath):
    edited_lines = []
    with open(filepath, 'r') as file1:
        lines = file1.readlines()
        for line in lines:
            line = line.strip()
            if line == "":
                edited_lines.append(None)
            else:
                edited_lines.append(literal_eval(line.strip()))
    return edited_lines

def filter_score_increase(lines, score_index = -1):
    good_lines = []
    for i in range(len(lines)-1):
        line = lines[i]
        next_line = lines[i+1]
        if line is None or next_line is None:
            continue
        if line[score_index] < next_line[score_index]:
            good_lines.append(line)
    return good_lines

def save_model(model, filepath):
    with open(filepath, 'wb') as f:
        pickle.dump(model, f)

def load_model(filepath):
    with open(filepath, 'rb') as f:
        return pickle.load(f)

def create_rf_regr(features, values):
    regr = RandomForestRegressor(max_depth=3)
    regr.fit(features, values)
    return regr

def normalize_values(values):
    max_val = max(values)
    return [round(val/max_val,3)for val in values]

def create_eval_state():
    eval_state = "eval_state"
    eval_state_raw = model_data_dir_filepath(f"{eval_state}.raw")
    lines = file2lines(eval_state_raw)
    lines = filter_score_increase(lines)

    features = [line[:-1] for line in lines]
    values = normalize_values([line[-1] for line in lines])
    regr = create_rf_regr(features, values)

    #print(regr.predict([[20, 96, 19, 19, 34, 175, 3]]))

    model_path = models_dir_filepath("eval_state_rf.model")
    save_model(regr, model_path)

#l_regr = load_model(model_path)
#print(l_regr.predict([[20, 96, 19, 15, 34, 175, 3]]))

create_eval_state()