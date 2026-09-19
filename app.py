from flask import Flask, render_template

app = Flask(__name__, template_folder='vues')

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/clients')
def clients():
    return render_template('clients.html')

@app.route('/stock')
def stock():
    return render_template('stock.html')

if __name__ == '__main__':
    app.run(debug=True)
