from base_test import prepara, nuovo, db
import datetime
f = prepara("t_prom_bk")
def avvisi(at):
    return [w.value for w in at.sidebar.warning if "copia di sicurezza" in w.value], [t.value for t in at.toast]
at = nuovo(f, "pagina_dashboard")
print("mai fatto:", avvisi(at))
at.run(); print("secondo giro stessa sessione (toast una sola volta):", avvisi(at))
c = db()
c.execute("INSERT INTO impostazioni (chiave, valore) VALUES ('ultimo_backup', ?) ON CONFLICT(chiave) DO UPDATE SET valore = excluded.valore",
          [(datetime.date.today() - datetime.timedelta(days=10)).isoformat()]); c.commit()
print("10 giorni fa:", avvisi(nuovo(f, "pagina_dashboard")))
c.execute("UPDATE impostazioni SET valore = ? WHERE chiave = 'ultimo_backup'", [(datetime.date.today() - datetime.timedelta(days=6)).isoformat()]); c.commit()
print("6 giorni fa:", avvisi(nuovo(f, "pagina_dashboard")))
nuovo(f, "registra_backup")
print("dopo download:", c.execute("SELECT valore FROM impostazioni WHERE chiave = 'ultimo_backup'").fetchone())
at = nuovo(f, "pagina_backup")
print("didascalia:", [x.value for x in at.caption if "Ultima copia" in x.value], "| avvisi:", avvisi(at))
print("TUTTO OK")
