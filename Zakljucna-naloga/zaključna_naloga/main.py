from flask import Flask, render_template, request, redirect, url_for, flash

app = Flask(__name__)
app.secret_key = "ključ123"

#shranjevanje uporabnikov
users_db = {}

@app.route('/')
def home():
    return render_template("index.html")

@app.route('/register', methods=['GET', 'POST'])
def register_user():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        if username in users_db: #preveri če je uporabnik že v bazi
            flash("Uporabniško ime že obstaja. Poskusite z drugim")
        else:
            users_db[username] = password
            flash(f"Uporabnik '{username}' uspešno registriran!")
            return redirect(url_for('login_user'))
        
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login_user():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        if username in users_db and users_db[username] == password:
            flash(f"Pozdravljeni nazaj, {username}!")
            return redirect(url_for('home'))
        else:
            flash('Napačno uporabniško ime ali geslo')
    
    return render_template('login.html')

if __name__ == '__main__':
    app.run(debug=True)