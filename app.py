import os
import firebase_admin
import re
from firebase import Firebase
from flask import Flask, request, jsonify, render_template, redirect, url_for, request, session
from firebase_admin import credentials, firestore, initialize_app

#App initialization
app = Flask(__name__)

#App Pages
@app.route('/')
def home():
    msg = ''
    return render_template('index.html', msg = msg)
    
@app.route('/greet', methods=['GET'])
def greet():
    name = request.args.get('name')
    return f'Hello, {name}!'

@app.route('/login', methods =['GET', 'POST'])
def login():
    msg = ''
    if request.method == 'POST' and 'username' in request.form and 'password' in request.form:
        username = request.form['username']
        password = request.form['password'] 
        try:
            user = auth.sign_in_with_email_and_password(username, password)
            msg = f'Welcome {username}!'
            return render_template('home.html', msg = msg)
        except:
            msg = 'Please check your login details and try again'
            return render_template('login.html', msg = msg)
    else:
        return render_template('login.html', msg = msg)
 
@app.route('/logout')
def logout():
    auth.current_user = None
    return redirect(url_for('login'))
 

@app.route('/register', methods =['GET', 'POST'])
def register():
    msg = ''
    if request.method == 'POST' and 'fullname' in request.form and 'userid' in request.form and 'confirmPassword' in request.form and 'password' in request.form and 'email' in request.form :
        #Grab fields from register page
        fullname = request.form['fullname']
        userid = request.form['userid']
        email = request.form['email']
        password = request.form['password']
        confirmPassword = request.form['confirmPassword']

        #Error check user entry
        if not re.match(r'[^@]+@[^@]+\.[^@]+', email):
            msg = 'Invalid email address !'
        elif len(userid) >16:
            msg = 'User ID must be less than 16 characters !'
        elif re.match(r'[^a-zA-Z0-9]', userid):
            msg = 'User ID must be alphanumeric !'
        elif re.match(r'[^a-zA-Z0-9]+[^ ]', fullname):
            msg = 'Full name must be alphanumeric !'
        elif password != confirmPassword:
            msg = 'Passwords do not match !'
        elif len(password) < 8: 
            msg = 'Password must be at least 8 characters !'
        elif not confirmPassword or not password or not email or not userid or not fullname:
            msg = 'Please fill out all fields !'
        else:
            #Create user in Firebase otherwise return error if registration unsuccessful
            try: 
                auth.create_user_with_email_and_password(email, password)
                msg = 'Account created successfully !'
                #Add user to database
                data = {
                    'name': fullname,
                    'userid': userid,
                    'email': email,
                }
                db.collection('users').document(userid).set(data)
                return render_template('login.html', msg = msg)
            except:
                msg = 'Account Creation Failed !'
                return render_template('register.html', msg = msg)

    #Incompleted form
    elif request.method == 'POST':
        msg = 'Please fill out the form !'

    return render_template('register.html', msg = msg)

#Main function
if __name__ == '__main__':
    #Intialize Firebase APIs
    cred = credentials.Certificate("key.json")
    firebase_admin.initialize_app(cred)
    firebaseConfig = {
        "apiKey": "AIzaSyAp9sn0EJli86ELaO9idVcqLEGqckdFHYw",
        "authDomain": "fredsocialbot.firebaseapp.com",
        "databaseURL": "https://fredsocialbot.firebaseio.com",
        "storageBucket": "fredsocialbot.appspot.com",
    }
    firebase = Firebase(firebaseConfig)
    auth = firebase.auth()
    db = firestore.client()

    #Run app
    app.run(debug=True,host='0.0.0.0',port=int(os.environ.get('PORT', 8080)))
    
