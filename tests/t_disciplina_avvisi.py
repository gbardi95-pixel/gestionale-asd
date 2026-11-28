"""Squalifiche e diffide: valgono alla data della gara (compresa), la diffida resta nei comunicati successivi, segnalati anche i dirigenti."""
import datetime
import warnings
warnings.filterwarnings("ignore")
import streamlit as st
from streamlit.testing.v1 import AppTest
from base_test import prepara, nuovo, db, campo, vai

f = prepara("t_disciplina_avvisi", 'APP_PASSWORD = "prova"\nNOME_SOCIETA = "ASD Prova"\nACCESSI_PERSONALI = true\n')
from modules import disciplina as d

# --- regole -------------------------------------------------------------
sq = {"tipo": "SQUALIFICA_GIORNATE", "data_comunicato": "2026-11-25", "numero_comunicato": 10, "giornate": 1, "fino_al": None}
partite = ["2026-11-21", "2026-11-28", "2026-12-05"]
assert d.situazione([sq], "2026-11-28", partite)[0] == "SQUALIFICATO", "il giorno della gara la squalifica vale ancora"
assert d.situazione([sq], "2026-11-29", partite)[0] is None, "scontata dopo la gara"
assert d.situazione([sq], "2026-12-05", partite)[0] is None, "per la gara successiva è già scontata"
assert d.situazione([sq], "2026-11-21", partite)[0] is None, "un comunicato successivo non riguarda una gara precedente"
due = dict(sq, giornate=2)
assert d.situazione([due], "2026-12-05", partite)[0] == "SQUALIFICATO" and d.situazione([due], "2026-12-06", partite)[0] is None
diff = {"tipo": "DIFFIDA", "data_comunicato": "2026-11-04", "numero_comunicato": 7, "giornate": None, "fino_al": None}
assert d.situazione([diff], "2026-12-20", partite)[0] == "DIFFIDATO", "la diffida resta anche se i comunicati successivi non la ripetono"
somma = {"tipo": "SQUALIFICA_SOMMA", "data_comunicato": "2026-11-18", "numero_comunicato": 9, "giornate": 1, "fino_al": None}
assert d.situazione([somma, diff], "2026-11-20", partite)[0] == "SQUALIFICATO"
assert d.situazione([somma, diff], "2026-12-20", partite)[0] is None, "dopo la squalifica per somma la diffida è superata"
nuova = dict(diff, data_comunicato="2026-12-09", numero_comunicato=12)
assert d.situazione([nuova, somma, diff], "2026-12-20", partite)[0] == "DIFFIDATO"
tempo = dict(sq, tipo="SQUALIFICA_TEMPO", fino_al="2026-11-30")
assert d.situazione([tempo], "2026-11-30")[0] == "SQUALIFICATO" and d.situazione([tempo], "2026-12-01")[0] is None
print("regole OK")

# --- schermate: la partita è oggi ---------------------------------------
nuovo(f, "pagina_dashboard")
c = db()
oggi = datetime.date.today()
ids = {}
for nome, cat, gioca in (("Dino Diffidato", "PRIMA_SQUADRA", 1), ("Dario Dirigente", "STAFF", 0), ("Mario Libero", "PRIMA_SQUADRA", 1)):
    aid = c.execute("INSERT INTO anagrafiche (tipo, denominazione) VALUES ('SOCIO_CALCIATORE', ?)", [nome]).lastrowid
    c.execute("INSERT INTO tesserati_calcio (anagrafica_id, numero_tessera, categoria, gioca) VALUES (?, 'T', ?, ?)", [aid, cat, gioca])
    c.execute("INSERT INTO certificati_medici (anagrafica_id, tipo, data_rilascio, data_scadenza, stato_idoneita) VALUES (?, 'AGONISTICO', '2025-01-01', ?, 'IDONEO')",
              [aid, str(oggi + datetime.timedelta(days=200))])
    ids[nome] = aid
ev = c.execute("INSERT INTO eventi_squadra (tipo, data, categoria, avversario) VALUES ('PARTITA', ?, 'PRIMA_SQUADRA', 'Avversari')", [str(oggi)]).lastrowid
inizio_stagione = datetime.date(oggi.year if oggi.month >= 7 else oggi.year - 1, 7, 1)  # stagione sportiva 1/7 - 30/6
for numero, giorni, voci in ((1, 10, [("Dino Diffidato", "DIFFIDA", None)]), (2, 3, [("Dario Dirigente", "SQUALIFICA_GIORNATE", 1)])):
    data_cu = max(oggi - datetime.timedelta(days=giorni), inizio_stagione)
    cu = c.execute("INSERT INTO comunicati_disciplina (numero, data) VALUES (?, ?)", [numero, str(data_cu)]).lastrowid
    for nome, tipo, giornate in voci:
        c.execute("INSERT INTO provvedimenti_disciplinari (comunicato_id, anagrafica_id, tipo, giornate) VALUES (?, ?, ?, ?)", [cu, ids[nome], tipo, giornate])
c.execute("INSERT INTO utenti (id, nome_utente, nome, ruolo, squadre, password_hash, cambio_password) VALUES (1, 'mister', 'Mister', 'ALLENATORE', 'PRIMA_SQUADRA', 'x', 0)")
c.execute("INSERT INTO utenti (id, nome_utente, nome, ruolo, squadre, password_hash, cambio_password) VALUES (2, 'admin', 'Admin', 'ADMIN', '', 'x', 0)")
c.commit()


def come(pagina, utente):
    st.cache_data.clear()
    at = AppTest.from_file(f, default_timeout=120)
    at.session_state["autenticato"] = True
    at.session_state["utente"] = utente
    at.session_state["pagina_test"] = pagina
    at.run()
    assert not at.exception, at.exception
    return at


admin = {"id": 2, "nome_utente": "admin", "nome": "Admin", "ruolo": "ADMIN", "squadre": [], "cambio_password": False}
mister = {"id": 1, "nome_utente": "mister", "nome": "Mister", "ruolo": "ALLENATORE", "squadre": ["PRIMA_SQUADRA"], "cambio_password": False}

# dashboard dell'allenatore: il dirigente squalificato e il diffidato si vedono anche il giorno della gara
at = come("pagina_dashboard", mister)
colonne = {col: list(t.value[col]) for t in at.dataframe for col in t.value.columns}
assert colonne.get("⛔ Squalificati (non disponibili)") == ["Dario Dirigente"], colonne
assert colonne.get("⚠️ A rischio: alla prossima ammonizione scatta la squalifica") == ["Dino Diffidato"], colonne

# distinta della gara di oggi: segnalati nei due elenchi, con avviso per chi è squalificato
at = come("pagina_distinte", admin)
sel = at.selectbox(key="dist_sel")
sel.set_value(f"c{ev}").run()
assert not at.exception, at.exception
giocatori = campo(at.multiselect, "Giocatori convocati")
dirigenti = campo(at.multiselect, "Allenatori e dirigenti")
assert any("Dino Diffidato" in str(o) and "diffidato" in str(o) for o in giocatori.options), giocatori.options
assert any("Dario Dirigente" in str(o) and "squalificato" in str(o) for o in dirigenti.options), dirigenti.options
dirigenti.set_value([ids["Dario Dirigente"]]).run()
assert not at.exception, at.exception
assert any("Dario Dirigente" in w.value and "Squalificato" in w.value for w in at.warning), [w.value for w in at.warning]

# distinta per la settimana dopo: la squalifica di una giornata è scontata con la gara di oggi
campo(at.date_input, "Data gara").set_value(oggi + datetime.timedelta(days=7)).run()
assert not at.exception, at.exception
assert not any("squalificato" in str(o) for o in campo(at.multiselect, "Allenatori e dirigenti").options)
assert any("diffidato" in str(o) for o in campo(at.multiselect, "Giocatori convocati").options)

# la diffida dura la stagione sportiva (anche a cavallo dell'anno, con esercizio contabile su anno solare), non oltre
fine_stagione = datetime.date(inizio_stagione.year + 1, 6, 30)
for data_gara, attesa in ((datetime.date(inizio_stagione.year + 1, 1, 15), True), (fine_stagione, True), (fine_stagione + datetime.timedelta(days=1), False)):
    if data_gara < oggi:
        continue
    c.execute("UPDATE certificati_medici SET data_scadenza = ?", [str(fine_stagione + datetime.timedelta(days=90))])
    c.commit()
    st.cache_data.clear()
    campo(at.date_input, "Data gara").set_value(data_gara).run()
    assert not at.exception, at.exception
    opzioni = campo(at.multiselect, "Giocatori convocati").options
    assert any("Dino Diffidato" in str(o) for o in opzioni), opzioni
    assert any("diffidato" in str(o) for o in opzioni) == attesa, (data_gara, opzioni)

# anche le ammonizioni del tabellino si contano sulla stagione sportiva: restano se nel mezzo inizia un nuovo esercizio contabile
prima = max(inizio_stagione, oggi.replace(day=1) - datetime.timedelta(days=1))
c.execute("INSERT OR REPLACE INTO impostazioni (chiave, valore) VALUES ('mese_inizio_esercizio', ?)", [str(oggi.month)])
vecchia = c.execute("INSERT INTO eventi_squadra (tipo, data, categoria, avversario) VALUES ('PARTITA', ?, 'PRIMA_SQUADRA', 'Altri')", [str(prima)]).lastrowid
c.execute("INSERT INTO tabellino_giocatori (evento_id, anagrafica_id, titolare, minuti, reti, assist, ammonizioni, espulso) VALUES (?, ?, 1, 90, 0, 0, 2, 0)",
          [vecchia, ids["Mario Libero"]])
c.commit()
at = come("pagina_dashboard", mister)
a_rischio = [x for t in at.dataframe for col in t.value.columns if col.startswith("⚠️ A rischio") for x in t.value[col]]
assert "Mario Libero" in a_rischio, a_rischio

# anche le statistiche seguono la stagione sportiva, nella dashboard dell'allenatore e nella scheda «Statistiche»
stagione = f"Stagione sportiva {inizio_stagione.year}/{str(inizio_stagione.year + 1)[2:]}"
metriche = {m.label: m.value for m in at.metric}
assert metriche["Partite con tabellino"] == "1" and metriche["Ammonizioni"] == "2", metriche
assert any(stagione in x.value for x in at.caption), [x.value for x in at.caption]
at = come("pagina_squadra", admin)
vai(at, "squadra_scheda", "Statistiche")
tabella = [t.value for t in at.dataframe if "Squalifiche" in t.value.columns][0]
riga = tabella[tabella["Giocatore"] == "Mario Libero"].iloc[0]
assert riga["Ammonizioni"] == 2 and riga["Minuti"] == 90, tabella.to_string()
assert any(stagione in x.value for x in at.caption), [x.value for x in at.caption]
print("TUTTO OK")
