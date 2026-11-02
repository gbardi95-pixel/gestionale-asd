"""Distinta da convocazione: giocatori in ordine alfabetico, dati della partita precompilati, convocazione non riproposta."""
import warnings, datetime
warnings.filterwarnings("ignore")
from base_test import prepara, nuovo, db, bottone, campo

f = prepara("t_distinta_conv")
at = nuovo(f, "pagina_dashboard")
c = db()
dom = (datetime.date.today() + datetime.timedelta(days=5)).isoformat()
fra = (datetime.date.today() + datetime.timedelta(days=400)).isoformat()
nomi = ["Zeta Zeno", "Bianchi Aldo", "Rossi Mario", "Anselmi Gino"]
ids = []
for i, n in enumerate(nomi):
    a = c.execute("INSERT INTO anagrafiche (tipo, denominazione, codice_fiscale) VALUES ('SOCIO_CALCIATORE', ?, ?)", [n, f"AAAAAA00A01H50{i}X"]).lastrowid
    c.execute("INSERT INTO tesserati_calcio (anagrafica_id, numero_tessera, categoria, ruolo, gioca, stato) VALUES (?, ?, 'PRIMA_SQUADRA', 'Calciatore', 1, 'ATTIVO')", [a, f"T{i}"])
    c.execute("INSERT INTO certificati_medici (anagrafica_id, tipo, data_rilascio, data_scadenza) VALUES (?, 'AGONISTICO', '', ?)", [a, fra if n != "Rossi Mario" else "2020-01-01"])
    ids.append(a)
ev = c.execute("INSERT INTO eventi_squadra (tipo, data, ora, categoria, avversario, luogo) VALUES ('PARTITA', ?, '15:00', 'PRIMA_SQUADRA', 'Avversari FC', 'Campo Prova')", [dom]).lastrowid
for a in ids:
    c.execute("INSERT INTO presenze_evento (evento_id, anagrafica_id, stato) VALUES (?, ?, 'CONVOCATO')", [ev, a])
c.commit()

at = nuovo(f, "pagina_distinte")
sel = campo(at.selectbox, "Distinta da compilare")
print("opzioni:", sel.options)
at.session_state["dist_sel"] = "c%d" % ev; at.run()
assert not at.exception, at.exception
print("ora/campo/ospite:", campo(at.text_input, "Ora").value, campo(at.text_input, "Campo").value, campo(at.text_input, "Squadra ospite").value)
print("giocatori preselezionati:", campo(at.multiselect, "Giocatori convocati").value, "| avvisi:", [w.value[:90] for w in at.warning])
bottone(at, "💾 Salva distinta").click().run()
assert not at.exception, at.exception
print("distinte:", c.execute("SELECT id, evento_id, squadra_ospite FROM distinte_gara").fetchall())
print("ordine righe:", [r[0] for r in c.execute("SELECT nominativo FROM distinte_gara_righe WHERE sezione='GIOCATORE' ORDER BY ordine")])
at = nuovo(f, "pagina_distinte")
print("opzioni dopo il salvataggio:", campo(at.selectbox, "Distinta da compilare").options)
# Word: ordine alfabetico anche con selezione in ordine sparso
import sys; sys.path.insert(0, ".")
at = nuovo(f, "pagina_distinte")
at.session_state["dist_sel"] = 1; at.run()
print("download prima:", [b.label for b in at.get("download_button")])
[b for b in at.button if b.label.startswith("📄 Prepara")][0].click().run()
assert not at.exception, at.exception
print("errori:", [e.value for e in at.error])
print("download dopo:", [b.label for b in at.get("download_button")])
import streamlit as st
pdf = [v for k, v in at.session_state.filtered_state.items() if str(k).startswith("pdf_distinta_")]
print("pdf valido:", bool(pdf) and pdf[0][:4] == b"%PDF", len(pdf[0]) if pdf else 0)
print("ok")
