import base64
import os
import socket
import subprocess
import time

import requests
from pynput import mouse

from config import OPENROUTER_API_KEY, IMAGE_MODEL


OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"

ESP8266_DISCOVERY_PORT = 4210
ESP8266_DISCOVERY_TIMEOUT = 2

SCREENSHOT_DIR = os.path.expanduser("~/Pictures/TripleClick")

TRIPLE_CLICK_WINDOW = 0.5
REQUEST_TIMEOUT = 60

click_times = []


def take_screenshot():
    os.makedirs(SCREENSHOT_DIR, exist_ok=True)

    timestamp = time.strftime("%Y%m%d_%H%M%S")

    filepath = os.path.join(
        SCREENSHOT_DIR,
        f"screenshot_{timestamp}.png"
    )

    subprocess.run(
        [
            "/usr/sbin/screencapture",
            "-x",
            filepath
        ],
        check=True
    )

    return filepath


def find_esp8266():
    """
    Cerca l'ESP8266 sulla rete tramite UDP broadcast.

    L'ESP8266 ascolta sulla porta 4210 e risponde con:
        NOOKAI_ESP8266 <IP>
    """

    sock = socket.socket(
        socket.AF_INET,
        socket.SOCK_DGRAM
    )

    sock.setsockopt(
        socket.SOL_SOCKET,
        socket.SO_BROADCAST,
        1
    )

    sock.settimeout(ESP8266_DISCOVERY_TIMEOUT)

    try:
        print("Cerco ESP8266 sulla rete...")

        sock.sendto(
            b"NOOKAI_DISCOVER",
            (
                "255.255.255.255",
                ESP8266_DISCOVERY_PORT
            )
        )

        while True:
            data, addr = sock.recvfrom(1024)

            response = data.decode(
                "utf-8",
                errors="ignore"
            ).strip()

            if response.startswith("NOOKAI_ESP8266"):
                ip = addr[0]

                print(
                    f"ESP8266 trovato: {ip}"
                )

                return ip

    except socket.timeout:
        print("ESP8266 non trovato sulla rete")
        return None

    except OSError as e:
        print(
            f"Errore discovery ESP8266: {e}"
        )
        return None

    finally:
        sock.close()


def send_to_esp8266(answer):
    """
    Invia A/B/C/D all'ESP8266.

    L'IP viene scoperto dinamicamente ogni volta,
    quindi non dipende da un IP statico.
    """

    answer = answer.strip().upper()

    if len(answer) != 1 or answer not in (
        "A",
        "B",
        "C",
        "D"
    ):
        print(
            f"Risposta non valida per ESP8266: {answer}"
        )
        return

    try:
        esp_ip = find_esp8266()

        if not esp_ip:
            return

        url = f"http://{esp_ip}/{answer}"

        print(
            f"Invio comando {answer} a {esp_ip}"
        )

        response = requests.get(
            url,
            timeout=3
        )

        response.raise_for_status()

        print(
            "Risposta ESP:",
            response.text.strip()
        )

    except requests.RequestException as e:
        print(
            f"Errore comunicazione ESP8266: {e}"
        )


def ask_ai(image_path):
    print("Invio screenshot all'AI...")

    with open(
        image_path,
        "rb"
    ) as file:
        image_base64 = base64.b64encode(
            file.read()
        ).decode("utf-8")

    screenshot = (
        "data:image/png;base64,"
        + image_base64
    )

    headers = {
        "Content-Type": "application/json",
        "Authorization": (
            f"Bearer {OPENROUTER_API_KEY}"
        ),
    }

    payload = {
        "model": IMAGE_MODEL,

        "temperature": 0,

        "messages": [
            {
                "role": "system",

                "content": """
Sei un esperto di AIMMS.

Devi risolvere una domanda a risposta multipla.

L'immagine allegata è uno screenshot dello schermo.

Individua la domanda attualmente visibile e analizza attentamente:

- il testo della domanda;
- tutte le opzioni;
- eventuali immagini contenute nelle opzioni;
- diagrammi, grafici, interfacce o altri elementi visivi presenti nelle risposte.

Devi determinare quale opzione è corretta.

La risposta può essere esclusivamente:

A

B

C

D

Rispondi con UNA SOLA LETTERA.

Non scrivere spiegazioni.

Non scrivere altro testo.
"""
            },

            {
                "role": "user",

                "content": [
                    {
                        "type": "text",

                        "text": (
                            "Risolvi la domanda visibile "
                            "nello screenshot. "
                            "Restituisci esclusivamente "
                            "A, B, C oppure D."
                        )
                    },

                    {
                        "type": "image_url",

                        "image_url": {
                            "url": screenshot
                        }
                    }
                ]
            }
        ]
    }

    response = requests.post(
        OPENROUTER_URL,
        headers=headers,
        json=payload,
        timeout=REQUEST_TIMEOUT
    )

    response.raise_for_status()

    data = response.json()

    content = (
        data["choices"][0]["message"]["content"]
        .strip()
    )

    print(
        "Risposta AI:",
        content
    )

    for char in content.upper():

        if char in (
            "A",
            "B",
            "C",
            "D"
        ):
            return char

    raise ValueError(
        f"Risposta AI non riconosciuta: {content}"
    )


def handle_click(
    x,
    y,
    button,
    pressed
):
    global click_times

    if not pressed:
        return

    if button != mouse.Button.left:
        return

    now = time.monotonic()

    click_times.append(now)

    click_times = [
        t
        for t in click_times
        if now - t <= TRIPLE_CLICK_WINDOW
    ]

    if len(click_times) >= 3:

        click_times.clear()

        print()
        print(
            "=== TRIPLO CLICK RILEVATO ==="
        )

        try:

            screenshot = take_screenshot()

            print(
                "Screenshot:",
                screenshot
            )

            answer = ask_ai(
                screenshot
            )

            send_to_esp8266(
                answer
            )

            print(
                "Risposta:",
                answer
            )

            print()

        except Exception as e:

            print(
                "ERRORE:",
                e
            )

            print()


def main():

    print(
        "==================================="
    )

    print(
        "       CLICK-RELEVATOR"
    )

    print(
        "==================================="
    )

    print()

    print(
        "In ascolto del triplo click sinistro..."
    )

    print(
        "ESP8266: discovery UDP dinamico"
    )

    print(
        "Premi CTRL+C per uscire."
    )

    print()

    with mouse.Listener(
        on_click=handle_click
    ) as listener:

        listener.join()


if __name__ == "__main__":
    main()