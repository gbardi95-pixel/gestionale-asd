"""Secondo blocco: correzione/eliminazione spese con prima nota coerente, sezioni della prima nota, elenco soci."""
import warnings
warnings.filterwarnings("ignore")
from base_test import prepara, nuovo, db, bottone, campo

f = prepara("t_blocco2")
at = nuovo(f, "pagina_dashboard")
c = db()

def saldo(codice):
    return c.execute("SELECT ROUND(COALESCE(SUM(r.dare - r.avere), 0), 2) FROM righe_prima_nota r JOIN piano_dei_conti p ON p.id = r.sottoconto_id "
                     "WHERE p.codice = ?", [codice]).fetchone()[0]

def nuova_spesa(at, nome, totale, stato):
    campo(at.text_input, "Nome del nuovo fornitore").input(nome)
    campo(at.text_input, "Descrizione").input("prova " + nome)
    campo(at.number_input, "Totale pagato").set_value(totale)
    campo(at.selectbox, "Pagamento").set_value(stato)
    bottone(at, "💾 Registra la spesa").click().run()
    assert not at.exception, at.exception

# 1. spesa da pagare 100, poi pagata con bonifico; poi corretta a 120
at = nuovo(f, "pagina_spese")
nuova_spesa(at, "Forn A", 100.0, "Da pagare")
bottone(at, "✅ Registra il pagamento").click().run()
sid = c.execute("SELECT id FROM fatture_passive").fetchone()[0]
at = nuovo(f, "pagina_spese")
campo(at.selectbox, "Spesa da correggere").set_value(sid).run()
campo(at.number_input, "Totale (€)").set_value(120.0)
bottone(at, "💾 Salva la correzione").click().run()
assert not at.exception, at.exception
print("dopo correzione:", [s.value for s in at.success][:1], "| registro", c.execute("SELECT totale, imponibile FROM fatture_passive").fetchall())
print("  costo", saldo(c.execute("SELECT categoria_spesa FROM fatture_passive").fetchone()[0]), "debiti", saldo("20.01.001"), "banca", saldo("10.01.001"))

# 2. spesa pagata subito in contanti 50, corretta a 40 con altra categoria
at = nuovo(f, "pagina_spese")
nuova_spesa(at, "Forn B", 50.0, "Pagata con CONTANTI")
sid2 = c.execute("SELECT MAX(id) FROM fatture_passive").fetchone()[0]
at = nuovo(f, "pagina_spese")
campo(at.selectbox, "Spesa da correggere").set_value(sid2).run()
campo(at.selectbox, "Categoria").select_index(2)
campo(at.number_input, "Totale (€)").set_value(40.0)
bottone(at, "💾 Salva la correzione").click().run()
assert not at.exception, at.exception
cat2 = c.execute("SELECT categoria_spesa FROM fatture_passive WHERE id = ?", [sid2]).fetchone()[0]
print("spesa 2: categoria", cat2, "costo", saldo(cat2), "cassa", saldo("10.01.002"),
      "| righe", c.execute("SELECT COUNT(*) FROM righe_prima_nota").fetchone()[0])

# 3. eliminazione della prima spesa (con il suo pagamento separato)
at = nuovo(f, "pagina_spese")
campo(at.selectbox, "Spesa da correggere").set_value(sid).run()
campo(at.checkbox, "Confermo di voler eliminare").check().run()
bottone(at, "🗑️ Elimina la spesa").click().run()
assert not at.exception, at.exception
print("dopo eliminazione: spese", c.execute("SELECT COUNT(*) FROM fatture_passive").fetchone()[0],
      "movimenti", c.execute("SELECT COUNT(*) FROM movimenti_prima_nota").fetchone()[0], "banca", saldo("10.01.001"), "debiti", saldo("20.01.001"))
print("bilancio totale dare-avere:", c.execute("SELECT ROUND(SUM(dare - avere), 2) FROM righe_prima_nota").fetchone()[0])

# 4. prima nota: le tre sezioni si aprono; vista semplice
for sez in ("movimenti", "mese", "anno"):
    import streamlit as st
    from streamlit.testing.v1 import AppTest
    st.cache_data.clear()
    at = AppTest.from_file(f, default_timeout=120)
    at.session_state["autenticato"] = True
    at.session_state["pagina_test"] = "pagina_prima_nota"
    at.session_state["pn_sezione"] = sez
    at.run()
    assert not at.exception, (sez, at.exception)
    print("sezione", sez, "schede:", [t.label for t in at.tabs], "| colonne giornale:",
          list(at.dataframe[-1].value.columns) if sez == "movimenti" else "-")

# 5. soci
at = nuovo(f, "pagina_soci")
print("soci colonne:", list(at.dataframe[0].value.columns))
print("ok")
