# Suivi périodique — relancé par l'OS (terminal fermé)

Tu **anticipes** un retournement (baissier → *distribution*, haussier → *accumulation*)
sur un symbole et une TF. Le mode `--once` fait **une** analyse de la dernière barre
**clôturée**, alerte si un déclencheur frais tombe, persiste son état, puis rend la main.
L'OS le relance à intervalle fixe : ce n'est pas un suivi continu, c'est une analyse
régulière et systématique. Terminal fermé / PC en veille entre deux runs = sans effet.

## États possibles (une ligne par run dans `.cache/monitor.log`)
- `NONE` — rien d'exploitable (ou schéma contraire à ce que tu anticipes).
- `WATCH` — le schéma attendu se construit (climax / AR / test présents, avancement %).
- `ALERT` — déclencheur frais conforme au biais anticipé : **c'est le moment de regarder**
  (FORCE = SOS/SPRING/LPS côté accumulation ; FAIBLESSE = SOW/UTAD/LPSY côté distribution).
  Une seule alerte par barre clôturée (dédup via `.cache/monitor_<sym>_<tf>.json`).

## Mise en place
```bash
cp scripts/monitor.env.example scripts/monitor.env   # puis remplis TG_BOT_TOKEN / TG_CHAT_ID + params
chmod +x scripts/monitor_cron.sh
scripts/monitor_cron.sh                               # test manuel : doit écrire dans .cache/monitor.log
```

## Linux / macOS — cron
`crontab -e` puis (analyse en haut de chaque heure, ~30 s après la clôture) :
```
1 * * * * /chemin/vers/wyckoff-screener/scripts/monitor_cron.sh
```
Toutes les 4 h :
```
1 */4 * * * /chemin/vers/wyckoff-screener/scripts/monitor_cron.sh
```
> Astuce : aligne le cron sur la TF (`--timeframe 1h` → toutes les heures, `4h` → toutes les 4 h).
> Le wrapper charge `monitor.env`, fixe le bon dossier et journalise — cron n'a aucun env par défaut.

## Linux — systemd timer (alternative robuste à cron)
`~/.config/systemd/user/wyckoff.service` :
```ini
[Service]
Type=oneshot
ExecStart=/chemin/vers/wyckoff-screener/scripts/monitor_cron.sh
```
`~/.config/systemd/user/wyckoff.timer` :
```ini
[Timer]
OnCalendar=hourly
Persistent=true        # rattrape un run manqué si la machine était éteinte
[Install]
WantedBy=timers.target
```
```bash
systemctl --user enable --now wyckoff.timer
systemctl --user list-timers | grep wyckoff
```

## Windows — Planificateur de tâches
```powershell
$action  = New-ScheduledTaskAction -Execute "python" `
           -Argument "-m screener.cli --once --symbols BTC/USDT --timeframe 1h --expect distribution" `
           -WorkingDirectory "C:\chemin\vers\wyckoff-screener"
$trigger = New-ScheduledTaskTrigger -Once -At (Get-Date) `
           -RepetitionInterval (New-TimeSpan -Hours 1)
Register-ScheduledTask -TaskName "WyckoffMonitor" -Action $action -Trigger $trigger
```
Définis `TG_BOT_TOKEN` / `TG_CHAT_ID` en variables d'environnement utilisateur (sinon : alerte console).

## Vérifier / suivre
```bash
tail -f .cache/monitor.log            # flux des runs
cat .cache/monitor_BTC_USDT_1h.json   # dernière barre vue / dernière barre alertée
```
