

# %%
import json
import pandas as pd
import numpy as np

from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report,confusion_matrix
from sklearn.preprocessing import StandardScaler
from sklearn.neural_network import MLPClassifier
from sklearn.base import BaseEstimator, TransformerMixin


from pfo_passage_monitor import util
from pfo_passage_monitor.models import Passage
from pfo_passage_monitor.passage import Pattern

# from sklearn.externals import joblib
from sklearn.pipeline import make_pipeline

# from . import utils as utl

from datetime import datetime, time
# import time
import pickle as pkl
import os
# import codecs

# %%

class MlpDirectionStrategy():

    def __init__(self, model_path):

        self.mdl = load_model(os.path.join(model_path,"nnet.pkl"))

    def get_direction(self, passage: Passage):

        pred = score(self.mdl, passage)[0]
        direction = {
          "direction": pred["pred"],
          "strategy": "nnet",
          "proba": pred["proba"]
        } 
        return direction





def update(config):

    data = load_data(config)

    df = create_df(data)

    result = build_model(df[0], df[1])

    store_model(result[0], os.path.join(util.config["direction"]["nnet"]["model_path"],"nnet.pkl"))

    store_report(result[1], os.path.join(util.config["direction"]["nnet"]["report_path"],"nnet.json"))

    return True


# %%

def load_data(config):

    # with open(src, 'r') as data:
    #   passages = json.load(data)
    #   return passages
    with util.get_sa_session(util.config) as session:
        return session.query(Passage).all()

# %%
def create_df(passages):

    y = [
        p.doc["direction"]["manual"] if "manual" in p.doc["direction"] else p.doc["direction"]["direction"]
    for p in passages]
    
    X = passages
    # pd.DataFrame([ utl.densify_pattern(p["pattern"], 600) +
    # [p["duration"]] + utl.feat_daily(p["start"])
    #  for p in passages])

    return (X, y)

# %%
def build_model(X, y):

    X_train, X_test, y_train, y_test = train_test_split(X, y)
    
    pipln = make_pipeline(
                      PassagePreprocessor(600),
                      StandardScaler(),
                      MLPClassifier(hidden_layer_sizes=(10,10,10),max_iter=500)
                      )
    
    pipln.fit(X_train, y_train)
    
    # pipln.predict(X_test)

    predictions = pipln.predict(X_test)

    report = classification_report(y_test, predictions, output_dict=True)
    report["timestamp"] = int(round(datetime.timestamp(datetime.now())))

    # Fit model on whole data
    pipln.fit(X, y)
    
    return (pipln, report)

# %%
def store_model(mdl, target):
    os.makedirs(os.path.dirname(target), exist_ok=True)
    with open(target, "wb") as f:
        pkl.dump(mdl, f)
  
# %%
def store_report(report, target):
    os.makedirs(os.path.dirname(target), exist_ok=True)
    with open(target, "w") as f:
        json.dump(report, f)

def load_model(src):

    with open(src, "rb") as f:
        mdl = pkl.load(f)
    return mdl

def parse_data(data):

    decoded = base64.b64decode(data)  

    return json.loads(decoded)

def score(model, passage: Passage):
  
    if type(passage) != list:
        X = [passage]
    else:
        X = passage

    pred = model.predict(X)
    proba = model.predict_proba(X)
    
    return [{"id": X[i].id, "pred": pred[i], "proba": max(proba[i]) } for i in range(len(X))]

def feat_daily(ts):
    """
    Returns a a pair of of features that in combintation describe the time of day
    """
    if ts > 999999999:
        ts = int(ts / 1000)
    # dt_obj = datetime.fromtimestamp(ts)

    seconds_per_day = 24*60*60

    seconds_into_day = ts % seconds_per_day

    # utcnow = datetime.utcnow()
    # midnight = datetime.combine(dt_obj.date(), time(0))
    # delta = dt_obj - midnight
    # print(delta.seconds)  # <-- careful
    feat = cyclical_feat(seconds_into_day, seconds_per_day)
    return feat

def cyclical_feat(x, max_x):
    return [np.sin(2 * np.pi * x / max_x),
        np.cos(2 * np.pi * x / max_x)]

def feat_yearly(ts):
    if ts > 999999999:
        ts = int(ts / 1000)
    dt_obj = datetime.fromtimestamp(ts)

    days_per_year = 365 # it's ok to do this since we are after the rought time in the year an can thus ignore leap years
    day_of_year = dt_obj.timetuple().tm_yday

    feat = cyclical_feat(day_of_year, days_per_year)
    return feat


class PassagePreprocessor(BaseEstimator, TransformerMixin):

  def __init__(self, dense_pat_len):
    self._dense_pat_len = dense_pat_len

  def fit(self, X: pd.DataFrame, y=None):
    return self

  def transform(self, X, y=None):
    return pd.DataFrame([ Pattern.decompress(Pattern.scale(p.pattern, self._dense_pat_len)) +
      [p.duration] + feat_daily(p.start) + feat_yearly(p.start)
      for p in X])