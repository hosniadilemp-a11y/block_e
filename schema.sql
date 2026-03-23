DROP TABLE IF EXISTS logs;
DROP TABLE IF EXISTS votes;
DROP TABLE IF EXISTS poll_options;
DROP TABLE IF EXISTS polls;
DROP TABLE IF EXISTS annonces;
DROP TABLE IF EXISTS depenses;
DROP TABLE IF EXISTS cotisations;
DROP TABLE IF EXISTS appartements;
DROP TABLE IF EXISTS suggestions_votes;
DROP TABLE IF EXISTS suggestions;
DROP TABLE IF EXISTS documents;
DROP TABLE IF EXISTS users;

CREATE TABLE users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT NOT NULL UNIQUE,
    password TEXT NOT NULL,
    role TEXT NOT NULL DEFAULT 'resident'
);

CREATE TABLE appartements (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    numero INTEGER NOT NULL UNIQUE,
    resident TEXT,
    statut TEXT DEFAULT 'inconnu'
);

CREATE TABLE cotisations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    appartement_id INTEGER NOT NULL,
    montant REAL NOT NULL,
    annee INTEGER NOT NULL DEFAULT 2025,
    date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (appartement_id) REFERENCES appartements (id)
);

CREATE TABLE documents (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    titre TEXT NOT NULL,
    chemin TEXT NOT NULL,
    categorie TEXT NOT NULL,
    annee INTEGER NOT NULL,
    date_upload TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE depenses (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    description TEXT NOT NULL,
    montant REAL NOT NULL,
    date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    categorie TEXT NOT NULL,
    payePar TEXT NOT NULL,
    soldeApres REAL NOT NULL,
    document TEXT
);

CREATE TABLE polls (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    question TEXT NOT NULL,
    is_active BOOLEAN DEFAULT 1,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE poll_options (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    poll_id INTEGER NOT NULL,
    texte TEXT NOT NULL,
    FOREIGN KEY (poll_id) REFERENCES polls (id)
);

CREATE TABLE votes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    option_id INTEGER NOT NULL,
    poll_id INTEGER NOT NULL,
    FOREIGN KEY (user_id) REFERENCES users (id),
    FOREIGN KEY (option_id) REFERENCES poll_options (id),
    FOREIGN KEY (poll_id) REFERENCES polls (id),
    UNIQUE(user_id, poll_id)
);

CREATE TABLE suggestions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    titre TEXT NOT NULL,
    description TEXT NOT NULL,
    auteur_id INTEGER NOT NULL,
    statut TEXT DEFAULT 'En attente', -- En attente / Approuvee / Rejetee / En cours
    date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (auteur_id) REFERENCES users(id)
);

CREATE TABLE suggestions_votes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    suggestion_id INTEGER NOT NULL,
    user_id INTEGER NOT NULL,
    type_vote TEXT NOT NULL, -- 'up' or 'down'
    FOREIGN KEY (suggestion_id) REFERENCES suggestions(id),
    FOREIGN KEY (user_id) REFERENCES users(id),
    UNIQUE(suggestion_id, user_id)
);

CREATE TABLE annonces (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    titre TEXT NOT NULL,
    contenu TEXT NOT NULL,
    date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER,
    action TEXT NOT NULL,
    details TEXT,
    date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(user_id) REFERENCES users(id)
);
