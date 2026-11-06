"""Base comune per i test: copia l'app in una cartella di prova con database SQLite locale vuoto."""
import os, shutil, sqlite3, sys
import tempfile
AQUI = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.dirname(AQUI)
SCR = os.path.join(tempfile.gettempdir(), "prove_gestionale")
os.makedirs(SCR, exist_ok=True)
sys.path.insert(0, AQUI)


def prepara(nome, segreti='APP_PASSWORD = "prova"\nNOME_SOCIETA = "ASD Prova"\n'):
    T = os.path.join(SCR, nome)
    shutil.rmtree(T, ignore_errors=True)
    os.makedirs(os.path.join(T, ".streamlit"))
    shutil.copy(os.path.join(SRC, "app.py"), T)
    shutil.copytree(os.path.join(SRC, "modules"), os.path.join(T, "modules"), ignore=shutil.ignore_patterns("__pycache__"))
    shutil.copytree(os.path.join(SRC, "modelli"), os.path.join(T, "modelli"))
    open(os.path.join(T, ".streamlit", "secrets.toml"), "w").write(segreti)
    os.chdir(T)
    for k in ("TURSO_DATABASE_URL", "TURSO_AUTH_TOKEN"):
        os.environ.pop(k, None)
    sys.path.insert(0, T)
    f = os.path.join(T, "app.py")
    s = open(f, encoding="utf-8").read().replace("pagina.run()", "_scelta = st.session_state.get('pagina_test')\nglobals()[_scelta]() if _scelta else pagina.run()")
    open(f, "w", encoding="utf-8").write(s)
    return f


def nuovo(f, pagina):
    import streamlit as st
    from streamlit.testing.v1 import AppTest
    st.cache_data.clear()
    at = AppTest.from_file(f, default_timeout=120)
    at.session_state["autenticato"] = True
    at.session_state["pagina_test"] = pagina
    at.run()
    assert not at.exception, at.exception
    return at


def db():
    return sqlite3.connect(os.path.join("data", "contabilita_asd.db"))


def bottone(at, inizio):
    return [b for b in at.button if b.label.startswith(inizio)][0]


def campo(elenco, etichetta):
    return [x for x in elenco if x.label.startswith(etichetta)][0]


def vai(at, chiave, inizio):
    """Sceglie la scheda di una pagina (le schede non si vedono più tutte insieme) e rilancia la pagina."""
    import ast
    albero = ast.parse(open("app.py", encoding="utf-8").read())
    for n in ast.walk(albero):
        if isinstance(n, ast.Assign) and isinstance(n.targets[0], ast.Name) and n.targets[0].id.startswith("schede_") and isinstance(n.value, ast.List):
            for e in n.value.elts:
                if e.value.split(" ", 1)[-1].startswith(inizio) or e.value.startswith(inizio):
                    at.session_state[chiave] = e.value
                    at.run()
                    assert not at.exception, at.exception
                    return at
    raise AssertionError(f"scheda non trovata: {inizio}")
