"""Piano dei conti: tesseramenti, affiliazione, iscrizione ai campionati e multe sono conti separati; un database vecchio viene aggiornato."""
import warnings
warnings.filterwarnings("ignore")
from base_test import prepara, nuovo, db

f = prepara("t_conti_divisi")
nuovo(f, "pagina_dashboard")
c = db()
# simula un database con i nomi di prima e senza i conti nuovi
c.execute("UPDATE piano_dei_conti SET nome = 'Tasse Affiliazione e Tesseramenti Federazione/Ente' WHERE codice = '40.01.002'")
c.execute("UPDATE piano_dei_conti SET nome = 'Iscrizione Campionati, Multe e Sanzioni Sportive' WHERE codice = '40.01.006'")
c.execute("DELETE FROM piano_dei_conti WHERE codice IN ('40.01.009', '40.01.010')")
c.commit()
c.close()
from modules.db import init_db
init_db(21)  # l'aggiornamento che parte all'avvio quando la versione dello schema cambia
c = db()
conti = dict(c.execute("SELECT codice, nome FROM piano_dei_conti WHERE codice IN ('40.01.002', '40.01.006', '40.01.009', '40.01.010')").fetchall())
print(conti)
assert conti == {"40.01.002": "Tesseramenti (Tessere e Schede Attività)", "40.01.006": "Iscrizione ai Campionati",
                 "40.01.009": "Affiliazione alla Federazione/Ente", "40.01.010": "Multe e Sanzioni Sportive"}
# un conto rinominato a mano non viene toccato
c.execute("UPDATE piano_dei_conti SET nome = 'Nome scelto da me' WHERE codice = '40.01.006'")
c.commit()
c.close()
init_db(21)
c = db()
assert c.execute("SELECT nome FROM piano_dei_conti WHERE codice = '40.01.006'").fetchone()[0] == "Nome scelto da me"
nuovi = [r[0] for r in c.execute("SELECT codice FROM piano_dei_conti WHERE codice IN ('40.01.011', '40.01.012', '40.01.013', '40.01.014', '50.01.004', '50.01.005', '50.01.006', '50.01.007')")]
assert len(nuovi) == 8, nuovi
print("TUTTO OK")
