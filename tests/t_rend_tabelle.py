import os, warnings
warnings.filterwarnings("ignore")
import copia_locale
assert "TURSO_DATABASE_URL" not in os.environ
import streamlit as st
from streamlit.testing.v1 import AppTest
st.cache_data.clear()
at = AppTest.from_file(os.path.abspath("app.py"), default_timeout=300)
at.session_state["autenticato"] = True
at.session_state["pagina_test"] = "pagina_prima_nota"
at.session_state["pn_sezione"] = "anno"
at.run()
assert not at.exception, at.exception
print([(m.label, m.value) for m in at.metric])
for d in at.dataframe[:2]:
    v = d.value
    print(list(v.columns), len(v), "totale", round(v["Importo (€)"].sum(), 2))
