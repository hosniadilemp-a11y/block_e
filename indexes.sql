-- Indexes for GesImmeuble on Supabase PostgreSQL
-- Speeds up the most frequent queries in the application

-- cotisations: most filtered table (by user_id and annee)
CREATE INDEX IF NOT EXISTS idx_cotisations_user_id ON cotisations(user_id);
CREATE INDEX IF NOT EXISTS idx_cotisations_annee    ON cotisations(annee);

-- depenses: filtered by date year
CREATE INDEX IF NOT EXISTS idx_depenses_date ON depenses(date);

-- annonces: ordered by date DESC
CREATE INDEX IF NOT EXISTS idx_annonces_date ON annonces(date DESC);

-- logs: ordered by date DESC, filtered by user_id
CREATE INDEX IF NOT EXISTS idx_logs_date    ON logs(date DESC);
CREATE INDEX IF NOT EXISTS idx_logs_user_id ON logs(user_id);

-- votes: lookup by user + poll
CREATE INDEX IF NOT EXISTS idx_votes_user_id ON votes(user_id);
CREATE INDEX IF NOT EXISTS idx_votes_poll_id ON votes(poll_id);

-- suggestions: filtered by status
CREATE INDEX IF NOT EXISTS idx_suggestions_statut ON suggestions(statut);

-- poll_options: join on poll_id
CREATE INDEX IF NOT EXISTS idx_poll_options_poll_id ON poll_options(poll_id);

-- suggestions_votes: lookup by suggestion + user
CREATE INDEX IF NOT EXISTS idx_sv_suggestion_id ON suggestions_votes(suggestion_id);
CREATE INDEX IF NOT EXISTS idx_sv_user_id        ON suggestions_votes(user_id);
