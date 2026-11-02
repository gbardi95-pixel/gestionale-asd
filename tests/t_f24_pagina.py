from base_test import prepara, nuovo
f = prepara("t_f24pag")
at = nuovo(f, "pagina_prima_nota")
print("schede:", [t.label for t in at.tabs], "| errori:", at.exception)
print("info F24:", [i.value for i in at.info if "F24" in i.value])
