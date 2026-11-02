from base_test import prepara, nuovo, db, bottone, campo
import datetime
f = prepara("t_cert")
at = nuovo(f, "pagina_dashboard")
c = db()
def p(nome, tel, scad):
    aid = c.execute("INSERT INTO anagrafiche (tipo, denominazione, telefono) VALUES ('SOCIO_CALCIATORE', ?, ?)", [nome, tel]).lastrowid
    c.execute("INSERT INTO tesserati_calcio (anagrafica_id, numero_tessera, categoria, gioca) VALUES (?, 'T', 'PRIMA_SQUADRA', 1)", [aid])
    if scad:
        c.execute("INSERT INTO certificati_medici (anagrafica_id, tipo, data_rilascio, data_scadenza, stato_idoneita) VALUES (?, 'AGONISTICO', '', ?, 'IDONEO')", [aid, scad])
oggi = datetime.date.today()
p("Scaduto Sam", "3331112223", (oggi - datetime.timedelta(days=10)).isoformat())
p("Manca Max", None, None)
p("Inscadenza Ivo", "3334445556", (oggi + datetime.timedelta(days=12)).isoformat())
p("Valido Vic", "3337778889", (oggi + datetime.timedelta(days=200)).isoformat())
c.commit()
at = nuovo(f, "pagina_dashboard")
print("expander:", [e.label for e in at.expander])
print("messaggi:", [x.value for x in at.code])
print("link:", [b.proto.url[:45] for b in at.get("link_button")])
at.text_area[0].set_value("Ciao {nome}: certificato {situazione}. {societa}")
bottone(at, "💾 Salva il testo").click().run()
assert not at.exception, at.exception
at = nuovo(f, "pagina_dashboard")
print("nuovo testo:", [x.value for x in at.code][:1])
print("TUTTO OK")
