import datetime
from base_test import prepara, nuovo, db, bottone, campo
f = prepara("t_f24split")
at = nuovo(f, "pagina_ricevute")
c = db()
anno = str(datetime.date.today().year)
aid = c.execute("INSERT INTO anagrafiche (tipo, denominazione, codice_fiscale) VALUES ('SOCIO_CALCIATORE', 'Rossi Luca', 'RSSLCU12A01H501X')").lastrowid
c.execute("INSERT INTO tesserati_calcio (anagrafica_id, numero_tessera, categoria, tipo_tessera, gioca) VALUES (?, 'T1', 'PRIMA_SQUADRA', 'A', 1)", [aid])
c.execute("INSERT INTO parametri_stagione (esercizio, voce, categoria, costo_societa, quota_richiesta) VALUES (?, 'ATLETA', '', 9.5, 20)", [anno])
c.commit()

def emetti(importo, dividi=True, tipo="Quota Associativa Annua"):
    at = nuovo(f, "pagina_ricevute")
    campo(at.selectbox, "Socio").set_value(campo(at.selectbox, "Socio").options[0])
    campo(at.selectbox, "Tipologia").set_value(tipo)
    campo(at.number_input, "Importo Incassato").set_value(importo)
    if not dividi:
        campo(at.checkbox, "Se si versa più").uncheck()
    bottone(at, "Emetti Ricevuta").click().run()
    assert not at.exception, at.exception
    return [s.value for s in at.success][:1] + [e.value for e in at.error]

print("50 € con quota 20:", emetti(50.0))
print("altri 10 € (quota già pagata):", emetti(10.0))
print("10 € senza divisione:", emetti(10.0, dividi=False))
print("ricevute:", c.execute("SELECT numero_ricevuta, causale, importo, length(pdf_base64) > 1000 FROM ricevute_istituzionali ORDER BY id").fetchall())
print("conti:", c.execute("SELECT p.codice, SUM(r.avere) FROM righe_prima_nota r JOIN piano_dei_conti p ON p.id = r.sottoconto_id WHERE r.avere > 0 GROUP BY p.codice").fetchall())
# PDF salvato: è quello che si scarica
import base64
from modules import ricevuta_pdf
pdf = base64.b64decode(c.execute("SELECT pdf_base64 FROM ricevute_istituzionali WHERE causale LIKE 'Erogazione%'").fetchone()[0])
open(r"..\ricevuta_salvata_prova.pdf", "wb").write(pdf); print("pdf salvato:", pdf[:8])

# F24: IVA 3° trimestre 55 € (detrazione 50%) + IRES saldo 19,15 €
c.execute("INSERT INTO movimenti_prima_nota (data_registrazione, numero_documento, causale) VALUES (?, 'X', 'debito iva')", [f"{anno}-09-30"])
mid = c.execute("SELECT MAX(id) FROM movimenti_prima_nota").fetchone()[0]
iva_id = c.execute("SELECT id FROM piano_dei_conti WHERE codice = '20.02.001'").fetchone()[0]
cred_id = c.execute("SELECT id FROM piano_dei_conti WHERE codice = '10.02.002'").fetchone()[0]
c.execute("INSERT INTO righe_prima_nota (movimento_id, sottoconto_id, dare, avere) VALUES (?, ?, 110, 0), (?, ?, 0, 110)", [mid, cred_id, mid, iva_id]); c.commit()
at = nuovo(f, "pagina_prima_nota")
import pandas as pd
ed = at.get("data_editor")[0] if at.get("data_editor") else None
print("editor:", ed is not None)
EOF_MARKER = None
