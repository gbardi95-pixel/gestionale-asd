"""Lettura di una partita dalla pagina pubblica di Sportbit (piattaforma usata da alcune leghe per risultati e referti):
risultato, data, campo e, per ogni giocatore, reti, ammonizioni ed espulsioni.

La pagina non ha un'interfaccia pensata per i programmi: la lettura dipende dalla sua impaginazione. Se Sportbit la cambia,
`leggi_partita` lo segnala con un errore invece di restituire dati sbagliati.

Parametri da adattare per un'altra lega o un altro sito: l'indirizzo della pagina partita (ADDRESS, o il Secret SPORTBIT_URL, con
{codice} al posto del codice della partita, sempre https) e, se cambia l'impaginazione, le funzioni di lettura qui sotto. Il codice della
partita (es. «2321-180498»: campionato e partita) si ricava dal link copiato dal sito."""
import html
import re
import urllib.error
import urllib.request

ADDRESS = "https://www.sportbit.it/Page/GameDetails.aspx?GameCompleteCode={codice}"  # modello predefinito: {codice} = campionato-partita
_CODICE = re.compile(r"(?:GameCompleteCode=)?\b(\d{1,6}-\d{1,9})\b", re.I)


def codice_partita(testo):
    """Codice della partita (es. «2321-180498») dal link copiato dal sito o scritto a mano; None se non si riconosce.
    Si usa solo il codice: l'indirizzo da aprire viene sempre costruito qui, mai preso dal testo incollato."""
    m = _CODICE.search(str(testo or ""))
    return m.group(1) if m else None


def scarica_partita(codice, timeout=20, indirizzo=None):
    """Testo della pagina pubblica della partita. Solleva RuntimeError con un messaggio comprensibile se non è raggiungibile.
    indirizzo: modello dell'indirizzo con {codice} (Secret SPORTBIT_URL); se manca si usa ADDRESS."""
    if not re.fullmatch(r"\d{1,6}-\d{1,9}", str(codice)):
        raise RuntimeError("Il codice della partita non è valido.")
    indirizzo = (indirizzo or ADDRESS).strip()
    if not indirizzo.lower().startswith("https://") or "{codice}" not in indirizzo:
        raise RuntimeError("L'indirizzo SPORTBIT_URL nei Secrets non è valido: deve iniziare con https:// e contenere {codice}.")
    richiesta = urllib.request.Request(indirizzo.replace("{codice}", str(codice)), headers={"User-Agent": "Mozilla/5.0 (gestionale ASD)"})
    try:
        with urllib.request.urlopen(richiesta, timeout=timeout) as risposta:
            return risposta.read().decode("utf-8", errors="replace")
    except (urllib.error.URLError, TimeoutError, OSError) as ex:
        raise RuntimeError(f"Non riesco a collegarmi a Sportbit ({ex}). Riprova più tardi o inserisci i dati a mano.") from ex


def _testo(pagina, identificatore):
    m = re.search(r'id="ctl00_cphMain_' + identificatore + r'"[^>]*>([^<]*)<', pagina)
    return html.unescape(m.group(1)).strip() if m else ""


def _giocatori(pagina, tabella):
    """Righe di una delle due tabelle dei giocatori (ctl30 = squadra di casa, ctl31 = ospite): nome e conteggio delle icone."""
    inizio = pagina.find(f'id="ctl00_cphMain_{tabella}_ctl00"')
    if inizio < 0:
        raise ValueError("Non trovo l'elenco dei giocatori nella pagina di Sportbit: l'impaginazione potrebbe essere cambiata.")
    fine = pagina.find("</table>", inizio)
    giocatori = []
    for riga in re.findall(r'<tr class="rg(?:Alt)?Row".*?</tr>', pagina[inizio:fine], re.S):
        celle = re.findall(r"<td[^>]*>(.*?)</td>", riga, re.S)
        if len(celle) < 4:
            raise ValueError("Le colonne dei giocatori nella pagina di Sportbit non sono quelle previste.")
        giocatori.append({
            "nome": html.unescape(re.sub(r"<[^>]+>", "", celle[0])).strip(),
            "reti": celle[1].count("gol.png"),
            "ammonizioni": celle[2].count("yellow_card"),
            "espulsioni": celle[3].count("red_card"),
        })
    return giocatori


def leggi_partita(pagina):
    """Dati della partita dal testo della pagina.

    Restituisce {casa, ospite, reti_casa, reti_ospite (None se non ancora giocata), data (AAAA-MM-GG o None), ora, campo,
    giocatori_casa, giocatori_ospite}, con giocatori = [{nome, reti, ammonizioni, espulsioni}]."""
    casa, ospite = _testo(pagina, "lblTeamNameHomeFull"), _testo(pagina, "lblTeamNameGuestFull")
    if not casa or not ospite:
        raise ValueError("Non trovo le squadre nella pagina di Sportbit: il codice potrebbe essere sbagliato o l'impaginazione cambiata.")

    def reti(chiave):
        t = _testo(pagina, chiave)
        return int(t) if t.isdigit() else None

    data = re.search(r"(\d{2})/(\d{2})/(\d{4})", _testo(pagina, "lblGameDate"))
    return {
        "casa": casa, "ospite": ospite,
        "reti_casa": reti("lblHomeTeamPoints"), "reti_ospite": reti("lblGuestTeamPoints"),
        "data": f"{data.group(3)}-{data.group(2)}-{data.group(1)}" if data else None,
        "ora": _testo(pagina, "lblGameDateHour"), "campo": _testo(pagina, "lnkPlayingField"),
        "giocatori_casa": _giocatori(pagina, "ctl30"), "giocatori_ospite": _giocatori(pagina, "ctl31"),
    }
