"""Pulizia dei testi e rimozione degli artefatti di formattazione.

HC3 contiene artefatti di preprocessing su entrambe le classi:
- lato umano: testi passati per un tokenizzatore e ricomposti con join
  sugli spazi (spazio prima della punteggiatura, contrazioni spezzate);
- lato macchina: newline ed elenchi puntati rimossi in fase di costruzione
  del dataset, che lasciano punteggiatura attaccata alla parola successiva.

Entrambi sono tracce del preprocessing di HC3, non dei rispettivi autori.
Rimuoverne uno solo significherebbe ripulire una classe e lasciare
all'altra un marcatore quasi perfetto.
"""

import re
from pathlib import Path

import pandas as pd

RADICE = Path(__file__).resolve().parent.parent

RE_SPAZI = re.compile(r"\s+")
RE_SPAZIO_PRIMA_PUNTEGGIATURA = re.compile(r"\s+([,.;:!?)\]])")
RE_SPAZIO_DOPO_APERTURA = re.compile(r"([(\[])\s+")

# Contrazioni inglesi spezzate dal tokenizzatore: "do n't" -> "don't"
RE_CONTRAZIONI = re.compile(r"\s+(n't|'s|'re|'ve|'ll|'d|'m)\b", re.IGNORECASE)

# Punteggiatura attaccata alla parola successiva: "balance.There" -> "balance. There"
# Il primo gruppo e' minuscolo per non toccare acronimi tipo "U.S.A".
RE_PUNTO_ATTACCATO = re.compile(r"([a-z])([.!?:;])([A-Z])")


def normalizza(testo: str) -> str:
    """Rimuove gli artefatti di spaziatura senza toccare lo stile.

    L'ordine e' vincolante: le virgolette vanno rimosse per prime, perche'
    toglierle dopo ricrea spazi orfani davanti alla punteggiatura. Per lo
    stesso motivo serve un secondo passaggio finale.
    """
    t = testo.replace("\u00a0", " ")

    # Virgolette rimosse da entrambe le classi: distinguere apertura da
    # chiusura e' inaffidabile, e si preferisce una perdita d'informazione
    # nota e simmetrica a un artefatto residuo asimmetrico.
    t = t.replace('"', "")
    t = t.replace("\u201c", "").replace("\u201d", "")

    t = RE_PUNTO_ATTACCATO.sub(r"\1\2 \3", t)
    t = RE_CONTRAZIONI.sub(r"\1", t)
    t = RE_SPAZIO_PRIMA_PUNTEGGIATURA.sub(r"\1", t)
    t = RE_SPAZIO_DOPO_APERTURA.sub(r"\1", t)
    t = RE_SPAZI.sub(" ", t)

    # Secondo passaggio: le sostituzioni precedenti possono aver generato
    # nuovi spazi orfani.
    t = RE_SPAZIO_PRIMA_PUNTEGGIATURA.sub(r"\1", t)

    return t.strip()


def conta_parole(testo: str) -> int:
    return len(testo.split())


def filtra_lunghezza(df: pd.DataFrame, minimo: int = 50, massimo: int = 600) -> pd.DataFrame:
    """Scarta testi troppo corti o troppo lunghi.

    La soglia minima di 50 parole e' fissata a priori: sotto tale lunghezza
    le misure di ricchezza lessicale (TTR, MATTR, hapax) sono instabili.
    """
    n_parole = df["text"].map(conta_parole)
    tenuti = (n_parole >= minimo) & (n_parole <= massimo)
    print(f"Filtro lunghezza [{minimo}-{massimo}]: tengo {tenuti.sum()} su {len(df)}")
    return df[tenuti].copy()


def appaia_lunghezze(df: pd.DataFrame, tolleranza: float = 0.50) -> pd.DataFrame:
    """Tiene solo le coppie umano/macchina di lunghezza comparabile.

    Senza questo controllo il classificatore impara che i testi lunghi sono
    generati: ChatGPT scrive sistematicamente piu' lungo, con rapporti fra
    mediane da 1.13 (wiki_csai) a 2.50 (medicine).

    La tolleranza 0.50 e' la condizione principale, scelta a priori come
    compromesso fra controllo della lunghezza e rappresentativita' del
    campione (0.30 scartava il 77% delle coppie, selezionando un
    sottoinsieme atipico). Non va ottimizzata guardando i risultati a valle:
    e' prevista un'analisi di sensibilita' dopo la Fase 6.
    """
    df = df.copy()
    df["n_parole"] = df["text"].map(conta_parole)
    tenuti = []
    for _, gruppo in df.groupby("question_id"):
        if len(gruppo) != 2:
            continue
        a, b = gruppo["n_parole"].values
        if min(a, b) == 0:
            continue
        if abs(a - b) / max(a, b) <= tolleranza:
            tenuti.append(gruppo)
    risultato = pd.concat(tenuti, ignore_index=True) if tenuti else df.iloc[0:0]
    print(f"Appaiamento lunghezze (tolleranza {tolleranza}): "
          f"tengo {len(risultato)} su {len(df)}")
    return risultato


def pulisci(
    percorso_in=None,
    percorso_out=None,
    tolleranza: float = 0.50,
    domini_esclusi=("open_qa",),
    lung_min: int = 50,
    lung_max: int = 600,
) -> pd.DataFrame:
    """Pipeline completa di pulizia.

    Il dominio open_qa e' escluso: le sue risposte umane hanno mediana 27
    parole e Q3 = 38, quindi il filtro a 50 parole ne rimuove il 95%
    lasciando 54 coppie. Si preferisce escluderlo piuttosto che abbassare
    la soglia, perche' modificare un criterio per salvare un dominio
    significherebbe sceglierlo guardando il risultato.
    """
    if percorso_in is None:
        percorso_in = RADICE / "data" / "raw" / "hc3_flat.parquet"
    if percorso_out is None:
        percorso_out = RADICE / "data" / "processed" / "hc3_clean.parquet"
    percorso_in = Path(percorso_in)
    percorso_out = Path(percorso_out)

    df = pd.read_parquet(percorso_in)
    print(f"Partenza: {len(df)} righe, {df['domain'].nunique()} domini")

    if domini_esclusi:
        df = df[~df["domain"].isin(domini_esclusi)].copy()
        print(f"Esclusi {list(domini_esclusi)}: restano {len(df)} righe")

    df["text"] = df["text"].map(normalizza)
    df = df[df["text"].str.len() > 0]
    df = filtra_lunghezza(df, minimo=lung_min, massimo=lung_max)

    if tolleranza is not None:
        df = appaia_lunghezze(df, tolleranza=tolleranza)

    percorso_out.parent.mkdir(parents=True, exist_ok=True)
    df.to_parquet(percorso_out, index=False)
    print(f"Salvate {len(df)} righe ({df['question_id'].nunique()} coppie) "
          f"in {percorso_out}")
    return df


if __name__ == "__main__":
    pulisci()