from flask import Flask, request, render_template, redirect, send_from_directory
#from google.cloud import translate_v2 as translate
from google.cloud import datastore

#translate_client = translate.Client()
user = datastore.Client()
kind = 'Client Table'

app = Flask(__name__) 
# Index Page retrieves all records in kind and puts them into list for navigation selection

@app.route('/', methods=['GET'])
def index():
    # Get Client List
    # retrieves all data with Kind Client Table
    query = user.query(kind=kind)
    # fetch method that retrieve all results that match query
    results = list(query.fetch())
    # all data stored in simple list and list is passed thru to the index.html page
    return render_template('index.html', users = results)
# Static directory for css

@app.route('/static/<path:path>')
def send_js(path):
    return send_from_directory('static', path)
# CRUD ENDPOINTS
# Create

@app.route('/create', methods=['POST', 'GET'])
def create():
    if request.method == 'POST':
        data = request.form.to_dict(flat=True)      # Data from form
        # Put client record
        complete_key = user.key(kind, data['Name'])
        currentUser = datastore.Entity(key = complete_key)
        currentUser.update({
            'Name': data['Name'],
            'Email': data['Email'],
            'Class': data['Class'],
            'Language': data['Language']
        })
        user.put(currentUser)
        # Redirect to user page
        return redirect("/read/" + data['Name'])
    else:
        # GET - Render user creation form
        return render_template('create.html')
# Read

@app.route('/read/<name>', methods=['GET'])
def read(name):
    # Retrieve user Data
    key = user.key(kind, name)
    currentUser = user.get(key)
    #tinst = user['instructions']
    #tlang = 'es'
    #result = translate_client.translate(tinst, target_language=tlang)
    # Render the page
    # translate process should go here
    return render_template('user.html', Name = currentUser['Name'], Email = currentUser['Email'], Language=currentUser['Language'], Class=currentUser['Class'])
# Update

@app.route('/update/<name>', methods=['GET', 'POST'])
def update(name):
    if request.method == 'POST':
        data = request.form.to_dict(flat=True)      # Data from form
        # Update user Data
        key = user.key(kind, name)
        currentUser = user.get(key)
        currentUser['Email'] = data['Email']
        currentUser['Class'] = data['Class']
        currentUser['Language'] = data['Language']
        user.put(currentUser)
        # Redirect to user page
        return redirect("/read/" + name)
    else:
        # Get user data
        key = user.key(kind, name)
        currentUser = user.get(key)
        # Renders update page with existing data
        return render_template('update.html', Name=currentUser['Name'], Email=currentUser['Email'],
                               Class=currentUser['Class'], Language=currentUser['Language'])
# Delete

@app.route('/delete/<name>', methods=['GET'])
def delete(name):
    # Delete user Record
    key = user.key(kind, name)
    user.delete(key)
    # Redirect to index page
    return redirect('/')
# Don't worry about this part
if __name__ == '__main__':
    app.run(host='127.0.0.1', port=8080, debug=True)