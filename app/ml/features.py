import pandas as pd
import numpy as np


def add_basic_features(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df["ret1"] = df["close"].pct_change(1)
    df["ret5"] = df["close"].pct_change(5)
    df["ret10"] = df["close"].pct_change(10)
    df["sma5"] = df["close"].rolling(5).mean()
    df["sma10"] = df["close"].rolling(10).mean()
    df["sma20"] = df["close"].rolling(20).mean()
    df["dist_sma5"] = df["close"] / df["sma5"] - 1.0
    df["dist_sma10"] = df["close"] / df["sma10"] - 1.0
    df["dist_sma20"] = df["close"] / df["sma20"] - 1.0
    df["vol10"] = df["close"].pct_change().rolling(10).std()
    df = df.dropna()
    return df


def make_label(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df["close_t1"] = df["close"].shift(-1)
    df["label"] = (df["close_t1"] > df["close"]).astype(int)
    df = df.dropna()
    return df
