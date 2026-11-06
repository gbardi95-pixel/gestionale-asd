"""Disciplina: l'allenatore vede i provvedimenti dei giocatori delle sue squadre, ma non registra i debiti delle ammende; la segreteria sì."""
import warnings
warnings.filterwarnings("ignore")
import streamlit as st
from streamlit.testing.v1 import AppTest
from base_test import prepara, nuovo, db

f = prepara("t_disciplina_ruoli", 'APP_PASSWORD = "prova"\nNOME_SOCIETA = "ASD Prova"\nACCESSI_PERSONALI = true\n')
nuovo(f, "pagina_dashboard")
c = db()
ids = {}
for nome, cat in (("Andrea Gialli", "PRIMA_SQUADRA"), ("Luca Juniores", "JUNIORES")):
    aid = c.execute("INSERT INTO anagrafiche (tipo, denominazione) VALUES ('SOCIO_CALCIATORE', ?)", [nome]).lastrowid
    c.execute("INSERT INTO tesserati_calcio (anagrafica_id, numero_tessera, categoria, gioca) VALUES (?, 'T', ?, 1)", [aid, cat])
    ids[nome] = aid
cu = c.execute("INSERT INTO comunicati_disciplina (numero, data) VALUES (7, '2026-10-30')").lastrowid
c.execute("INSERT INTO provvedimenti_disciplinari (comunicato_id, anagrafica_id, tipo, giornate) VALUES (?, ?, 'SQUALIFICA_GIORNATE', 2)", [cu, ids["Andrea Gialli"]])
c.execute("INSERT INTO provvedimenti_disciplinari (comunicato_id, anagrafica_id, tipo) VALUES (?, ?, 'AMMONIZIONE')", [cu, ids["Luca Juniores"]])
c.execute("INSERT INTO provvedimenti_disciplinari (comunicato_id, tipo, importo) VALUES (?, 'AMMENDA', 30)", [cu])
for i, (ruolo, squadre) in enumerate((("ALLENATORE", "PRIMA_SQUADRA"), ("SEGRETERIA", None)), 1):
    c.execute("INSERT INTO utenti (id, nome_utente, nome, ruolo, squadre, password_hash, cambio_password) VALUES (?, ?, ?, ?, ?, 'x', 0)",
              [i, ruolo.lower(), ruolo, ruolo, squadre])
c.commit()


def apri(i, ruolo, squadre):
    st.cache_data.clear()
    at = AppTest.from_file(f, default_timeout=120)
    at.session_state["autenticato"] = True
    at.session_state["utente"] = {"id": i, "nome_utente": ruolo.lower(), "nome": ruolo, "ruolo": ruolo, "squadre": squadre, "cambio_password": False}
    at.session_state["pagina_test"] = "pagina_squadra"
    at.session_state["squadra_scheda"] = "⚖️ Disciplina"
    at.run()
    assert not at.exception, at.exception
    return at


at = apri(1, "ALLENATORE", ["PRIMA_SQUADRA"])
reg = [x for x in at.dataframe if "Provvedimento" in x.value.columns][0].value
print(reg.to_string())
assert set(reg["Persona"]) == {"Andrea Gialli", "Società"}
assert not [b for b in at.button if b.label.startswith("➕ Registra il debito")]
assert any("Se ne occupa la segreteria" in i.value for i in at.info)

at = apri(2, "SEGRETERIA", [])
reg = [x for x in at.dataframe if "Provvedimento" in x.value.columns][0].value
assert set(reg["Persona"]) == {"Andrea Gialli", "Luca Juniores", "Società"}
assert [b for b in at.button if b.label.startswith("➕ Registra il debito")]
print("TUTTO OK")
