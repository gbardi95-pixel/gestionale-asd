SEGRETI_ACCESSI = chr(10).join(["APP_PASSWORD = \"prova\"", "NOME_SOCIETA = \"ASD Prova\"", "ACCESSI_PERSONALI = true", ""])
from base_test import prepara, nuovo, db, bottone, campo
import datetime
from streamlit.testing.v1 import AppTest
import streamlit as st
f = prepara("t_utenti", segreti=SEGRETI_ACCESSI)

def login_app():
    st.cache_data.clear()
    at = AppTest.from_file(f, default_timeout=120); at.run(); assert not at.exception, at.exception
    return at

# 0. nessun utente: solo password generale
at = login_app()
print("0 senza utenti:", [i.value[:45] for i in at.info], [t.label for t in at.text_input])
campo(at.text_input, "Password generale").set_value("sbagliata"); at.button[0].click().run()
print("  errata:", [e.value for e in at.error])
campo(at.text_input, "Password generale").set_value("prova"); at.button[0].click().run()
print("  generale ok:", at.session_state["autenticato"], "| subheader:", [s.value for s in at.subheader][:1])

c = db()
# 1. creazione utenti dalla pagina (come amministratore con password generale)
for cid in range(1):
    pass
squadra_id = c.execute("INSERT INTO anagrafiche (tipo, denominazione, telefono) VALUES ('SOCIO_CALCIATORE', 'Gioc Prima', '3330000001')").lastrowid
c.execute("INSERT INTO tesserati_calcio (anagrafica_id, numero_tessera, categoria, gioca) VALUES (?, 'T1', 'PRIMA_SQUADRA', 1)", [squadra_id])
j = c.execute("INSERT INTO anagrafiche (tipo, denominazione) VALUES ('SOCIO_CALCIATORE', 'Gioc Juniores')").lastrowid
c.execute("INSERT INTO tesserati_calcio (anagrafica_id, numero_tessera, categoria, gioca) VALUES (?, 'T2', 'JUNIORES', 1)", [j])
c.commit()
password = {}
for nome, nu, ruolo, squadre in (("Presidente Prova", "presidente", "ADMIN", []), ("Mister Prova", "mister", "ALLENATORE", ["PRIMA_SQUADRA"]),
                                 ("Revisore Prova", "revisore", "CONSULTAZIONE", []), ("Senza Squadre", "vuoto", "ALLENATORE", [])):
    at = nuovo(f, "pagina_utenti")
    campo(at.text_input, "Nome e cognome").set_value(nome)
    campo(at.text_input, "Nome utente per entrare").set_value(nu)
    sel = campo(at.selectbox, "Ruolo"); sel.set_value(ruolo)
    if squadre: campo(at.multiselect, "Squadre").set_value(squadre)
    bottone(at, "Crea l'utente").click().run()
    assert not at.exception, at.exception
    if at.code:
        password[nu] = at.code[0].value
    print(f"1 crea {nu}:", "ok" if nu in password else [e.value for e in at.error])
print("  utenti nel db:", c.execute("SELECT nome_utente, ruolo, squadre, cambio_password, substr(password_hash,1,7) FROM utenti").fetchall())
# nome utente doppio / non valido
at = nuovo(f, "pagina_utenti")
campo(at.text_input, "Nome e cognome").set_value("X"); campo(at.text_input, "Nome utente per entrare").set_value("Mister")
bottone(at, "Crea l'utente").click().run(); print("  doppio:", [e.value for e in at.error])

# 2. accesso personale, primo accesso con cambio password
at = login_app()
print("2 form:", [t.label for t in at.text_input])
campo(at.text_input, "Nome utente").set_value("Mister "); campo(at.text_input, "Password").set_value(password["mister"])
bottone(at, "Entra").click().run(); assert not at.exception, at.exception
print("  dopo login:", [i.value[:40] for i in at.info], [t.label for t in at.text_input])
campo(at.text_input, "Nuova password").set_value("corta"); campo(at.text_input, "Ripeti").set_value("corta")
bottone(at, "Salva la password").click().run(); print("  corta:", [e.value for e in at.error])
campo(at.text_input, "Nuova password").set_value("MisterNuova1"); campo(at.text_input, "Ripeti").set_value("MisterNuova1")
bottone(at, "Salva la password").click().run(); assert not at.exception, at.exception
print("  pagina iniziale allenatore:", [s.value for s in at.subheader][:1])
assert [s.value for s in at.subheader][:1] == ["📊 La tua squadra"]
print("  barra:", [m.value for m in at.sidebar.markdown][:1])

# 3. blocco dopo 5 tentativi
at = login_app()
for i in range(5):
    campo(at.text_input, "Nome utente").set_value("revisore"); campo(at.text_input, "Password").set_value("sbagliata")
    bottone(at, "Entra").click().run()
print("3 dopo 5 errori:", [e.value for e in at.error])
campo(at.text_input, "Nome utente").set_value("revisore"); campo(at.text_input, "Password").set_value(password["revisore"])
bottone(at, "Entra").click().run(); print("  anche con password giusta:", [e.value for e in at.error])
c.execute("UPDATE utenti SET bloccato_fino = NULL WHERE nome_utente = 'revisore'"); c.commit()

# 4. sola consultazione: niente salvataggi
at = login_app()
campo(at.text_input, "Nome utente").set_value("revisore"); campo(at.text_input, "Password").set_value(password["revisore"])
bottone(at, "Entra").click().run()
campo(at.text_input, "Nuova password").set_value("Revisore123"); campo(at.text_input, "Ripeti").set_value("Revisore123")
bottone(at, "Salva la password").click().run(); assert not at.exception, at.exception
print("4 revisore:", [s.value for s in at.subheader][:1], [i.value[:50] for i in at.info][:1])
at.session_state["pagina_test"] = "registra_backup"; at.run()
print("  scrittura bloccata:", [e.value for e in at.error], c.execute("SELECT valore FROM impostazioni WHERE chiave='ultimo_backup'").fetchone())

# 5. allenatore senza squadre / distinte filtrate
at = nuovo(f, "pagina_squadra")
uv = c.execute("INSERT INTO utenti (nome_utente, nome, ruolo, password_hash) VALUES ('vuoto', 'Senza Squadre', 'ALLENATORE', 'x')").lastrowid; c.commit()
at.session_state["utente"] = {"id": uv, "nome_utente": "vuoto", "nome": "Senza Squadre", "ruolo": "ALLENATORE", "squadre": [], "cambio_password": False}
at.run(); print("5 senza squadre:", [i.value[:50] for i in at.info])
um = c.execute("SELECT id FROM utenti WHERE nome_utente='mister'").fetchone()[0]
at.session_state["utente"] = {"id": um, "nome_utente": "mister", "nome": "Mister Prova", "ruolo": "ALLENATORE", "squadre": ["PRIMA_SQUADRA"], "cambio_password": False}
at.session_state["pagina_test"] = "pagina_distinte"; at.run(); assert not at.exception, at.exception
print("  distinte, giocatori selezionabili:", campo(at.multiselect, "Giocatori convocati").options)

# 6. disattivazione: chi è dentro viene fatto uscire
c.execute("UPDATE utenti SET attivo = 0 WHERE nome_utente='mister'"); c.commit(); st.cache_data.clear()
at.run(); print("6 disattivato:", at.session_state["autenticato"] if "autenticato" in at.session_state else "uscito", [t.label for t in at.text_input])

# 7. registro attività
print("7 registro:")
for r in c.execute("SELECT utente, pagina, azione FROM registro_attivita ORDER BY id"): print("   ", r)
at = nuovo(f, "pagina_utenti")
print("  tab registro righe:", len(at.dataframe[-1].value))

# 8. backup senza utenti, ripristino non cancella il registro
from modules import backup
copia, conteggi = backup.backup_completo(c, 13)
print("8 tabelle nel backup:", "utenti" in [x["Tabella"] for x in conteggi], "registro" in str(conteggi))
n_reg = c.execute("SELECT COUNT(*) FROM registro_attivita").fetchone()[0]
c.execute("INSERT INTO registro_attivita (quando, utente, azione) VALUES ('2026-10-23 23:59:00', 'x', 'dopo il backup')"); c.commit()
_, tab = backup.leggi_copia(copia); script, attese = backup.script_ripristino(c, tab); c.executescript(script)
print("  registro dopo ripristino:", c.execute("SELECT COUNT(*) FROM registro_attivita").fetchone()[0], "(prima", n_reg + 1, ") utenti:", c.execute("SELECT COUNT(*) FROM utenti").fetchone()[0])
print("TUTTO OK")
