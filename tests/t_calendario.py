"""Calendario delle partite (Excel di Sportbit, inventato): lettura, registrazione, convocazione di una partita del calendario e distinta già compilata."""
import datetime, io, os, sys, tempfile, warnings
warnings.filterwarnings("ignore")
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from openpyxl import Workbook
from modules import calendario

oggi = datetime.date.today()
GIORNI = ["lunedì", "martedì", "mercoledì", "giovedì", "venerdì", "sabato", "domenica"]


def data_it(d):
    return f"{GIORNI[d.weekday()]} {d.strftime('%d/%m/%Y')}"


PARTITE = [  # (giornata, numero gara, casa, ospite, giorni da oggi, ora, campo)
    ("1 A", "5", "BLU BOYS", "ASD ROSSA", -20, "15:00", "CAMPO UNO - VIA PROVA 1, CITTA (XX)"),
    ("2 A", "13", "ASD ROSSA", "VERDE ALTA", 3, "15:15", "STADIO DUE - VIA ROMA 2, CITTA (XX)"),
    ("3 A", "20", "GIALLI", "ASD ROSSA", 10, "20:45", "CAMPO TRE - VIA ROMA 3, CITTA (XX)"),
]
wb = Workbook()
ws = wb.active
ws["F3"] = "GIRONE 1 - C11 - PROVA"
ws["C8"] = "FASE: UNICO  -  GIRONE: UNICO   SQUADRA "
riga = 10
for g, n, casa, ospite, delta, ora, campo in PARTITE:
    ws[f"B{riga}"], ws[f"C{riga}"], ws[f"E{riga}"], ws[f"F{riga}"] = g, casa, ospite, data_it(oggi + datetime.timedelta(days=delta))
    ws[f"B{riga + 1}"], ws[f"C{riga + 1}"], ws[f"F{riga + 1}"] = n, campo, ora
    riga += 3
buf = io.BytesIO()
wb.save(buf)
XLSX = buf.getvalue()
percorso = os.path.join(tempfile.gettempdir(), "calendario_prova.xlsx")
open(percorso, "wb").write(XLSX)

d = calendario.leggi_calendario(XLSX)
assert d["squadra"] == "ASD ROSSA" and d["competizione"] == "GIRONE 1 - C11 - PROVA" and len(d["partite"]) == 3
p0, p1 = d["partite"][0], d["partite"][1]
assert (p0["in_casa"], p0["avversario"], p0["numero_gara"], p0["giornata"]) == (False, "BLU BOYS", "5", "1 A")
assert (p1["in_casa"], p1["avversario"], p1["ora"], p1["data"]) == (True, "VERDE ALTA", "15:15", (oggi + datetime.timedelta(days=3)).isoformat())
for rotto in (b"non e' un excel",):
    try:
        calendario.leggi_calendario(rotto)
        raise SystemExit("doveva dare errore")
    except ValueError:
        pass
vuoto = Workbook()
vuoto.active["A1"] = "niente"
b2 = io.BytesIO()
vuoto.save(b2)
try:
    calendario.leggi_calendario(b2.getvalue())
    raise SystemExit("doveva dare errore")
except ValueError as ex:
    assert "Sportbit" in str(ex)
print("lettura calendario OK")

from base_test import prepara, nuovo, db, bottone, campo
f = prepara("t_calendario")
s = open(f, encoding="utf-8").read()
vecchio = 'file = st.file_uploader("File Excel del calendario", type=["xlsx"], key="cal_xlsx")'
assert vecchio in s
open(f, "w", encoding="utf-8").write(s.replace(vecchio, f'file = type("F", (), {{"getvalue": lambda self: open(r"{percorso}", "rb").read()}})()'))
nuovo(f, "pagina_dashboard")
c = db()
ids = {}
for nome in ("Mario Rossi", "Paolo Verdi"):
    aid = c.execute("INSERT INTO anagrafiche (tipo, denominazione) VALUES ('SOCIO_CALCIATORE', ?)", [nome]).lastrowid
    c.execute("INSERT INTO tesserati_calcio (anagrafica_id, numero_tessera, categoria, gioca) VALUES (?, 'T', 'PRIMA_SQUADRA', 1)", [aid])
    c.execute("INSERT INTO certificati_medici (anagrafica_id, tipo, data_rilascio, data_scadenza, stato_idoneita) VALUES (?, 'AGONISTICO', '', ?, 'IDONEO')",
              [aid, (oggi + datetime.timedelta(days=300)).isoformat()])
    ids[nome] = aid
c.commit()

at = nuovo(f, "pagina_squadra")
bottone(at, "💾 Registra le partite").click().run()
assert not at.exception, at.exception
righe = c.execute("SELECT numero_gara, avversario, squadra_casa, squadra_ospite, competizione, ora FROM eventi_squadra ORDER BY data").fetchall()
print(righe)
assert len(righe) == 3 and righe[1] == ("13", "VERDE ALTA", "ASD ROSSA", "VERDE ALTA", "GIRONE 1 - C11 - PROVA", "15:15")
# secondo caricamento: partite aggiornate, non doppie (anche se l'ora cambia)
c.execute("UPDATE eventi_squadra SET ora = '10:00' WHERE numero_gara = '13'")
c.commit()
at = nuovo(f, "pagina_squadra")
bottone(at, "💾 Registra le partite").click().run()
assert c.execute("SELECT COUNT(*) FROM eventi_squadra").fetchone()[0] == 3
assert c.execute("SELECT ora FROM eventi_squadra WHERE numero_gara = '13'").fetchone()[0] == "15:15"
print("registrazione calendario OK")

# senza convocati le partite non sono tra le «convocazioni salvate»; compaiono nel menu «Partita da convocare» e in Distinte
at = nuovo(f, "pagina_squadra")
assert any("Nessuna convocazione salvata" in i.value for i in at.info)
partite = campo(at.selectbox, "Partita da convocare")
print("da convocare:", partite.options)
assert len(partite.options) == 3  # fuori calendario + 2 future
at2 = nuovo(f, "pagina_distinte")
sel = campo(at2.selectbox, "Distinta da compilare")
cal_distinte = [o for o in sel.options if "Dal calendario" in str(o)]
print("distinte:", sel.options)
assert len(cal_distinte) == 3  # anche quella di 20 giorni fa, senza distinta

# convocazione di una partita del calendario: gli stessi dati, ora con i convocati; nessuna partita doppia
partite.set_value(partite.options[1]).run()
assert campo(at.text_input, "Avversario").value == "VERDE ALTA" and campo(at.text_input, "Campo").value.startswith("STADIO DUE")
campo(at.multiselect, "Convocati").set_value([ids["Mario Rossi"]])
bottone(at, "💾 Salva la convocazione").click().run()
assert not at.exception, at.exception
assert c.execute("SELECT COUNT(*) FROM eventi_squadra").fetchone()[0] == 3
assert c.execute("SELECT COUNT(*) FROM presenze_evento WHERE stato = 'CONVOCATO'").fetchone()[0] == 1
at = nuovo(f, "pagina_squadra")
assert any("Convocazioni salvate" in m.value for m in at.markdown)
# eliminando la convocazione la partita resta nel calendario
bottone(at, "🗑️ Elimina questa convocazione").click().run()
assert c.execute("SELECT COUNT(*) FROM eventi_squadra").fetchone()[0] == 3
assert c.execute("SELECT COUNT(*) FROM presenze_evento").fetchone()[0] == 0
print("convocazione dal calendario OK")

# distinta dalla partita del calendario: squadre, data, ora e campo già compilati
ev_trasferta = c.execute("SELECT id FROM eventi_squadra WHERE numero_gara = '20'").fetchone()[0]
at2 = nuovo(f, "pagina_distinte")
at2.session_state["dist_sel"] = f"c{ev_trasferta}"
at2.run()
assert not at2.exception, at2.exception
valori = {x.label: x.value for x in at2.text_input}
print({k: v for k, v in valori.items() if k.startswith(("Ora", "Campo", "Squadra", "Competizione"))})
assert valori["Squadra di casa (1ª nominata)"] == "GIALLI" and valori["Squadra ospite (2ª nominata)"] == "ASD ROSSA"
assert valori["Ora"] == "20:45" and valori["Campo"].startswith("CAMPO TRE") and valori["Competizione"] == "GIRONE 1 - C11 - PROVA"
print("TUTTO OK")
