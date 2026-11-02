"""Nuovo tesseramento su database di prova vuoto: persona nuova con quota divisa, persona esistente, controlli."""
import warnings
warnings.filterwarnings("ignore")
from base_test import prepara, nuovo, db, bottone, campo

f = prepara("t_tesseramento")
at = nuovo(f, "pagina_dashboard")
c = db()
anno = __import__("datetime").date.today().year
c.execute("INSERT INTO parametri_stagione (esercizio, voce, categoria, quota_richiesta) VALUES (?, 'ATLETA', '', 100), (?, 'SCHEDA_ATTIVITA', '', 20)",
          [str(anno), str(anno)])
c.commit()

def gruppo(at, etichetta):
    return [g for g in at.get("button_group") if g.label == etichetta][0]

# 1. persona nuova, atleta, paga 130 in contanti: 100 di quota + 30 di erogazione liberale
at = nuovo(f, "pagina_tesseramento")
campo(at.text_input, "Cognome e nome").input("Rossi Mario").run()
campo(at.text_input, "Codice fiscale").input("rssmra00a01h501u").run()
campo(at.text_input, "Telefono").input("333 1234567").run()
print("importo proposto:", campo(at.number_input, "Importo").value)
campo(at.number_input, "Importo").set_value(130.0).run()
bottone(at, "💾 Salva").click().run()
print("senza pagamento:", [e.value for e in at.error])
gruppo(at, "Pagamento").set_value("CONTANTI").run()
bottone(at, "💾 Salva").click().run()
assert not at.exception, at.exception
print("esito:", [s.value for s in at.success])
print("bottoni:", [b.label for b in at.get("download_button")], [b.proto.label for b in at.get("link_button")])
print("anagrafica:", c.execute("SELECT denominazione, codice_fiscale, telefono FROM anagrafiche").fetchall())
print("tesserato:", c.execute("SELECT tipo_tessera, categoria, ruolo, gioca FROM tesserati_calcio").fetchall())
print("ricevute:", c.execute("SELECT numero_ricevuta, causale, importo, modalita_pagamento, length(pdf_base64) > 100 FROM ricevute_istituzionali").fetchall())
print("prima nota righe:", c.execute("SELECT COUNT(*) FROM righe_prima_nota").fetchone()[0])

# 2. stesso codice fiscale di nuovo: rifiutato
bottone(at, "➕ Nuovo tesseramento").click().run()
campo(at.text_input, "Cognome e nome").input("Rossi Mario bis").run()
campo(at.text_input, "Codice fiscale").input("RSSMRA00A01H501U").run()
campo(at.toggle, "Incassa").set_value(False).run()
bottone(at, "💾 Salva").click().run()
print("doppione:", [e.value for e in at.error])

# 3. persona già in anagrafica: ha già versato tutto, un nuovo incasso è rifiutato; poi una persona senza quota pagata
gruppo(at, "Persona").set_value("Già in anagrafica").run()
at.selectbox[0].set_value(1).run()
print("proposto per chi ha pagato:", campo(at.number_input, "Importo").value)
campo(at.number_input, "Importo").set_value(10.0).run()
gruppo(at, "Pagamento").set_value("BONIFICO").run()
bottone(at, "💾 Salva").click().run()
print("già pagato:", [e.value[:60] for e in at.error])

# 4. pagina ricevute e soci si aprono, con il registro e l'invio
at = nuovo(f, "pagina_ricevute")
print("ricevute: link", [b.proto.label for b in at.get("link_button")], "| pdf", [b.label for b in at.get("download_button")])
nuovo(f, "pagina_soci")
print("ok")
