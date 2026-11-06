"""Mastrino di un conto nel rendiconto; campo squadre vuoto (NaN) letto senza errori."""
import datetime
from base_test import prepara, nuovo, db, bottone, campo

f = prepara("t_mastrino")
import math
from modules import utenti
assert utenti.squadre_da_testo(float("nan")) == [] and utenti.squadre_da_testo(None) == [] and utenti.squadre_da_testo("") == []
assert utenti.squadre_da_testo("A, B,,") == ["A", "B"]

at = nuovo(f, "pagina_prima_nota")
c = db()
cassa = c.execute("SELECT id FROM piano_dei_conti WHERE codice = '10.01.002'").fetchone()[0]
costo = c.execute("SELECT id FROM piano_dei_conti WHERE codice = '40.01.010'").fetchone()[0]
oggi = datetime.date.today().isoformat()
for importo, desc in ((40.0, "Ammenda prova"), (25.0, "Altra multa")):
    mid = c.execute("INSERT INTO movimenti_prima_nota (data_registrazione, numero_documento, causale, tipo_attivita) VALUES (?, 'X', ?, 'ISTITUZIONALE')",
                    [oggi, desc]).lastrowid
    c.execute("INSERT INTO righe_prima_nota (movimento_id, sottoconto_id, descrizione, dare, avere) VALUES (?, ?, ?, ?, 0)", [mid, costo, desc, importo])
    c.execute("INSERT INTO righe_prima_nota (movimento_id, sottoconto_id, descrizione, dare, avere) VALUES (?, ?, 'Cassa', 0, ?)", [mid, cassa, importo])
c.commit()

at = nuovo(f, "pagina_prima_nota")
at.session_state["pn_sezione"] = "anno"
at.run()
assert not at.exception, at.exception
sel = [s for s in at.selectbox if s.label == "Conto"]
assert sel and any(o.startswith("40.01.010") for o in sel[0].options), [o for o in (sel[0].options if sel else [])]
sel[0].set_value([o for o in sel[0].options if o.startswith("40.01.010")][0]).run()
assert not at.exception, at.exception
tot = [m for m in at.metric if m.label.startswith("Totale 40.01.010")]
assert tot and "65.00" in tot[0].value, [(m.label, m.value) for m in at.metric]
print("TUTTO OK")
