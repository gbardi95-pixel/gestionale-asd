import datetime
from base_test import prepara, nuovo, db, bottone, campo
f = prepara("t_erogazione")
at = nuovo(f, "pagina_ricevute")
c = db()
aid = c.execute("INSERT INTO anagrafiche (tipo, denominazione, codice_fiscale) VALUES ('SOCIO_CALCIATORE', 'Rossi Luca', 'RSSLCU12A01H501X')").lastrowid
c.execute("INSERT INTO tesserati_calcio (anagrafica_id, numero_tessera, categoria, quota_stagionale) VALUES (?, 'T1', 'JUNIORES', 100)", [aid])
c.commit()
def emetti(tipo, importo, pregresso=False):
    at = nuovo(f, "pagina_ricevute")
    campo(at.selectbox, "Tipologia").set_value(tipo)
    campo(at.number_input, "Importo Incassato").set_value(importo)
    if pregresso: campo(at.checkbox, "Incasso di una quota").check()
    bottone(at, "Emetti Ricevuta").click().run(); assert not at.exception, at.exception
    return [e.value for e in at.error]
print("erogazione + pregresso:", emetti("Erogazione Liberale", 50.0, True))
print("erogazione:", emetti("Erogazione Liberale", 50.0))
print("quota:", emetti("Quota Associativa Annua", 30.0))
print("ricevute:", c.execute("SELECT numero_ricevuta, causale, importo FROM ricevute_istituzionali").fetchall())
print("prima nota:", c.execute("SELECT p.codice, r.avere FROM righe_prima_nota r JOIN piano_dei_conti p ON p.id = r.sottoconto_id WHERE r.avere > 0").fetchall())
at = nuovo(f, "pagina_dashboard")
print("metriche dashboard:", [(m.label, m.value) for m in at.metric][:6])
at = nuovo(f, "pagina_soci")
print("libro soci/quote:", [d.value.to_string()[:400] for d in at.dataframe if "ersat" in d.value.to_string()][:1])
from modules import ricevuta_pdf
pdf = ricevuta_pdf.genera({"denominazione": "ASD Prova", "sede": "Via Prova 1", "codice_fiscale": "91000000000", "attivita": "Calcio"},
                          {"numero": "2/2026", "data": "28/10/2026", "praticante": "Rossi Luca", "praticante_cf": "RSSLCU12A01H501X",
                           "causale": "Erogazione Liberale - Anno 2026", "importo": 50.0, "pagamento": "BONIFICO", "bollo": 0})
open(r"..\ricevuta_erogazione_prova.pdf", "wb").write(pdf)
print("TUTTO OK")
