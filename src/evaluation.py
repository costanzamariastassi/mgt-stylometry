import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from sklearn.metrics import (
    ConfusionMatrixDisplay,
    accuracy_score,
    confusion_matrix,
    precision_recall_fscore_support,
    roc_auc_score,
)


def valuta(y_vero, y_pred, y_prob=None, nome: str = "modello") -> dict:
    prec, rec, f1, _ = precision_recall_fscore_support(
        y_vero, y_pred, average="binary", zero_division=0
    )
    tn, fp, fn, tp = confusion_matrix(y_vero, y_pred).ravel()
    risultato = {
        "modello": nome,
        "accuracy": accuracy_score(y_vero, y_pred),
        "precision": prec,
        "recall": rec,
        "f1": f1,
        "fpr": fp / (fp + tn) if (fp + tn) else np.nan,
        "n_falsi_positivi": int(fp),
        "n_falsi_negativi": int(fn),
    }
    if y_prob is not None:
        risultato["auroc"] = roc_auc_score(y_vero, y_prob)
    return risultato


def salva_matrice_confusione(y_vero, y_pred, percorso: str, titolo: str):
    fig, ax = plt.subplots(figsize=(4.5, 4))
    ConfusionMatrixDisplay.from_predictions(
        y_vero, y_pred,
        display_labels=["umano", "macchina"],
        cmap="Blues", colorbar=False, ax=ax,
    )
    ax.set_title(titolo)
    fig.savefig(percorso, dpi=150, bbox_inches="tight")
    plt.close(fig)