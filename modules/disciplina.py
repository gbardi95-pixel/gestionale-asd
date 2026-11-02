"""Disciplina e statistiche dei giocatori: lettura del comunicato ufficiale (PDF) per la propria società, abbinamento dei nomi,
situazione di ogni giocatore (diffidato, squalificato) e tabella delle statistiche.

Il comunicato non ha un formato di legge: la lettura è pensata per quelli delle leghe che usano l'impaginazione dei comunicati
UISP (sezioni «PRIME AMMONIZIONI», «DIFFIDATI», «SQUALIFICHE…», «AMMENDE», classifica marcatori). Se la lega cambia
impaginazione, `leggi_comunicato` lo segnala con degli avvisi invece di registrare dati sbagliati."""
import difflib
import io
import re
import unicodedata

import pandas as pd

TIPI = {
    "AMMONIZIONE": "Ammonizione",
    "DIFFIDA": "Diffidato",
    "SQUALIFICA_SOMMA": "Squalifica per somma di ammonizioni",
    "SQUALIFICA_GIORNATE": "Squalifica a giornate",
    "SQUALIFICA_TEMPO": "Squalifica a tempo",
    "AMMENDA": "Ammenda alla società",
    "ALTRO": "Altro provvedimento",
}
_INTESTAZIONI_PAGINA = ("UISP", "UNIONE ITALIANA")
_SEZIONE = re.compile(r"«\s*(.+?)\s*»")
_FINE_SEZIONE = re.compile(r"^(CLASSIFICA|RISULTATI|PROSSIMI|PROVVEDIMENTI|GIRONE)\b", re.I)


def testo_pdf(contenuto):
    """Testo di tutte le pagine di un PDF (byte)."""
    from pypdf import PdfReader
    lettore = PdfReader(io.BytesIO(contenuto))
    return "\n".join((p.extract_text() or "") for p in lettore.pages)


def chiave_nome(nome):
    """Insieme ordinato delle parole del nome, senza maiuscole, accenti e apostrofi: «Rossi Mario» e «MARIO ROSSI» coincidono."""
    s = unicodedata.normalize("NFKD", str(nome or ""))
    s = "".join(c for c in s if not unicodedata.combining(c)).casefold()
    s = re.sub(r"['’`´]", "", s)
    return tuple(sorted(re.findall(r"[a-z0-9]+", s)))


def abbina_nome(nome, candidati):
    """Cerca il nome tra le persone della società.

    candidati: {anagrafica_id: denominazione}. Restituisce (id, suggerimenti): l'id se il nome coincide in modo certo,
    altrimenti None e fino a 3 persone dal nome simile da proporre."""
    chiave = chiave_nome(nome)
    esatti = [aid for aid, den in candidati.items() if chiave_nome(den) == chiave]
    if len(esatti) == 1:
        return esatti[0], []
    simili = sorted(((difflib.SequenceMatcher(None, " ".join(chiave), " ".join(chiave_nome(den))).ratio(), aid)
                     for aid, den in candidati.items()), reverse=True)
    return None, [aid for punteggio, aid in simili[:3] if punteggio >= 0.75]


def _righe_utili(testo):
    """Righe del comunicato senza intestazioni di pagina, indirizzi e numeri di pagina."""
    for riga in testo.splitlines():
        r = " ".join(riga.split())
        if not r or r.isdigit():
            continue
        if r.upper().startswith(_INTESTAZIONI_PAGINA) or "@" in r or "www." in r.lower() or "Tel." in r:
            continue
        yield r


def intestazione(testo):
    """(numero, data AAAA-MM-GG, ente) del comunicato, o None dove non si trovano."""
    m = re.search(r"CU\s*(\d+)\s+del\s+(\d{2})/(\d{2})/(\d{4})", testo, re.I)
    ente = next((" ".join(r.split()) for r in testo.splitlines() if "COMITATO" in r.upper()), None)
    if not m:
        return None, None, ente
    return int(m.group(1)), f"{m.group(4)}-{m.group(3)}-{m.group(2)}", ente


def nomi_squadre(testo):
    """Squadre elencate nella classifica (nome seguito dalle 9 colonne di numeri PT PG PV PN PP GF GS DF CD)."""
    riga_classifica = re.compile(r"^(.*?)\s+" + r"\s+".join([r"-?\d+"] * 9) + r"$")
    squadre, precedente = [], ""
    for r in _righe_utili(testo):
        m = riga_classifica.match(r)
        if m and not r.isdigit():
            nome = (precedente + " " + m.group(1)).strip() if precedente.endswith("-") else m.group(1).strip()
            if nome and nome not in squadre:
                squadre.append(nome)
        precedente = r
    return squadre


def _tipo_sezione(titolo):
    t = titolo.upper()
    if t.startswith("PRIME AMMONIZIONI") or t.startswith("AMMONIZIONI"):
        return "AMMONIZIONE", None
    if t.startswith("DIFFIDAT"):
        return "DIFFIDA", None
    if "SOMMA DI AMMONIZIONI" in t:
        return "SQUALIFICA_SOMMA", 1
    m = re.search(r"SQUALIFICHE DI (\d+) GIORNAT", t)
    if m:
        return "SQUALIFICA_GIORNATE", int(m.group(1))
    if "SQUALIFICHE A TEMPO" in t:
        return "SQUALIFICA_TEMPO", None
    if t.startswith("AMMENDE"):
        return "AMMENDA", None
    return "ALTRO", None


def _squadra_della_riga(riga, squadre):
    """La squadra con cui comincia la riga (la più lunga, perché un nome può contenerne un altro), o None."""
    for s in sorted(squadre, key=len, reverse=True):
        if riga.upper() == s.upper() or riga.upper().startswith(s.upper() + " "):
            return s
    return None


def _dettagli(testo):
    """Nome del tesserato e dati del provvedimento dal testo di una voce."""
    t = " ".join(testo.split())
    art = re.search(r"ART\.?\s*(\d+)", t, re.I)
    fino = re.search(r"FINO A TUTTO IL\s+(\d{2})/(\d{2})/(\d{4})", t, re.I)
    importo = re.search(r"AMMENDA DI\s*€\s*(\d+(?:\.\d{3})*(?:,\d{1,2})?)", t, re.I)
    nome = re.split(r"\s*(?:\(|SQUALIFICA|AMMENDA)", t, maxsplit=1, flags=re.I)[0].strip()
    return {
        "nome": nome, "articolo": art.group(1) if art else None,
        "fino_al": f"{fino.group(3)}-{fino.group(2)}-{fino.group(1)}" if fino else None,
        "importo": float(importo.group(1).replace(".", "").replace(",", ".")) if importo else None,
        "testo": t,
    }


def leggi_comunicato(testo, squadra):
    """Dati del comunicato che riguardano la squadra indicata.

    Restituisce {numero, data, ente, provvedimenti: [...], marcatori: [{nome, reti}], avvisi: [...]}. Ogni provvedimento ha
    tipo (chiavi di TIPI), nome (vuoto per le ammende, che sono della società), giornate, fino_al, articolo, importo, testo."""
    numero, data, ente = intestazione(testo)
    squadre = nomi_squadre(testo)
    avvisi = []
    if numero is None:
        avvisi.append("Non trovo il numero e la data del comunicato (di solito «CU 6 del 28/10/2026» in alto).")
    if not squadre:
        avvisi.append("Non trovo la classifica con l'elenco delle squadre: il formato del comunicato potrebbe essere cambiato.")
    if squadra not in squadre and squadre:
        avvisi.append(f"La squadra «{squadra}» non compare nell'elenco di questo comunicato.")

    provvedimenti, marcatori = [], []
    sezione, voce, in_marcatori, reti_correnti = None, None, False, 0

    def chiudi_voce():
        nonlocal voce
        if voce and voce["squadra"] == squadra:
            d = _dettagli(voce["testo"])
            provvedimenti.append({"tipo": voce["tipo"], "giornate": voce["giornate"], "sezione": voce["sezione"], **d})
        voce = None

    for r in _righe_utili(testo):
        if re.search(r"MARCATORI", r, re.I) and _FINE_SEZIONE.match(r):
            chiudi_voce()
            sezione, in_marcatori = None, True
            continue
        m_sez = _SEZIONE.search(r)
        if m_sez:
            chiudi_voce()
            in_marcatori = False
            tipo, giornate = _tipo_sezione(m_sez.group(1))
            sezione = {"titolo": m_sez.group(1), "tipo": tipo, "giornate": giornate}
            continue
        if _FINE_SEZIONE.match(r):
            chiudi_voce()
            sezione, in_marcatori = None, False
            continue
        if in_marcatori:
            m = re.match(r"^(\d+)\s+rete?i?\s+(.*)$", r, re.I)
            resto = m.group(2) if m else r
            if m:
                reti_correnti = int(m.group(1))
            if resto.upper().endswith(" " + squadra.upper()):
                marcatori.append({"nome": resto[:-len(squadra)].strip(), "reti": reti_correnti})
            continue
        if sezione is None:
            continue
        s = _squadra_della_riga(r, squadre)
        if s:
            chiudi_voce()
            voce = {"squadra": s, "testo": r[len(s):].strip(), "tipo": sezione["tipo"], "giornate": sezione["giornate"],
                    "sezione": sezione["titolo"]}
        elif voce:
            voce["testo"] += " " + r
    chiudi_voce()

    for p in provvedimenti:
        if p["tipo"] == "ALTRO":
            avvisi.append(f"Sezione non riconosciuta «{p['sezione']}»: registrata come «altro provvedimento», controllala.")
        elif p["tipo"] != "AMMENDA" and not p["nome"]:
            avvisi.append(f"Nella sezione «{p['sezione']}» c'è una riga senza nome: {p['testo']}")
        elif p["tipo"] == "AMMENDA" and p["importo"] is None:
            avvisi.append(f"Non riesco a leggere l'importo dell'ammenda: {p['testo']}")
    return {"numero": numero, "data": data, "ente": ente, "squadre": squadre, "provvedimenti": provvedimenti,
            "marcatori": marcatori, "avvisi": list(dict.fromkeys(avvisi))}


def situazione(provvedimenti, oggi, partite_dopo=lambda data: 0, ultimo_comunicato=None):
    """Situazione disciplinare attuale di un giocatore, dai suoi provvedimenti (ordinati dal più recente).

    provvedimenti: elenco di dict con tipo, data_comunicato, numero_comunicato, giornate, fino_al.
    partite_dopo(data): quante partite della squadra sono state giocate dopo quella data.
    ultimo_comunicato: (data, numero) dell'ultimo comunicato importato: la diffida vale solo se è elencata lì.
    Restituisce (stato, testo): stato è «SQUALIFICATO», «DIFFIDATO» o None. Per le squalifiche a giornate il testo riporta le partite
    giocate dopo il comunicato: stabilire se la squalifica è scontata resta una verifica da fare sul comunicato."""
    if not provvedimenti:
        return None, ""
    ultimo_numero = ultimo_comunicato or max((p["data_comunicato"], p["numero_comunicato"]) for p in provvedimenti)
    for p in provvedimenti:
        quando = f"comunicato {p['numero_comunicato']} del {'/'.join(reversed(str(p['data_comunicato']).split('-')))}"
        if p["tipo"] == "SQUALIFICA_TEMPO" and p.get("fino_al") and str(p["fino_al"]) >= str(oggi):
            return "SQUALIFICATO", f"Squalifica a tempo fino al {'/'.join(reversed(str(p['fino_al']).split('-')))} ({quando})"
        if p["tipo"] in ("SQUALIFICA_GIORNATE", "SQUALIFICA_SOMMA"):
            n = int(p.get("giornate") or 1)
            giocate = partite_dopo(p["data_comunicato"])
            if giocate < n:
                return "SQUALIFICATO", (f"Squalificato per {n} giornat{'a' if n == 1 else 'e'} ({quando}); "
                                        f"partite registrate dopo il comunicato: {giocate}")
    for p in provvedimenti:
        if p["tipo"] == "DIFFIDA" and (p["data_comunicato"], p["numero_comunicato"]) == ultimo_numero:
            return "DIFFIDATO", "Diffidato: alla prossima ammonizione scatta la squalifica"
    return None, ""


COLONNE_STATISTICHE = ["Giocatore", "Allenamenti", "Presenze", "Presenza (%)", "Convocazioni", "In distinta", "Partite (tabellino)",
                       "Titolare", "Minuti", "Reti", "Assist", "Ammonizioni", "Espulsioni", "Squalifiche"]


def statistiche(nomi, df_presenze, df_distinte, df_tabellino, df_disciplina):
    """Una riga per giocatore con presenze, convocazioni, partite, gol e provvedimenti.

    nomi: {anagrafica_id: nome} dei giocatori da mostrare. df_presenze: anagrafica_id, nome, tipo, stato. df_distinte: anagrafica_id, n. df_tabellino: anagrafica_id, titolare, minuti, reti,
    assist, ammonizioni, espulso (una riga per partita). df_disciplina: anagrafica_id, tipo (provvedimenti importati dai comunicati)."""
    if not nomi:
        return pd.DataFrame(columns=COLONNE_STATISTICHE)
    righe = []
    for aid, nome in nomi.items():
        g = df_presenze[df_presenze["anagrafica_id"] == aid] if not df_presenze.empty else df_presenze
        all_ = g[g["tipo"] == "ALLENAMENTO"] if len(g) else g
        pres = int((all_["stato"] == "PRESENTE").sum()) if len(all_) else 0
        t = df_tabellino[df_tabellino["anagrafica_id"] == aid] if not df_tabellino.empty else df_tabellino
        d = df_disciplina[df_disciplina["anagrafica_id"] == aid] if not df_disciplina.empty else df_disciplina
        dist = int(df_distinte.loc[df_distinte["anagrafica_id"] == aid, "n"].sum()) if not df_distinte.empty else 0
        righe.append({
            "Giocatore": nome, "Allenamenti": len(all_), "Presenze": pres,
            "Presenza (%)": round(pres / len(all_) * 100) if len(all_) else None,
            "Convocazioni": int(((g["tipo"] == "PARTITA") & (g["stato"] == "CONVOCATO")).sum()) if len(g) else 0,
            "In distinta": dist, "Partite (tabellino)": len(t),
            "Titolare": int(t["titolare"].fillna(0).sum()) if len(t) else 0,
            "Minuti": int(t["minuti"].fillna(0).sum()) if len(t) else 0,
            "Reti": int(t["reti"].fillna(0).sum()) if len(t) else 0,
            "Assist": int(t["assist"].fillna(0).sum()) if len(t) else 0,
            "Ammonizioni": int(t["ammonizioni"].fillna(0).sum()) if len(t) else 0,
            "Espulsioni": int(t["espulso"].fillna(0).sum()) if len(t) else 0,
            "Squalifiche": int(d["tipo"].isin(["SQUALIFICA_SOMMA", "SQUALIFICA_GIORNATE", "SQUALIFICA_TEMPO"]).sum()) if len(d) else 0,
        })
    return pd.DataFrame(righe, columns=COLONNE_STATISTICHE).sort_values("Giocatore", key=lambda s: s.str.casefold())
