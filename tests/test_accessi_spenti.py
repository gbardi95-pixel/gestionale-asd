from base_test import prepara, nuovo, db, bottone, campo
from streamlit.testing.v1 import AppTest
import streamlit as st
f = prepara("t_spenti")
st.cache_data.clear()
at = AppTest.from_file(f, default_timeout=120); at.run()
print("login:", [t.label for t in at.text_input], [i.value[:30] for i in at.info])
campo(at.text_input, "Password").set_value("prova"); bottone(at, "Entra").click().run(); assert not at.exception, at.exception
print("dentro:", at.session_state["autenticato"], [s.value for s in at.subheader][:1], "| barra:", [m.value[:20] for m in at.sidebar.markdown])
c = db()
# un utente nel db non deve poter entrare né cambiare nulla finché l'interruttore è spento
from modules import utenti
c.execute("INSERT INTO utenti (nome_utente, nome, ruolo, password_hash, cambio_password) VALUES ('mario', 'Mario', 'CONSULTAZIONE', ?, 0)", [utenti.cifra_password("Password123")]); c.commit()
st.cache_data.clear(); at2 = AppTest.from_file(f, default_timeout=120); at2.run()
print("login con utenti presenti:", [t.label for t in at2.text_input])
# salvataggio e registro
at.session_state["pagina_test"] = "registra_backup"; at.run()
at.session_state["pagina_test"] = "pagina_utenti"; at.run(); assert not at.exception, at.exception
print("pagina registro:", [s.value for s in at.subheader], "| schede:", len(at.tabs), "| righe:", len(at.dataframe[0].value))
print(at.dataframe[0].value.to_string())
print("TUTTO OK")
