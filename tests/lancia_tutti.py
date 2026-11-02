"""Lancia tutte le prove (una alla volta) e dice quali riescono. Uso: python tests/lancia_tutti.py"""
import glob, os, subprocess, sys

AQUI = os.path.dirname(os.path.abspath(__file__))
ambiente = dict(os.environ, PYTHONIOENCODING="utf-8")
for k in ("TURSO_DATABASE_URL", "TURSO_AUTH_TOKEN"):
    ambiente.pop(k, None)  # le prove non devono mai toccare il database vero
falliti = []
prove = sorted(glob.glob(os.path.join(AQUI, "t_*.py")) + glob.glob(os.path.join(AQUI, "test_*.py")))
for f in prove:
    r = subprocess.run([sys.executable, f], cwd=AQUI, env=ambiente, capture_output=True, text=True, encoding="utf-8", errors="replace")
    ok = r.returncode == 0
    print(("OK      " if ok else "FALLITA ") + os.path.basename(f))
    if not ok:
        falliti.append(f)
        print("\n".join((r.stdout + r.stderr).strip().splitlines()[-6:]))
print(f"\n{len(prove) - len(falliti)} riuscite su {len(prove)}")
sys.exit(1 if falliti else 0)
