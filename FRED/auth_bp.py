from flask import Blueprint, render_template, redirect, url_for, request, current_app, session
import google.oauth2.credentials
import google_auth_oauthlib.flow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from datetime import datetime, timedelta
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
                    'patients': []
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

    events_service = build("calendar", "v3", credentials=credentials)
    tasks_service = build("tasks", "v1", credentials=credentials)


    # Retrieve the user's available calendars
    calendar_list = events_service.calendarList().list().execute()
    calendars = calendar_list.get('items', [])

    if request.method == 'POST':
        # Retrieve the selected calendar ID from the form data
        selected_calendar_id = request.form.get('calendar_id')
    else:
        # Use the default calendar ID ('primary')
        selected_calendar_id = 'primary'

    # Prepare the start and end dates for the current week in both local and UTC time
    today = datetime.utcnow().date()
    start_of_week = today - timedelta(days=today.weekday())
    end_of_week = start_of_week + timedelta(days=6)
    start_of_week_utc = datetime.combine(start_of_week, datetime.min.time()).isoformat() + 'Z'
    end_of_week_utc = datetime.combine(end_of_week, datetime.max.time()).isoformat() + 'Z'

    # Create a list of days in the week
    week_days = []
    for i in range(7):
        day = start_of_week + timedelta(days=i)
        week_days.append(day)

    # Fetch events/tasks/reminders for the selected calendar ID and time range
    events_by_day = {}
    tasks_by_day = {}
    reminders_by_day = {}

    for day in week_days:
        events_by_day[day] = []
        tasks_by_day[day] = []
        reminders_by_day[day] = []

    try:
        #Fetch events
        events_result = events_service.events().list(calendarId=selected_calendar_id, timeMin=start_of_week_utc, timeMax=end_of_week_utc, maxResults=10, singleEvents=True, orderBy='startTime').execute()
        events = events_result.get('items', [])
        for event in events:
            start = event['start'].get('dateTime', event['start'].get('date'))
            event_date = datetime.fromisoformat(start).date()
            if event_date in events_by_day:
                events_by_day[event_date].append(event)

        # Fetch tasks
        tasks_result = tasks_service.tasks().list(tasklist=selected_calendar_id).execute()
        tasks = tasks_result.get('items', [])
        for task in tasks:
            due_date_str = task.get('due')
            if due_date_str:
                due_date = datetime.strptime(due_date_str, '%Y-%m-%dT%H:%M:%S.%fZ').date()
                if due_date in tasks_by_day:
                    tasks_by_day[due_date].append(task)

        # Fetch reminders
        reminders_result = tasks_service.tasks().list(tasklist=selected_calendar_id, showCompleted=False, dueMin=start_of_week_utc, dueMax=end_of_week_utc).execute()
        reminders = reminders_result.get('items', [])
        for reminder in reminders:
            due_date_str = reminder.get('due')
            if due_date_str:
                due_date = datetime.strptime(due_date_str, '%Y-%m-%dT%H:%M:%S.%fZ').date()
                if due_date in reminders_by_day:
                    reminders_by_day[due_date].append(reminder)

    except HttpError as error:
        print('An error occurred: %s' % error)
        events = []

    return render_template('calendar.html', events_by_day=events_by_day, tasks_by_day=tasks_by_day, reminders_by_day=reminders_by_day, 
                            week_days=week_days, calendars=calendars, selected_calendar_id=selected_calendar_id)

@auth_bp.route('/google_auth')
def google_auth():
    flow = google_auth_oauthlib.flow.Flow.from_client_secrets_file(client_key_file_path, scopes=client_scopes)
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
