import numpy as np
import pandas as pd
from sklearn.dummy import DummyClassifier
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import GroupShuffleSplit
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler

SEED = 42

COLONNE_META = {"question_id", "question", "text", "label", "domain", "n_parole"}


def colonne_feature(df: pd.DataFrame) -> list:
    return [c for c in df.columns if c not in COLONNE_META and df[c].dtype != object]


def split_per_domanda(df: pd.DataFrame, test_size: float = 0.25):
    gss = GroupShuffleSplit(n_splits=1, test_size=test_size, random_state=SEED)
    idx_tr, idx_te = next(gss.split(df, groups=df["question_id"]))
    return df.iloc[idx_tr].copy(), df.iloc[idx_te].copy()


def modello_stilometrico():
    return make_pipeline(
        StandardScaler(),
        LogisticRegression(max_iter=2000, random_state=SEED),
    )


def modello_tfidf():
    return make_pipeline(
        TfidfVectorizer(max_features=5000, ngram_range=(1, 2), sublinear_tf=True),
        LogisticRegression(max_iter=2000, random_state=SEED),
    )


def modello_baseline():
    return DummyClassifier(strategy="most_frequent")