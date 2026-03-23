import os
import sqlite3
import csv
from io import StringIO
from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify, Response, send_from_directory
from werkzeug.security import check_password_hash, generate_password_hash
from functools import wraps
from datetime import datetime
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'default_secret_key_if_missing')
app.config['UPLOAD_FOLDER'] = os.path.join(app.root_path, 'static', 'uploads')
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

from database import get_db_connection

def add_log(user_id, action, details):
    conn = get_db_connection()
    conn.execute("INSERT INTO logs (user_id, action, details) VALUES (?, ?, ?)", (user_id, action, details))
    conn.commit()
    conn.close()

# Authentication decorators
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash("Veuillez vous connecter pour accéder à cette fonctionnalité.", "warning")
            return redirect(url_for('login', next=request.url))
        return f(*args, **kwargs)
    return decorated_function

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session or session.get('role') != 'admin':
            flash("Accès refusé. Vous devez être administrateur.", "danger")
            return redirect(url_for('index'))
        return f(*args, **kwargs)
    return decorated_function

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        conn = get_db_connection()
        if username == 'admin':
            # Strictly use ADMIN_PASSWORD from environment
            admin_pass = os.environ.get('ADMIN_PASSWORD')
            if admin_pass and password == admin_pass:
                # Success for admin
                user = conn.execute("SELECT * FROM users WHERE username = 'admin'").fetchone()
                if not user:
                    # Create admin if it doesn't exist (failsafe)
                    conn.execute("INSERT INTO users (username, password, role) VALUES ('admin', ?, 'admin')", 
                                 (generate_password_hash(admin_pass),))
                    conn.commit()
                    user = conn.execute("SELECT * FROM users WHERE username = 'admin'").fetchone()
                
                session['user_id'] = user['id']
                session['username'] = user['username']
                session['role'] = user['role']
                conn.close()
                flash("Connexion réussie (Admin).", "success")
                return redirect(url_for('index'))
        
        # Normal user login
        user = conn.execute("SELECT * FROM users WHERE username = ?", (username,)).fetchone()
        conn.close()
        
        if user and check_password_hash(user['password'], password):
            session['user_id'] = user['id']
            session['username'] = user['username']
            session['role'] = user['role']
            flash("Connexion réussie.", "success")
            return redirect(url_for('index'))
        else:
            flash("Nom d'utilisateur ou mot de passe incorrect.", "danger")
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    flash("Vous avez été déconnecté.", "info")
    return redirect(url_for('login'))

@app.route('/')
def index():
    annee_str = request.args.get('annee', 'all')
    conn = get_db_connection()
    
    # 1. SOLDE (GLOBAL TOUS LES TEMPS)
    total_cot_all = conn.execute("SELECT SUM(montant) FROM cotisations").fetchone()[0] or 0
    total_dep_all = conn.execute("SELECT SUM(montant) FROM depenses").fetchone()[0] or 0
    solde = total_cot_all - total_dep_all
    
    # For display of total "collected this year" vs "spent this year" 
    if annee_str.lower() == 'all':
        total_cotisations = total_cot_all
        total_depenses = total_dep_all
    else:
        try:
            annee = int(annee_str)
        except:
            annee = 2026
        total_cotisations = conn.execute("SELECT SUM(montant) FROM cotisations WHERE annee = ?", (annee,)).fetchone()[0] or 0
        total_depenses = conn.execute("SELECT SUM(montant) FROM depenses WHERE strftime('%Y', date) = ?", (str(annee),)).fetchone()[0] or 0
        
    appts = conn.execute("SELECT id FROM users WHERE role = 'resident'").fetchall()
    nb_a_jour = 0
    for a in appts:
        if annee_str.lower() == 'all':
            paid = conn.execute("SELECT SUM(montant) FROM cotisations WHERE user_id = ?", (a['id'],)).fetchone()[0] or 0
        else:
            paid = conn.execute("SELECT SUM(montant) FROM cotisations WHERE user_id = ? AND annee = ?", (a['id'], annee)).fetchone()[0] or 0
        if paid >= 10000:
            nb_a_jour += 1
    nb_en_retard = len(appts) - nb_a_jour

    polls = conn.execute("SELECT * FROM polls WHERE is_active = 1 ORDER BY created_at DESC").fetchall()
    polls_data = []
    for p in polls:
        options = conn.execute("SELECT * FROM poll_options WHERE poll_id = ?", (p['id'],)).fetchall()
        user_voted = None
        if 'user_id' in session:
            user_voted = conn.execute("SELECT * FROM votes WHERE user_id = ? AND poll_id = ?", 
                                     (session['user_id'], p['id'])).fetchone()
        
        options_data = []
        for opt in options:
            votes_count = conn.execute("SELECT COUNT(*) FROM votes WHERE option_id = ?", (opt['id'],)).fetchone()[0]
            options_data.append({'id': opt['id'], 'texte': opt['texte'], 'votes': votes_count})
            
        polls_data.append({
            'id': p['id'], 'question': p['question'], 'options': options_data,
            'user_voted': bool(user_voted),
            'user_vote_option_id': user_voted['option_id'] if user_voted else None
        })
        
    annonces = conn.execute("SELECT * FROM annonces ORDER BY date DESC LIMIT 5").fetchall()
    
    timeline_query = """
    SELECT 'cotisation' as type, CAST(c.date AS DATE) as date_str, c.date as full_date, c.montant, 'Cotisation Apt ' || u.appartement_numero as description 
    FROM cotisations c JOIN users u ON c.user_id = u.id
    UNION ALL
    SELECT 'depense' as type, CAST(date AS DATE) as date_str, date as full_date, montant, description 
    FROM depenses
    ORDER BY full_date DESC LIMIT 20
    """
    timeline = conn.execute(timeline_query).fetchall()
    
    if annee_str.lower() == 'all':
        dep_par_mois = conn.execute("SELECT strftime('%m', date) as mois, SUM(montant) FROM depenses GROUP BY mois").fetchall()
        dep_par_cat = conn.execute("SELECT categorie, SUM(montant) FROM depenses GROUP BY categorie").fetchall()
    else:
        dep_par_mois = conn.execute("SELECT strftime('%m', date) as mois, SUM(montant) FROM depenses WHERE strftime('%Y', date) = ? GROUP BY mois", (str(annee),)).fetchall()
        dep_par_cat = conn.execute("SELECT categorie, SUM(montant) FROM depenses WHERE strftime('%Y', date) = ? GROUP BY categorie", (str(annee),)).fetchall()
        
    chart_evo = {d[0]: d[1] for d in dep_par_mois if d[0]}
    chart_cat = {d[0]: d[1] for d in dep_par_cat}
    conn.close()
    
    return render_template('dashboard.html', 
                           solde=solde, total_cotisations=total_cotisations, total_depenses=total_depenses,
                           nb_a_jour=nb_a_jour, nb_en_retard=nb_en_retard, current_annee=str(annee_str),
                           polls=polls_data, annonces=annonces, timeline=timeline,
                           chart_evo=chart_evo, chart_cat=chart_cat)

@app.route('/vote/<int:poll_id>', methods=['POST'])
@login_required
def vote(poll_id):
    option_id = request.form.get('option_id')
    if option_id:
        try:
            conn = get_db_connection()
            conn.execute("INSERT INTO votes (user_id, option_id, poll_id) VALUES (?, ?, ?)", 
                        (session['user_id'], option_id, poll_id))
            conn.commit()
            conn.close()
            flash("Vote enregistré.", "success")
            add_log(session['user_id'], 'Vote', f'Poll ID {poll_id}')
        except sqlite3.IntegrityError:
            flash("Vous avez déjà voté.", "danger")
    return redirect(url_for('index'))

@app.route('/annonces')
def annonces():
    conn = get_db_connection()
    ann_list = conn.execute("SELECT * FROM annonces ORDER BY date DESC").fetchall()
    conn.close()
    return render_template('annonces.html', annonces=ann_list)

@app.route('/appartements')
def appartements():
    annee_str = request.args.get('annee', 'all')
    conn = get_db_connection()
    appts = conn.execute("SELECT * FROM users WHERE role = 'resident' ORDER BY appartement_numero DESC").fetchall()
    
    enriched_appts = []
    total_amount = 0
    for a in appts:
        if annee_str.lower() == 'all':
            total_paye = conn.execute("SELECT SUM(montant) FROM cotisations WHERE user_id = ?", (a['id'],)).fetchone()[0] or 0
        else:
            try:
                annee = int(annee_str)
            except:
                annee = 2026
            total_paye = conn.execute("SELECT SUM(montant) FROM cotisations WHERE user_id = ? AND annee = ?", (a['id'], annee)).fetchone()[0] or 0
        
        statut = 'inconnu'
        if total_paye >= 10000:
            statut = 'paye'
        elif total_paye > 0:
            statut = 'a ete deja informe'
        else:
            statut = 'non paye'
            
        enriched_appts.append({
            'id': a['id'],
            'numero': a['appartement_numero'],
            'resident': a['nom_complet'] or a['username'],
            'telephone': a['telephone'],
            'statut_annee': statut,
            'total_paye': total_paye
        })
        total_amount += total_paye
    conn.close()
    return render_template('appartements.html', appartements=enriched_appts, current_annee=str(annee_str), total_amount=total_amount)

@app.route('/api/appartement/<int:appt_id>')
def get_appartement(appt_id):
    conn = get_db_connection()
    appt = conn.execute("SELECT * FROM users WHERE id = ?", (appt_id,)).fetchone()
    if not appt: return jsonify({'error': 'Not found'}), 404
    cotisations = conn.execute("SELECT montant, annee, date FROM cotisations WHERE user_id = ? ORDER BY date DESC", (appt_id,)).fetchall()
    conn.close()
    
    return jsonify({
        'numero': appt['appartement_numero'], 'resident': appt['nom_complet'] or appt['username'], 'statut': appt['statut'],
        'total_paye': sum([c['montant'] for c in cotisations]),
        'historique': [{'montant': c['montant'], 'date': c['date'], 'annee': c['annee']} for c in cotisations]
    })

@app.route('/depenses')
def depenses():
    cat = request.args.get('categorie')
    annee = request.args.get('annee', 'all')
    conn = get_db_connection()
    
    q = "SELECT * FROM depenses WHERE 1=1"
    params = []
    
    if annee != 'all':
        q += " AND strftime('%Y', date) = ?"
        params.append(str(annee))
        
    if cat:
        q += " AND categorie = ?"
        params.append(cat)
        
    q += " ORDER BY date DESC"
    
    deps = conn.execute(q, tuple(params)).fetchall()
    categories_rows = conn.execute("SELECT DISTINCT categorie FROM depenses").fetchall()
    
    # Calculate Total for current filtered view
    q_total = "SELECT SUM(montant) FROM depenses WHERE 1=1"
    if annee != 'all': q_total += " AND strftime('%Y', date) = ?"
    if cat: q_total += " AND categorie = ?"
    
    total_val = conn.execute(q_total, tuple(params)).fetchone()[0] or 0
    
    conn.close()
    return render_template('depenses.html', depenses=deps, 
                           categories=[c['categorie'] for c in categories_rows], 
                           current_cat=cat, current_annee=str(annee), 
                           total_depenses=total_val)

# Exports
@app.route('/export/depenses')
@login_required
def export_depenses():
    conn = get_db_connection()
    depenses = conn.execute("SELECT date, description, categorie, montant, payePar FROM depenses ORDER BY date").fetchall()
    conn.close()
    def generate():
        data = StringIO()
        w = csv.writer(data)
        w.writerow(('Date', 'Description', 'Categorie', 'Montant', 'PayePar'))
        yield data.getvalue()
        data.seek(0); data.truncate(0)
        for d in depenses:
            w.writerow((d[0], d[1], d[2], d[3], d[4]))
            yield data.getvalue()
            data.seek(0); data.truncate(0)
    response = Response(generate(), mimetype='text/csv')
    response.headers.set("Content-Disposition", "attachment", filename="export_depenses.csv")
    return response

@app.route('/export/cotisations')
@login_required
def export_cotisations():
    conn = get_db_connection()
    cots = conn.execute("SELECT c.date, u.appartement_numero, u.nom_complet, c.annee, c.montant FROM cotisations c JOIN users u ON c.user_id = u.id ORDER BY c.date").fetchall()
    conn.close()
    def generate():
        data = StringIO()
        w = csv.writer(data)
        w.writerow(('Date', 'Appartement', 'Resident', 'Annee', 'Montant'))
        yield data.getvalue()
        data.seek(0); data.truncate(0)
        for c in cots:
            w.writerow((c[0], c[1], c[2], c[3], c[4]))
            yield data.getvalue()
            data.seek(0); data.truncate(0)
    response = Response(generate(), mimetype='text/csv')
    response.headers.set("Content-Disposition", "attachment", filename="export_cotisations.csv")
    return response

# Admin
@app.route('/admin', methods=['GET'])
@admin_required
def admin_dashboard():
    conn = get_db_connection()
    appts = conn.execute("SELECT * FROM users WHERE role = 'resident' ORDER BY appartement_numero").fetchall()
    depenses_recentes = conn.execute("SELECT * FROM depenses ORDER BY date DESC LIMIT 40").fetchall()
    cotisations_recentes = conn.execute("SELECT c.*, u.appartement_numero as numero FROM cotisations c JOIN users u ON c.user_id = u.id ORDER BY c.date DESC LIMIT 40").fetchall()
    active_polls = conn.execute("SELECT * FROM polls WHERE is_active = 1 ORDER BY created_at DESC").fetchall()
    annonces_recentes = conn.execute("SELECT * FROM annonces ORDER BY date DESC LIMIT 40").fetchall()
    system_users = conn.execute("SELECT * FROM users WHERE username != 'admin' ORDER BY role, username").fetchall()
    conn.close()
    return render_template('admin/admin_dashboard.html', 
                           appartements=appts, depenses=depenses_recentes,
                           cotisations=cotisations_recentes, active_polls=active_polls,
                           annonces=annonces_recentes, system_users=system_users)

@app.route('/admin/super_secret_logs_xyz123', methods=['GET'])
@admin_required
def admin_logs():
    if session.get('username') != 'admin':
        flash("Accès refusé. Journal d'audit réservé au compte Super Admin ('admin').", "danger")
        return redirect(url_for('admin_dashboard'))
    conn = get_db_connection()
    recent_logs = conn.execute("SELECT l.*, u.username FROM logs l JOIN users u ON l.user_id = u.id ORDER BY l.date DESC LIMIT 500").fetchall()
    conn.close()
    return render_template('admin/logs.html', logs=recent_logs)

@app.route('/admin/document', methods=['POST'])
@admin_required
def upload_document():
    if 'document' not in request.files: return redirect(url_for('admin_dashboard'))
    file = request.files['document']
    if file.filename == '': return redirect(url_for('admin_dashboard'))
    
    filename = secure_filename(file.filename)
    chemin = f"uploads/{filename}"
    file.save(os.path.join(app.root_path, 'static', os.path.normpath(chemin)))
    
    titre = request.form.get('titre')
    cat = request.form.get('categorie')
    annee = request.form.get('annee', datetime.now().year)
    
    conn = get_db_connection()
    
    # Auto-create announcement WITH document attached
    contenu_ann = f"Le document '{titre}' pour l'année {annee} vient d'être uploadé. Vous pouvez le visualiser depuis le panneau des annonces via le lien rattaché."
    conn.execute("INSERT INTO annonces (titre, contenu, date, chemin_document) VALUES (?, ?, ?, ?)", 
                 (f"📑 Nouveau Document: {titre} ({cat})", contenu_ann, datetime.now().strftime("%Y-%m-%d %H:%M:%S"), chemin))
                 
    conn.commit()
    conn.close()
    add_log(session['user_id'], 'Upload Document -> Annonces', f'Titre: {titre}')
    flash("Document uploadé et visible dans les annonces.", "success")
    return redirect(url_for('admin_dashboard'))

@app.route('/admin/annonce', methods=['POST'])
@admin_required
def add_annonce():
    titre = request.form.get('titre')
    contenu = request.form.get('contenu')
    if titre and contenu:
        conn = get_db_connection()
        conn.execute("INSERT INTO annonces (titre, contenu, date) VALUES (?, ?, ?)", (titre, contenu, datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
        conn.commit()
        conn.close()
        add_log(session['user_id'], 'Ajout Annonce', f'Titre: {titre}')
        flash("Annonce publiée.", "success")
    return redirect(url_for('admin_dashboard'))

@app.route('/admin/annonce/delete/<int:id>', methods=['POST'])
@admin_required
def delete_annonce(id):
    conn = get_db_connection()
    ann = conn.execute("SELECT * FROM annonces WHERE id = ?", (id,)).fetchone()
    if ann:
        if ann['chemin_document']:
            try:
                os.remove(os.path.join(app.root_path, 'static', ann['chemin_document']))
            except OSError:
                pass
        conn.execute("DELETE FROM annonces WHERE id = ?", (id,))
        conn.commit()
        add_log(session['user_id'], 'Suppression Annonce/Doc', f'ID {id}')
        flash("Annonce/Document supprimé définitivement.", "success")
    conn.close()
    return redirect(url_for('admin_dashboard'))

@app.route('/admin/annonce/edit/<int:id>', methods=['POST'])
@admin_required
def edit_annonce(id):
    titre = request.form.get('titre')
    contenu = request.form.get('contenu')
    if titre and contenu:
        conn = get_db_connection()
        conn.execute("UPDATE annonces SET titre = ?, contenu = ? WHERE id = ?", (titre, contenu, id))
        conn.commit()
        conn.close()
        add_log(session['user_id'], 'Édition Annonce', f'ID {id}')
        flash("Annonce mise à jour.", "success")
    return redirect(url_for('admin_dashboard'))


@app.route('/admin/cotisation', methods=['POST'])
@admin_required
def add_cotisation():
    numero = request.form.get('numero')
    montant = request.form.get('montant')
    annee = request.form.get('annee', 2026)
    date_val = request.form.get('date') or datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    if ' ' not in date_val: date_val += " 12:00:00" # fallback suffix if input=date
    
    if numero and montant:
        conn = get_db_connection()
        user_row = conn.execute("SELECT id FROM users WHERE appartement_numero = ?", (numero,)).fetchone()
        if user_row:
            conn.execute("INSERT INTO cotisations (user_id, montant, annee, date) VALUES (?, ?, ?, ?)", 
                        (user_row['id'], float(montant), int(annee), date_val))
            conn.commit()
            add_log(session['user_id'], 'Ajout Cotisation', f'Appt {numero}, Montant: {montant}, Date: {date_val}')
            flash(f"Cotisation de {montant} DA pour l'Apt {numero} ajoutée.", "success")
        else:
            flash(f"Erreur: Impossible de trouver l'Apt {numero} dans la base de données.", "danger")
        conn.close()
    else:
        flash("Veuillez remplir tous les champs obligatoires.", "warning")
    return redirect(url_for('admin_dashboard'))

@app.route('/admin/cotisation/delete/<int:id>', methods=['POST'])
@admin_required
def delete_cotisation(id):
    conn = get_db_connection()
    conn.execute("DELETE FROM cotisations WHERE id = ?", (id,))
    conn.commit()
    conn.close()
    add_log(session['user_id'], 'Suppression Cotisation', f'ID {id}')
    flash("Cotisation supprimée.", "success")
    return redirect(url_for('admin_dashboard'))

@app.route('/admin/depense/edit/<int:id>', methods=['POST'])
@admin_required
def edit_depense(id):
    desc = request.form.get('description')
    mont = request.form.get('montant')
    cat = request.form.get('categorie')
    date_val = request.form.get('date')
    if desc and mont:
        conn = get_db_connection()
        if date_val:
            conn.execute("UPDATE depenses SET description = ?, montant = ?, categorie = ?, date = ? WHERE id = ?", (desc, float(mont), cat, date_val, id))
        else:
            conn.execute("UPDATE depenses SET description = ?, montant = ?, categorie = ? WHERE id = ?", (desc, float(mont), cat, id))
        conn.commit()
        conn.close()
        add_log(session['user_id'], 'Edition Dépense', f'ID {id} -> {desc}')
        flash("Dépense mise à jour.", "success")
    return redirect(url_for('admin_dashboard'))

@app.route('/admin/cotisation/edit/<int:id>', methods=['POST'])
@admin_required
def edit_cotisation(id):
    montant = request.form.get('montant')
    annee = request.form.get('annee')
    date_val = request.form.get('date')
    if montant and annee:
        conn = get_db_connection()
        if date_val:
            conn.execute("UPDATE cotisations SET montant = ?, annee = ?, date = ? WHERE id = ?", (float(montant), int(annee), date_val, id))
        else:
            conn.execute("UPDATE cotisations SET montant = ?, annee = ? WHERE id = ?", (float(montant), int(annee), id))
        conn.commit()
        conn.close()
        add_log(session['user_id'], 'Edition Cotisation', f'ID {id} -> {montant} DA, {annee}')
        flash("Cotisation mise à jour.", "success")
    else:
        flash("Montant et Année requis pour la mise à jour.", "warning")
    return redirect(url_for('admin_dashboard'))

@app.route('/admin/depense', methods=['POST'])
@admin_required
def add_depense():
    desc = request.form.get('description')
    mont = float(request.form.get('montant', 0))
    cat = request.form.get('categorie')
    paye = request.form.get('payePar')
    date_val = request.form.get('date') or datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    if ' ' not in date_val: date_val += " 12:00:00"
    
    if desc and mont >= 0:
        conn = get_db_connection()
        total_cot = conn.execute("SELECT SUM(montant) FROM cotisations").fetchone()[0] or 0
        total_dep = conn.execute("SELECT SUM(montant) FROM depenses").fetchone()[0] or 0
        solde_apres = total_cot - total_dep - mont
        
        conn.execute("INSERT INTO depenses (description, montant, date, categorie, payePar, soldeApres) VALUES (?, ?, ?, ?, ?, ?)",
                    (desc, mont, date_val, cat, paye, solde_apres))
        conn.commit()
        conn.close()
        add_log(session['user_id'], 'Ajout Dépense', f'Montant: {mont}, Date: {date_val}')
        flash("Dépense ajoutée.", "success")
    return redirect(url_for('admin_dashboard'))

@app.route('/admin/depense/delete/<int:id>', methods=['POST'])
@admin_required
def delete_depense(id):
    conn = get_db_connection()
    conn.execute("DELETE FROM depenses WHERE id = ?", (id,))
    conn.commit()
    conn.close()
    add_log(session['user_id'], 'Suppression Dépense', f'ID {id}')
    flash("Dépense supprimée.", "success")
    return redirect(url_for('admin_dashboard'))

@app.route('/admin/poll', methods=['POST'])
@admin_required
def add_poll():
    question = request.form.get('question')
    options = request.form.getlist('options')
    options = [opt.strip() for opt in options if opt and opt.strip()]
    if question and len(options) > 1:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("INSERT INTO polls (question) VALUES (?)", (question,))
        last = cur.lastrowid
        for opt in options:
            cur.execute("INSERT INTO poll_options (poll_id, texte) VALUES (?, ?)", (last, opt))
        conn.commit()
        conn.close()
        add_log(session['user_id'], 'Ajout Sondage', f'Question: {question}')
        flash("Sondage créé.", "success")
    return redirect(url_for('admin_dashboard'))

@app.route('/admin/poll/close/<int:id>', methods=['POST'])
@admin_required
def close_poll(id):
    conn = get_db_connection()
    poll = conn.execute("SELECT * FROM polls WHERE id = ?", (id,)).fetchone()
    if poll:
        opts = conn.execute("SELECT * FROM poll_options WHERE poll_id = ?", (id,)).fetchall()
        total_votes = conn.execute("SELECT COUNT(*) FROM votes WHERE poll_id = ?", (id,)).fetchone()[0]
        
        results_text = f"Le sondage '{poll['question']}' est terminé avec {total_votes} votes au total.\n\nRésultats :\n"
        for opt in opts:
            votes = conn.execute("SELECT COUNT(*) FROM votes WHERE option_id = ?", (opt['id'],)).fetchone()[0]
            pct = (votes / total_votes * 100) if total_votes > 0 else 0
            results_text += f"- {opt['texte']} : {int(pct)}% ({votes} votes)\n"
            
        conn.execute("UPDATE polls SET is_active = 0 WHERE id = ?", (id,))
        conn.execute("INSERT INTO annonces (titre, contenu, date) VALUES (?, ?, ?)", 
                 (f"📊 Résultats du Sondage: {poll['question']}", results_text, datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
        conn.commit()
        add_log(session['user_id'], 'Clôture Sondage', f'Poll ID {id}')
        flash("Sondage clôturé et résultats publiés dans les annonces.", "success")
    conn.close()
    return redirect(url_for('admin_dashboard'))

@app.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():
    conn = get_db_connection()
    user = conn.execute("SELECT * FROM users WHERE id = ?", (session['user_id'],)).fetchone()
    
    if request.method == 'POST':
        new_username = request.form.get('new_username')
        new_phone = request.form.get('telephone')
        new_nom = request.form.get('nom_complet')
        new_password = request.form.get('new_password')
        new_password_confirm = request.form.get('new_password_confirm')
        
        updates = []
        params = []
        
        if new_username and new_username != user['username']:
            check = conn.execute("SELECT id FROM users WHERE username = ?", (new_username,)).fetchone()
            if check:
                flash("Ce nom d'utilisateur est déjà pris.", "danger")
            else:
                updates.append("username = ?")
                params.append(new_username)
                session['username'] = new_username
                
        if new_phone is not None and new_phone != user['telephone']:
            updates.append("telephone = ?")
            params.append(new_phone)
            
        if new_nom is not None and new_nom != user['nom_complet']:
            updates.append("nom_complet = ?")
            params.append(new_nom)
            
        if new_password:
            if new_password == new_password_confirm:
                updates.append("password = ?")
                params.append(generate_password_hash(new_password))
            else:
                flash("Les mots de passe ne correspondent pas.", "danger")
                
        if updates:
            params.append(session['user_id'])
            query = f"UPDATE users SET {', '.join(updates)} WHERE id = ?"
            conn.execute(query, tuple(params))
            conn.commit()
            flash("Profil mis à jour avec succès.", "success")
            
    conn.close()
    return render_template('profile.html', user=user)

@app.route('/admin/users/add', methods=['POST'])
@admin_required
def admin_add_user():
    username = request.form.get('username')
    password = request.form.get('password')
    role = request.form.get('role', 'resident')
    
    if username and password:
        conn = get_db_connection()
        check = conn.execute("SELECT id FROM users WHERE username = ?", (username,)).fetchone()
        if check:
            flash("Ce nom d'utilisateur existe déjà.", "danger")
        else:
            conn.execute("INSERT INTO users (username, password, role) VALUES (?, ?, ?)", 
                         (username, generate_password_hash(password), role))
            conn.commit()
            add_log(session['user_id'], f'Création {role}', f'User: {username}')
            flash(f"Utilisateur {username} créé avec succès.", "success")
        conn.close()
    return redirect(url_for('admin_dashboard'))

@app.route('/admin/users/reset/<int:id>', methods=['POST'])
@admin_required
def admin_reset_user(id):
    conn = get_db_connection()
    target_user = conn.execute("SELECT username FROM users WHERE id = ?", (id,)).fetchone()
    if target_user and target_user['username'] == 'admin':
        conn.close()
        flash("Action interdite sur le compte Super Admin.", "danger")
        return redirect(url_for('admin_dashboard'))
        
    new_password = request.form.get('new_password')
    if new_password:
        conn.execute("UPDATE users SET password = ? WHERE id = ?", (generate_password_hash(new_password), id))
        conn.commit()
        conn.close()
        add_log(session['user_id'], 'Reset Password', f'User ID: {id}')
        flash("Mot de passe de l'utilisateur réinitialisé.", "success")
    return redirect(url_for('admin_dashboard'))

@app.route('/admin/users/delete/<int:id>', methods=['POST'])
@admin_required
def admin_delete_user(id):
    if id == session['user_id']:
        flash("Vous ne pouvez pas supprimer votre propre compte.", "danger")
        return redirect(url_for('admin_dashboard'))
        
    conn = get_db_connection()
    target_user = conn.execute("SELECT username FROM users WHERE id = ?", (id,)).fetchone()
    if target_user and target_user['username'] == 'admin':
        conn.close()
        flash("Action interdite sur le compte Super Admin.", "danger")
        return redirect(url_for('admin_dashboard'))
        
    conn.execute("DELETE FROM users WHERE id = ?", (id,))
    conn.commit()
    conn.close()
    add_log(session['user_id'], 'Suppression User', f'ID: {id}')
    flash("Utilisateur supprimé.", "success")
    return redirect(url_for('admin_dashboard'))

if __name__ == '__main__':
    app.run(debug=True, port=5000)
