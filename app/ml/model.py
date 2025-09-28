import pandas as pd
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, f1_score
import joblib

FEATURES = ["ret1", "ret5", "ret10", "dist_sma5", "dist_sma10", "dist_sma20", "vol10"]


def train_classifier(df: pd.DataFrame):
    X = df[FEATURES]
    y = df["label"]
    clf = LogisticRegression(max_iter=200)
    clf.fit(X, y)
    return clf


def evaluate(clf, df: pd.DataFrame):
    X = df[FEATURES]
    y = df["label"]
    p = clf.predict(X)
    return {
        "accuracy": float(accuracy_score(y, p)),
        "f1": float(f1_score(y, p)),
    }


def save_model(clf, path: str):
    joblib.dump(clf, path)


def load_model(path: str):
    return joblib.load(path)
