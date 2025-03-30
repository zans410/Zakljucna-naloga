import requests
from flask import Flask, render_template, request, redirect, url_for, flash, session
from functools import wraps

app = Flask(__name__)
app.secret_key = 'kljuc123'

#moj google Places API ključ
API_KEY = "AIzaSyBOW8o0C9ZML3aNkyFaDokMM4Hy5fSOsOk"

users_db = {}  #sharanjevanje uporabnikov

def get_coordinates(place_name):
    url = "https://maps.googleapis.com/maps/api/geocode/json"
    params = {
        "address": place_name,
        "key": API_KEY
    }
    response = requests.get(url, params=params)
    data = response.json()

    if data["status"] == "OK":
        location = data["results"][0]["geometry"]["location"]
        return f"{location['lat']},{location['lng']}"
    else:
        return None
    
def get_basketball_courts(place_name, radius=5000):
    location = get_coordinates(place_name)
    if not location:
        return []
    
    url = "https://maps.googleapis.com/maps/api/place/nearbysearch/json"
    params = {
        "key": API_KEY,
        "location": location,
        "radius": radius,
        "keyword": "basketball court"
    }

    response = requests.get(url, params=params)
    data = response.json()

    courts = []
    if "results" in data:
        for place in data['results']: #Preveri če je za igrišče najdena še slika
            photo_url = None
            photos = place.get("photos")
            if photos and isinstance(photos, list): #preveri ce je seznam in ce je prazen
                photo_reference = photos[0].get("photo_reference")
                if photo_reference:
                    photo_url = f"https://maps.googleapis.com/maps/api/place/photo?maxwidth=400&photoreference={photo_reference}&key={API_KEY}"

            courts.append({
                "name": place.get("name", "N/A"), 
                "vicinity": place.get('vicinity', "Ni podatkov o lokaciji"), #dodav sem privzeto vrednost zaradi debugga
                "photo_url": photo_url
            })
        
        return courts

def login_required(f):
    @wraps(f)
    def wrap(*args, **kwargs): #zahtevanje prijave
        if "user" not in session:
            flash("Najprej se morate prijaviti!")
            return redirect(url_for("login_user"))
        return f(*args, **kwargs)
    return wrap

@app.route('/register', methods=['GET', 'POST'])
def register_user(): #stran za registracijo uporabnika
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        if username in users_db:
            flash("Uporabniško ime že obstaja. Poskusite z drugim.")
        else:
            users_db[username] = password
            flash(f"Uporabnik '{username}' uspešno registriran!")
            return redirect(url_for('login_user'))
    
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login_user(): #stran za prijavo uporabnika
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        if username in users_db and users_db[username] == password:
            session['user'] = username #shrani uporabnika v sejo
            flash(f"Pozdravljeni nazaj, {username}!")
            return redirect(url_for('search_courts'))
        else:
            flash('Napačno uporabniško ime ali geslo')

    return render_template('login.html')

@app.route('/logout')
def logout(): #odjava uporabnika
    session.pop('user', None)
    flash("Uspešno ste se odjavili.")
    return redirect(url_for('login_user'))

@app.route('/search', methods=['GET', 'POST'])
@login_required
def search_courts(): #stran za iskanje košarkarskih igrišč (samo za prijavljene uporabnike)
    courts = []
    if request.method == 'POST':
        place_name = request.form['place_name']
        courts = get_basketball_courts(place_name)
    return render_template("search.html", courts=courts)

if __name__ == "__main__":
    app.run(debug=True)