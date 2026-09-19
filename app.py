from flask import Flask, render_template, request, redirect, url_for

# On initialise l'application en lui disant que les templates sont dans le dossier 'vues'
app = Flask(__name__, template_folder='vues')

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/clients')
def clients():
    return render_template('clients.html')

@app.route('/expire')
def expire():
    return render_template('expire.html')

@app.route('/facture')
def facture():
    return render_template('facture.html')

@app.route('/historique_vehicule')
def historique_vehicule():
    return render_template('historique_vehicule.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        # Logique de connexion à compléter plus tard
        return redirect(url_for('index'))
    return render_template('login.html')

@app.route('/mecaniciens')
def mecaniciens():
    return render_template('mecaniciens.html')

@app.route('/paiement')
def paiement():
    return render_template('paiement.html')

@app.route('/stock')
def stock():
    return render_template('stock.html')

@app.route('/vehicules')
def vehicules():
    return render_template('vehicules.html')

if __name__ == '__main__':
    app.run(debug=True)
