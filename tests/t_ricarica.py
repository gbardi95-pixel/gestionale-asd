from base_test import prepara
from streamlit.testing.v1 import AppTest
f = prepara("t_ricarica")
at = AppTest.from_file(f, default_timeout=120); at.session_state["autenticato"] = True; at.run()
[b for b in at.sidebar.button if "Ricarica" in b.label][0].click().run()
print("ricarica:", "ERRORE " + str(at.exception) if at.exception else "ok")
