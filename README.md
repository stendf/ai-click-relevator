# Click-Relevator

Piccolo script per macOS che rileva un triplo clic sinistro, acquisisce uno screenshot e chiede a un modello visivo su OpenRouter di scegliere una risposta A/B/C/D. La scelta viene inviata a un ESP8266, che la segnala facendo lampeggiare il LED integrato.

## Requisiti

- Python 3 e dipendenze `requests` e `pynput`.
- Una API key OpenRouter e un modello vision configurati in [`config.py`](config.py).
- ESP8266 con il firmware [`nodemcu/nodemcu.ino`](nodemcu/nodemcu.ino), collegato alla stessa rete Wi-Fi del Mac.

## Avvio

1. Installa le dipendenze: `python3 -m pip install requests pynput`.
2. Inserisci la tua API key OpenRouter in [`config.py`](config.py). Non condividere né committare la chiave.
3. Imposta SSID e password Wi-Fi nel firmware, caricalo sull'ESP8266 e avvialo.
4. Avvia lo script: `python3 main.py`.
5. Fai tre clic sinistri entro mezzo secondo. Al primo utilizzo, consenti a macOS l'accesso richiesto per acquisizione schermo e monitoraggio input.

Gli screenshot vengono salvati in `~/Pictures/TripleClick`. L'ESP8266 viene cercato automaticamente sulla rete tramite UDP.
