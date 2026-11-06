"""Una distinta fatta per prima crea la partita e la convocazione nella parte sportiva; una modifica della distinta aggiorna i convocati."""
import warnings, datetime
warnings.filterwarnings("ignore")
from base_test import prepara, nuovo, db, bottone, campo

f = prepara("t_distinta_convocazione")
nuovo(f, "pagina_dashboard")
c = db()
dom = datetime.date.today() + datetime.timedelta(days=5)
fra = (datetime.date.today() + datetime.timedelta(days=400)).isoformat()
ids = []
for i, n in enumerate(["Bianchi Aldo", "Rossi Mario", "Verdi Gino"]):
    a = c.execute("INSERT INTO anagrafiche (tipo, denominazione, codice_fiscale) VALUES ('SOCIO_CALCIATORE', ?, ?)", [n, f"AAAAAA00A01H50{i}X"]).lastrowid
    c.execute("INSERT INTO tesserati_calcio (anagrafica_id, numero_tessera, categoria, ruolo, gioca, stato) VALUES (?, ?, 'PRIMA_SQUADRA', 'Calciatore', 1, 'ATTIVO')", [a, f"T{i}"])
    c.execute("INSERT INTO certificati_medici (anagrafica_id, tipo, data_rilascio, data_scadenza) VALUES (?, 'AGONISTICO', '', ?)", [a, fra])
    ids.append(a)
c.commit()

at = nuovo(f, "pagina_distinte")
campo(at.date_input, "Data gara").set_value(dom)
campo(at.text_input, "Squadra ospite (2ª nominata)").set_value("Avversari FC")
campo(at.multiselect, "Giocatori convocati").set_value(ids[:2])
bottone(at, "💾 Salva distinta").click().run()
assert not at.exception, at.exception
ev = c.execute("SELECT id, categoria, data, avversario FROM eventi_squadra WHERE tipo = 'PARTITA'").fetchall()
print("partite:", ev)
assert len(ev) == 1 and ev[0][1] == "PRIMA_SQUADRA" and ev[0][2] == str(dom)
conv = sorted(r[0] for r in c.execute("SELECT anagrafica_id FROM presenze_evento WHERE evento_id = ? AND stato = 'CONVOCATO'", [ev[0][0]]))
assert conv == sorted(ids[:2]), conv
assert c.execute("SELECT evento_id FROM distinte_gara").fetchone()[0] == ev[0][0]

# la convocazione si vede nella parte sportiva
at = nuovo(f, "pagina_squadra")
assert any("Convocazioni salvate" in m.value for m in at.markdown), "convocazione non visibile"

# modifica della distinta: il terzo giocatore entra, il primo esce
at = nuovo(f, "pagina_distinte")
at.session_state["dist_sel"] = 1; at.run()
campo(at.multiselect, "Giocatori convocati").set_value([ids[1], ids[2]])
bottone(at, "💾 Salva modifiche alla distinta").click().run()
assert not at.exception, at.exception
conv = sorted(r[0] for r in c.execute("SELECT anagrafica_id FROM presenze_evento WHERE evento_id = ? AND stato = 'CONVOCATO'", [ev[0][0]]))
assert conv == sorted(ids[1:]), conv
assert c.execute("SELECT COUNT(*) FROM eventi_squadra WHERE tipo = 'PARTITA'").fetchone()[0] == 1
print("TUTTO OK")
