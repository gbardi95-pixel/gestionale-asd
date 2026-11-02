"""Disciplina: importazione del comunicato dalla schermata (PDF inventato, generato qui) fino alla registrazione nel database."""
import io, os, sys, tempfile, warnings
warnings.filterwarnings("ignore")
from base_test import prepara, nuovo, db, bottone, campo

SQ = ["ASD ROSSA", "BLU BOYS"]
RIGHE = ["CU 7 del 04/11/2026", "COMITATO TERRITORIALE DI PROVA APS", "CLASSIFICA – GIRONE 1"]
for i, s in enumerate(SQ):
    RIGHE += [str(i + 1), f"{s} 3 1 1 0 0 2 1 1 0"]
RIGHE += ["CLASSIFICA MARCATORI – GIRONE 1", "2 reti ROSSI MARIO ASD ROSSA", " NERI LUCA BLU BOYS",
          "PROVVEDIMENTI DISCIPLINARI – GIRONE 1", "«  DIFFIDATI  »", "ASD ROSSA VERDI PAOLO", "BLU BOYS NERI LUCA",
          "«  SQUALIFICHE DI 1 GIORNATE  »", "ASD ROSSA SCONOSCIUTO ZETA (ART. 222 R.T.N.)",
          "«  AMMENDE  »", "ASD ROSSA AMMENDA DI € 20,00 (ART. 214 R.T.N.)"]
from reportlab.pdfgen import canvas
buf = io.BytesIO()
pdf = canvas.Canvas(buf)
y = 800
for riga in RIGHE:
    pdf.drawString(40, y, riga)
    y -= 16
pdf.save()
percorso = os.path.join(tempfile.gettempdir(), "comunicato_prova.pdf")
open(percorso, "wb").write(buf.getvalue())

f = prepara("t_disciplina_import")
s = open(f, encoding="utf-8").read()
vecchio = 'file = st.file_uploader("Comunicato (PDF)", type="pdf", key="disc_pdf")'
assert vecchio in s
open(f, "w", encoding="utf-8").write(s.replace(vecchio, f'file = type("F", (), {{"getvalue": lambda self: open(r"{percorso}", "rb").read()}})()'))
at = nuovo(f, "pagina_dashboard")
c = db()
ids = {}
for nome in ("Mario Rossi", "Paolo Verdi"):
    aid = c.execute("INSERT INTO anagrafiche (tipo, denominazione) VALUES ('SOCIO_CALCIATORE', ?)", [nome]).lastrowid
    c.execute("INSERT INTO tesserati_calcio (anagrafica_id, numero_tessera, categoria, gioca) VALUES (?, 'T', 'PRIMA_SQUADRA', 1)", [aid])
    ids[nome] = aid
c.commit()

at = nuovo(f, "pagina_squadra")
sel = campo(at.selectbox, "Il nome della tua società")
print("squadre trovate:", sel.options)
assert sel.options == SQ
sel.set_value("ASD ROSSA").run()
assert not at.exception, at.exception
print("avvisi:", [w.value for w in at.warning])
persone = [x for x in at.selectbox if x.key and x.key.startswith("disc_ab_")]
print("voci da abbinare:", [(x.key, x.value) for x in persone])
assert len(persone) == 3  # diffida, squalifica, reti: nessun dato di BLU BOYS
assert persone[0].value == ids["Paolo Verdi"] and persone[1].value is None and persone[2].value == ids["Mario Rossi"]
bottone(at, "💾 Registra nel programma").click().run()
assert not at.exception, at.exception
print([ (r) for r in c.execute("SELECT tipo, anagrafica_id, importo FROM provvedimenti_disciplinari ORDER BY id").fetchall()])
tipi = [r[0] for r in c.execute("SELECT tipo FROM provvedimenti_disciplinari").fetchall()]
assert sorted(tipi) == ["AMMENDA", "DIFFIDA"], tipi
assert c.execute("SELECT numero, data FROM comunicati_disciplina").fetchall() == [(7, "2026-11-04")]
assert c.execute("SELECT anagrafica_id, reti FROM reti_comunicato").fetchall() == [(ids["Mario Rossi"], 2)]
assert c.execute("SELECT valore FROM impostazioni WHERE chiave = 'nome_nei_comunicati'").fetchone()[0] == "ASD ROSSA"
# secondo import dello stesso comunicato: nessun doppione
at = nuovo(f, "pagina_squadra")
campo(at.selectbox, "Il nome della tua società").set_value("ASD ROSSA").run()
bottone(at, "💾 Registra nel programma").click().run()
assert c.execute("SELECT COUNT(*) FROM provvedimenti_disciplinari").fetchone()[0] == 2
print("TUTTO OK")
