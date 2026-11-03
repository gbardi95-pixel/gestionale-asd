"""Registrazione guidata in prima nota (spesa, incasso, spostamento), saldi, 'Da fare' della dashboard, tendine vuote di modifica persona e collaboratore."""
import datetime
from base_test import prepara, nuovo, db, bottone, campo

f = prepara("t_nuove_schermate")
at = nuovo(f, "pagina_prima_nota")
assert not at.exception, at.exception
c = db()


def righe(m):
    return c.execute("SELECT p.codice, r.dare, r.avere FROM righe_prima_nota r JOIN piano_dei_conti p ON p.id = r.sottoconto_id WHERE r.movimento_id = ? ORDER BY r.id", [m]).fetchall()


# spesa pagata: costo in dare, banca in avere
at = nuovo(f, "pagina_prima_nota")
campo(at.number_input, "Importo").set_value(40.0)
bottone(at, "Salva la registrazione").click().run()
assert any("Scegli il tipo" in e.value for e in at.error), [e.value for e in at.error]
campo(at.selectbox, "Tipo di spesa").set_value(campo(at.selectbox, "Tipo di spesa").options[0])
campo(at.number_input, "Importo").set_value(40.0)
bottone(at, "Salva la registrazione").click().run()
assert not at.exception, at.exception
m = c.execute("SELECT MAX(id) FROM movimenti_prima_nota").fetchone()[0]
r = righe(m)
print("spesa:", r)
assert len(r) == 2 and r[0][1] == 40.0 and r[1] == ("10.01.001", 0.0, 40.0)

# saldi in alto
at = nuovo(f, "pagina_prima_nota")
saldi = {x.label: x.value for x in at.metric}
print("saldi:", saldi)
assert saldi["🏦 Banca"] == "€ -40.00"

# dashboard: voci da fare
c.execute("INSERT INTO anagrafiche (tipo, denominazione) VALUES ('FORNITORE', 'Ditta Prova')")
forn = c.execute("SELECT MAX(id) FROM anagrafiche").fetchone()[0]
c.execute("INSERT INTO fatture_passive (fornitore_id, numero_doc, data_doc, causale_spesa, imponibile, iva, totale, categoria_spesa) VALUES (?, '1', '2026-01-01', 'x', 10, 0, 10, '40.01.006')", [forn])
c.commit()
at = nuovo(f, "pagina_dashboard")
assert not at.exception, at.exception
testi = " ".join(m.value for m in at.markdown)
print("da fare:", [t for t in testi.split("\n") if "spese da pagare" in t])
assert "1 spese da pagare" in testi

# modifica persona e collaboratore: partono vuote
aid = c.execute("INSERT INTO anagrafiche (tipo, denominazione, codice_fiscale) VALUES ('SOCIO_CALCIATORE', 'Rossi Luca', 'RSSLCU12A01H501X')").lastrowid
c.execute("INSERT INTO tesserati_calcio (anagrafica_id, numero_tessera, categoria) VALUES (?, 'T1', 'JUNIORES')", [aid])
cid = c.execute("INSERT INTO anagrafiche (tipo, denominazione) VALUES ('COLLABORATORE_SPORTIVO', 'Mister Uno')").lastrowid
c.execute("INSERT INTO collaboratori_sportivi (anagrafica_id, mansione, tipo_contratto) VALUES (?, 'Allenatore', 'CO.CO.CO_SPORTIVO')", [cid])
c.commit()
at = nuovo(f, "pagina_soci")
assert not at.exception, at.exception
sel = campo(at.selectbox, "Seleziona Persona da Modificare")
assert sel.value is None
sel.set_value(sel.options[0]).run()
assert not at.exception, at.exception
at = nuovo(f, "pagina_lavoro_sportivo")
assert not at.exception, at.exception
sel = campo(at.selectbox, "Collaboratore")
assert sel.value is None
sel.set_value(sel.options[0]).run()
assert not at.exception, at.exception
print("TUTTO OK")
