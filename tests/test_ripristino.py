from base_test import prepara, nuovo, db
f = prepara("t_ripristino")
at = nuovo(f, "pagina_backup")
c = db()
# dati di prova con testi particolari, vuoti obbligatori e collegamenti
aid = c.execute("INSERT INTO anagrafiche (tipo, denominazione, codice_fiscale, note, telefono) VALUES ('SOCIO_CALCIATORE', 'D''Angelo Luca', 'X', '=1+1 formula', '3331234567')").lastrowid
c.execute("INSERT INTO tesserati_calcio (anagrafica_id, numero_tessera, categoria, quota_stagionale) VALUES (?, '270164435', 'PRIMA_SQUADRA', 12.5)", [aid])
c.execute("INSERT INTO certificati_medici (anagrafica_id, tipo, data_rilascio, data_scadenza, stato_idoneita) VALUES (?, 'AGONISTICO', '', '2027-01-01', 'IDONEO')", [aid])
m = c.execute("INSERT INTO movimenti_prima_nota (data_registrazione, numero_documento, causale) VALUES ('2026-05-01', 'F1', 'Prova')").lastrowid
c.execute("INSERT INTO righe_prima_nota (movimento_id, sottoconto_id, dare, avere) VALUES (?, 1, 10.5, 0), (?, 2, 0, 10.5)", [m, m])
c.execute("INSERT INTO modelli_documenti (nome, contenuto_base64) VALUES ('prova', 'abc')") if c.execute("SELECT COUNT(*) FROM sqlite_master WHERE name='modelli_documenti'").fetchone()[0] else None
c.commit()
import sys
from modules import backup
def istantanea():
    return {t: sorted(map(repr, c.execute(f'SELECT * FROM "{t}"').fetchall())) for t in backup.elenco_tabelle(c)}
prima = istantanea()
copia, _ = backup.backup_completo(c, 12)
# si rovinano i dati
c.execute("DELETE FROM righe_prima_nota"); c.execute("UPDATE anagrafiche SET denominazione = 'ROVINATO'")
c.execute("INSERT INTO anagrafiche (tipo, denominazione) VALUES ('ALTRO', 'Intruso')"); c.commit()
versione, tabelle = backup.leggi_copia(copia)
script, attese = backup.script_ripristino(c, tabelle)
c.executescript(script)
dopo = istantanea()
diff = {t: (prima[t][:2], dopo[t][:2]) for t in prima if prima[t] != dopo[t]}
print("versione:", versione, "| tabelle:", len(attese), "| differenze:", diff)
print("anagrafica:", c.execute("SELECT denominazione, note, telefono FROM anagrafiche").fetchall(), c.execute("SELECT numero_tessera, quota_stagionale FROM tesserati_calcio").fetchall())
print("cert rilascio vuoto:", c.execute("SELECT data_rilascio FROM certificati_medici").fetchall())
print("FK attive:", c.execute("PRAGMA foreign_keys").fetchone())
# file non valido
try:
    backup.leggi_copia(b"non un excel")
except ValueError as e:
    print("file non valido:", e)
at = nuovo(f, "pagina_backup")
print("pagina:", [x.label for x in at.get("file_uploader")] if hasattr(at, "get") else "")
print("TUTTO OK")
