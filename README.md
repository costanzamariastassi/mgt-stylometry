# Riconoscere la mano della macchina

**Un classificatore stilometrico distingue il testo umano da quello generato,
o distingue un registro di scrittura da un altro?**

Progetto d'esame per il corso *Tecnologie dei dati e del linguaggio*
(Prof. Alfio Ferrara), traccia 20.

| | |
|---|---|
| Autrice | Costanza Maria Stassi — matricola 85086A |
| Anno accademico | 2025/26 |
| Dataset | HC3 — Human ChatGPT Comparison Corpus (Guo et al., 2023) |
| Lingua | inglese |
| Modello principale | regressione logistica su 30 feature stilometriche interpretabili |

> **Prima di eseguire il codice: aggiornare i percorsi.**
> Alcuni script in `src/` contengono percorsi assoluti riferiti al computer
> dell'autrice (per esempio `/Users/costanzastassi/Desktop/mgt-stylometry/...`).
> Per eseguirli su un altro computer bisogna sostituire la parte iniziale del
> percorso con quella della cartella in cui è stato clonato il repository.
> Per trovare tutte le righe da modificare, dalla radice del repository:
>
> ```bash
> grep -rn "/Users/costanzastassi" src/ notebooks/
> ```
>
> In ciascuna riga trovata va sostituito `/Users/costanzastassi/Desktop/mgt-stylometry`
> con il percorso della propria copia del repository, lasciando invariata la
> parte finale (`data/processed/...`).

---

## In breve

Un classificatore basato su trenta tratti stilistici distingue risposte umane
e risposte di ChatGPT con AUROC 0.971. Il risultato interessante non è questo
numero, ma la struttura degli errori:

- **i testi umani classificati come generati non sono casi ambigui**: sulle
  feature decisive hanno gli stessi valori dei testi generati. Il modello
  riconosce un registro (prosa regolare, formale, poco varia), non un'origine;
- **il tasso di falsi positivi varia di un fattore sette fra domini**: dal
  2.7% dei testi medici al 19.9% delle voci enciclopediche;
- **fuori dominio non cede la capacità di discriminare, ma la soglia di
  decisione**: l'AUROC resta sopra 0.90 ovunque, mentre sulle voci
  enciclopediche quattro testi umani su dieci vengono classificati come
  generati.

In una frase: **il classificatore separa registri, non origini**, e il costo
dei suoi errori ricade in modo sistematico su chi scrive in modo formale e
regolare.

---

## Indice

1. [Consegna](#consegna)
2. [Domanda di ricerca e ipotesi](#domanda-di-ricerca-e-ipotesi)
3. [Dati](#dati)
4. [Metodo](#metodo)
5. [Risultati](#risultati)
6. [Discussione](#discussione)
7. [Limiti](#limiti)
8. [Struttura del repository](#struttura-del-repository)
9. [Riproduzione](#riproduzione)
10. [Uso di strumenti di IA](#uso-di-strumenti-di-ia)
11. [Riferimenti](#riferimenti)

---

## Consegna

Il progetto risponde ai requisiti del corso:

- una **domanda di ricerca precisa**, con ipotesi dichiarate prima
  dell'analisi;
- **fonti e dati** motivati, con criteri di esclusione e limiti espliciti;
- una **pipeline documentata** e riproducibile, con seed fissato;
- **criteri di verifica** orientati a confermare o respingere ciascuna
  ipotesi;
- repository pubblico, presentazione di dieci minuti con slide, colloquio
  orale.

Il criterio di valutazione dichiarato dal docente non premia le prestazioni
elevate ma la discussione critica dei risultati. Il progetto è costruito di
conseguenza: le metriche alte sono il punto di partenza per chiedersi che cosa
nascondono.

---

## Domanda di ricerca e ipotesi

> Un classificatore stilometrico addestrato a distinguere testo umano da testo
> generato apprende tratti della **generazione automatica** o tratti di un
> **registro testuale**? I suoi errori sono rumore casuale, oppure sono
> sistematici rispetto a proprietà misurabili del testo umano?

| | ipotesi | esito |
|---|---------|-------|
| **H1** | Un classificatore su poche feature stilometriche interpretabili raggiunge AUROC > 0.85 in-domain | **confermata** (0.971) |
| **H2** | I falsi positivi si concentrano sui testi umani più formali, più regolari e lessicalmente meno vari | **confermata**, in forma più forte del previsto |
| **H3** | Le prestazioni crollano fuori dominio | **smentita e riformulata**: cede la calibrazione della soglia, non la capacità di discriminare |

H1 serve a stabilire che il modello funziona abbastanza da rendere
interessante l'analisi degli errori. Il cuore del progetto sono H2 e H3.

---

## Dati

### Perché HC3

HC3 contiene coppie domanda-risposta in cui **la stessa domanda** ha una
risposta scritta da una persona e una generata da ChatGPT (dicembre 2022).
L'appaiamento sullo stesso prompt è la ragione della scelta: separa la
*differenza di autore* dalla *differenza di argomento*. Senza di esso un
classificatore potrebbe distinguere le classi solo perché parlano di cose
diverse.

### Dal corpus grezzo al corpus di lavoro

| passaggio | righe | coppie |
|-----------|------:|-------:|
| corpus grezzo, 5 domini | 47.730 | 23.865 |
| esclusione di `open_qa` | 45.356 | — |
| filtro di lunghezza (50–600 parole) | 38.848 | — |
| appaiamento per lunghezza (tolleranza 0.50) | **19.980** | **9.990** |

| dominio | coppie | quota del corpus | ritenzione |
|---------|-------:|-----------------:|-----------:|
| reddit_eli5 | 6.984 | 69.9% | 42% |
| finance | 2.029 | 20.3% | 52% |
| wiki_csai | 538 | 5.4% | 64% |
| medicine | 439 | 4.4% | 35% |

### Scelte e motivazioni

**Filtro di lunghezza a 50 parole.** Fissato a priori: sotto questa soglia le
misure di ricchezza lessicale (type-token ratio, hapax) sono statisticamente
instabili.

**Esclusione di `open_qa`.** Le risposte umane di questo dominio hanno mediana
27 parole; il filtro ne rimuoveva il 95%, lasciando 54 coppie. Si è scelto di
escludere il dominio invece di abbassare la soglia: modificare un criterio per
salvare un dominio significherebbe sceglierlo guardando il risultato.

**Appaiamento per lunghezza.** ChatGPT scrive sistematicamente più lungo, con
rapporti fra le mediane da 1.13 (wiki_csai) a 2.50 (medicine). Senza controllo
il classificatore imparerebbe soltanto che un testo lungo è generato. Si
tengono le coppie in cui le due risposte differiscono in lunghezza di non più
del 50%. Dopo l'appaiamento il rapporto fra le mediane scende a 1.19
(150 contro 178 parole).

### Il leakage nascosto nel dataset

Prima di misurare lo stile è stato necessario rimuovere due artefatti del
preprocessing di HC3, uno per classe:

- i testi **umani** erano passati per un tokenizzatore e ricomposti con spazi
  (`do n't`, `command - line`, spazio prima della punteggiatura);
- i testi **generati** avevano perso gli a capo degli elenchi, lasciando la
  punteggiatura attaccata alla parola successiva (`balance.There are`).

| artefatto | umano prima | macchina prima | umano dopo | macchina dopo |
|-----------|------------:|---------------:|-----------:|--------------:|
| spazio prima del punto | 0.712 | 0.002 | 0.000 | 0.000 |
| spazio prima della virgola | 0.619 | 0.001 | 0.000 | 0.000 |
| contrazione spezzata | 0.469 | 0.000 | 0.002 | 0.000 |
| doppio spazio | 0.118 | 0.000 | 0.000 | 0.000 |
| punto senza spazio | 0.032 | 0.202 | 0.003 | 0.000 |

*Valori: quota di testi che contengono l'artefatto.*

Ciascuno di questi artefatti, da solo, separa quasi perfettamente le classi.
Senza la pulizia si otterrebbe un'accuratezza altissima misurando la
formattazione del dataset invece dello stile degli autori. Gli artefatti sono
stati rimossi **da entrambe le classi**: ripulirne una sola avrebbe lasciato
all'altra un marcatore quasi perfetto.

La verifica è automatizzata in `src/check_leakage.py`, con soglia dichiarata
nel codice (differenza massima di 0.02 fra le classi). Le virgolette doppie
sono state rimosse da entrambe le classi, perché dopo la tokenizzazione
distinguere apertura e chiusura non è affidabile: si è preferita una perdita di
informazione nota e simmetrica a un artefatto residuo asimmetrico.

---

## Metodo

### Feature

Trenta feature interpretabili, ciascuna spiegabile a parole:

| categoria | feature |
|-----------|---------|
| lunghezza e ritmo | lunghezza media e deviazione standard delle frasi, lunghezza media delle parole, numero di frasi |
| ricchezza lessicale | MATTR, quota di hapax, entropia della distribuzione dei token |
| sintassi | profondità media dell'albero delle dipendenze, subordinate e coordinate per frase |
| lessico funzionale | connettivi (*however, moreover...*), hedging (*may, might, often...*), prima persona |
| categorie grammaticali | quota di nomi, verbi, aggettivi, avverbi, pronomi, preposizioni, congiunzioni coordinanti e subordinanti |
| punteggiatura | virgole, punti e virgola, due punti, parentesi, esclamativi, interrogativi (ogni 100 parole) |
| strutture tipiche | elenchi di tre elementi, lineetta lunga (em dash), lineetta media (en dash) |

Estrazione con spaCy (`en_core_web_sm`).

Il set è passato per quattro versioni, documentate in
`notebooks/02_features.ipynb`: rimossa una feature costante, rinominate quelle
con nomi fuorvianti, rimossa una feature che misurava un residuo del leakage,
aggiunte tre feature per verificare due ipotesi. **Nessuna decisione sul set di
feature è stata presa guardando le prestazioni di un classificatore**: a quel
punto nessun modello era ancora stato addestrato.

### Due ipotesi formulate a priori

| ipotesi | esito |
|---------|-------|
| L'eccesso di lineette lunghe segnala il testo generato | **smentita**: l'em dash compare nell'1.12% dei testi umani contro lo 0.16% di quelli generati; in frequenza per 100 parole è circa 13 volte più comune nei testi umani |
| Gli elenchi di tre elementi segnalano il testo generato | **confermata**: rapporto macchina/umano 2.01, seconda feature più sbilanciata dopo i connettivi |

L'em dash è oggi considerato un marcatore dei testi generati, ma HC3 risale a
dicembre 2022: su questo corpus discrimina nella direzione opposta. È una prima
evidenza che **i marcatori stilistici non sono stabili fra generazioni di
modelli**.

### Modelli

| modello | ruolo |
|---------|-------|
| baseline maggioritaria | pavimento di riferimento |
| **regressione logistica su feature stilometriche** | modello principale |
| regressione logistica su TF-IDF (unigrammi e bigrammi) | confronto fra segnale stilistico e segnale lessicale |

La regressione logistica è stata scelta perché i suoi coefficienti sono
leggibili. Un transformer addestrato sul compito avrebbe alzato le metriche e
reso impossibile l'analisi degli errori, che è l'oggetto del progetto.

### Protocollo di valutazione

- **Split per `question_id`** (`GroupShuffleSplit`): le due risposte alla
  stessa domanda finiscono sempre dallo stesso lato, altrimenti il modello
  vedrebbe in addestramento il gemello del testo che deve classificare.
- Tre partizioni: train, validation (per l'unico iperparametro tarato, `C`),
  test usato una sola volta.
- Standardizzazione delle feature prima della logistica.
- Seed fissato a 42.
- Metriche: accuracy, precision, recall, F1, AUROC e soprattutto **tasso di
  falsi positivi (FPR)**. Nel caso d'uso reale classificare come generato un
  testo umano e non individuare un testo generato non hanno lo stesso costo.

### Parametri non ottimizzati

I parametri di preprocessing (soglia di lunghezza, tolleranza di appaiamento,
esclusione di domini) definiscono **quale campione si studia**, non come lo si
studia. Ottimizzarli guardando l'accuratezza significherebbe scegliere i dati
che danno il risultato migliore. Sono stati fissati a priori, e la loro
influenza è verificata con un'analisi di sensibilità che riporta tutte le
condizioni e non solo la migliore.

---

## Risultati

### 1. In-domain

| modello | accuracy | precision | recall | F1 | FPR | AUROC |
|---------|---------:|----------:|-------:|---:|----:|------:|
| baseline | 0.500 | — | — | — | — | — |
| stilometrico | 0.919 | 0.921 | 0.917 | 0.919 | 0.079 | 0.971 |
| TF-IDF | 0.971 | 0.973 | 0.968 | 0.971 | 0.026 | 0.996 |

**197 falsi positivi su 2.498 testi umani del test set.** In un uso didattico
sarebbero 197 autori sospettati a torto.

TF-IDF fa meglio in-domain perché impara anche il lessico tematico, non solo
l'autore: il token *financial*, per esempio, separa le classi solo dentro il
dominio finance, mentre *important* mantiene il divario in tutti e quattro i
domini.

### 2. Che cosa ha imparato il modello

| verso "umano" | peso | verso "macchina" | peso |
|---------------|-----:|------------------|-----:|
| quota di hapax | −2.06 | congiunzioni coordinanti | +1.11 |
| numero di frasi | −1.11 | profondità dell'albero sintattico | +0.82 |
| parentesi | −1.01 | hedging | +0.57 |
| variabilità della lunghezza di frase | −0.96 | subordinate per frase | +0.53 |
| punto e virgola | −0.87 | connettivi | +0.46 |

Il modello riconosce l'umano dall'**irregolarità** (vocabolario vario, ritmo
mutevole, incisi) e la macchina dalla **regolarità sintattica**. Conta la
variabilità della lunghezza delle frasi, non la loro lunghezza media (peso
−0.22).

Delle otto previsioni sul segno dei coefficienti registrate prima
dell'addestramento, sette sono confermate. L'eccezione, `coordinate_per_frase`,
è un effetto di soppressione dovuto alla correlazione 0.72 con la quota di
congiunzioni coordinanti.

### 3. Chi sono i falsi positivi (H2)

Confronto fra i testi umani classificati come generati e quelli classificati
correttamente: test di Mann-Whitney, correzione di Benjamini-Hochberg per test
multipli, delta di Cliff come misura della dimensione dell'effetto.

| feature | umano corretto | **falso positivo** | generato |
|---------|---------------:|-------------------:|---------:|
| MATTR | 0.689 | **0.615** | 0.611 |
| lunghezza media di frase | 19.1 | **23.1** | 23.3 |
| profondità dell'albero | 2.78 | **3.15** | 3.24 |
| quota di hapax | 0.449 | **0.363** | 0.328 |

I falsi positivi **non hanno valori intermedi fra le classi: sono sovrapposti
alla macchina**. Il modello non sbaglia su testi ambigui, ma applica
correttamente criteri che identificano un registro.

| dominio | testi umani nel test | falsi positivi | tasso |
|---------|---------------------:|---------------:|------:|
| wiki_csai | 136 | 27 | **19.9%** |
| finance | 521 | 49 | 9.4% |
| reddit_eli5 | 1.729 | 118 | 6.8% |
| medicine | 112 | 3 | 2.7% |

Questa seconda evidenza non dipende da come sono state definite le feature, e
conferma la stessa conclusione per una via indipendente: la prosa
enciclopedica, editata e impersonale è la più penalizzata.

Tre osservazioni complementari:

- **l'errore segue i pesi del modello**: la correlazione fra il peso di una
  feature e la sua capacità di separare i falsi positivi è 0.54;
- **il modello sbaglia con sicurezza**: il 58% dei falsi positivi ha
  probabilità superiore a 0.7, e 23 superano 0.95;
- **gli errori sono speculari**: i testi generati che sfuggono sono quelli
  lessicalmente più vari e sintatticamente meno regolari. Un solo asse,
  percorso nelle due direzioni.

**Alzare la soglia non risolve, sposta il costo:**

| soglia | falsi positivi | falsi negativi |
|-------:|---------------:|---------------:|
| 0.50 | 197 | 207 |
| 0.70 | 115 | 364 |
| 0.90 | 46 | 806 |
| 0.95 | 23 | 1.146 |

### 4. Fuori dominio (H3)

Leave-one-domain-out: il modello è addestrato su tre domini e valutato sul
quarto.

| dominio di test | AUROC stilometrico | FPR stilometrico | AUROC TF-IDF | FPR TF-IDF |
|-----------------|-------------------:|-----------------:|-------------:|-----------:|
| medicine | 0.987 | 0.027 | 1.000 | 0.073 |
| finance | 0.974 | 0.118 | 0.998 | 0.013 |
| reddit_eli5 | 0.949 | 0.046 | 0.945 | 0.002 |
| wiki_csai | 0.908 | **0.403** | 0.923 | **0.470** |
| *in-domain* | *0.971* | *0.079* | *0.996* | *0.026* |

- L'AUROC **non crolla**: resta sopra 0.90 ovunque, con un calo medio di
  0.016. La capacità di ordinare i testi dal più umano al più artificiale si
  trasferisce fra domini.
- Il tasso di falsi positivi a soglia fissa invece **varia dallo 0.2% al 47%**.
- Ciò che non si trasferisce è **la soglia di decisione**. Su testi formali
  tutti i punteggi si alzano, e la soglia finisce dentro la distribuzione dei
  testi umani.

Uno strumento con AUROC 0.91 sembra affidabile in un rapporto tecnico, e
intanto classifica come generati quattro testi umani su dieci.

Il caso opposto è TF-IDF su reddit_eli5: FPR quasi nullo ma recall 0.46. Il
modello, addestrato su soli 6.012 testi degli altri domini, classifica quasi
tutto come umano e lascia sfuggire più della metà dei testi generati. È l'altra
faccia della stessa soglia mal calibrata.

### 5. Post-editing automatico

Tre trasformazioni meccaniche applicate ai 2.498 testi generati del test set:

| trasformazione | testi generati ancora riconosciuti |
|----------------|-----------------------------------:|
| nessuna | 91.7% |
| aggiungere contrazioni | 91.4% |
| togliere i connettivi | 90.3% |
| spezzare le frasi lunghe | 76.9% |
| tutte e tre | **73.8%** |

Nessuna riscrittura: un quarto dei testi generati sfugge con tre espressioni
regolari, e la sola rottura delle frasi lunghe vale quasi quindici punti.

### 6. Robustezza

Pipeline rieseguita a diverse tolleranze di appaiamento:

| tolleranza | coppie | accuracy | FPR | AUROC | H2 nella direzione attesa |
|-----------:|-------:|---------:|----:|------:|:-------------------------:|
| 0.30 | 5.397 | 0.912 | 0.102 | 0.966 | sì |
| 0.40 | 7.585 | 0.919 | 0.093 | 0.969 | sì |
| **0.50** | **9.990** | **0.919** | **0.079** | **0.971** | **sì** |
| nessuna | 22.629 | 0.927 | 0.101 | 0.975 | sì |

L'AUROC oscilla di meno di 0.01 su campioni da 5.397 a 22.629 coppie, e H2
regge in tutte le condizioni: le conclusioni non dipendono dal valore fissato a
priori. Senza appaiamento l'AUROC è la più alta ma il tasso di falsi positivi
peggiora: le metriche aggregate non catturano il costo che ricade sulla classe
umana.

---

## Discussione

**Il classificatore separa registri, non origini.** I risultati convergono: i
falsi positivi coincidono con la classe macchina sulle feature decisive, il
loro tasso segue la formalità del dominio, e gli errori sulla classe generata
percorrono lo stesso asse in direzione opposta.

**H3 era formulata male, e il risultato vero è più grave.** Uno strumento che
smette di funzionare fuori dominio verrebbe abbandonato. Uno strumento che
ordina bene ma taglia nel punto sbagliato mantiene metriche eccellenti e
produce accuse concentrate su un tipo preciso di scrittura. Una soglia
calibrata su una popolazione di testi non è trasferibile a un'altra, e chi usa
uno strumento di questo tipo raramente sa in anticipo quale popolazione
riceverà.

**Chi paga l'errore.** Viene penalizzata la scrittura formale, ordinata e
impersonale. È plausibile che lo stesso meccanismo colpisca chi scrive in una
seconda lingua, ma HC3 non contiene metadati sugli autori e questa ipotesi non
è verificabile qui.

**Risposta alla domanda pratica.** Uno strumento di questo tipo non dovrebbe
essere usato per valutare uno studente. Non perché funzioni male, ma perché
funziona esattamente come è stato addestrato a funzionare, e questo basta a
produrre accuse ingiuste distribuite in modo non casuale.

---

## Limiti

1. **Un solo generatore e una sola lingua**: ChatGPT di dicembre 2022,
   inglese. L'osservazione sull'em dash suggerisce che i marcatori cambiano fra
   generazioni di modelli, ma la generalizzazione fra generatori non è
   misurata.
2. **Nessun rilevatore commerciale è stato testato**: le conclusioni
   riguardano il meccanismo osservato su un modello ispezionabile, non prodotti
   specifici.
3. **Analisi correlazionale, non causale**: stabilire che la formalità causa il
   falso positivo richiederebbe di modificare una proprietà del testo alla
   volta. Il post-editing va in quella direzione, ma ogni trasformazione agisce
   su più feature insieme.
4. **Il filtro di lunghezza non è neutro fra domini**: la ritenzione va dal 35%
   al 64%, e colpisce di più i domini con il divario di lunghezza maggiore.
5. **Corpus sbilanciato**: reddit_eli5 è il 70% del corpus, quindi il modello
   impara soprattutto il contrasto fra divulgazione informale e testo generato.
6. **wiki_csai non è prosa umana tipica**: è testo collaborativo ed editato, il
   che rafforza la lettura per registri ma ne limita la generalizzazione.
7. **Liste lessicali scritte a mano**: connettivi e hedging sono liste brevi
   fissate a priori; la regex degli elenchi di tre cattura solo parole singole
   e presumibilmente sottostima il fenomeno.
8. **Pulizia non esaustiva**: gli artefatti noti sono sotto la soglia
   dichiarata, ma residui non individuati restano possibili.

---

## Struttura del repository

```
mgt-stylometry/
├── README.md
├── AI_usage.md              dichiarazione sull'uso di strumenti di IA
├── CLAUDE.md                contesto e decisioni metodologiche del progetto
├── requirements.txt
├── data/
│   ├── raw/                 non versionato, rigenerato dallo script di caricamento
│   └── processed/           corpus pulito e feature
├── src/
│   ├── loading.py           scarica HC3 da HuggingFace e appiattisce le coppie
│   ├── cleaning.py          normalizzazione, filtri, appaiamento
│   ├── check_leakage.py     verifica degli artefatti residui
│   ├── features.py          estrazione delle 30 feature
│   ├── models.py            modelli e split per gruppo
│   └── evaluation.py        metriche e matrice di confusione
├── notebooks/
│   ├── 01_eda.ipynb                 esplorazione del corpus
│   ├── 02_features.ipynb            documentazione delle scelte sulle feature
│   ├── 03_models.ipynb              addestramento e confronto dei modelli
│   ├── 04_error_analysis.ipynb      analisi dei falsi positivi e negativi
│   └── 05_generalizzazione.ipynb    leave-one-domain-out, sensibilità, post-editing
└── results/
    ├── figures/
    └── tables/
```

I file con prefisso `1_` in `results/` corrispondono alla prima esecuzione,
conservata per confronto; quelli con prefisso `2_` o senza prefisso sono i
risultati finali.

---

## Riproduzione

Requisiti: Python 3.10 o superiore e connessione a internet per il primo
download.

```bash
git clone https://github.com/costanzamariastassi/mgt-stylometry.git
cd mgt-stylometry

python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python -m spacy download en_core_web_sm

# prima di proseguire: aggiornare i percorsi assoluti (vedi l'inizio del README)

python src/loading.py         # scarica HC3 in data/raw/
python src/cleaning.py        # produce data/processed/hc3_clean.parquet
python src/check_leakage.py   # termina con errore se un artefatto supera la soglia
python src/features.py        # produce data/processed/hc3_features.parquet (circa 3 minuti)
```

Poi i notebook in ordine, da `01` a `05`. L'analisi di sensibilità nel
notebook `05` richiede circa venti minuti e si attiva impostando
`RIGENERA = True`.

Note:

- HC3 è pubblicato su HuggingFace con uno script di caricamento non più
  supportato da `datasets` 4.x: `loading.py` scarica quindi direttamente i file
  `.jsonl` con `huggingface_hub`.
- Alcuni script contengono percorsi assoluti riferiti al computer
  dell'autrice: vanno aggiornati prima dell'esecuzione, come indicato
  all'inizio di questo README.
- Seed fissato a 42 in tutti i passaggi casuali.

---

## Uso di strumenti di IA

L'uso di strumenti di IA generativa nella scrittura del codice, nella
discussione metodologica e nella preparazione dei materiali è dichiarato in
dettaglio in [`AI_usage.md`](AI_usage.md), insieme ai contributi originali
dell'autrice e alle verifiche svolte di persona.

---

## Riferimenti

- Guo, B., Zhang, X., Wang, Z., Jiang, M., Nie, J., Ding, Y., Yue, J., Wu, Y.
  (2023). *How Close is ChatGPT to Human Experts? Comparison Corpus,
  Evaluation, and Detection*. arXiv:2301.07597.
- Dataset: [Hello-SimpleAI/HC3](https://huggingface.co/datasets/Hello-SimpleAI/HC3)
  su HuggingFace.
- Honnibal, M., Montani, I., Van Landeghem, S., Boyd, A. (2020). *spaCy:
  Industrial-strength Natural Language Processing in Python*.
