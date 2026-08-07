"""Verifica che gli artefatti di formattazione siano stati rimossi."""

from pathlib import Path

import pandas as pd

RADICE = Path(__file__).resolve().parent.parent

TEST = [
    ("doppio_spazio", lambda t: "  " in t),
    ("spazio_prima_punto", lambda t: " ." in t),
    ("spazio_prima_virgola", lambda t: " ," in t),
    ("contrazione_spezzata", lambda t: " n't" in t or " 're" in t or " 's" in t),
    ("virgoletta_spaziata", lambda t: '" ' in t or ' "' in t),
]


def confronta():
    grezzo = pd.read_parquet(RADICE / "data" / "raw" / "hc3_flat.parquet")
    pulito = pd.read_parquet(RADICE / "data" / "processed" / "hc3_clean.parquet")

    for nome, df in [("GREZZO", grezzo), ("PULITO", pulito)]:
        print(f"--- {nome} ({len(df)} righe)")
        for col, fn in TEST:
            m = df.groupby("label")["text"].apply(lambda s: s.map(fn).mean())
            delta = abs(m.get(0, 0) - m.get(1, 0))
            print(f"{col:22s} umano={m.get(0, 0):.3f}  macchina={m.get(1, 0):.3f}  delta={delta:.3f}")
        print()


if __name__ == "__main__":
    confronta()