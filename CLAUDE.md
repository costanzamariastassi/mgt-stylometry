# Contesto del progetto

## Cos'è

Progetto d'esame per il corso **Tecnologie dei dati e del linguaggio**
(Prof. Alfio Ferrara, Studi Umanistici, Università di Milano).
Traccia 20: "Riconoscere la mano della macchina".

Consegna: repository GitHub pubblico con codice e risultati riproducibili,
presentazione di 10 minuti con slide, colloquio orale in cui ogni scelta
tecnica va giustificata a voce.

**Criterio di valutazione dichiarato dal docente**: la valutazione non premia
le prestazioni elevate ma la discussione critica dei risultati. Un
classificatore con accuracy 0.97 presentato come successo vale meno dello
stesso classificatore usato per mostrare dove e perché fallisce.

## Domanda di ricerca

Un classificatore stilometrico addestrato a distinguere testo umano da testo
generato apprende tratti della *generazione automatica* o tratti di un
*registro testuale*? I suoi errori sono rumore casuale o sono sistematici
rispetto a proprietà misurabili del testo umano?

### Ipotesi

- **H1** — Un classificatore su poche feature stilometriche interpretabili
  raggiunge prestazioni non banali in-domain (AUROC > 0.85).
- **H2** — I falsi positivi (testo umano classificato come macchina) si
  concentrano in modo statisticamente significativo sui testi umani più
  formali, più lunghi e sintatticamente più regolari.
- **H3** — Le prestazioni crollano fuori dominio e fuori generatore.

H2 e H3 sono il cuore del progetto. H1 serve solo a stabilire che il
classificatore funziona abbastanza da rendere interessante l'analisi degli
errori.


## Dati

**Fonte**: `Hello-SimpleAI/HC3` su HuggingFace. Coppie domanda-risposta con
una risposta umana e una generata da ChatGPT **sullo stesso prompt**. Questo
appaiamento è la proprietà centrale del dataset: elimina il confondimento tra
"differenza di argomento" e "differenza di autore".

**Numeri**:
- Grezzo: 47.730 righe / 23.865 coppie, 5 domini
- Pulito: 20.078 righe / 10.039 coppie, 4 domini

**Distribuzione dopo la pulizia** (fortemente sbilanciata, da dichiarare
come limite):

| dominio | coppie |
|---------|--------|
| reddit_eli5 | 6.988 |
| finance | 2.043 |
| wiki_csai | 539 |
| medicine | 415 |

## Decisioni già prese e loro motivazione

Queste scelte sono state discusse e motivate. **Non cambiarle senza
segnalarlo esplicitamente**, perché ciascuna va difesa al colloquio.

### 1. Rimozione degli artefatti di tokenizzazione (critica)

I testi umani di HC3 sono passati per un tokenizzatore e ricomposti con
join sugli spazi. Producono marcatori quasi perfetti della classe umana:

| artefatto | grezzo umano | grezzo macchina | pulito umano | pulito macchina |
|-----------|--------------|-----------------|--------------|-----------------|
| doppio spazio | 0.118 | 0.000 | 0.000 | 0.000 |
| spazio prima del punto | 0.712 | 0.002 | 0.000 | 0.000 |
| spazio prima della virgola | 0.619 | 0.001 | 0.000 | 0.000 |
| contrazione spezzata | 0.469 | 0.000 | 0.002 | 0.000 |
| virgoletta spaziata | 0.250 | 0.207 | 0.000 | 0.000 |

Senza questa pulizia il classificatore impara la formattazione invece dello
stile. `src/check_leakage.py` verifica che i delta restino sotto 0.02.
**Va rilanciato dopo ogni modifica a `normalizza()`.**

L'ordine delle sostituzioni in `normalizza()` è vincolante: le virgolette
vanno rimosse **prima** della punteggiatura, altrimenti si ricreano spazi
orfani. Serve un secondo passaggio di `RE_SPAZIO_PRIMA_PUNTEGGIATURA` alla
fine.

Le virgolette doppie vengono rimosse da entrambe le classi: distinguere
apertura da chiusura è inaffidabile, e si preferisce una perdita
d'informazione nota e simmetrica a un artefatto residuo asimmetrico.

### 2. Filtro di lunghezza: 50-600 parole

Sotto le 50 parole le misure di ricchezza lessicale (TTR, MATTR, hapax)
sono instabili. Criterio fissato *a priori*.

### 3. Esclusione del dominio `open_qa`

Le risposte umane di `open_qa` hanno mediana 27 parole e Q3 = 38. Il filtro
a 50 parole ne rimuove il 95%, lasciando 54 coppie.

Il dominio è escluso **senza abbassare la soglia**: modificare il criterio
per salvare un dominio significherebbe scegliere il parametro guardando il
risultato.

### 4. Appaiamento per lunghezza, tolleranza 0.50

ChatGPT scrive sistematicamente più lungo, e il divario varia molto per
dominio (mediana umano/macchina):

| dominio | umano | macchina | rapporto |
|---------|-------|----------|----------|
| finance | 129 | 206 | 1.60 |
| medicine | 74 | 185 | 2.50 |
| reddit_eli5 | 95 | 173 | 1.82 |
| wiki_csai | 166 | 188 | 1.13 |

Senza controllo, il classificatore impara "lungo = macchina". La tolleranza
0.30 scartava il 77% delle coppie selezionando un sottoinsieme atipico;
0.50 mantiene circa metà del campione.

**Il valore 0.50 è la condizione principale e non va ottimizzato.** È
prevista un'analisi di sensibilità (0.30 / 0.40 / 0.50 / nessun
appaiamento) da eseguire **dopo** la Fase 6, per mostrare che le conclusioni
non dipendono dal parametro — non per sceglierne uno migliore.

### 5. Split per `question_id`, mai per riga

Le due risposte alla stessa domanda devono stare nello stesso fold. Usare
`GroupShuffleSplit` o `GroupKFold` con `groups=df["question_id"]`.

## Convenzioni di codice

- **Lingua**: commenti, docstring e nomi di variabili in italiano.
- **Niente emoji né emoticon nel codice.**
- **Percorsi**: ancorati alla radice con
  `RADICE = Path(__file__).resolve().parent.parent`, mai relativi alla
  directory di lavoro. Gli script si lanciano dalla radice del progetto.
- **Seed**: `SEED = 42` fissato ovunque compaia casualità.
- **Formati**: parquet per i file intermedi della pipeline, CSV per le
  tabelle di risultato in `results/tables/`.
- **Figure**: `plt.savefig(percorso, dpi=150, bbox_inches="tight")` in
  `results/figures/`.
- **Ambiente**: virtualenv in `mgt/` (non `.venv/`), presente nel
  `.gitignore` insieme a `data/`.

## Struttura

```
mgt-stylometry/
├── CLAUDE.md
├── README.md
├── requirements.txt
├── data/
│   ├── raw/hc3_flat.parquet
│   └── processed/hc3_clean.parquet
├── notebooks/
│   └── 01_eda.ipynb
├── src/
│   ├── loading.py
│   ├── cleaning.py
│   ├── check_leakage.py
│   ├── features.py
│   ├── models.py
│   └── evaluation.py
└── results/
    ├── figures/
    └── tables/
```

## Vincoli sul lavoro da svolgere

### Feature stilometriche (Fase 4)

Set **piccolo e interpretabile**: 15-25 feature, non migliaia. Ogni feature
deve avere un nome spiegabile a voce in cinque secondi. L'interpretabilità
è un requisito, non una preferenza: senza coefficienti leggibili l'analisi
dei falsi positivi (Fase 6) è impossibile.

Categorie: lunghezza e ritmo, ricchezza lessicale (MATTR, hapax, entropia),
sintassi via spaCy (profondità dell'albero, subordinate/coordinate),
distribuzione POS, punteggiatura, connettivi e hedging.

### Modelli (Fase 5)

Tre livelli: baseline maggioritaria, regressione logistica su feature
stilometriche (modello principale), TF-IDF + logistica (confronto
stile vs lessico).

**Non fine-tunare un transformer.** Alzerebbe l'accuracy e distruggerebbe
l'interpretabilità su cui poggia l'intero progetto.

### Metriche

Accuracy, precision, recall, F1, matrice di confusione — il vocabolario
esplicito del corso. Più AUROC e soprattutto **FPR**: nel caso d'uso reale
il costo di accusare uno studente innocente non è simmetrico a quello di
non individuare un imbroglio.

### Analisi dei falsi positivi (Fase 6, cuore del progetto)

1. Confronto statistico feature per feature tra falsi positivi e veri
   negativi (Mann-Whitney), **con correzione per test multipli** (FDR
   Benjamini-Hochberg): con 30 feature si trova significatività per caso.
2. Lettura ordinata dei coefficienti della logistica.
3. Cinque casi commentati qualitativamente.

### Generalizzazione (Fase 7)

Leave-one-domain-out sui 4 domini, più test esterno su M4GT-Bench
(`mbzuai-nlp/M4GT-Bench`), che include l'italiano. Se si usa la porzione
italiana: caricare `it_core_news_sm`, tradurre le liste di connettivi e
hedging, sostituire Flesch con **Gulpease**.
