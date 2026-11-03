"""Dashboard ridotta dell'allenatore: certificati prima della prossima partita, squalificati e diffidati, statistiche aggregate."""
import datetime
import warnings
warnings.filterwarnings("ignore")
import streamlit as st
from streamlit.testing.v1 import AppTest
from base_test import prepara, nuovo, db

f = prepara("t_dash_all", 'APP_PASSWORD = "prova"\nNOME_SOCIETA = "ASD Prova"\nACCESSI_PERSONALI = true\n')
nuovo(f, "pagina_dashboard")
c = db()
oggi = datetime.date.today()
partita = oggi + datetime.timedelta(days=5)
ids = {}
for nome, scad in (("Mario Valido", oggi + datetime.timedelta(days=200)), ("Luigi Scaduto", oggi - datetime.timedelta(days=3)),
                   ("Paolo InScadenza", oggi + datetime.timedelta(days=2)), ("Carlo Senza", None), ("Sergio Squalificato", oggi + datetime.timedelta(days=200)),
                   ("Dino Diffidato", oggi + datetime.timedelta(days=200))):
    aid = c.execute("INSERT INTO anagrafiche (tipo, denominazione) VALUES ('SOCIO_CALCIATORE', ?)", [nome]).lastrowid
    c.execute("INSERT INTO tesserati_calcio (anagrafica_id, numero_tessera, categoria, gioca) VALUES (?, 'T', 'PRIMA_SQUADRA', 1)", [aid])
    if scad:
        c.execute("INSERT INTO certificati_medici (anagrafica_id, tipo, data_rilascio, data_scadenza, stato_idoneita) VALUES (?, 'AGONISTICO', '2025-01-01', ?, 'IDONEO')", [aid, str(scad)])
    ids[nome] = aid
c.execute("INSERT INTO eventi_squadra (tipo, data, categoria, avversario) VALUES ('PARTITA', ?, 'PRIMA_SQUADRA', 'Avversari Prova')", [str(partita)])
ev = c.execute("INSERT INTO eventi_squadra (tipo, data, categoria) VALUES ('PARTITA', ?, 'PRIMA_SQUADRA')", [str(oggi - datetime.timedelta(days=7))]).lastrowid
c.execute("INSERT INTO tabellino_giocatori (evento_id, anagrafica_id, titolare, reti, ammonizioni) VALUES (?, ?, 1, 2, 1)", [ev, ids["Mario Valido"]])
cu = c.execute("INSERT INTO comunicati_disciplina (numero, data) VALUES (9, ?)", [str(oggi - datetime.timedelta(days=1))]).lastrowid
c.execute("INSERT INTO provvedimenti_disciplinari (comunicato_id, anagrafica_id, tipo, giornate) VALUES (?, ?, 'SQUALIFICA_GIORNATE', 2)", [cu, ids["Sergio Squalificato"]])
c.execute("INSERT INTO provvedimenti_disciplinari (comunicato_id, anagrafica_id, tipo) VALUES (?, ?, 'DIFFIDA')", [cu, ids["Dino Diffidato"]])
ev2 = c.execute("INSERT INTO eventi_squadra (tipo, data, categoria) VALUES ('PARTITA', ?, 'PRIMA_SQUADRA')", [str(oggi - datetime.timedelta(days=14))]).lastrowid
for e in (ev, ev2):
    c.execute("INSERT OR REPLACE INTO tabellino_giocatori (evento_id, anagrafica_id, titolare, reti, ammonizioni) VALUES (?, ?, 1, 0, 1)", [e, ids["Carlo Senza"]])
c.execute("INSERT INTO utenti (id, nome_utente, nome, ruolo, squadre, password_hash, cambio_password) VALUES (1, 'mister', 'Mister', 'ALLENATORE', 'PRIMA_SQUADRA', 'x', 0)")
c.commit()

st.cache_data.clear()
at = AppTest.from_file(f, default_timeout=120)
at.session_state["autenticato"] = True
at.session_state["utente"] = {"id": 1, "nome_utente": "mister", "nome": "Mister", "ruolo": "ALLENATORE", "squadre": ["PRIMA_SQUADRA"], "cambio_password": False}
at.session_state["pagina_test"] = "pagina_dashboard"
at.run()
assert not at.exception, at.exception
tabelle = {i: t.value for i, t in enumerate(at.dataframe)}
testo = " ".join(m.value for m in at.markdown)
print(tabelle)
cert = tabelle[0]
assert set(cert["Giocatore"]) == {"Luigi Scaduto", "Paolo InScadenza", "Carlo Senza"}, cert
assert list(tabelle[1]["⛔ Squalificati (non disponibili)"]) == ["Sergio Squalificato"]
assert list(tabelle[2]["⚠️ A rischio: alla prossima ammonizione scatta la squalifica"]) == ["Dino Diffidato", "Carlo Senza"]
metriche = {m.label: m.value for m in at.metric}
print(metriche)
assert metriche["Reti"] == "2" and metriche["Ammonizioni"] == "3" and metriche["Partite con tabellino"] == "2"
assert not any("Incassi" in m.value or "IVA" in m.value for m in at.markdown)
print("TUTTO OK")
