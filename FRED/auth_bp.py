from flask import Blueprint, render_template, redirect, url_for, request, current_app, session
import google.oauth2.credentials
import google_auth_oauthlib.flow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from datetime import datetime, time, timedelta
from google.auth.transport import requests
import json
import os
#from firebase_admin.auth import sign_in_with_email_and_password

import re


auth_bp = Blueprint('auth_bp', __name__)
client_key_file_path = os.path.join(os.path.dirname(__file__), 'key', 'client_secret.json')
client_scopes = [ "https://www.googleapis.com/auth/calendar",  "https://www.googleapis.com/auth/userinfo.email",    "openid"]
url_callback = "https://127.0.0.1:8080/oauth2callback"



@auth_bp.route('/login', methods = ['GET', 'POST'])
def login():
    msg = ''
    dbAD = current_app.config['dbAD']
    auth = current_app.config['auth']

    if request.method == 'POST' and 'email' in request.form and 'password' in request.form:
        email = request.form['email']
        password = request.form['password'] 
        try:
            current_user = auth.sign_in_with_email_and_password(email, password)
            user = current_user
            user['displayName'] = dbAD.collection('users').document(user['email']).get().to_dict()['userid']
            return redirect(url_for('views.dashboard'))
        except Exception as e:
            print(str(e))
            msg = 'Please check your login details and try again'
            return render_template('login.html', msg = msg)

    else:
        return render_template('login.html', msg = msg)
    

@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    msg = ''
    dbAD = current_app.config['dbAD']
    auth = current_app.config['auth']


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
                    'FREDs': []
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

@auth_bp.route('/logout')
def logout():
    auth = current_app.config['auth']
    auth.current_user = None
    return redirect(url_for('auth_bp.login'))


@auth_bp.route('/calendar', methods = ['GET', 'POST'])
def calendar():
    if "credentials" not in session:
        return redirect(url_for("auth_bp.google_auth"))

    # Load the credentials from the session
    credentials = google.oauth2.credentials.Credentials.from_authorized_user_info(json.loads(session["credentials"]))

    # Check if the access token is expired
    if credentials.expired:
        # Refresh the access token using the refresh token
        credentials.refresh(requests.Request())

        # Save the updated credentials in the session
        session["credentials"] = credentials.to_json()

    service = build("calendar", "v3", credentials=credentials)

    #maybe let user decide what calendar shows up here with POST
    calendar_list = service.calendarList().list().execute()
    calendar_IDs = calendar_list.get('items', []) 
    calendar_names = [calendar['summary'] for calendar in calendar_IDs]

    today = datetime.utcnow().date()
    start_of_week = today - timedelta(days=today.weekday())
    end_of_week = start_of_week + timedelta(days=6)

    start_of_week_utc = datetime.combine(start_of_week, datetime.min.time()).isoformat() + 'Z'
    end_of_week_utc = datetime.combine(end_of_week, datetime.max.time()).isoformat() + 'Z'

    try:
        #api call
        events_result = service.events().list(
            calendarId='primary', 
            timeMin=start_of_week_utc, 
            timeMax=end_of_week_utc, 
            maxResults=10, 
            singleEvents=True, 
            orderBy='startTime'
        ).execute()
        events = events_result.get('items', [])
        print('Should be working')
    except HttpError as error:
        print('An error occurred: %s' % error)
        events = []

    print(events)
    return render_template('calendar.html',events=events, calendar_names = calendar_names)


@auth_bp.route('/google_auth')
def google_auth():
    flow = google_auth_oauthlib.flow.Flow.from_client_secrets_file(client_key_file_path, scopes=client_scopes)
    #flow.redirect_uri = url_for("auth_bp.oauth2callback", _external=True)
    flow.redirect_uri = url_callback
    authorization_url, state = flow.authorization_url(access_type="offline", prompt="consent")
    session["state"] = state
    return redirect(authorization_url)

@auth_bp.route("/oauth2callback")
def oauth2callback():
    state = session["state"]
    flow = google_auth_oauthlib.flow.Flow.from_client_secrets_file(client_key_file_path, scopes=client_scopes, state=state)
    
    flow.redirect_uri = url_callback
    authorization_response = url_callback + request.full_path

    flow.fetch_token(authorization_response=authorization_response)
    credentials = flow.credentials
    refresh_token = credentials.refresh_token
    session['refresh_token'] = refresh_token

    session["credentials"] = {
        "token": credentials.token,
        "refresh_token": refresh_token,
        "token_uri": credentials.token_uri,
        "client_id": credentials.client_id,
        "client_secret": credentials.client_secret,
        "scopes": credentials.scopes,
    }
    session["credentials"] = credentials.to_json()
    return redirect(url_for("auth_bp.calendar"))