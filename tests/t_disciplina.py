"""Disciplina: lettura di un comunicato (testo inventato), abbinamento dei nomi, avvisi di squalifica/diffida, tabellino e schermate."""
import sys, os, datetime, warnings
warnings.filterwarnings("ignore")
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from modules import disciplina as d

SQ = ["ASD ROSSA", "BLU BOYS", "US VERDE ALTA", "VERDE"]
righe_classifica = "\n".join(f"{i + 1}\n \n{s} 3 1 1 0 0 2 1 1 0" for i, s in enumerate(SQ))
TESTO = f"""CU 7 del 04/11/2026
COMITATO TERRITORIALE DI PROVA APS
UISP COMITATO TERRITORIALE DI PROVA
19100 Città - Tel. +39.000 - prova@esempio.it
CLASSIFICA – GIRONE 1
{righe_classifica}
CLASSIFICA MARCATORI – GIRONE 1
3 reti ROSSI MARIO ASD ROSSA
 NERI LUCA BLU BOYS
 DE LUCA GIO' ASD ROSSA
1 rete BIANCHI CARLO US VERDE ALTA
PROVVEDIMENTI DISCIPLINARI – GIRONE 1
«  PRIME AMMONIZIONI  »
ASD ROSSA ROSSI MARIO
BLU BOYS NERI LUCA
ASD ROSSA DE LUCA GIO'
«  DIFFIDATI  »
ASD ROSSA VERDI PAOLO
«  SQUALIFICHE DI 2 GIORNATE  »
ASD ROSSA GIALLI ANDREA (ART. 222 R.T.N.)
US VERDE ALTA BIANCHI CARLO (ART. 222 R.T.N.)
«  SQUALIFICHE A TEMPO  »
ASD ROSSA
VIOLA SERGIO
SQUALIFICA DI 1 MESE FINO A TUTTO IL 30/11/2026) (ART. 221
R.T.N.
«  AMMENDE  »
ASD ROSSA AMMENDA DI € 1.020,50 (ART. 214 R.T.N.)
BLU BOYS AMMENDA DI € 10,00 (ART. 213 R.T.N.)
"""

n, data, ente = d.intestazione(TESTO)
assert (n, data) == (7, "2026-11-04") and "COMITATO" in ente, (n, data, ente)
assert d.nomi_squadre(TESTO) == SQ, d.nomi_squadre(TESTO)
r = d.leggi_comunicato(TESTO, "ASD ROSSA")
tipi = [(p["tipo"], p["nome"]) for p in r["provvedimenti"]]
print(tipi)
assert ("AMMONIZIONE", "ROSSI MARIO") in tipi and ("AMMONIZIONE", "DE LUCA GIO'") in tipi
assert ("DIFFIDA", "VERDI PAOLO") in tipi
sq = [p for p in r["provvedimenti"] if p["tipo"] == "SQUALIFICA_GIORNATE"]
assert len(sq) == 1 and sq[0]["nome"] == "GIALLI ANDREA" and sq[0]["giornate"] == 2 and sq[0]["articolo"] == "222"
tempo = [p for p in r["provvedimenti"] if p["tipo"] == "SQUALIFICA_TEMPO"][0]
assert tempo["nome"] == "VIOLA SERGIO" and tempo["fino_al"] == "2026-11-30" and tempo["articolo"] == "221", tempo
amm = [p for p in r["provvedimenti"] if p["tipo"] == "AMMENDA"]
assert len(amm) == 1 and amm[0]["importo"] == 1020.5 and amm[0]["nome"] == ""
assert [(m["nome"], m["reti"]) for m in r["marcatori"]] == [("ROSSI MARIO", 3), ("DE LUCA GIO'", 3)], r["marcatori"]
assert not any("BLU" in str(p) or "NERI" in str(p) or "BIANCHI" in str(p) for p in r["provvedimenti"] + r["marcatori"]), "dati di altre società"
assert r["avvisi"] == [], r["avvisi"]
# una squadra il cui nome è contenuto in quello di un'altra
assert [p["nome"] for p in d.leggi_comunicato(TESTO, "VERDE")["provvedimenti"]] == []
assert [p["nome"] for p in d.leggi_comunicato(TESTO, "US VERDE ALTA")["provvedimenti"]] == ["BIANCHI CARLO"]
# formato non riconosciuto -> avvisi, nessun dato
vuoto = d.leggi_comunicato("testo qualunque", "ASD ROSSA")
assert vuoto["avvisi"] and not vuoto["provvedimenti"]
print("lettura comunicato OK")

# abbinamento dei nomi
cand = {1: "Mario Rossi", 2: "Gio' De Luca", 3: "Rossi Maria", 4: "Paolo Verdi"}
assert d.abbina_nome("ROSSI MARIO", cand) == (1, [])
assert d.abbina_nome("DE LUCA GIO'", cand)[0] == 2
assert d.abbina_nome("VERDE PAOLO", cand)[0] is None and 4 in d.abbina_nome("VERDE PAOLO", cand)[1]
assert d.abbina_nome("SCONOSCIUTO NOME", cand) == (None, [])
print("abbinamento nomi OK")

# situazione: squalifica a giornate (partite dopo il comunicato), a tempo, diffida solo se nell'ultimo comunicato
base = {"data_comunicato": "2026-11-04", "numero_comunicato": 7, "giornate": 2, "fino_al": None}
assert d.situazione([dict(base, tipo="SQUALIFICA_GIORNATE")], "2026-11-10", lambda x: 1)[0] == "SQUALIFICATO"
assert d.situazione([dict(base, tipo="SQUALIFICA_GIORNATE")], "2026-11-20", lambda x: 2)[0] is None
assert d.situazione([dict(base, tipo="SQUALIFICA_TEMPO", fino_al="2026-11-30")], "2026-11-29")[0] == "SQUALIFICATO"
assert d.situazione([dict(base, tipo="SQUALIFICA_TEMPO", fino_al="2026-11-30")], "2026-12-01")[0] is None
assert d.situazione([dict(base, tipo="DIFFIDA")], "2026-11-10", ultimo_comunicato=("2026-11-04", 7))[0] == "DIFFIDATO"
assert d.situazione([dict(base, tipo="DIFFIDA")], "2026-11-20", ultimo_comunicato=("2026-11-11", 8))[0] is None
print("situazione OK")

# schermate
from base_test import prepara, nuovo, db, bottone, campo
import pandas as pd
f = prepara("t_disciplina")
at = nuovo(f, "pagina_dashboard")
c = db()
oggi = datetime.date.today()
ids = {}
for nome in ("Mario Rossi", "Paolo Verdi", "Andrea Gialli"):
    aid = c.execute("INSERT INTO anagrafiche (tipo, denominazione) VALUES ('SOCIO_CALCIATORE', ?)", [nome]).lastrowid
    c.execute("INSERT INTO tesserati_calcio (anagrafica_id, numero_tessera, categoria, gioca) VALUES (?, 'T', 'PRIMA_SQUADRA', 1)", [aid])
    c.execute("INSERT INTO certificati_medici (anagrafica_id, tipo, data_rilascio, data_scadenza, stato_idoneita) VALUES (?, 'AGONISTICO', '', ?, 'IDONEO')",
              [aid, (oggi + datetime.timedelta(days=200)).isoformat()])
    ids[nome] = aid
dopo = oggi - datetime.timedelta(days=3)
cu = c.execute("INSERT INTO comunicati_disciplina (numero, data) VALUES (7, ?)", [dopo.isoformat()]).lastrowid
c.execute("INSERT INTO provvedimenti_disciplinari (comunicato_id, anagrafica_id, tipo) VALUES (?, ?, 'DIFFIDA')", [cu, ids["Paolo Verdi"]])
c.execute("INSERT INTO provvedimenti_disciplinari (comunicato_id, anagrafica_id, tipo, giornate) VALUES (?, ?, 'SQUALIFICA_GIORNATE', 2)", [cu, ids["Andrea Gialli"]])
c.execute("INSERT INTO provvedimenti_disciplinari (comunicato_id, tipo, importo) VALUES (?, 'AMMENDA', 20)", [cu])
ev = c.execute("INSERT INTO eventi_squadra (tipo, data, categoria, avversario) VALUES ('PARTITA', ?, 'PRIMA_SQUADRA', 'Avversari')",
               [(oggi - datetime.timedelta(days=1)).isoformat()]).lastrowid
for nome in ("Mario Rossi", "Andrea Gialli"):
    c.execute("INSERT INTO presenze_evento (evento_id, anagrafica_id, stato) VALUES (?, ?, 'CONVOCATO')", [ev, ids[nome]])
c.commit()

at = nuovo(f, "pagina_squadra")
etichette = campo(at.multiselect, "Convocati").options
print("opzioni convocati:", etichette)
assert any("diffidato" in str(o) for o in etichette) and any("squalificato" in str(o) for o in etichette)
rosa = [x for x in at.dataframe if "Disciplina" in x.value.columns][0].value
print(rosa.to_string())
assert (rosa["Disciplina"] != "").sum() == 2

# tabellino: reti e cartellini di una partita
at.session_state["tab_partita"] = at.session_state["tab_partita"] if "tab_partita" in at.session_state else None
bottone(at, "💾 Salva il tabellino").click().run()
assert not at.exception, at.exception
print("salvataggio tabellino vuoto OK:", c.execute("SELECT COUNT(*) FROM tabellino_giocatori").fetchone())
c.execute("INSERT INTO tabellino_giocatori (evento_id, anagrafica_id, titolare, minuti, reti, assist, ammonizioni, espulso) VALUES (?, ?, 1, 90, 2, 1, 1, 0)",
          [ev, ids["Mario Rossi"]])
c.commit()
at = nuovo(f, "pagina_squadra")
stat = [x for x in at.dataframe if "Squalifiche" in x.value.columns][0].value
print(stat.to_string())
riga = stat[stat["Giocatore"] == "Mario Rossi"].iloc[0]
assert riga["Reti"] == 2 and riga["Assist"] == 1 and riga["Minuti"] == 90 and riga["Ammonizioni"] == 1
assert stat[stat["Giocatore"] == "Andrea Gialli"].iloc[0]["Squalifiche"] == 1
assert not at.exception

# ammenda: diventa un debito da pagare (spesa non pagata) in prima nota, una sola volta
assert any("Disciplina" in t.label for t in at.tabs)
campo(at.text_input, "Creditore").set_value("Ente di prova")
bottone(at, "➕ Registra il debito").click().run()
assert not at.exception, at.exception
sp = c.execute("SELECT id, totale, numero_doc, data_pagamento, categoria_spesa, movimento_id FROM fatture_passive").fetchall()
print("spesa:", sp)
assert len(sp) == 1 and sp[0][1] == 20 and sp[0][2] == "CU 7" and sp[0][3] is None and sp[0][4] == "40.01.006"
righe = c.execute("SELECT SUM(dare), SUM(avere) FROM righe_prima_nota WHERE movimento_id = ?", [sp[0][5]]).fetchone()
assert righe == (20, 20), righe
assert c.execute("SELECT spesa_id FROM provvedimenti_disciplinari WHERE tipo = 'AMMENDA'").fetchone()[0] == sp[0][0]
at = nuovo(f, "pagina_squadra")
assert not [b for b in at.button if b.label.startswith("➕ Registra il debito")], "ammenda proposta due volte"
at = nuovo(f, "pagina_spese")
assert any("da pagare" in e.label for e in at.expander), [e.label for e in at.expander]
print("TUTTO OK")
