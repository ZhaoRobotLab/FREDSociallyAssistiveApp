import os
import firebase_admin
import pyrebase
import re
#from firebase import Firebase
from flask import Flask, request, jsonify, render_template, redirect, url_for, request, session
from firebase_admin import credentials, firestore, initialize_app

#App initialization
app = Flask(__name__)

#App Pages
@app.route('/')
def home():
    msg = ''
    return render_template('index.html', msg = msg)

@app.route('/dashboard', methods=['GET', 'POST'])
def dashboard():
    msg = ''
    #get current user
    user = auth.current_user
    userid = auth.current_user['displayName']

    return render_template('dashboard.html', userid = userid)

@app.route('/profile', methods=['GET', 'POST'])
def profile():
    #get current user information from db
    user = auth.current_user
    email = auth.current_user['email']
    name = dbAD.collection('users').document(email).get().to_dict()['name']
    userid = dbAD.collection('users').document(email).get().to_dict()['userid']
    phone = dbAD.collection('users').document(email).get().to_dict()['phone']
    return render_template('profile.html', email=email, name=name, userid=userid, phone=phone)

@app.route('/settings', methods=['GET', 'POST'])
def settings():
    msg = ''
    return render_template('settings.html', msg = msg)

@app.route('/patients', methods=['GET', 'POST'])
def patients():
    msg = ''
    if request.method == 'POST' and 'patient' in request.form:
        patientName = request.form['patient']
    #db.child("patients").order_by_child("name").equal_to(10).get()
    return render_template('patients.html', msg = msg)

@app.route('/login', methods =['GET', 'POST'])
def login():
    msg = ''
    if request.method == 'POST' and 'email' in request.form and 'password' in request.form:
        email = request.form['email']
        password = request.form['password'] 
        try:
            auth.current_user = auth.sign_in_with_email_and_password(email, password)
            user = auth.current_user
            auth.current_user['displayName'] = dbAD.collection('users').document(user['email']).get().to_dict()['userid']
            return redirect(url_for('dashboard'))
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
    if request.method == 'POST' and 'fullname' in request.form and 'phone' in request.form and 'userid' in request.form and 'confirmPassword' in request.form and 'password' in request.form and 'email' in request.form :
        #Grab fields from register page
        fullname = request.form['fullname']
        phone = request.form['phone']
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
        elif not confirmPassword or not password or not email or not userid or not phone or not fullname:
            msg = 'Please fill out all fields !'
        else:
            #Create user in Firebase otherwise return error if registration unsuccessful
            try: 
                auth.create_user_with_email_and_password(email, password)
                msg = 'Account created successfully !'
                #Add user to database
                data = {
                    'name': fullname,
                    'phone': phone,
                    'userid': userid,
                    'email': email,
                }
                dbAD.collection('users').document(email).set(data)
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
    firebaseConfig = {
        "apiKey": "AIzaSyAp9sn0EJli86ELaO9idVcqLEGqckdFHYw",
        "authDomain": "fredsocialbot.firebaseapp.com",
        "databaseURL": "https://fredsocialbot.firebaseio.com",
        "storageBucket": "fredsocialbot.appspot.com",
    }

    #Admin API
    cred = credentials.Certificate("key.json")
    firebaseAD = firebase_admin.initialize_app(cred)
    dbAD = firestore.client()

    #User API
    firebase = pyrebase.initialize_app(firebaseConfig)
    auth = firebase.auth()
    db = firebase.database()

    #Run app
    app.run(debug=True,host='0.0.0.0',port=int(os.environ.get('PORT', 8080)))
    
