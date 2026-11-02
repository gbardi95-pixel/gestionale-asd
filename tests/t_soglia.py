import os, warnings
warnings.filterwarnings("ignore")
import copia_locale
assert "TURSO_DATABASE_URL" not in os.environ
from base_test import nuovo, db
f = os.path.abspath("app.py")
print([p.proto.text for p in nuovo(f, "pagina_dashboard").get("progress")])
c = db()  # fattura 2026 da 1.000 € non incassata a uno sponsor esistente
sid = c.execute("SELECT sponsor_id FROM fatture_sponsor_398 LIMIT 1").fetchone()[0]
c.execute("INSERT INTO fatture_sponsor_398 (numero_fattura, data_fattura, sponsor_id, oggetto_contratto, imponibile, iva_totale, totale_fattura, iva_da_versare_50, stima_ires_3) VALUES ('9/26', '2026-10-28', ?, 'prova', 1000, 220, 1220, 110, 30)", [sid])
# incasso 2026 di una fattura 2025 (sponsor nuovo, senza fatture registrate)
c.execute("INSERT INTO incassi_sponsor (sponsor_id, data_incasso, importo) VALUES (999, '2026-03-01', 122)"); c.commit()
print([p.proto.text for p in nuovo(f, "pagina_dashboard").get("progress")])
