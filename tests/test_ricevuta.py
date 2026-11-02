import datetime
from base_test import prepara, nuovo, db, bottone, campo
f = prepara("t_ricevuta")
at = nuovo(f, "pagina_ricevute")
c = db()
aid = c.execute("INSERT INTO anagrafiche (tipo, denominazione, codice_fiscale) VALUES ('SOCIO_CALCIATORE', 'Rossi Luca', 'RSSLCU12A01H501X')").lastrowid
c.execute("INSERT INTO tesserati_calcio (anagrafica_id, numero_tessera, categoria) VALUES (?, 'T1', 'JUNIORES')", [aid])
c.commit()
at = nuovo(f, "pagina_ricevute")
print("expander:", [e.label for e in at.expander][:2])
# dati associazione
[x for x in at.text_input if x.label.startswith("Sede legale")][0].set_value("Via Roma 1, 00100 Città (XX)")
[x for x in at.text_input if x.label == "Codice fiscale"][0].set_value("91000000000")
[x for x in at.text_input if x.label.startswith("Attività sportiva")][0].set_value("Calcio")
bottone(at, "💾 Salva i dati dell'associazione").click().run()
assert not at.exception, at.exception
print("impostazioni:", c.execute("SELECT chiave, valore FROM impostazioni WHERE chiave LIKE 'societa_%' ORDER BY chiave").fetchall())
# ricevuta pagata dal genitore
campo(at.number_input, "Importo Incassato").set_value(150.0)
campo(at.text_input, "Pagato da").set_value("Rossi Mario")
campo(at.text_input, "Codice fiscale di chi ha pagato").set_value("rssmra80a01h501u")
bottone(at, "Emetti Ricevuta").click().run()
assert not at.exception, at.exception
print("flash:", [s.value for s in at.success][:1], [e.value for e in at.error])
print("ricevuta:", c.execute("SELECT numero_ricevuta, importo, versante_nome, versante_cf, marca_da_bollo FROM ricevute_istituzionali").fetchall())
at = nuovo(f, "pagina_ricevute")
print("download:", [b.label for b in at.get("download_button")])
import importlib, sys
app_mod = None
# genera il PDF con la funzione del modulo per salvarlo e controllarlo
from modules import ricevuta_pdf
pdf = ricevuta_pdf.genera({"denominazione": "ASD Prova", "sede": "Via Roma 1, 00100 Città (XX)", "codice_fiscale": "91000000000", "partita_iva": "", "attivita": "Calcio"},
                          {"numero": "1/2026", "data": "23/10/2026", "praticante": "Rossi Luca", "praticante_cf": "RSSLCU12A01H501X",
                           "versante": "Rossi Mario", "versante_cf": "RSSMRA80A01H501U", "causale": "Quota Associativa Annua - Anno 2026",
                           "importo": 150.0, "pagamento": "BONIFICO", "bollo": 2.0})
open(r"..\ricevuta_prova.pdf", "wb").write(pdf)
print("TUTTO OK")
