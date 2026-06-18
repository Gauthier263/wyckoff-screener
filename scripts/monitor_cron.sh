#!/usr/bin/env bash
# monitor_cron.sh — lance UNE analyse (mode --once) puis rend la main.
# Conçu pour être relancé par l'OS (cron / systemd timer / Planificateur Windows).
# Charge les secrets/params depuis scripts/monitor.env, journalise dans .cache/monitor.log.
set -euo pipefail

# Racine du projet = dossier parent de ce script (insensible au cwd du planificateur).
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT="$(dirname "$HERE")"
cd "$ROOT"

# Identifiants + paramètres (facultatif : si absent, on s'en remet aux valeurs par défaut).
[ -f "$HERE/monitor.env" ] && . "$HERE/monitor.env"

SYMBOLS="${WS_SYMBOLS:-BTC/USDT}"
TIMEFRAME="${WS_TIMEFRAME:-1h}"
EXPECT="${WS_EXPECT:-distribution}"
PYTHON="${WS_PYTHON:-python}"

LOG="$ROOT/.cache/monitor.log"
mkdir -p "$ROOT/.cache"

{
  echo "----- $(date '+%Y-%m-%d %H:%M:%S %z') -----"
  # shellcheck disable=SC2086  # on veut le split de WS_SYMBOLS en plusieurs arguments
  "$PYTHON" -m screener.cli --once --symbols $SYMBOLS --timeframe "$TIMEFRAME" --expect "$EXPECT"
} >> "$LOG" 2>&1
