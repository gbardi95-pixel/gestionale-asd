"""Accesso personale con «Ricordami»: la chiave nasce legata all'utente e alla sua password attuale."""
import warnings
warnings.filterwarnings("ignore")
from base_test import prepara, db, campo
import streamlit as st
from streamlit.testing.v1 import AppTest
f = prepara("t_ricordami", 'APP_PASSWORD = "prova"\nNOME_SOCIETA = "ASD Prova"\nACCESSI_PERSONALI = true\n')
at = AppTest.from_file(f, default_timeout=120); at.run()
from modules import utenti
c = db()
c.execute("INSERT INTO utenti (nome_utente, nome, ruolo, password_hash, cambio_password, attivo) VALUES ('mario', 'Mario', 'SEGRETERIA', ?, 0, 1)",
          [utenti.cifra_password("passwordlunga1")]); c.commit()
st.cache_data.clear()
at = AppTest.from_file(f, default_timeout=120); at.run()
campo(at.text_input, "Nome utente").input("mario")
campo(at.text_input, "Password").input("passwordlunga1")
campo(at.checkbox, "Ricordami").check()
[b for b in at.button if b.label == "Entra"][0].click().run()
assert not at.exception, at.exception
r = c.execute("SELECT utente_id, segreto_impronta, scadenza FROM accessi_ricordati").fetchall()
ph = c.execute("SELECT password_hash FROM utenti WHERE nome_utente='mario'").fetchone()[0]
print("chiavi:", len(r), "utente", r[0][0], "| legata alla password attuale:", r[0][1] == utenti.impronta(ph), "| scade", r[0][2][:10])
print("entrato:", at.session_state["autenticato"], at.session_state["utente"]["nome_utente"])
