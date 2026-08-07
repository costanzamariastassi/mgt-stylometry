"""Caricamento e appiattimento del dataset HC3 (senza loading script)."""

import json
from pathlib import Path

import pandas as pd
from huggingface_hub import hf_hub_download, list_repo_files

REPO = "Hello-SimpleAI/HC3"
DOMINI = ["reddit_eli5", "open_qa", "wiki_csai", "medicine", "finance"]

# Radice del progetto, calcolata a partire dalla posizione di questo file.
# src/loading.py -> src -> mgt-stylometry
# Cosi' i percorsi funzionano da qualunque directory si lanci lo script.
RADICE = Path(__file__).resolve().parent.parent


def trova_file_dominio(dominio: str) -> str:
    """Individua il file jsonl corrispondente a un dominio."""
    file_disponibili = list_repo_files(REPO, repo_type="dataset")
    candidati = [
        f for f in file_disponibili
        if dominio in f and f.endswith((".jsonl", ".json"))
    ]
    if not candidati:
        raise FileNotFoundError(
            f"Nessun file trovato per '{dominio}'. Disponibili: {file_disponibili}"
        )
    return candidati[0]


def carica_hc3(dominio: str) -> pd.DataFrame:
    percorso_remoto = trova_file_dominio(dominio)
    percorso_locale = hf_hub_download(
        repo_id=REPO,
        filename=percorso_remoto,
        repo_type="dataset",
    )
    righe = []
    with open(percorso_locale, encoding="utf-8") as fh:
        for linea in fh:
            linea = linea.strip()
            if linea:
                righe.append(json.loads(linea))
    return pd.DataFrame(righe)


def appiattisci(df: pd.DataFrame, dominio: str) -> pd.DataFrame:
    """Trasforma le liste di risposte in righe singole, una per testo."""
    righe = []
    for i, r in df.iterrows():
        umane = r.get("human_answers") or []
        macchina = r.get("chatgpt_answers") or []
        if len(umane) == 0 or len(macchina) == 0:
            continue
        if not umane[0].strip() or not macchina[0].strip():
            continue
        qid = r.get("id", f"{dominio}_{i}")
        righe.append({
            "question_id": qid,
            "question": r.get("question", ""),
            "text": umane[0],
            "label": 0,
            "domain": dominio,
        })
        righe.append({
            "question_id": qid,
            "question": r.get("question", ""),
            "text": macchina[0],
            "label": 1,
            "domain": dominio,
        })
    return pd.DataFrame(righe)


def costruisci_dataset(destinazione=None) -> pd.DataFrame:
    if destinazione is None:
        destinazione = RADICE / "data" / "raw" / "hc3_flat.parquet"
    destinazione = Path(destinazione)

    pezzi = []
    for d in DOMINI:
        print(f"Carico {d}...")
        try:
            grezzo = carica_hc3(d)
            pezzi.append(appiattisci(grezzo, d))
        except FileNotFoundError as e:
            print(f"  saltato: {e}")

    completo = pd.concat(pezzi, ignore_index=True)
    destinazione.parent.mkdir(parents=True, exist_ok=True)
    completo.to_parquet(destinazione, index=False)
    print(f"Salvate {len(completo)} righe in {destinazione}")
    return completo


if __name__ == "__main__":
    costruisci_dataset()