import os, warnings
warnings.filterwarnings("ignore")
import copia_locale
assert "TURSO_DATABASE_URL" not in os.environ
from base_test import nuovo, db
f = os.path.abspath("app.py")
at = nuovo(f, "pagina_dashboard")
print([m.value for m in at.markdown if "Scadenze" in m.value])
for k in ("error", "warning", "info", "success"):
    print(k, [x.value for x in getattr(at, k)][:6])
print("progress:", [p.proto.text for p in at.get("progress")])
# simulo una ritenuta di settembre non versata
c = db()
mid = c.execute("INSERT INTO movimenti_prima_nota (data_registrazione, numero_documento, causale) VALUES ('2026-09-30', 'X', 'compenso prova')").lastrowid
r3 = c.execute("SELECT id FROM piano_dei_conti WHERE codice='20.02.003'").fetchone()[0]; cs = c.execute("SELECT id FROM piano_dei_conti WHERE codice='40.01.001'").fetchone()[0]
c.execute("INSERT INTO righe_prima_nota (movimento_id, sottoconto_id, dare, avere) VALUES (?, ?, 40, 0), (?, ?, 0, 40)", [mid, cs, mid, r3]); c.commit()
at = nuovo(f, "pagina_dashboard")
print("con ritenuta:", [x.value for x in at.error], [x.value for x in at.warning][:3])
