# Uso di strumenti di IA generativa

Dichiarazione sull'uso di strumenti di IA generativa nel progetto, come
richiesto dal docente.

Autrice: Costanza Maria Stassi — matricola 85086A

## Strumenti usati

| strumento | versione / modello | impiego |
|-----------|--------------------|---------|
| Claude (Anthropic) | Opus 5 | impostazione metodologica, stesura del codice, generazione dei notebook, discussione dei risultati |
| Claude Code | 2.12 | revisione del repository, individuazione di incoerenze fra file |

Non sono stati usati altri strumenti di IA generativa.

Nessun contenuto del corpus è stato generato per questo progetto: i testi
analizzati provengono interamente da HC3 (Guo et al., 2023), generati da
ChatGPT nel dicembre 2022 dagli autori del dataset.

## Cosa è stato fatto con l'assistenza dell'IA

### Codice

Gli script in `src/` e i notebook in `notebooks/` sono stati scritti con
l'assistenza di Claude, a partire da specifiche discusse volta per volta.
Nessun file è stato accettato senza esecuzione e verifica dell'output.

Interventi dell'autrice sul codice generato:

- richiesta di commentare il codice riga per riga, specificando che cosa fa
  ciascuna istruzione, in modo da poter leggere e spiegare ogni passaggio;
- test aggiuntivi: controlli su più valori della tolleranza di appaiamento,
  confronti multipli fra falsi positivi e falsi negativi, curve ROC;
- implementazione di feature specifiche (em dash, en dash, elenchi di tre
  elementi, hapax);
- correzione dei problemi emersi eseguendo il codice sul proprio computer:
  il caricamento di HC3 non più supportato dalla versione 4 della libreria
  `datasets`, i percorsi dei file scritti in forma assoluta, l'ordine delle
  sostituzioni nella pulizia dei testi, il caricamento dei moduli con nomi
  numerati;
- inserimento di punti di controllo e di stampe di verifica (zone di debug)
  per assicurarsi che ogni fase girasse correttamente e producesse i numeri
  attesi prima di passare alla successiva.

### Impostazione metodologica

Discussa in dialogo con Claude, con decisione finale dell'autrice:

- la scelta della traccia e il disegno sperimentale a tre ipotesi;
- la distinzione fra parametri di preprocessing (non ottimizzabili) e
  iperparametri del modello (tarabili su validation set), documentata in
  `CLAUDE.md`;
- la decisione di non addestrare un transformer, per preservare
  l'interpretabilità dei coefficienti;
- il trattamento simmetrico degli artefatti di preprocessing sulle due
  classi.

### Analisi e interpretazione

Le tabelle e le figure sono prodotte dal codice. La loro interpretazione è
stata discussa con Claude; le conclusioni riportate nel README sono
dell'autrice.

## Contributi originali dell'autrice

### Ipotesi sui marcatori stilistici

Due ipotesi formulate dall'autrice a partire dall'esperienza di lettura di
testi generati, prima di guardare i dati, e poi sottoposte a verifica
(notebook `02_features.ipynb`, sezione 4):

1. **Eccesso di lineette come marcatore di testo generato.** Ipotesi
   **smentita** su HC3: l'em dash compare nell'1,12% dei testi umani contro lo
   0,16% di quelli generati, e in frequenza per 100 parole è circa 13 volte più
   comune nei testi umani. La verifica ha portato a distinguere tre caratteri
   (`-`, `–`, `—`) e a formulare l'osservazione che i marcatori stilistici non
   sono stabili fra generazioni di modelli, risultato entrato nella discussione
   di H3.

2. **Elenchi di tre elementi come marcatore di testo generato.** Ipotesi
   **confermata**: la feature `tripletta_per_100parole` risulta seconda per
   rapporto fra classi (2,01), dopo `ratio_connettivi`.

Entrambe le feature sono state aggiunte al set su iniziativa dell'autrice.

### Verifiche che hanno modificato il disegno

- La verifica della coerenza dei token sbilanciati fra domini, che ha separato
  il segnale del generatore (*important*, presente in tutti i domini) da quello
  di dominio (*financial*, presente solo in finance).
- L'ispezione dei valori estremi della feature sul trattino, che ha portato a
  escluderla perché misurava composti spezzati dal tokenizzatore e non l'uso
  stilistico del segno.
- La scoperta che il filtro di lunghezza faceva aumentare il leakage delle
  contrazioni (da 0,469 a 0,556), che ha reso necessaria una pulizia più
  completa dei testi.
- Il controllo sulla lunghezza delle risposte di `open_qa` (mediana 27 parole),
  che ha motivato l'esclusione del dominio.
- La scelta di non usare la tolleranza 0,30, che scartava il 77% delle coppie.
- Il dubbio sollevato dall'autrice sul valore della tolleranza di
  appaiamento (0,50), con la proposta di provarne altri. Da qui è nata la
  decisione di rieseguire l'intera pipeline a quattro tolleranze (0,30, 0,40,
  0,50 e nessun appaiamento) e di riportare tutte le condizioni, non solo la
  migliore: è la sezione "Robustezza" del README.
- La domanda dell'autrice sul perché non si cercassero i parametri migliori.
  La risposta è diventata la nota metodologica in `CLAUDE.md`, che distingue i
  parametri di preprocessing, fissati a priori perché definiscono il campione,
  dagli iperparametri del modello, tarati solo sul validation set.
- Il debug delle fasi finali. Eseguendo la pipeline sono emersi file
  intermedi non aggiornati e versioni duplicate degli script, che facevano
  girare i notebook su codice diverso da quello corretto. Risolvere questi
  problemi ha richiesto di rendere configurabile la pulizia dei testi. Da qui
  è nata gran parte dell'ultima fase del progetto: l'analisi di sensibilità
  sulla tolleranza di appaiamento e la verifica che le conclusioni reggano in
  tutte le condizioni.

## Cosa è stato verificato di persona

- Creazione dell'ambiente di sviluppo: ambiente virtuale Python,
  installazione delle dipendenze e del modello linguistico di spaCy.
- Esecuzione di ogni script e di ogni notebook sul proprio computer personale,
  con analisi dell'output di ciascuna fase prima di passare alla successiva.
- Lettura diretta dei testi in più punti: coppie appaiate in Fase 3, valori
  estremi del trattino in Fase 4, cinque falsi positivi commentati in Fase 6.
- Verifica dell'assenza di leakage tramite `src/check_leakage.py`, con soglia
  dichiarata nel codice.
- Archiviazione dei risultati di ogni tentativo con prefissi distinti (`1_`,
  `2_`), scelta dall'autrice per confrontare le esecuzioni successive. Il
  confronto fra prima e dopo la pulizia ha mostrato che il segnale lessicale
  (per esempio *important*, presente nel 41% dei testi generati contro il 6%
  di quelli umani) non dipendeva dagli artefatti di formattazione.

## Limiti di questa dichiarazione

L'autrice parte da conoscenze di programmazione limitate. Nonostante questo,
durante il progetto ha cercato di approfondire gli aspetti tecnici e di capire
i meccanismi alla base del codice, chiedendone la spiegazione riga per riga e
verificando in prima persona il comportamento di ogni fase.

## Riferimento

Guo et al. (2023), *How Close is ChatGPT to Human Experts? Comparison
Corpus, Evaluation, and Detection*, arXiv:2301.07597.
