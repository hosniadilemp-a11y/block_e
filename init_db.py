import sqlite3
import os
from werkzeug.security import generate_password_hash
from datetime import datetime

def init_db():
    conn = sqlite3.connect('database.db')
    with open('schema.sql', encoding='utf-8') as f:
        conn.executescript(f.read())
    cur = conn.cursor()

    # 1. Users
    admin_pwd = os.environ.get('ADMIN_PASSWORD', '123')
    cur.execute("INSERT INTO users (username, password, role) VALUES (?, ?, ?)",
                ('admin', generate_password_hash(admin_pwd), 'admin'))
    
    resident_pwd = generate_password_hash('123')
    for code in range(81, 101):
        cur.execute("INSERT INTO users (username, password, role) VALUES (?, ?, ?)",
                    (str(code), resident_pwd, 'resident'))

    # 2. Appartements & Cotisations data
    cotisations_data = [
      { "appartement": 81, "resident": "Islem", "paiement": 0, "statut": "a ete deja informe" },
      { "appartement": 82, "resident": "Hadjaj", "paiement": 10000, "statut": "paye" },
      { "appartement": 83, "resident": "Inconnu", "paiement": 10000, "statut": "paye" },
      { "appartement": 84, "resident": "Inconnu", "paiement": 0, "statut": "inconnu" },
      { "appartement": 85, "resident": "Mouhamed", "paiement": 10000, "statut": "paye" },
      { "appartement": 86, "resident": "Inconnu", "paiement": 0, "statut": "a ete deja informe" },
      { "appartement": 87, "resident": "Messaoud", "paiement": 10000, "statut": "paye" },
      { "appartement": 88, "resident": "Adel", "paiement": 13000, "statut": "paye" },
      { "appartement": 89, "resident": "Madjid", "paiement": 13000, "statut": "paye" },
      { "appartement": 90, "resident": "Saber", "paiement": 13000, "statut": "paye" },
      { "appartement": 91, "resident": "Lyes", "paiement": 14400, "statut": "paye" },
      { "appartement": 92, "resident": "Inconnu", "paiement": 10000, "statut": "paye" },
      { "appartement": 93, "resident": "Nadhir", "paiement": 10000, "statut": "paye" },
      { "appartement": 94, "resident": "Nacer", "paiement": 10000, "statut": "paye" },
      { "appartement": 95, "resident": "Athman / Raouf", "paiement": 13000, "statut": "paye" },
      { "appartement": 96, "resident": "Abdelouahab", "paiement": 14400, "statut": "paye" },
      { "appartement": 97, "resident": "Youcef / Locataire", "paiement": 10000, "statut": "paye" },
      { "appartement": 98, "resident": "Ali / Redha", "paiement": 20000, "statut": "paye" },
      { "appartement": 99, "resident": "Salim", "paiement": 10000, "statut": "paye" },
      { "appartement": 100, "resident": "Ameur / Idriss", "paiement": 13000, "statut": "paye" }
    ]

    for item in cotisations_data:
        cur.execute("INSERT INTO appartements (numero, resident, statut) VALUES (?, ?, ?)",
                    (item['appartement'], item['resident'], item['statut']))
        appt_id = cur.lastrowid
        if item['paiement'] > 0:
            cur.execute("INSERT INTO cotisations (appartement_id, montant, annee, date) VALUES (?, ?, ?, ?)",
                        (appt_id, item['paiement'], 2025, '2025-01-01 10:00:00'))

    # 3. Dépenses data
    depenses_data = [
      { "date": "2025-01-15", "description": "Facture electricite 2024 avec penalite", "document": "Facture", "payePar": "Adel", "montant": 18800, "soldeApres": 185000, "categorie": "Utilities" },
      { "date": "2025-02-10", "description": "Digicode et fermeture magnetique (achat et installation)", "document": None, "payePar": "Lyes", "montant": 52000, "soldeApres": 133000, "categorie": "Securite" },
      { "date": "2025-03-05", "description": "Achat de 8 spots pour ASC (4 installes)", "document": "Bon", "payePar": "Abdelouahab et Lyes", "montant": 2800, "soldeApres": 130200, "categorie": "Maintenance" },
      { "date": "2025-04-12", "description": "Achat d'articles de menage", "document": "Facture", "payePar": "ABW", "montant": 6120, "soldeApres": 124080, "categorie": "Entretien" },
      { "date": "2025-05-20", "description": "Revision ASC", "document": "Bon", "payePar": "ABW", "montant": 6000, "soldeApres": 118080, "categorie": "Maintenance" },
      { "date": "2025-06-15", "description": "Gazon artificiel 3,25 m", "document": "Bon", "payePar": "ABW", "montant": 5200, "soldeApres": 112880, "categorie": "Amenagement" },
      { "date": "2025-07-02", "description": "Interrupteur pour la pompe ASC", "document": None, "payePar": "ABW", "montant": 200, "soldeApres": 112680, "categorie": "Maintenance" },
      { "date": "2025-07-06", "description": "Femme de menage", "document": None, "payePar": "ABW", "montant": 2500, "soldeApres": 110180, "categorie": "Entretien" },
      { "date": "2025-07-20", "description": "Imprimes de signalisation", "document": None, "payePar": "ABW", "montant": 1000, "soldeApres": 109180, "categorie": "Signalisation" },
      { "date": "2025-08-10", "description": "Peintures / papiers collants / teinte", "document": "Bon", "payePar": "ABW", "montant": 5240, "soldeApres": 103940, "categorie": "Renovation" },
      { "date": "2025-08-15", "description": "Peintre", "document": None, "payePar": "ABW", "montant": 8000, "soldeApres": 95940, "categorie": "Main d'oeuvre" },
      { "date": "2025-08-25", "description": "Electricite 2025", "document": "Facture", "payePar": "Lyes", "montant": 11175, "soldeApres": 84765, "categorie": "Utilities" },
      { "date": "2025-08-28", "description": "Femme de menage", "document": None, "payePar": "ABW", "montant": 2000, "soldeApres": 82765, "categorie": "Entretien" },
      { "date": "2025-10-09", "description": "Femme de menage", "document": None, "payePar": "Adel", "montant": 2000, "soldeApres": 80765, "categorie": "Entretien" },
      { "date": "2025-10-23", "description": "Femme de menage", "document": None, "payePar": "ABW", "montant": 2000, "soldeApres": 78765, "categorie": "Entretien" },
      { "date": "2025-10-27", "description": "Femme de menage", "document": None, "payePar": "ABW", "montant": 2500, "soldeApres": 76265, "categorie": "Entretien" },
      { "date": "2025-10-30", "description": "Nettoyage alentour du parking cote bloc E", "document": None, "payePar": "Lyes", "montant": 5000, "soldeApres": 71265, "categorie": "Entretien exterieur" },
      { "date": "2025-10-30", "description": "Achat de 2 projecteurs", "document": None, "payePar": "Ilyes", "montant": 5000, "soldeApres": 66265, "categorie": "Equipement" },
      { "date": "2025-10-30", "description": "Femme de menage", "document": None, "payePar": "Adel", "montant": 5000, "soldeApres": 56265, "categorie": "Entretien" }
    ]

    for d in depenses_data:
        cur.execute("INSERT INTO depenses (description, montant, date, categorie, payePar, soldeApres, document) VALUES (?, ?, ?, ?, ?, ?, ?)",
                    (d['description'], d['montant'], d['date'] + " 10:00:00", d['categorie'], d['payePar'], d['soldeApres'], d['document']))

    conn.commit()
    conn.close()

if __name__ == '__main__':
    init_db()
    print("Base de donnees V3 initialisee avec succes.")
