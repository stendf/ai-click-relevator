# Click-Relevator

Applicazione per macOS che ascolta il triplo clic sinistro. Acquisisce in memoria **solo la finestra attiva**, invia l'immagine a un modello vision tramite OpenRouter e inoltra la risposta A/B/C/D a un ESP8266. La scheda fa lampeggiare il LED integrato: A = 1 lampeggio, B = 2, C = 3, D = 4.

## Requisiti

- macOS e Python 3
- Una API key OpenRouter e accesso a un modello che accetta immagini
- ESP8266 e computer connessi alla stessa rete Wi-Fi/LAN
- Arduino IDE con il supporto per le schede ESP8266 installato

## Installazione e configurazione

Dalla cartella del progetto, installa le dipendenze Python:

```bash
python3 -m pip install requests pynput Pillow pyobjc-framework-Quartz pyobjc-framework-Cocoa
```

Crea il file di configurazione locale a partire dal modello:

```bash
cp config.example.py config.py
```

Modifica [`config.py`](config.py): inserisci la tua API key OpenRouter in `OPENROUTER_API_KEY` e imposta il modello vision in `IMAGE_MODEL`. Il file è escluso dal controllo versione tramite [`.gitignore`](.gitignore); non pubblicare la chiave.

Apri [`nodemcu/nodemcu.ino`](nodemcu/nodemcu.ino) e sostituisci `NOME_RETE` e `PASSWORD_RETE` con le credenziali Wi-Fi. Seleziona la scheda ESP8266 corretta in Arduino IDE e carica lo sketch. Quando la scheda si connette alla rete, il LED lampeggia una volta per indicare che è pronta.

## Esecuzione

Esegui dalla cartella del progetto:

```bash
python3 main.py
```

Al messaggio di ascolto, fai tre clic sinistri entro mezzo secondo. Al primo avvio, autorizza il terminale o l'applicazione Python nelle impostazioni macOS per il monitoraggio dei clic e la registrazione schermo. Premi `Ctrl+C` per terminare.

Lo screenshot non viene salvato su disco: è acquisito in memoria e inviato a OpenRouter per l'analisi. Lo script cerca l'ESP8266 tramite broadcast UDP sulla porta 4210 e gli invia la risposta via HTTP.


## Note
è necessario che venga prima eseguito main.py e solo dopo venga acceso il NodeMCU