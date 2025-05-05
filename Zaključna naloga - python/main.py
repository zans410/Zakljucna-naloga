import requests
from flask import Flask, render_template, request, redirect, url_for, flash, session
from tinydb import TinyDB, Query

app = Flask(__name__)
app.secret_key = 'kljuc123'

#moj google Places API ključ
API_KEY = "AIzaSyBOW8o0C9ZML3aNkyFaDokMM4Hy5fSOsOk"

db = TinyDB('users.json') #databaza za uporabnike
users_table = db.table('users') #kreiranje tabele v databazi
activity_table = db.table('court_activity') #tabela za aktivnost na igriscih

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/register', methods=['GET', 'POST']) #stran za registracijo uporabnika
def register_user(): 
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        User = Query() 
        if users_table.contains(User.username == username): #preverja ce so uporabniki ze v bazi
            flash("Uporabniško ime je že v bazi. Poiskusite z drugim.")
        #dodajanje uporabnika v bazo ce se ne obstaja
        else: 
            users_table.insert({'username': username, 'password': password})
            flash(f"Uporabnik '{username}' uspešno registrtitan!")
            return redirect(url_for('login_user'))

    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST']) #stran za prijavo uporabnika
def login_user(): 
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        User = Query()
        user = users_table.search(User.username == username) #preveri ce je uporabnik v bazi
        if user and user[0]['password'] == password:
            session['user'] = username #shranjen uporabnik v sejo
            flash(f"Pozdravljeni nazaj, {username}!")
            return redirect(url_for('search_courts'))
        else:
            flash("Nepravilno uporabniško ime ali geslo.")

    return render_template('login.html')

@app.route('/logout')
def logout(): #odjava uporabnika
    session.pop('user', None)
    flash("Uspešno ste se odjavili.")
    return redirect(url_for('index'))

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

            place_id = place["place_id"]
            google_maps_url = f"https://www.google.com/maps/place/?q=place_id:{place_id}"

            court_name = place.get("name")
            active_users =  []
            all_activites = activity_table.all()

            for activity in all_activites:
                if activity['court_name'] == court_name and activity['status'] == 'active':
                    active_users.append(activity['user'])

            courts.append({
                "name": place.get("name", "N/A"), 
                "vicinity": place.get('vicinity', "Ni podatkov o lokaciji"), #dodav sem privzeto vrednost zaradi debugga
                "photo_url": photo_url,
                "google_maps_url": google_maps_url, #url za gumb
                "active_users": active_users
            })
        
        return courts

@app.route('/search', methods=['GET', 'POST'])
def search_courts(): #stran za iskanje košarkarskih igrišč (samo za prijavljene uporabnike)
    courts = []

    if request.method == 'POST':
        place_name = request.form.get('place_name')
    elif request.method == 'GET':
        place_name = request.args.get('place_name')

    if place_name:
        courts = get_basketball_courts(place_name)

    return render_template("search.html", courts=courts, place_name=place_name)

@app.route('/join_court/<court_name>', methods=['POST'])
def join_court(court_name):
    user = session['user']
    place_name = request.form.get('place_name')

    activity = {
        'court_name': court_name,
        'user': user,
        'status': 'active'
    }
    activity_table.insert(activity)

    flash(f"{user} se je uspešno pridružil igrišču {court_name}.")
    return redirect(url_for('search_courts') + f"?place_name={place_name}")

@app.route('/leave_court/<court_name>', methods=['POST'])
def leave_court(court_name):
    user = session['user']
    place_name = request.form.get('place_name')

    activity = Query()
    activity_table.remove((activity.court_name == court_name) & (activity.user == user))

    flash(f"{user} je zapustil igrišče {court_name}.")
    return redirect(url_for('search_courts') + f"?place_name={place_name}")

@app.route('/create_event', methods=['GET, POST'])
def create_event():
    if request.method == 'POST':
        event_name = request.form['event_name']
        event_date = request.form['event_date']
        court_name = request.form['court_name']

        event_table = db.table('events')
        event_table.insert({
            'event_name': event_name,
            'event_date': event_date,
            'court_name': court_name
        })

        flash(f"Dogodek '{event_name}' je bil uspešno ustvarjen!")
        return redirect(url_for('view_events'))

    return render_template('create_event.html')

@app.route('/events')
def view_events():
    event_table = db.table('events')
    events = event_table.all()
    return render_template('events.html', events=events)

@app.route('/join_event/<event_name>', methods=['POST'])
def join_event(event_name):
    user = session.get('user')

    event_table = db.table('events')
    user_event_table = db.table('user_events')

    event = event_table.search(Query().event_name == event_name)
    if event:
        user_event_table.insert({
            'user' : user,
            'event_name': event_name
        })
        flash(f"Uspešno ste se prijavili na dogodek '{event_name}'.")
    else:
        flash(f"Dogodek '{event_name}' ni na voljo.")

    return redirect(url_for('view_events'))

@app.route('/event_participants/<event_name>')
def event_participation(event_name):
    user_event_table = db.table('user_events')
    participants = user_event_table.search(Query().event_name == event_name)
    return render_template('event_participants.html', event_name=event_name, participants=participants)


if __name__ == "__main__":
    app.run(debug=True)
