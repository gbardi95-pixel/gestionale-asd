from base_test import prepara, nuovo, db, bottone, campo
import datetime
f = prepara("t_spese")
at = nuovo(f, "pagina_spese")
c = db()
righe = lambda m: c.execute("SELECT p.codice, r.dare, r.avere FROM righe_prima_nota r JOIN piano_dei_conti p ON p.id = r.sottoconto_id WHERE r.movimento_id = ? ORDER BY r.id", [m]).fetchall()

def spesa(fornitore_nuovo, piva, descr, cat_inizio, totale, iva, stato, fornitore=None):
    if fornitore:
        campo(at.selectbox, "Fornitore").set_value(fornitore)
    campo(at.text_input, "Nome del nuovo fornitore").set_value(fornitore_nuovo)
    campo(at.text_input, "Partita IVA").set_value(piva)
    campo(at.text_input, "Descrizione").set_value(descr)
    cs = campo(at.selectbox, "Categoria"); cs.set_value([o for o in cs.options if o.startswith(cat_inizio)][0])
    campo(at.number_input, "Totale").set_value(totale)
    campo(at.number_input, "di cui IVA").set_value(iva)
    campo(at.selectbox, "Pagamento").set_value(stato)
    bottone(at, "💾 Registra la spesa").click().run()
    assert not at.exception, at.exception

spesa("", "", "x", "Affitto", 100.0, 0.0, "Pagata con BONIFICO")
print("errore senza fornitore:", [e.value for e in at.error])
spesa("Comune di Prova", "00123456789", "Affitto campo ottobre", "Affitto", 300.0, 0.0, "Pagata con BONIFICO")
print("flash:", [s.value for s in at.success][:1])
spesa("Sport Shop", "", "20 palloni", "Materiale", 244.0, 44.0, "Da pagare")
spesa("", "", "Divise", "Materiale", 122.0, 22.0, "Pagata con CONTANTI", fornitore="Sport Shop")
print("spese:", c.execute("SELECT f.id, a.denominazione, a.partita_iva, f.totale, f.imponibile, f.iva, f.categoria_spesa, f.modalita_pagamento, f.data_pagamento, f.movimento_id, f.movimento_pagamento_id FROM fatture_passive f JOIN anagrafiche a ON a.id = f.fornitore_id").fetchall())
print("fornitori:", c.execute("SELECT COUNT(*) FROM anagrafiche WHERE tipo = 'FORNITORE'").fetchone())
for m in (1, 2, 3):
    print("mov", m, righe(m))
print("expander:", [e.label for e in at.expander])
# pagamento della spesa da pagare
campo(at.selectbox, "Con").set_value("PAYPAL")
bottone(at, "✅ Registra il pagamento").click().run()
assert not at.exception, at.exception
print("dopo pagamento:", c.execute("SELECT modalita_pagamento, data_pagamento, movimento_pagamento_id FROM fatture_passive WHERE id = 2").fetchone(), righe(4))
print("registro:", at.dataframe[0].value[["Fornitore", "Categoria", "Totale (€)", "Pagata"]].values.tolist())
print("caption:", [x.value for x in at.caption if "Esercizio" in x.value])
# eliminazione del pagamento dalla prima nota: la spesa torna da pagare
at = nuovo(f, "pagina_prima_nota")
sb = at.selectbox(key="pn_mod_sel"); sb.set_value([o for o in sb.options if o.startswith("N° 4 ")][0]).run()
print("avvisi:", [w.value[:60] for w in at.warning if "registro spese" in w.value])
at.checkbox(key="pn_mod_4_conferma").check().run(); at.button(key="pn_mod_4_elimina").click().run()
print("spesa 2 dopo eliminazione pagamento:", c.execute("SELECT data_pagamento, movimento_pagamento_id FROM fatture_passive WHERE id = 2").fetchone())
sb = at.selectbox(key="pn_mod_sel"); sb.set_value([o for o in sb.options if o.startswith("N° 1 ")][0]).run()
at.checkbox(key="pn_mod_1_conferma").check().run(); at.button(key="pn_mod_1_elimina").click().run()
print("spese rimaste:", c.execute("SELECT id FROM fatture_passive").fetchall())
print("TUTTO OK")
