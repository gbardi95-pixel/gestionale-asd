"""Calendario delle partite dal file Excel scaricato dal sito della lega (Sportbit, «Calendario per singola squadra»):
giornata, numero gara, squadre, data, ora e campo. Da qui partono convocazioni e distinte già compilate.

Il file ha un blocco di due righe per partita: nella prima giornata (es. «1 A»), squadra di casa, squadra ospite e data
(«sabato 26/09/2026»); nella seconda numero gara, campo e ora. Se la lega usa un altro modello, `leggi_calendario` lo segnala."""
import io
import re
from collections import Counter

_GIORNATA = re.compile(r"^\s*(\d+)\s*([AR])?\s*$", re.I)
_DATA = re.compile(r"(\d{2})/(\d{2})/(\d{4})")
_ORA = re.compile(r"(\d{1,2})[:.](\d{2})")


def leggi_calendario(contenuto):
    """Partite del file Excel (byte).

    Restituisce {squadra, competizione, partite: [{giornata, numero_gara, casa, ospite, data (AAAA-MM-GG), ora, campo, in_casa, avversario}]}.
    Solleva ValueError con un messaggio comprensibile se il file non ha la struttura prevista."""
    from openpyxl import load_workbook
    try:
        foglio = load_workbook(io.BytesIO(contenuto), data_only=True).active
    except Exception as ex:
        raise ValueError(f"Non riesco a leggere il file Excel ({ex}).") from ex
    righe = [[(str(c).strip() if c is not None else "") for c in r] for r in foglio.iter_rows(min_col=1, max_col=12, values_only=True)]
    competizione = next((c for r in righe[:7] for c in r if c), "")
    partite = []
    for i, r in enumerate(righe[:-1]):
        # colonne dopo il foglio: B giornata, C casa, E ospite, F data (seconda riga: B numero gara, C campo, F ora)
        if len(r) < 6 or not _GIORNATA.match(r[1]) or not r[2] or not r[4]:
            continue
        data = _DATA.search(r[5])
        if not data:
            continue
        sotto = righe[i + 1]
        ora = _ORA.search(sotto[5]) if len(sotto) > 5 else None
        partite.append({
            "giornata": r[1], "numero_gara": sotto[1] if len(sotto) > 1 else "", "casa": r[2], "ospite": r[4],
            "data": f"{data.group(3)}-{data.group(2)}-{data.group(1)}",
            "ora": f"{int(ora.group(1)):02d}:{ora.group(2)}" if ora else "", "campo": sotto[2] if len(sotto) > 2 else "",
        })
    if not partite:
        raise ValueError("Nel file non trovo le partite: serve il «Calendario per singola squadra» in Excel scaricato da Sportbit "
                         "(giornata, squadre e data in una riga; numero gara, campo e ora in quella sotto).")
    # la squadra del calendario è quella presente in ogni partita
    frequenze = Counter(nome for p in partite for nome in (p["casa"], p["ospite"]))
    squadra = frequenze.most_common(1)[0][0]
    for p in partite:
        p["in_casa"] = p["casa"] == squadra
        p["avversario"] = p["ospite"] if p["in_casa"] else p["casa"]
    return {"squadra": squadra, "competizione": competizione, "partite": partite}
