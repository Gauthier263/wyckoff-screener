"""
notify.py — Canaux d'alerte pour le mode suivi (monitor.py).

Volontairement sans dépendance externe : Telegram via l'API HTTP (urllib stdlib).
Le token et le chat-id se lisent depuis l'environnement (TG_BOT_TOKEN / TG_CHAT_ID)
ou la config. Si rien n'est configuré, l'envoi est un no-op silencieux : le mode
suivi continue de fonctionner en console seule.

Pour obtenir les identifiants :
  1. Créer un bot via @BotFather → récupère le token (TG_BOT_TOKEN).
  2. Écrire un message au bot, puis ouvrir
     https://api.telegram.org/bot<TOKEN>/getUpdates → champ chat.id (TG_CHAT_ID).
"""
from __future__ import annotations

import os
from urllib.parse import urlencode
from urllib.request import Request, urlopen


def telegram_configured(token: str | None = None, chat_id: str | None = None) -> bool:
    token = token or os.getenv("TG_BOT_TOKEN")
    chat_id = chat_id or os.getenv("TG_CHAT_ID")
    return bool(token and chat_id)


def send_telegram(text: str, token: str | None = None, chat_id: str | None = None,
                  timeout: float = 10.0) -> bool:
    """Envoie `text` sur Telegram. Renvoie True si l'envoi a réussi.

    No-op silencieux (renvoie False) si le bot n'est pas configuré ou en cas
    d'erreur réseau — une alerte ratée ne doit jamais casser la boucle de suivi.
    """
    token = token or os.getenv("TG_BOT_TOKEN")
    chat_id = chat_id or os.getenv("TG_CHAT_ID")
    if not token or not chat_id:
        return False
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    data = urlencode({
        "chat_id": chat_id,
        "text": text,
        "parse_mode": "HTML",
        "disable_web_page_preview": "true",
    }).encode()
    try:
        with urlopen(Request(url, data=data), timeout=timeout) as resp:
            return 200 <= resp.status < 300
    except Exception:
        return False
