"""Correzione ed eliminazione di una ricevuta già emessa: ricevuta, prima nota e PDF restano allineati."""
import datetime
from base_test import prepara, nuovo, db, bottone, campo

f = prepara("t_ricevuta_modifica")
at = nuovo(f, "pagina_ricevute")
c = db()
aid = c.execute("INSERT INTO anagrafiche (tipo, denominazione, codice_fiscale) VALUES ('SOCIO_CALCIATORE', 'Rossi Luca', 'RSSLCU12A01H501X')").lastrowid
c.commit()
at = nuovo(f, "pagina_ricevute")
campo(at.selectbox, "Socio").set_value(campo(at.selectbox, "Socio").options[0])
campo(at.number_input, "Importo Incassato").set_value(150.0)
bottone(at, "Emetti Ricevuta").click().run()
assert not at.exception, at.exception
ric = c.execute("SELECT id, numero_ricevuta, data_emissione FROM ricevute_istituzionali").fetchall()
assert len(ric) == 1, ric
rid, numero, data = ric[0]


def saldi(cod):
    return c.execute("SELECT COALESCE(SUM(r.dare), 0), COALESCE(SUM(r.avere), 0) FROM righe_prima_nota r JOIN piano_dei_conti p ON p.id = r.sottoconto_id "
                     "WHERE p.codice = ?", [cod]).fetchone()


assert saldi("10.01.001") == (150.0, 0.0) and saldi("50.01.001") == (0.0, 150.0), (saldi("10.01.001"), saldi("50.01.001"))

# correzione: importo, tipologia, pagamento e data dell'anno prima
at = nuovo(f, "pagina_ricevute")
nuova_data = datetime.date(2025, 9, 10)
at.date_input(key=f"ric_mod_{rid}_data").set_value(nuova_data)
at.text_input(key=f"ric_mod_{rid}_num").set_value("5/2025")
at.number_input(key=f"ric_mod_{rid}_imp").set_value(120.0)
at.selectbox(key=f"ric_mod_{rid}_tipo").set_value("Quota Iscrizione e Frequenza Campionato")
at.selectbox(key=f"ric_mod_{rid}_pag").set_value("CONTANTI")
bottone(at, "💾 Salva le correzioni").click().run()
assert not at.exception, at.exception
assert not at.error, [e.value for e in at.error]
r = c.execute("SELECT numero_ricevuta, data_emissione, importo, causale, modalita_pagamento, length(pdf_base64) FROM ricevute_istituzionali WHERE id = ?", [rid]).fetchone()
assert r[0] == "5/2025" and r[1] == "2025-09-10" and r[2] == 120.0 and r[3].startswith("Quota Iscrizione") and r[4] == "CONTANTI" and r[5] > 100, r
assert c.execute("SELECT COUNT(*) FROM movimenti_prima_nota WHERE causale LIKE 'Incasso%'").fetchone()[0] == 1
assert saldi("10.01.001") == (0.0, 0.0), saldi("10.01.001")
assert saldi("10.01.002") == (120.0, 0.0) and saldi("50.01.002") == (0.0, 120.0), (saldi("10.01.001"), saldi("50.01.002"))
assert saldi("50.01.001") == (0.0, 0.0)
m = c.execute("SELECT numero_documento, data_registrazione FROM movimenti_prima_nota WHERE causale LIKE 'Incasso%'").fetchone()
assert m == ("5/2025", "2025-09-10"), m

# numero senza l'anno della data: rifiutato
at = nuovo(f, "pagina_ricevute")
at.text_input(key=f"ric_mod_{rid}_num").set_value("7")
bottone(at, "💾 Salva le correzioni").click().run()
assert at.error and "anno" in at.error[0].value, [e.value for e in at.error]
assert c.execute("SELECT numero_ricevuta FROM ricevute_istituzionali WHERE id = ?", [rid]).fetchone()[0] == "5/2025"

# eliminazione: sparisce anche la scrittura
at = nuovo(f, "pagina_ricevute")
[x for x in at.checkbox if x.label.startswith("Confermo di voler eliminare questa ricevuta")][0].check().run()
bottone(at, "🗑️ Elimina la ricevuta").click().run()
assert not at.exception, at.exception
assert c.execute("SELECT COUNT(*) FROM ricevute_istituzionali").fetchone()[0] == 0
assert c.execute("SELECT COUNT(*) FROM movimenti_prima_nota WHERE causale LIKE 'Incasso%'").fetchone()[0] == 0
assert c.execute("SELECT COUNT(*) FROM righe_prima_nota").fetchone()[0] == 0
print("TUTTO OK")
