"""Journal des trades (A7) : entrée, stop, sortie, raison, leçon, verdict du garde-fou.

Un CSV simple, lisible et modifiable à la main. Les heures sont saisies et stockées **en heure
de Paris** (« AAAA-MM-JJ HH:MM »), comme Gauthier les donne. Le journal alimente le garde-fou
(:func:`attempts_today` → point « tentatives ») et le bilan hebdomadaire (:func:`weekly_summary`).

CLI :
    python -m screener.journal add --side short --entry 60985 --stop 61100 --at "2026-11-22 15:40" --why "…"
    python -m screener.journal close 1 --exit 61100 --at "2026-11-22 17:10" --lesson "…"
    python -m screener.journal list
    python -m screener.journal week [--date 2026-11-22]
"""
from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd

DEFAULT_PATH = Path(__file__).resolve().parent.parent / "journal" / "trades.csv"
COLUMNS = ["id", "actif", "sens", "entree_at", "entree", "stop", "taille", "cible",
           "sortie_at", "sortie", "pts", "r", "garde_fou", "raison", "lecon"]
TEXT = ["actif", "sens", "entree_at", "sortie_at", "garde_fou", "raison", "lecon"]


def load(path: Path | str = DEFAULT_PATH) -> pd.DataFrame:
    path = Path(path)
    if not path.exists():
        return pd.DataFrame(columns=COLUMNS)
    df = pd.read_csv(path, dtype={c: "object" for c in TEXT})
    for c in COLUMNS:
        if c not in df:
            df[c] = pd.NA
    for c in TEXT:
        df[c] = df[c].astype("object")
    return df[COLUMNS]


def save(df: pd.DataFrame, path: Path | str = DEFAULT_PATH) -> None:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    df[COLUMNS].to_csv(path, index=False)


def _result(side: str, entry: float, stop: float, exit_: float) -> tuple[float, float]:
    sgn = 1 if side == "long" else -1
    pts = (exit_ - entry) * sgn
    risk = abs(stop - entry)
    return round(pts, 2), round(pts / risk, 2) if risk else float("nan")


def add(*, side: str, entry: float, stop: float, at: str, actif: str = "BTCUSDT.P",
        taille: float | None = None, cible: float | None = None, garde_fou: str = "",
        raison: str = "", exit_: float | None = None, exit_at: str | None = None,
        lecon: str = "", path: Path | str = DEFAULT_PATH) -> int:
    """Ajoute un trade (ouvert, ou déjà clos si ``exit_`` est donné). Renvoie son id."""
    side = side.lower()
    if side not in ("short", "long"):
        raise ValueError("sens = short ou long")
    df = load(path)
    tid = int(df["id"].max()) + 1 if len(df) else 1
    row = dict.fromkeys(COLUMNS, pd.NA)
    row.update(id=tid, actif=actif, sens=side, entree_at=at, entree=entry, stop=stop,
               taille=taille, cible=cible, garde_fou=garde_fou, raison=raison, lecon=lecon)
    if exit_ is not None:
        row.update(sortie_at=exit_at, sortie=exit_)
        row["pts"], row["r"] = _result(side, entry, stop, exit_)
    df = pd.concat([df, pd.DataFrame([row])], ignore_index=True) if len(df) else pd.DataFrame([row])
    save(df, path)
    return tid


def close(tid: int, *, exit_: float, at: str, lecon: str = "",
          path: Path | str = DEFAULT_PATH) -> None:
    df = load(path)
    m = df["id"] == tid
    if not m.any():
        raise KeyError(f"trade {tid} absent du journal")
    r = df[m].iloc[0]
    df.loc[m, "sortie_at"] = at
    df.loc[m, "sortie"] = exit_
    df.loc[m, ["pts", "r"]] = _result(r["sens"], float(r["entree"]), float(r["stop"]), exit_)
    if lecon:
        df.loc[m, "lecon"] = lecon
    save(df, path)


def attempts_today(side: str, day: str, path: Path | str = DEFAULT_PATH) -> int:
    """Nombre de trades déjà pris dans ce sens le jour ``day`` (« AAAA-MM-JJ », heure de Paris)."""
    df = load(path)
    if df.empty:
        return 0
    return int(((df["sens"] == side.lower()) & df["entree_at"].astype(str).str.startswith(day)).sum())


def weekly_summary(day: str | None = None, path: Path | str = DEFAULT_PATH) -> dict:
    """Bilan de la semaine (lundi → dimanche, heure de Paris) contenant ``day`` (défaut :
    aujourd'hui) : nombre de trades, gagnants / perdants, points, R total et moyen, verdicts du
    garde-fou à l'entrée, leçons."""
    df = load(path)
    d = pd.Timestamp(day) if day else pd.Timestamp.now(tz="Europe/Paris").tz_localize(None)
    monday = (d - pd.Timedelta(days=d.dayofweek)).normalize()
    sunday = monday + pd.Timedelta(days=7)
    t = pd.to_datetime(df["entree_at"], errors="coerce")
    w = df[(t >= monday) & (t < sunday)]
    closed = w[w["r"].notna()]
    r = closed["r"].astype(float)
    return {
        "semaine": f"{monday:%d/%m} → {(sunday - pd.Timedelta(days=1)):%d/%m}",
        "trades": len(w),
        "clos": len(closed),
        "gagnants": int((r > 0).sum()),
        "perdants": int((r < 0).sum()),
        "points": round(float(closed["pts"].astype(float).sum()), 2) if len(closed) else 0.0,
        "r_total": round(float(r.sum()), 2) if len(closed) else 0.0,
        "r_moyen": round(float(r.mean()), 2) if len(closed) else float("nan"),
        "garde_fou": w["garde_fou"].fillna("").replace("", "non noté").value_counts().to_dict(),
        "lecons": [x for x in w["lecon"].dropna().astype(str) if x.strip()],
    }


def main(argv=None) -> None:
    ap = argparse.ArgumentParser(description="Journal des trades (heure de Paris).")
    ap.add_argument("--path", default=str(DEFAULT_PATH))
    sub = ap.add_subparsers(dest="cmd", required=True)
    a = sub.add_parser("add")
    a.add_argument("--side", required=True)
    a.add_argument("--entry", type=float, required=True)
    a.add_argument("--stop", type=float, required=True)
    a.add_argument("--at", required=True, help="« AAAA-MM-JJ HH:MM », heure de Paris")
    a.add_argument("--actif", default="BTCUSDT.P")
    a.add_argument("--size", type=float)
    a.add_argument("--target", type=float)
    a.add_argument("--guard", default="", help="verdict du garde-fou à l'entrée")
    a.add_argument("--why", default="")
    c = sub.add_parser("close")
    c.add_argument("id", type=int)
    c.add_argument("--exit", type=float, required=True)
    c.add_argument("--at", required=True)
    c.add_argument("--lesson", default="")
    sub.add_parser("list")
    w = sub.add_parser("week")
    w.add_argument("--date")
    ns = ap.parse_args(argv)
    if ns.cmd == "add":
        tid = add(side=ns.side, entry=ns.entry, stop=ns.stop, at=ns.at, actif=ns.actif,
                  taille=ns.size, cible=ns.target, garde_fou=ns.guard, raison=ns.why, path=ns.path)
        print(f"trade {tid} ajouté")
    elif ns.cmd == "close":
        close(ns.id, exit_=ns.exit, at=ns.at, lecon=ns.lesson, path=ns.path)
        print(f"trade {ns.id} clos")
    elif ns.cmd == "list":
        print(load(ns.path).to_string(index=False))
    else:
        for k, v in weekly_summary(ns.date, ns.path).items():
            print(f"{k:10} {v}")


if __name__ == "__main__":
    main()
