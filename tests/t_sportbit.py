"""Sportbit: lettura di una pagina partita (HTML inventato con la stessa struttura) e importazione nel tabellino."""
import io, os, sys, urllib.error, urllib.request, warnings
warnings.filterwarnings("ignore")
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from modules import sportbit

GOL, GIALLO, ROSSO = "gol.png", "hand_yellow_card.png", "hand_red_card.png"


def cella(*icone):
    return f'<td align="center">' + "".join(f'<img src="../Images/Statistics/{i}" />' for i in icone) + "</td>" if icone else '<td align="center">&nbsp;</td>'


def tabella(sigla, giocatori):
    righe = "".join(f'<tr class="rg{"Alt" if i % 2 else ""}Row"><td align="left">{nome}</td>{cella(*[GOL] * g)}{cella(*[GIALLO] * y)}{cella(*[ROSSO] * r)}</tr>'
                    for i, (nome, g, y, r) in enumerate(giocatori))
    return (f'<table class="rgMasterTable" id="ctl00_cphMain_{sigla}_ctl00"><thead><tr><th>GIOCATORE</th>'
            f'<th><img src="../Images/Statistics/{GOL}" /></th><th><img src="../Images/Statistics/{GIALLO}" /></th><th><img src="../Images/Statistics/{ROSSO}" /></th></tr></thead>'
            f'<tbody>{righe}</tbody></table>')


def pagina(casa, ospite, rc, ro, gioc_casa, gioc_ospite, data="SABATO 26/09/2026"):
    return (f'<html><body><span id="ctl00_cphMain_lblHomeTeamPoints">{rc}</span><span id="ctl00_cphMain_lblGuestTeamPoints">{ro}</span>'
            f'<span id="ctl00_cphMain_lblGameDate">{data}</span><span id="ctl00_cphMain_lblGameDateHour">15:00</span>'
            f'<a id="ctl00_cphMain_lnkPlayingField" href="#">CAMPO DI PROVA</a>'
            f'<span id="ctl00_cphMain_lblTeamNameHomeFull">{casa}</span><span id="ctl00_cphMain_lblTeamNameGuestFull">{ospite}</span>'
            f'{tabella("ctl30", gioc_casa)}{tabella("ctl31", gioc_ospite)}</body></html>')


PAG = pagina("ASD ROSSA", "BLU BOYS", 3, 1,
             [("ROSSI MARIO", 2, 0, 0), ("VERDI PAOLO", 1, 1, 0), ("SCONOSCIUTO ZETA", 0, 0, 1)], [("NERI LUCA", 1, 0, 0)])
p = sportbit.leggi_partita(PAG)
assert (p["casa"], p["ospite"], p["reti_casa"], p["reti_ospite"], p["data"], p["ora"], p["campo"]) == ("ASD ROSSA", "BLU BOYS", 3, 1, "2026-09-26", "15:00", "CAMPO DI PROVA")
assert p["giocatori_casa"] == [{"nome": "ROSSI MARIO", "reti": 2, "ammonizioni": 0, "espulsioni": 0},
                               {"nome": "VERDI PAOLO", "reti": 1, "ammonizioni": 1, "espulsioni": 0},
                               {"nome": "SCONOSCIUTO ZETA", "reti": 0, "ammonizioni": 0, "espulsioni": 1}], p["giocatori_casa"]
assert p["giocatori_ospite"][0]["reti"] == 1
vuota = sportbit.leggi_partita(pagina("A", "B", "", "", [], []))
assert vuota["reti_casa"] is None and vuota["giocatori_casa"] == []
for rotto in ("<html>niente</html>", PAG.replace("ctl30_ctl00", "altro")):
    try:
        sportbit.leggi_partita(rotto)
        raise SystemExit("doveva dare errore")
    except ValueError as ex:
        assert "Sportbit" in str(ex)
assert sportbit.codice_partita("https://www.sportbit.it/Page/GameDetails.aspx?GameCompleteCode=2321-180498") == "2321-180498"
assert sportbit.codice_partita("2321-180498") == "2321-180498" and sportbit.codice_partita("ciao") is None
for cattivo in ("../x", "2321-1/../a", "http://altro.it"):
    try:
        sportbit.scarica_partita(cattivo)
        raise SystemExit("codice non valido accettato")
    except RuntimeError:
        pass
for cattivo in ("http://sito.it/{codice}", "https://sito.it/senza-codice"):
    try:
        sportbit.scarica_partita("2321-1", indirizzo=cattivo)
        raise SystemExit("indirizzo non valido accettato")
    except RuntimeError as ex:
        assert "SPORTBIT_URL" in str(ex)
print("lettura pagina OK")

# schermata
from base_test import prepara, nuovo, db, bottone, campo, vai
import datetime
f = prepara("t_sportbit")
nuovo(f, "pagina_dashboard")
c = db()
ids = {}
for nome in ("Mario Rossi", "Paolo Verdi", "Giovanni Altro"):
    aid = c.execute("INSERT INTO anagrafiche (tipo, denominazione) VALUES ('SOCIO_CALCIATORE', ?)", [nome]).lastrowid
    c.execute("INSERT INTO tesserati_calcio (anagrafica_id, numero_tessera, categoria, gioca) VALUES (?, 'T', 'PRIMA_SQUADRA', 1)", [aid])
    ids[nome] = aid
ev = c.execute("INSERT INTO eventi_squadra (tipo, data, categoria, avversario) VALUES ('PARTITA', '2026-09-26', 'PRIMA_SQUADRA', 'Blu Boys')").lastrowid
c.execute("INSERT INTO presenze_evento (evento_id, anagrafica_id, stato) VALUES (?, ?, 'CONVOCATO')", [ev, ids["Mario Rossi"]])
c.execute("INSERT INTO tabellino_giocatori (evento_id, anagrafica_id, titolare, minuti, assist) VALUES (?, ?, 1, 90, 2)", [ev, ids["Mario Rossi"]])
c.execute("INSERT INTO impostazioni (chiave, valore) VALUES ('nome_nei_comunicati', 'ASD ROSSA')")
c.commit()

richieste = []


class Risposta(io.BytesIO):
    def __enter__(self):
        return self

    def __exit__(self, *a):
        return False


def finto(richiesta, timeout=None):
    richieste.append(richiesta.full_url)
    if "GameCompleteCode=9999-1" in richiesta.full_url:
        raise urllib.error.URLError("rete assente")
    return Risposta(PAG.encode("utf-8"))


urllib.request.urlopen = finto
at = nuovo(f, "pagina_squadra")
vai(at, "squadra_scheda", "Tabellino")
campo(at.text_input, "Link o codice").set_value("https://esempio.it/x?GameCompleteCode=9999-1")
bottone(at, "🔍 Leggi").click().run()
assert not at.exception, at.exception
assert any("Non riesco a collegarmi" in e.value for e in at.error), [e.value for e in at.error]
assert richieste == ["https://www.sportbit.it/Page/GameDetails.aspx?GameCompleteCode=9999-1"], richieste  # l'indirizzo è sempre quello di Sportbit
urllib.request.urlopen = lambda r, timeout=None: (richieste.append(r.full_url), Risposta(PAG.encode("utf-8")))[1]
assert sportbit.leggi_partita(sportbit.scarica_partita("2321-7", indirizzo="https://lega.example/partita/{codice}.aspx"))["casa"] == "ASD ROSSA"
assert richieste[-1] == "https://lega.example/partita/2321-7.aspx", richieste[-1]  # indirizzo impostabile, sempre https
urllib.request.urlopen = finto

campo(at.text_input, "Link o codice").set_value("https://esempio.it/x?GameCompleteCode=2321-1")
bottone(at, "🔍 Leggi").click().run()
assert not at.exception, at.exception
assert richieste[-1] == "https://www.sportbit.it/Page/GameDetails.aspx?GameCompleteCode=2321-1"
assert at.radio[0].value == "casa", at.radio[0].value  # società riconosciuta dal nome salvato
scelte = [x for x in at.selectbox if x.key and x.key.startswith("sb_ab_")]
print("abbinamenti:", [(x.key, x.value) for x in scelte])
assert [x.value for x in scelte] == [ids["Mario Rossi"], ids["Paolo Verdi"], None]
bottone(at, "✅ Applica al tabellino").click().run()
assert not at.exception, at.exception
righe = {r[0]: r[1:] for r in c.execute("SELECT anagrafica_id, titolare, minuti, reti, assist, ammonizioni, espulso FROM tabellino_giocatori").fetchall()}
print(righe)
assert righe[ids["Mario Rossi"]] == (1, 90, 2, 2, 0, 0)      # minuti, titolare e assist inseriti a mano restano
assert righe[ids["Paolo Verdi"]] == (0, None, 1, 0, 1, 0)
assert len(righe) == 2
assert c.execute("SELECT gol_nostri, gol_avversari FROM eventi_squadra WHERE id = ?", [ev]).fetchone() == (3, 1)
assert any("Attenzione" in s.value or "Sportbit" in s.value for s in at.success), [s.value for s in at.success]
print("TUTTO OK")
