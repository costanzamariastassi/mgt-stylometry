# Uso di strumenti di IA generativa

Dichiarazione richiesta dal docente. Le voci contrassegnate con `[da
completare]` vanno compilate dall'autore: una dichiarazione precisa vale
piu' di una generica, e questo file viene letto.

## Strumenti usati

| strumento | versione / modello | impiego |
|-----------|--------------------|---------|
| Claude (Anthropic) | `Opus 5` | impostazione metodologica, stesura del codice, generazione dei notebook, discussione dei risultati |
| Claude Code | `2.12` | revisione del repository, individuazione di incoerenze fra file |
| `[altri strumenti, se usati]` | | |

Nessun contenuto del corpus e' stato generato per questo progetto: i testi
analizzati provengono interamente da HC3 (Guo et al., 2023), generati da
ChatGPT nel dicembre 2022 dagli autori del dataset.

## Cosa e' stato fatto con assistenza dell'IA

### Codice

Gli script in `src/` e i notebook in `notebooks/` sono stati scritti con
assistenza di Claude, a partire da specifiche discusse volta per volta.
Nessun file e' stato accettato senza esecuzione e verifica dell'output.

Interventi correttivi rilevanti effettuati dall'autore su codice generato:

- test specifici come i controlli su multiple istanze di tolleranza, confronti multipli di falsi positivi e falsi negativi, disegno di auroc
- Implementazioni di features specifiche (em/en dash, triplette e hapax)
- 
- `[altri]`

### Impostazione metodologica

Discusse in dialogo con Claude, con decisione finale dell'autore:

- la scelta della traccia e il disegno sperimentale a tre ipotesi;
- la distinzione fra parametri di preprocessing (non ottimizzabili) e
  iperparametri del modello (tarabili su validation set), documentata in
  `CLAUDE.md`;
- la decisione di non fine-tunare un transformer, per preservare
  l'interpretabilita' dei coefficienti;
- il trattamento simmetrico degli artefatti di preprocessing sulle due
  classi.

### Analisi e interpretazione

Le tabelle e le figure sono prodotte dal codice. La loro interpretazione e'
stata discussa con Claude; le conclusioni riportate nel README sono
dell'autore.


## Contributi originali dell'autore

(completare))

### Ipotesi sui marcatori stilistici

Due ipotesi formulate dall'autore a partire dall'esperienza di lettura di
testi generati, prima di guardare i dati, e poi sottoposte a verifica
(notebook `02_features.ipynb`, sezione 4):

1. **Eccesso di lineette come marcatore di testo generato.** Ipotesi
   **smentita** su HC3: l'em dash risulta circa sette volte piu' frequente
   nei testi umani. La verifica ha portato a distinguere tre caratteri
   (`-`, `–`, `—`) e a formulare l'osservazione che i marcatori stilistici
   non sono stabili fra generazioni di modelli — risultato entrato nella
   discussione di H3.

2. **Elenchi di tre elementi come marcatore di testo generato.** Ipotesi
   **confermata**: la feature `tripletta_per_100parole` risulta seconda per
   rapporto fra classi (2.01), dopo `ratio_connettivi`.

Entrambe le feature sono state aggiunte al set su iniziativa dell'autore.

### Verifiche che hanno modificato il disegno

- `[da completare: es. verifica della coerenza cross-dominio dei token
  sbilanciati, che ha distinto il segnale di generatore da quello di
  dominio]`
- `[altre]`

## Cosa e' stato verificato di persona

- Esecuzione di ogni script e controllo di ogni output.
- Ispezione diretta dei testi in piu' punti: coppie appaiate in Fase 3,
  outlier del trattino in Fase 4, cinque falsi positivi commentati in
  Fase 6.
- Verifica dell'assenza di leakage tramite `src/check_leakage.py`, con
  soglia dichiarata nel codice.
- `[da completare: altre verifiche]`

## Limiti di questa dichiarazione

L'autore ha compreso e sa esporre il funzionamento di ogni componente della
pipeline. Le parti in cui la comprensione e' meno approfondita, e che
verrebbero riscritte con piu' tempo, sono:

- `[da completare: essere onesti qui vale piu' che dichiarare padronanza
  completa]`

## Riferimento

Guo et al. (2023), *How Close is ChatGPT to Human Experts? Comparison
Corpus, Evaluation, and Detection*, arXiv:2301.07597.