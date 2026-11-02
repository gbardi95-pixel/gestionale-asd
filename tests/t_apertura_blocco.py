import os, sys, shutil
from base_test import prepara, nuovo
f = prepara("t_ap2")
nuovo(f, "pagina_dashboard")
os.chdir(os.path.dirname(f)); os.system(f'"{sys.executable}" ../storico_rendiconti.py data/contabilita_asd.db --scrivi > NUL 2>&1')
at = nuovo(f, "pagina_prima_nota")
print("avviso:", [w.value[:90] for w in at.warning])
print("salva disabilitato:", [b.disabled for b in at.button if "Salva apertura" in b.label])
