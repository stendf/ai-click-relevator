import base64
import io
import socket
import time

import requests
from PIL import Image
from pynput import mouse
import Quartz
import AppKit

from config import OPENROUTER_API_KEY, IMAGE_MODEL


OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"

ESP8266_DISCOVERY_PORT = 4210
ESP8266_DISCOVERY_TIMEOUT = 2

TRIPLE_CLICK_WINDOW = 0.5
REQUEST_TIMEOUT = 60

click_times = []


def take_screenshot():
    """
    Acquisisce esclusivamente la finestra attiva/frontmost
    direttamente in memoria.

    Non viene creato alcun file sul disco.
    """

    workspace = AppKit.NSWorkspace.sharedWorkspace()
    active_app = workspace.frontmostApplication()

    if active_app is None:
        raise RuntimeError(
            "Impossibile identificare l'applicazione attiva"
        )

    pid = active_app.processIdentifier()

    window_list = Quartz.CGWindowListCopyWindowInfo(
        Quartz.kCGWindowListOptionOnScreenOnly
        | Quartz.kCGWindowListExcludeDesktopElements,
        Quartz.kCGNullWindowID
    )

    window_id = None
    window_name = None
    window_bounds = None

    for window in window_list:

        owner_pid = window.get(
            Quartz.kCGWindowOwnerPID
        )

        if owner_pid != pid:
            continue

        layer = window.get(
            Quartz.kCGWindowLayer,
            -1
        )

        if layer != 0:
            continue

        bounds = window.get(
            Quartz.kCGWindowBounds
        )

        if not bounds:
            continue

        width = bounds.get("Width", 0)
        height = bounds.get("Height", 0)

        if width <= 0 or height <= 0:
            continue

        window_id = window.get(
            Quartz.kCGWindowNumber
        )

        window_name = window.get(
            Quartz.kCGWindowName
        )

        window_bounds = bounds

        break

    if window_id is None:
        raise RuntimeError(
            "Impossibile trovare la finestra attiva"
        )

    print(
        f"Finestra attiva: "
        f"{active_app.localizedName()}"
    )

    if window_name:
        print(
            f"Titolo finestra: {window_name}"
        )

    image = Quartz.CGWindowListCreateImage(
        Quartz.CGRectNull,
        Quartz.kCGWindowListOptionIncludingWindow,
        window_id,
        Quartz.kCGWindowImageBoundsIgnoreFraming
    )

    if image is None:
        raise RuntimeError(
            "Impossibile acquisire la finestra attiva"
        )

    width = Quartz.CGImageGetWidth(image)
    height = Quartz.CGImageGetHeight(image)

    if width <= 0 or height <= 0:
        raise RuntimeError(
            "La finestra attiva ha dimensioni non valide"
        )

    data_provider = Quartz.CGImageGetDataProvider(
        image
    )

    if data_provider is None:
        raise RuntimeError(
            "Data provider della finestra non disponibile"
        )

    data = Quartz.CGDataProviderCopyData(
        data_provider
    )

    if data is None:
        raise RuntimeError(
            "Dati della finestra non disponibili"
        )

    raw_data = bytes(data)

    bytes_per_row = Quartz.CGImageGetBytesPerRow(
        image
    )

    pil_image = Image.frombuffer(
        "RGBA",
        (width, height),
        raw_data,
        "raw",
        "BGRA",
        bytes_per_row,
        1
    )

    png_buffer = io.BytesIO()

    pil_image.save(
        png_buffer,
        format="PNG"
    )

    screenshot = png_buffer.getvalue()

    if not screenshot:
        raise RuntimeError(
            "Screenshot vuoto"
        )

    print(
        f"Screenshot finestra: "
        f"{width}x{height}, "
        f"{len(screenshot):,} bytes"
    )

    return screenshot


def find_esp8266():
    """
    Cerca l'ESP8266 sulla rete tramite UDP broadcast.

    L'ESP8266 risponde con:
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

    sock.settimeout(
        ESP8266_DISCOVERY_TIMEOUT
    )

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

            if response.startswith(
                "NOOKAI_ESP8266"
            ):
                ip = addr[0]

                print(
                    f"ESP8266 trovato: {ip}"
                )

                return ip

    except socket.timeout:
        print(
            "ESP8266 non trovato sulla rete"
        )
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


def ask_ai(image_data):
    """
    Invia lo screenshot della finestra attiva
    direttamente in memoria a OpenRouter.
    """

    print("Invio screenshot all'AI...")

    image_base64 = base64.b64encode(
        image_data
    ).decode("ascii")

    if not image_base64:
        raise RuntimeError(
            "Base64 dello screenshot vuoto"
        )

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

L'immagine allegata mostra la finestra attiva dello schermo.

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
                            "nella finestra attiva. "
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

    print(
        "HTTP:",
        response.status_code
    )

    if response.status_code >= 400:
        print(
            "OpenRouter:",
            response.text
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
        "Screenshot: solo finestra attiva"
    )

    print(
        "Screenshot: memoria (nessun file)"
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