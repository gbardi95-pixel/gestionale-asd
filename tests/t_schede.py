"""Apre una per una tutte le schede di tutte le pagine: nessuna deve dare errore (anche se le schede non si vedono insieme)."""
import ast
from base_test import prepara, nuovo, db

f = prepara("t_schede")
nuovo(f, "pagina_soci")  # crea il database
c = db()
# dati minimi perché le pagine abbiano qualcosa da mostrare
aid = c.execute("INSERT INTO anagrafiche (tipo, denominazione, codice_fiscale) VALUES ('SOCIO_CALCIATORE', 'Rossi Luca', 'RSSLCU12A01H501X')").lastrowid
c.execute("INSERT INTO tesserati_calcio (anagrafica_id, numero_tessera, categoria) VALUES (?, 'T1', 'JUNIORES')", [aid])
c.commit()

albero = ast.parse(open("app.py", encoding="utf-8").read())
elenchi = {}
for n in ast.walk(albero):
    if isinstance(n, ast.Assign) and isinstance(n.targets[0], ast.Name) and n.targets[0].id.startswith("schede_") and isinstance(n.value, ast.List):
        elenchi[n.targets[0].id] = [e.value for e in n.value.elts]

# (pagina, nome elenco, chiave, impostazioni di sessione)
PAGINE = [("pagina_soci", "schede_soci", "soci_scheda", {}),
          ("pagina_parametri", "schede_tariffe", "tariffe_scheda", {}),
          ("pagina_distinte", "schede_distinte", "distinte_scheda", {}),
          ("pagina_lavoro_sportivo", "schede_collab", "collab_scheda", {}),
          ("pagina_prima_nota", "schede_pn_mese", "pn_mese_scheda", {"pn_sezione": "mese"}),
          ("pagina_prima_nota", "schede_pn_anno", "pn_anno_scheda", {"pn_sezione": "anno"}),
          ("pagina_preventivo", "schede_preventivo", "preventivo_scheda", {}),
          ("pagina_squadra", "schede_squadra", "squadra_scheda", {}),
          ("pagina_utenti", "schede_utenti", "utenti_scheda", {})]
totale = 0
for pagina, nome, chiave, extra in PAGINE:
    assert nome in elenchi, nome
    for etichetta in elenchi[nome]:
        at = nuovo(f, pagina)
        for k, v in extra.items():
            at.session_state[k] = v
        at.session_state[chiave] = etichetta
        at.run()
        assert not at.exception, (pagina, etichetta, at.exception)
        totale += 1
print("schede aperte:", totale)
print("TUTTO OK")
