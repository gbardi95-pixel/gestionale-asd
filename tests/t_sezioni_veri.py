"""Le tre sezioni della prima nota, spese e soci sulla copia locale dei dati veri."""
import os, warnings
warnings.filterwarnings("ignore")
import copia_locale
assert "TURSO_DATABASE_URL" not in os.environ
import streamlit as st
from streamlit.testing.v1 import AppTest
f = os.path.abspath("app.py")
for pagina, sez in (("pagina_prima_nota", "movimenti"), ("pagina_prima_nota", "mese"), ("pagina_prima_nota", "anno"),
                    ("pagina_spese", None), ("pagina_soci", None), ("pagina_ricevute", None), ("pagina_tesseramento", None)):
    st.cache_data.clear()
    at = AppTest.from_file(f, default_timeout=300)
    at.session_state["autenticato"] = True
    at.session_state["pagina_test"] = pagina
    if sez:
        at.session_state["pn_sezione"] = sez
    at.run()
    print(pagina, sez or "", "ERRORE " + at.exception[0].message[:200] if at.exception else "ok")
