# Meteo GUI

Piccola applicazione desktop in Python con interfaccia grafica (`tkinter`) per visualizzare il meteo di una città usando le API di **Open-Meteo**.

L'app permette di:

- cercare una città per nome
- visualizzare le condizioni meteo attuali
- vedere le previsioni giornaliere per i prossimi 7 giorni
- salvare l'ultima città cercata e ricaricarla rapidamente al riavvio

## Caratteristiche

- Interfaccia grafica semplice e leggera
- Nessuna API key richiesta
- Ricerca città tramite geocoding Open-Meteo
- Meteo attuale:
  - temperatura
  - temperatura percepita
  - umidità relativa
  - vento
  - precipitazione
  - descrizione della condizione meteo
- Previsioni giornaliere:
  - data
  - condizione meteo
  - temperatura minima
  - temperatura massima
  - probabilità di pioggia
  - alba
  - tramonto
- Salvataggio automatico dell'ultima città usata in un file JSON locale

## Tecnologie usate

- Python 3
- `tkinter` per la GUI
- `requests` per le chiamate HTTP
- Open-Meteo Geocoding API
- Open-Meteo Forecast API

## Requisiti

- Python 3.9 o superiore consigliato
- Connessione Internet attiva

## Installazione

Clona o copia il progetto in una cartella locale.

Installa la dipendenza necessaria:

```bash
pip install requests
```

## Avvio

Esegui il file Python principale:

```bash
python weather_gui_openmeteo.py
```

## Struttura del progetto

```text
.
├── weather_gui_openmeteo.py
├── weather_config.json   # creato automaticamente al primo utilizzo
└── README.md
```

## Come funziona

### 1. Inserimento città
L'utente inserisce il nome di una città nel campo di ricerca e preme **Cerca**.

### 2. Geocoding
L'app usa l'API di geocoding di Open-Meteo per convertire il nome della città in coordinate geografiche (`latitudine`, `longitudine`).

### 3. Download dati meteo
Usando le coordinate ottenute, l'app interroga l'API forecast di Open-Meteo e scarica:

- meteo attuale
- previsioni giornaliere fino a 7 giorni

### 4. Visualizzazione nella GUI
I dati vengono mostrati nella finestra tramite:

- una sezione riepilogativa per il meteo attuale
- una tabella con le previsioni giornaliere

### 5. Salvataggio ultima città
L'ultima città cercata viene salvata nel file:

```text
weather_config.json
```

Al successivo avvio, l'app può ricaricarla automaticamente o tramite il pulsante **Usa ultima città**.

## File di configurazione

L'app crea automaticamente un file `weather_config.json` nella cartella del progetto.

Esempio:

```json
{
  "last_city": "Pisa"
}
```

Questo file viene usato per memorizzare l'ultima città selezionata.

## Note importanti

- Il progetto usa **solo Open-Meteo**
- Non usa provider multipli
- Non rileva automaticamente la posizione attuale del dispositivo
- Per ottenere il meteo di una località è necessario inserire almeno una città manualmente

## Possibili miglioramenti futuri

- rilevamento automatico della posizione
- gestione città preferite
- aggiornamento automatico ogni N minuti
- icone meteo
- tema grafico più moderno
- supporto a più lingue
- ricerca multipla in finestre o schede separate
- esportazione delle previsioni

## Esempio d'uso

1. Avvia il programma
2. Inserisci `Pisa`, `Milano`, `Roma` o qualsiasi altra città
3. Premi **Cerca**
4. Visualizza:
   - meteo attuale
   - previsioni dei prossimi 7 giorni
5. Chiudi e riapri l'app: l'ultima città resterà disponibile

## Dipendenze

Installazione minima:

```bash
pip install requests
```

`tkinter` normalmente è già incluso con Python nelle installazioni standard.

## Licenza

Puoi usare e modificare questo progetto liberamente per scopi personali o didattici.
