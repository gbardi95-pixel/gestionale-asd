from base_test import prepara, nuovo, db, bottone, campo, vai
import datetime
f = prepara("t_squadra")
at = nuovo(f, "pagina_squadra")
c = db()
oggi = datetime.date.today()
ids = {}
for nome, cat, gioca, scad in (("Alfa Uno", "PRIMA_SQUADRA", 1, (oggi + datetime.timedelta(days=100)).isoformat()),
                               ("Beta Due", "PRIMA_SQUADRA", 1, (oggi - datetime.timedelta(days=5)).isoformat()),
                               ("Gamma Tre", "PRIMA_SQUADRA", 1, (oggi + datetime.timedelta(days=100)).isoformat()),
                               ("Delta Dir", "STAFF", 0, None), ("Junior Uno", "JUNIORES", 1, None)):
    aid = c.execute("INSERT INTO anagrafiche (tipo, denominazione) VALUES ('SOCIO_CALCIATORE', ?)", [nome]).lastrowid
    c.execute("INSERT INTO tesserati_calcio (anagrafica_id, numero_tessera, categoria, gioca) VALUES (?, 'T', ?, ?)", [aid, cat, gioca])
    if scad:
        c.execute("INSERT INTO certificati_medici (anagrafica_id, tipo, data_rilascio, data_scadenza, stato_idoneita) VALUES (?, 'AGONISTICO', '', ?, 'IDONEO')", [aid, scad])
    ids[nome] = aid
c.commit()
at = nuovo(f, "pagina_squadra")
print("squadre:", at.selectbox(key="sq_categoria").options)
ms = campo(at.multiselect, "Convocati")
print("opzioni convocati:", ms.options)
ms.set_value([ids["Alfa Uno"], ids["Gamma Tre"]])
campo(at.text_input, "Avversario").set_value("Squadra Ospite")
campo(at.text_input, "Ora della partita").set_value("15:00")
campo(at.text_input, "Campo").set_value("Stadio Comunale")
campo(at.text_input, "Ora del ritrovo").set_value("13:45")
bottone(at, "💾 Salva la convocazione").click().run()
assert not at.exception, at.exception
print("flash:", [s.value for s in at.success][:1])
print("testo:\n" + at.code[0].value)
print("link:", [b.proto.url[:40] for b in at.get("link_button")])
# presenze: Beta assente, Gamma giustificato
vai(at, "squadra_scheda", "Presenze")
ma = campo(at.multiselect, "Assenti"); ma.set_value([ids["Beta Due"]])
mg = campo(at.multiselect, "Assenti giustificati"); mg.set_value([ids["Gamma Tre"]])
bottone(at, "💾 Salva le presenze").click().run()
assert not at.exception, at.exception
print("flash presenze:", [s.value for s in at.success][:1])
# stesso giorno: correzione (nessun assente)
at = nuovo(f, "pagina_squadra")
vai(at, "squadra_scheda", "Presenze")
print("info:", [i.value[:40] for i in at.info])
print("default assenti:", campo(at.multiselect, "Assenti").value)
campo(at.multiselect, "Assenti").set_value([])
bottone(at, "💾 Salva le presenze").click().run()
print("eventi:", c.execute("SELECT tipo, data, categoria FROM eventi_squadra").fetchall())
print("presenze:", c.execute("SELECT evento_id, anagrafica_id, stato FROM presenze_evento ORDER BY evento_id, anagrafica_id").fetchall())
at = nuovo(f, "pagina_squadra")
vai(at, "squadra_scheda", "Rosa")
print(at.dataframe[0].value.to_string())
vai(at, "squadra_scheda", "Convocazioni")
bottone(at, "🗑️ Elimina questa convocazione").click().run()
print("dopo eliminazione:", c.execute("SELECT COUNT(*) FROM eventi_squadra WHERE tipo = 'PARTITA'").fetchone(), c.execute("SELECT COUNT(*) FROM presenze_evento").fetchone())
print("TUTTO OK")
