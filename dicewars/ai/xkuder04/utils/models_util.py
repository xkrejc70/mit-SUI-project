import pickle
from os.path import join, dirname, realpath
from sklearn.ensemble import RandomForestRegressor, RandomForestClassifier
from sklearn.svm import SVC
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler
from ast import literal_eval
import numpy as np
import torch
import torch.nn as nn
import torch.nn.functional as F

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

def create_cf_prep_svm(features, classes):
    cf = make_pipeline(StandardScaler(), SVC())
    cf.fit(features, classes)
    return cf

def create_cf_prep_rf(features, classes):
    cf = make_pipeline(StandardScaler(), RandomForestClassifier(max_depth=10))
    cf.fit(features, classes)
    return cf

def create_cf_svm(features, classes):
    cf = SVC()
    cf.fit(features, classes)
    return cf

def create_cf_rf(features, classes):
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
    values = normalize_values([line[-1] for line in lines])
    regr = create_rf_regr(features, values)

    model_path = models_dir_filepath(f"{name}_rf.model")
    save_model(regr, model_path)

def cf_lines(lines):
    features = []
    classes = []
    groups = [(0, -1, 60), (1, 90, 110)]
    for line in lines:
        for group in groups:
            if line[-1] > group[1] and line[-1] < group[2]:
                features += [ line[:-1] ]
                classes += [ group[0] ]
    return features, classes

def create_cf_rf_model(name):
    eval_state_raw = model_data_dir_filepath(f"{name}.raw")
    lines = file2lines(eval_state_raw)
    features, classes = cf_lines(lines)

    cf = create_cf_rf(features, classes)

    model_path = models_dir_filepath(f"{name}_cf_rf.model")
    save_model(cf, model_path)

def create_cf_svm_model(name):
    eval_state_raw = model_data_dir_filepath(f"{name}.raw")
    lines = file2lines(eval_state_raw)
    features, classes = cf_lines(lines)

    cf = create_cf_svm(features, classes)

    model_path = models_dir_filepath(f"{name}_cf_svm.model")
    save_model(cf, model_path)

def create_cf_prep_rf_model(name):
    eval_state_raw = model_data_dir_filepath(f"{name}.raw")
    lines = file2lines(eval_state_raw)
    features, classes = cf_lines(lines)

    cf = create_cf_prep_rf(features, classes)

    model_path = models_dir_filepath(f"{name}_cf_prep_rf.model")
    save_model(cf, model_path)

def create_cf_prep_svm_model(name):
    eval_state_raw = model_data_dir_filepath(f"{name}.raw")
    lines = file2lines(eval_state_raw)
    features, classes = cf_lines(lines)

    cf = create_cf_prep_svm(features, classes)

    model_path = models_dir_filepath(f"{name}_cf_prep_svm.model")
    save_model(cf, model_path)

class NN_model(nn.Module):
    def __init__(self):
        super(NN_model,self).__init__()
        self.transformation1 = nn.Linear(11,20) #layer 1->2
        self.transformation2 = nn.Linear(20,2) #layer 2->3
        
    def forward(self,x):
        x = self.transformation1(x)
        x = torch.tanh(x)
        x = self.transformation2(x)
        return x
        
    def predict(self,x):
        pred = F.softmax(self.forward(x), dim=1)
        result = []
        for t in pred:
            if t[0]>t[1]:
                result.append(0)
            else:
                result.append(1)
        return torch.tensor(result)

def create_cf_nn(X, y, epochs = 1000):
    model = NN_model()
    criterion = nn.CrossEntropyLoss()
    optim = torch.optim.Adam(model.parameters(), lr=0.01)

    losses = []
    for i in range(epochs):
        print(f"It {i}")
        y_pred = model.forward(X)
        loss = criterion(y_pred,y)
        losses.append(loss.item())
        optim.zero_grad()
        loss.backward()
        optim.step()
    return model

def create_cf_nn_model(name):
    eval_state_raw = model_data_dir_filepath(f"{name}.raw")
    lines = file2lines(eval_state_raw)
    features, classes = cf_lines(lines)
    X = torch.from_numpy(np.array(features)).type(torch.FloatTensor)
    y = torch.from_numpy(np.array(classes)).type(torch.LongTensor)
    
    model = create_cf_nn(X, y)
    model_path = models_dir_filepath(f"{name}_cf_nn.model")
    save_model(model, model_path)