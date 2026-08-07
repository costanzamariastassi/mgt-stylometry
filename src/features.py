from collections import Counter
import re

import numpy as np
import pandas as pd
import spacy
from tqdm import tqdm

NLP = spacy.load("en_core_web_sm", disable=["ner", "lemmatizer"])

PUNTEGGIATURA = [",", ";", ":", "(", "!", "?"]

CONNETTIVI = {
    "however", "moreover", "furthermore", "additionally", "therefore",
    "consequently", "nevertheless", "overall", "importantly", "notably",
}

HEDGING = {
    "may", "might", "could", "generally", "typically", "often", "usually",
    "some", "several", "various", "certain",
}
RE_TRIPLETTA = re.compile(r"\b\w+, \w+,? and \w+\b")

def mattr(tokens, finestra: int = 100) -> float:
    """Type-token ratio a finestra mobile: non dipende dalla lunghezza."""
    if len(tokens) < finestra:
        return len(set(tokens)) / len(tokens) if tokens else 0.0
    valori = [
        len(set(tokens[i:i + finestra])) / finestra
        for i in range(len(tokens) - finestra + 1)
    ]
    return float(np.mean(valori))


def entropia_token(tokens) -> float:
    """Entropia della distribuzione di frequenza dei token (in bit)."""
    if not tokens:
        return 0.0
    conteggi = np.array(list(Counter(tokens).values()), dtype=float)
    p = conteggi / conteggi.sum()
    return float(-(p * np.log2(p)).sum())


def profondita_albero(token) -> int:
    d = 0
    while token.head != token:
        token = token.head
        d += 1
        if d > 100:
            break
    return d


def estrai(testo: str) -> dict:
    doc = NLP(testo)
    parole = [t.text.lower() for t in doc if t.is_alpha]
    frasi = list(doc.sents)

    if not parole or not frasi:
        return {}

    lunghezze_frasi = [len([t for t in s if t.is_alpha]) for s in frasi]
    pos = Counter(t.pos_ for t in doc)
    n_token = len(doc)

    f = {
        # Lunghezza e ritmo
        "lung_frase_media": float(np.mean(lunghezze_frasi)),
        "tripletta_per_100parole": 100 * len(RE_TRIPLETTA.findall(doc.text)) / len(parole),
        "em_dash_per_100parole": 100 * doc.text.count("\u2014") / len(parole),
        "en_dash_per_100parole": 100 * doc.text.count("\u2013") / len(parole),
        "lung_frase_std": float(np.std(lunghezze_frasi)),
        "lung_parola_media": float(np.mean([len(p) for p in parole])),
        "n_frasi": len(frasi),

        # Ricchezza lessicale
        "mattr": mattr(parole),
        "hapax_ratio": sum(1 for c in Counter(parole).values() if c == 1) / len(parole),
        "entropia": entropia_token(parole),

        # Sintassi
        "prof_albero_media": float(np.mean([profondita_albero(t) for t in doc])),
        "subordinate_per_frase": sum(1 for t in doc if t.dep_ in {"advcl", "ccomp", "xcomp", "relcl"}) / len(frasi),
        "coordinate_per_frase": sum(1 for t in doc if t.dep_ == "conj") / len(frasi),

        # Lessico funzionale
        "ratio_connettivi": sum(1 for p in parole if p in CONNETTIVI) / len(parole),
        "ratio_hedging": sum(1 for p in parole if p in HEDGING) / len(parole),
        "ratio_pron_prima_persona": sum(1 for t in doc if t.text.lower() in {"i", "we", "my", "our"}) / len(parole),
    }

    # Distribuzione POS normalizzata
    for tag in ["NOUN", "VERB", "ADJ", "ADV", "PRON", "ADP", "CCONJ", "SCONJ"]:
        f[f"pos_{tag.lower()}"] = pos.get(tag, 0) / n_token

    # Punteggiatura
    for segno in PUNTEGGIATURA:
        nome = {
            ",": "virgola", ";": "puntovirgola", ":": "duepunti",
            "-": "trattino", "(": "parentesi",
            "!": "esclamativo", "?": "interrogativo",
        }[segno]
        f[f"punt_per_100parole_{nome}"] = 100 * doc.text.count(segno) / len(parole)

    return f


def estrai_tutte(df: pd.DataFrame) -> pd.DataFrame:
    righe = []
    for testo in tqdm(df["text"], desc="Estrazione feature"):
        righe.append(estrai(testo))
    feats = pd.DataFrame(righe, index=df.index)
    return pd.concat([df.reset_index(drop=True), feats.reset_index(drop=True)], axis=1)


if __name__ == "__main__":
    df = pd.read_parquet("/Users/costanzastassi/Desktop/mgt-stylometry/data/processed/hc3_clean.parquet")
    out = estrai_tutte(df)
    out = out.dropna(subset=["mattr"])
    out.to_parquet("/Users/costanzastassi/Desktop/mgt-stylometry/data/processed/hc3_features.parquet", index=False)
    print(out.shape)