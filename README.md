# Click-Relevator

Script per macOS che, al triplo clic sinistro, cattura lo schermo e invia lo screenshot a un modello visivo tramite OpenRouter. La risposta A/B/C/D viene poi inviata via rete a un ESP8266, che fa lampeggiare il LED integrato.

## Requisiti

- macOS e Python 3
- Una API key OpenRouter
- Scheda ESP8266 collegata alla stessa rete Wi-Fi del computer
- Arduino IDE con supporto per ESP8266

## Installazione e configurazione

Installa i pacchetti Python richiesti:

```bash
python3 -m pip install requests pynput Pillow pyobjc-framework-Quartz pyobjc-framework-Cocoa
```

Crea il file di configurazione locale copiando [`config.example.py`](config.example.py), quindi inserisci la tua API key OpenRouter e, se necessario, scegli il modello vision:

```bash
cp config.example.py config.py
```

Non condividere né pubblicare la tua API key.

Apri [`nodemcu/nodemcu.ino`](nodemcu/nodemcu.ino) e imposta SSID e password della rete Wi-Fi. Carica il firmware sull'ESP8266 tramite Arduino IDE e accendi la scheda.

## Avvio

Esegui dalla cartella del progetto:

```bash
python3 main.py
```

Quando compare il messaggio di ascolto, fai tre clic sinistri entro mezzo secondo. Al primo avvio, concedi a Python i permessi macOS necessari per monitorare i clic e acquisire lo schermo. Gli screenshot vengono salvati in `~/Pictures/TripleClick`; l'ESP8266 viene individuato automaticamente sulla rete.
