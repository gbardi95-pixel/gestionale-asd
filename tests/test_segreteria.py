SEGRETI_ACCESSI = chr(10).join(["APP_PASSWORD = \"prova\"", "NOME_SOCIETA = \"ASD Prova\"", "ACCESSI_PERSONALI = true", ""])
from base_test import prepara, nuovo, db, bottone, campo
from streamlit.testing.v1 import AppTest
import streamlit as st

f = prepara("t_segreteria", segreti=SEGRETI_ACCESSI)
from modules import utenti
at = nuovo(f, "pagina_utenti")
campo(at.text_input, "Nome e cognome").set_value("Tesoriera Prova")
campo(at.text_input, "Nome utente per entrare").set_value("tesoreria")
campo(at.selectbox, "Ruolo").set_value("SEGRETERIA")
bottone(at, "Crea l'utente").click().run(); pw = at.code[0].value
c = db(); print("creato:", c.execute("SELECT nome_utente, ruolo, squadre FROM utenti").fetchall())
# accesso reale con menu
st.cache_data.clear(); at = AppTest.from_file(f, default_timeout=120); at.run()
campo(at.text_input, "Nome utente").set_value("tesoreria"); campo(at.text_input, "Password").set_value(pw); bottone(at, "Entra").click().run()
campo(at.text_input, "Nuova password").set_value("Tesoreria2026"); campo(at.text_input, "Ripeti").set_value("Tesoreria2026")
bottone(at, "Salva la password").click().run(); assert not at.exception, at.exception
print("pagina iniziale:", [s.value for s in at.subheader][:1], "| barra:", [m.value for m in at.sidebar.markdown][:1])
print("pagine nel menu:", sorted(utenti.PAGINE_RUOLO["SEGRETERIA"]))
print("negate:", [u for u in ("parametri", "utenti") if not utenti.pagina_permessa("SEGRETERIA", u)], "| può salvare:", utenti.puo_scrivere("SEGRETERIA"))
# backup: copia sì, ripristino no
at.session_state["pagina_test"] = "pagina_backup"; at.run(); assert not at.exception, at.exception
print("backup: copia completa", any("Prepara la copia" in b.label for b in at.button), "| ripristino visibile:", any("Ripristino" in m.value for m in at.markdown))
# salvataggio reale: un'impostazione via registra_backup
at.session_state["pagina_test"] = "registra_backup"; at.run()
print("salvataggio:", c.execute("SELECT valore FROM impostazioni WHERE chiave='ultimo_backup'").fetchone(), [e.value for e in at.error])
print("registro:", c.execute("SELECT utente, azione FROM registro_attivita ORDER BY id DESC LIMIT 1").fetchone())
print("TUTTO OK")
at.session_state["pagina_test"] = "pagina_parametri"; at.run(); assert not at.exception, at.exception
print("parametri:", [s.value for s in at.subheader][:1])
