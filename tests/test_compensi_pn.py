from base_test import prepara, nuovo, db, bottone, campo
import datetime
f = prepara("t_comp_pn")
at = nuovo(f, "pagina_lavoro_sportivo")
c = db()
aid = c.execute("INSERT INTO anagrafiche (tipo, denominazione) VALUES ('COLLABORATORE_SPORTIVO', 'Mister Uno')").lastrowid
c.execute("INSERT INTO collaboratori_sportivi (anagrafica_id, mansione, tipo_contratto) VALUES (?, 'Allenatore', 'CO.CO.CO_SPORTIVO')", [aid])
c.commit()
righe = lambda m: c.execute("SELECT p.codice, r.dare, r.avere FROM righe_prima_nota r JOIN piano_dei_conti p ON p.id = r.sottoconto_id WHERE r.movimento_id = ? ORDER BY r.id", [m]).fetchall()
print("conti nuovi:", c.execute("SELECT codice, nome FROM piano_dei_conti WHERE codice IN ('20.02.003', '20.02.004', '40.01.007')").fetchall())
at = nuovo(f, "pagina_lavoro_sportivo")
anno = datetime.date.today().year
def compenso(data, lordo, con="BONIFICO"):
    campo(at.date_input, "Data Erogazione").set_value(data)
    campo(at.number_input, "Importo Lordo").set_value(lordo)
    campo(at.selectbox, "Netto pagato con").set_value(con)
    bottone(at, "Eroga Compenso").click().run()
    assert not at.exception, at.exception
compenso(datetime.date(anno, 1, 31), 3000.0)
compenso(datetime.date(anno, 2, 28), 4000.0, "CONTANTI")
print("compensi:", c.execute("SELECT importo_lordo, ritenuta_inps, ritenuta_irpef, importo_netto, movimento_id FROM compensi_sportivi").fetchall())
print("mov 1:", righe(1))
print("mov 2:", righe(2), "bilanciato:", round(sum(r[1] for r in righe(2)), 2) == round(sum(r[2] for r in righe(2)), 2))
print("expander:", [e.label for e in at.expander if "F24" in e.label])
bottone(at, "Registra il versamento").click().run()
assert not at.exception, at.exception
print("F24:", [s.value for s in at.success][:1], righe(3))
print("expander dopo:", [e.label for e in at.expander if "F24" in e.label])
# eliminazione dalla prima nota del secondo compenso
at = nuovo(f, "pagina_prima_nota")
sb = at.selectbox(key="pn_mod_sel"); sb.set_value([o for o in sb.options if o.startswith("N° 2 ")][0]).run()
print("avviso:", [w.value[:50] for w in at.warning if "compenso" in w.value])
at.checkbox(key="pn_mod_2_conferma").check().run(); at.button(key="pn_mod_2_elimina").click().run()
print("compensi rimasti:", c.execute("SELECT id, importo_lordo FROM compensi_sportivi").fetchall())
print("TUTTO OK")
