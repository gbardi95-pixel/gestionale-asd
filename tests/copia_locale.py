import os, sys, warnings, sqlite3
warnings.filterwarnings("ignore")
from base_test import prepara, nuovo
f = prepara("t_carico")
nuovo(f, "pagina_dashboard")
RADICE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, RADICE)
import libsql
from modules import backup
for r in open(os.path.join(RADICE, ".env"), encoding="utf-8"):
    if "=" in r and not r.startswith("#"):
        k, v = r.strip().split("=", 1); os.environ[k] = v.strip().strip('"')
t = libsql.connect(os.environ["TURSO_DATABASE_URL"], auth_token=os.environ["TURSO_AUTH_TOKEN"])
dati, _ = backup.backup_completo(t, 13)
loc = sqlite3.connect(os.path.join("data", "contabilita_asd.db"))
_, tab = backup.leggi_copia(dati)
script, attese = backup.script_ripristino(loc, tab); loc.executescript(script)
print("copia locale:", sum(attese.values()), "righe")
for k in ("TURSO_DATABASE_URL", "TURSO_AUTH_TOKEN"):
    os.environ.pop(k, None)  # da qui in poi la prova usa solo la copia locale
