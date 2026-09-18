from datetime import datetime, timedelta
from flask import Flask, render_template, request, redirect, url_for, session
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.config['SECRET_KEY'] = 'votre_cle_secrete_garagepro'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///garage_saas.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)


# ==================== MODÈLES DE BASE DE DONNÉES ====================

class Garage(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nom = db.Column(db.String(100), nullable=False)
    sous_domaine = db.Column(db.String(50), unique=True, nullable=False)
    date_expiration = db.Column(db.DateTime, nullable=False)
    utilisateurs = db.relationship('User', backref='garage', lazy=True)
    clients = db.relationship('Client', backref='garage', lazy=True, cascade="all, delete-orphan")
    vehicules = db.relationship('Vehicule', backref='garage', lazy=True, cascade="all, delete-orphan")
    mecaniciens = db.relationship('Mecanicien', backref='garage', lazy=True, cascade="all, delete-orphan")
    produits = db.relationship('Produit', backref='garage', lazy=True, cascade="all, delete-orphan")


class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)
    is_superadmin = db.Column(db.Boolean, default=False)
    garage_id = db.Column(db.Integer, db.ForeignKey('garage.id'), nullable=True)


class Client(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nom = db.Column(db.String(100), nullable=False)
    telephone = db.Column(db.String(20), nullable=False)
    email = db.Column(db.String(120))
    garage_id = db.Column(db.Integer, db.ForeignKey('garage.id'), nullable=False)
    vehicules = db.relationship('Vehicule', backref='client', lazy=True, cascade="all, delete-orphan")


class Vehicule(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    marque = db.Column(db.String(50), nullable=False)
    modele = db.Column(db.String(50), nullable=False)
    immatriculation = db.Column(db.String(20), unique=True, nullable=False)
    client_id = db.Column(db.Integer, db.ForeignKey('client.id'), nullable=False)
    garage_id = db.Column(db.Integer, db.ForeignKey('garage.id'), nullable=False)


class Mecanicien(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nom = db.Column(db.String(100), nullable=False)
    specialite = db.Column(db.String(100), nullable=False)
    telephone = db.Column(db.String(20), nullable=False)
    garage_id = db.Column(db.Integer, db.ForeignKey('garage.id'), nullable=False)


class Produit(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nom = db.Column(db.String(100), nullable=False)
    reference = db.Column(db.String(50), nullable=False)
    quantite = db.Column(db.Integer, default=0)
    prix = db.Column(db.Float, nullable=False)
    garage_id = db.Column(db.Integer, db.ForeignKey('garage.id'), nullable=False)


# ==================== INITIALISATION DES DONNÉES ====================

with app.app_context():
    db.create_all()
    if not User.query.filter_by(email='superadmin@garagepro.com').first():
        super_admin = User(
            email='superadmin@garagepro.com',
            password=generate_password_hash('super123'),
            is_superadmin=True
        )
        db.session.add(super_admin)

        garage_test = Garage(
            nom='Garage Central',
            sous_domaine='central',
            date_expiration=datetime.utcnow() - timedelta(days=2)
        )
        db.session.add(garage_test)
        db.session.commit()

        admin_garage = User(
            email='admin@garagepro.com',
            password=generate_password_hash('admin123'),
            is_superadmin=False,
            garage_id=garage_test.id
        )
        db.session.add(admin_garage)
        db.session.commit()


# ==================== ROUTES DE CONNEXION & ABONNEMENT ====================

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')

        user = User.query.filter_by(email=email).first()

        if user and check_password_hash(user.password, password):
            session['user_id'] = user.id
            session['is_superadmin'] = user.is_superadmin

            if user.is_superadmin:
                return redirect(url_for('super_admin'))

            if user.garage:
                session['garage_id'] = user.garage.id
                if user.garage.date_expiration < datetime.utcnow():
                    return redirect(url_for('expire', garage_id=user.garage.id))
                return redirect(url_for('dashboard'))

    return render_template('login.html')

@app.route('/admin')
@app.route('/super_admin')
def super_admin():
    if not session.get('is_superadmin'):
        return redirect(url_for('login'))

    garages = Garage.query.all()
    return render_template('super_admin.html', garages=garages)


@app.route('/renouveler/<int:garage_id>')
def renouveler(garage_id):
    if not session.get('is_superadmin'):
        return redirect(url_for('login'))

    garage = Garage.query.get_or_404(garage_id)
    garage.date_expiration = datetime.utcnow() + timedelta(days=30)
    db.session.commit()
    return redirect(url_for('super_admin'))


@app.route('/expire/<int:garage_id>')
def expire(garage_id):
    garage = Garage.query.get_or_404(garage_id)
    return render_template('expire.html', garage=garage)


@app.route('/payer/<int:garage_id>', methods=['GET', 'POST'])
def payer(garage_id):
    garage = Garage.query.get_or_404(garage_id)
    if request.method == 'POST':
        garage.date_expiration = datetime.utcnow() + timedelta(days=30)
        db.session.commit()
        return redirect(url_for('dashboard'))
    return render_template('paiement.html', garage=garage)


@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))


# ==================== ROUTES MÉTIER (ATELIER) ====================

@app.route('/')
def dashboard():
    if 'garage_id' not in session:
        return redirect(url_for('login'))

    garage = Garage.query.get(session['garage_id'])
    if garage.date_expiration < datetime.utcnow():
        return redirect(url_for('expire', garage_id=garage.id))

    return render_template('index.html')


@app.route('/clients', methods=['GET', 'POST'])
def clients():
    if 'garage_id' not in session:
        return redirect(url_for('login'))

    current_garage_id = session['garage_id']

    if request.method == 'POST':
        nom = request.form.get('nom')
        telephone = request.form.get('telephone')
        email = request.form.get('email')

        if nom and telephone:
            nouveau_client = Client(nom=nom, telephone=telephone, email=email, garage_id=current_garage_id)
            db.session.add(nouveau_client)
            db.session.commit()
        return redirect(url_for('clients'))

    mes_clients = Client.query.filter_by(garage_id=current_garage_id).all()
    return render_template('clients.html', clients=mes_clients)


@app.route('/vehicules', methods=['GET', 'POST'])
def vehicules():
    if 'garage_id' not in session:
        return redirect(url_for('login'))

    current_garage_id = session['garage_id']

    if request.method == 'POST':
        marque = request.form.get('marque')
        modele = request.form.get('modele')
        immatriculation = request.form.get('immatriculation')
        client_id = request.form.get('client_id')

        if marque and modele and immatriculation and client_id:
            nouveau_vehicule = Vehicule(
                marque=marque, modele=modele, immatriculation=immatriculation,
                client_id=client_id, garage_id=current_garage_id
            )
            db.session.add(nouveau_vehicule)
            db.session.commit()
        return redirect(url_for('vehicules'))

    mes_vehicules = Vehicule.query.filter_by(garage_id=current_garage_id).all()
    mes_clients = Client.query.filter_by(garage_id=current_garage_id).all()
    return render_template('vehicules.html', vehicules=mes_vehicules, clients=mes_clients)


@app.route('/mecaniciens', methods=['GET', 'POST'])
def mecaniciens():
    if 'garage_id' not in session:
        return redirect(url_for('login'))

    current_garage_id = session['garage_id']

    if request.method == 'POST':
        nom = request.form.get('nom')
        specialite = request.form.get('specialite')
        telephone = request.form.get('telephone')

        if nom and specialite and telephone:
            nouveau_meca = Mecanicien(nom=nom, specialite=specialite, telephone=telephone, garage_id=current_garage_id)
            db.session.add(nouveau_meca)
            db.session.commit()
        return redirect(url_for('mecaniciens'))

    mes_mecaniciens = Mecanicien.query.filter_by(garage_id=current_garage_id).all()
    return render_template('mecaniciens.html', mecaniciens=mes_mecaniciens)


@app.route('/stock', methods=['GET', 'POST'])
def stock():
    if 'garage_id' not in session:
        return redirect(url_for('login'))

    current_garage_id = session['garage_id']

    if request.method == 'POST':
        nom = request.form.get('nom')
        reference = request.form.get('reference')
        quantite = request.form.get('quantite')
        prix = request.form.get('prix')

        if nom and reference and quantite and prix:
            nouveau_produit = Produit(
                nom=nom, reference=reference,
                quantite=int(quantite), prix=float(prix),
                garage_id=current_garage_id
            )
            db.session.add(nouveau_produit)
            db.session.commit()
        return redirect(url_for('stock'))

    mes_produits = Produit.query.filter_by(garage_id=current_garage_id).all()
    return render_template('stock.html', produits=mes_produits)


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)