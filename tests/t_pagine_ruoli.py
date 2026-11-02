"""Ogni pagina, per ogni ruolo, sulla copia locale dei dati veri: errori e tempi (prima apertura e riapertura)."""
import os, time, warnings
warnings.filterwarnings("ignore")
import copia_locale
assert "TURSO_DATABASE_URL" not in os.environ
import streamlit as st
from streamlit.testing.v1 import AppTest
from base_test import db
from modules import utenti

open(os.path.join(".streamlit", "secrets.toml"), "w").write(
    'APP_PASSWORD = "prova"\nNOME_SOCIETA = "ASD Prova"\nACCESSI_PERSONALI = true\n')
f = os.path.abspath("app.py")
PAGINE = {"dashboard": "pagina_dashboard", "tesseramento": "pagina_tesseramento", "account": "pagina_account", "soci": "pagina_soci", "distinte": "pagina_distinte",
          "convocazioni": "pagina_squadra", "ricevute": "pagina_ricevute", "sponsor": "pagina_sponsor", "spese": "pagina_spese",
          "collaboratori": "pagina_lavoro_sportivo", "prima-nota": "pagina_prima_nota",
          "preventivo": "pagina_preventivo", "parametri": "pagina_parametri", "piano-dei-conti": "pagina_piano_conti",
          "backup": "pagina_backup", "utenti": "pagina_utenti"}
c = db()
squadra = c.execute("SELECT categoria FROM tesserati_calcio WHERE categoria IS NOT NULL LIMIT 1").fetchone()[0]
for i, ruolo in enumerate(utenti.RUOLI, 1):
    c.execute("INSERT INTO utenti (id, nome_utente, nome, ruolo, squadre, password_hash, cambio_password) VALUES (?, ?, ?, ?, ?, 'x', 0)",
              [i, ruolo.lower(), f"Prova {ruolo}", ruolo, squadra if ruolo == "ALLENATORE" else None])
c.commit()

def apri(ruolo, funzione, at=None):
    i = list(utenti.RUOLI).index(ruolo) + 1
    if at is None:
        st.cache_data.clear()
        at = AppTest.from_file(f, default_timeout=300)
        at.session_state["autenticato"] = True
        at.session_state["utente"] = {"id": i, "nome_utente": ruolo.lower(), "nome": f"Prova {ruolo}", "ruolo": ruolo,
                                      "squadre": [squadra] if ruolo == "ALLENATORE" else [], "cambio_password": False}
    at.session_state["pagina_test"] = funzione
    t = time.time(); at.run(); return at, time.time() - t

problemi = []
for ruolo in utenti.RUOLI:
    permesse = [u for u in PAGINE if utenti.pagina_permessa(ruolo, u)]
    print(f"\n== {ruolo}: {', '.join(permesse)}")
    for url in permesse:
        at, t1 = apri(ruolo, PAGINE[url])
        at, t2 = apri(ruolo, PAGINE[url], at)
        err = at.exception
        if err:
            problemi.append((ruolo, url, err[0].message[:200]))
        if ruolo == "ADMIN" or err:
            print(f"   {url:16s} prima {t1:5.1f}s  riapertura {t2:5.1f}s  {'ERRORE ' + err[0].message[:150] if err else 'ok'}")

# sola consultazione: un salvataggio viene rifiutato
at, _ = apri("CONSULTAZIONE", "registra_backup")
print("\nconsultazione salva?", c.execute("SELECT COUNT(*) FROM impostazioni WHERE chiave='ultimo_backup'").fetchone(),
      [e.value for e in at.error][:1])
# allenatore: niente caricamento del modello Word, solo la sua squadra nelle convocazioni
at, _ = apri("ALLENATORE", "pagina_distinte")
print("allenatore modello Word caricabile?", any("Carica modello" in u.label for u in at.get("file_uploader")))
print("PROBLEMI:", problemi or "nessuno")
