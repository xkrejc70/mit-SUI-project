import pickle
from os.path import join, dirname, realpath
from sklearn.ensemble import RandomForestRegressor, RandomForestClassifier
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

def filter_score_decrease(lines, score_index = -1):
    good_lines = []
    for i in range(len(lines)-1):
        line = lines[i]
        next_line = lines[i+1]
        if line is None or next_line is None:
            continue
        if line[score_index] > next_line[score_index]:
            line[-1] = next_line[-1]
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

def create_cf_rf_regr(features, classes):
    cf = RandomForestClassifier(max_depth=10)
    cf.fit(features, classes)
    return cf

def normalize_values(values):
    max_val = max(values)
    return [round(val/max_val,3)for val in values]

def create_model(name):
    eval_state_raw = model_data_dir_filepath(f"{name}.raw")
    lines = file2lines(eval_state_raw)
    lines = filter_score_increase(lines)
    lines += filter_score_decrease(lines)

    features = [line[:-1] for line in lines]
    #features = lines
    values = normalize_values([line[-1] for line in lines])
    regr = create_rf_regr(features, values)

    model_path = models_dir_filepath(f"{name}_rf.model")
    save_model(regr, model_path)

def cf_lines(lines):
    features = []
    classes = []
    groups = [(0, -1, 60), (1, 90, 110)]
    #groups = [(0, -1, 60), (1, 80, 110)]
    #groups = [(0, -1, 70), (1, 95, 110)]
    for line in lines:
        for group in groups:
            if line[-1] > group[1] and line[-1] < group[2]:
                features += [ line[:-1] ]
                classes += [ group[0] ]
    return features, classes


def create_cf_model(name):
    eval_state_raw = model_data_dir_filepath(f"{name}.raw")
    lines = file2lines(eval_state_raw)
    features, classes = cf_lines(lines)

    cf = create_cf_rf_regr(features, classes)

    model_path = models_dir_filepath(f"{name}_cf_rf.model")
    save_model(cf, model_path)


#l_regr = load_model(model_path)
#print(l_regr.predict([[20, 96, 19, 15, 34, 175, 3]]))
