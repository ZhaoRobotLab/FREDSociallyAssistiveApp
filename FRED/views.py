from flask import Blueprint, render_template, request, current_app
from datetime import datetime
from google.cloud import firestore
#from firebase_admin import auth


#NEW
from flask import Blueprint, render_template, redirect, url_for, request, current_app, session
import google.oauth2.credentials
import google_auth_oauthlib.flow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from datetime import datetime, timedelta, date
from google.auth.transport import requests
import json
import os
from datetime import datetime
#from firebase_admin.auth import sign_in_with_email_and_password

import re
views = Blueprint('views', __name__)
client_key_file_path = os.path.join(os.path.dirname(__file__), 'key', 'client_secret.json')
client_scopes = [ "https://www.googleapis.com/auth/calendar",  "https://www.googleapis.com/auth/userinfo.email",'https://www.googleapis.com/auth/tasks.readonly' ,   "openid"]
url_callback = "https://127.0.0.1:8080/oauth2callback"

@views.route('/')
def home():
    return render_template('home.html')

@views.route('/dashboard',methods = ['GET', 'POST'])
def dashboard():
    dbAD = current_app.config['dbAD']
    auth = current_app.config['auth']
    user = auth.current_user
    user_email = user['email']
    user_ref = dbAD.collection('users').document(user_email)
    phone = dbAD.collection('users').document(user_email).get().to_dict()['phone']

    # Get all patient names from Firestore
    caretaker_ref = dbAD.collection('users').document(user_email)
    caretaker_dict = caretaker_ref.get().to_dict()
    patient_refs = caretaker_dict['patients']
    patient_names = []
    for patient_ref in patient_refs:
        patient_dict = patient_ref.get().to_dict()
        patient_name = patient_dict['name']
        patient_names.append({'name': patient_name})

    options = ''
    for patient in patient_names:
        options += f'<option value="{patient["name"]}">{patient["name"]}</option>'

    #Message Initialization
    msg_sent = ''
    patient_confirm = ''
    patient_error = ''

    #Send Notifications##############################################
    if request.method == 'POST' and 'patient' in request.form and 'message' in request.form:
        patient = request.form['patient'] #patient name
        message = request.form['message'] #message for patient

        #get patient email from patients list
        for patient_ref in patient_refs:
            patient_dict = patient_ref.get().to_dict()
            if(patient_dict['name'] == patient):
                patient_email = patient_dict['email']

        doc_ref = dbAD.collection('patients').document(patient_email)
        current_time = datetime.now().strftime('%m/%d/%Y %H:%M:%S')
        doc_ref.update({'messages.' + current_time: message})
        doc_ref.update({'notification': True})
        msg_sent='Message Sent!'

    #End Send Notifications##########################################


    #Add Patients####################################################
    if request.method == 'POST' and request.form.get('patientemail'):
        patient_email = request.form['patientemail']

        user_dict = user_ref.get().to_dict()
        user_patients = user_dict['patients']
        patient_emails = []
        for patient_ref in user_patients:
            patient_dict = patient_ref.get().to_dict()
            add_email = patient_dict['email']
            patient_emails.append(add_email)
        
        if patient_email in patient_emails: #Patient already paired
            patient_confirm = 'Patient already paired'
        else:
            patient_doc = dbAD.collection('patients').document(patient_email).get()
            if patient_doc.exists:
                ref = patient_doc = dbAD.collection('patients').document(patient_email)
                user_ref.update({
                    'patients': firestore.ArrayUnion([ref])
                })
                
                caretaker_ref = dbAD.collection('users').document(user_email)
                caretaker_dict = caretaker_ref.get().to_dict()
                patient_refs = caretaker_dict['patients']
                patient_names = []
                for patient_ref in patient_refs:
                    patient_dict = patient_ref.get().to_dict()
                    patient_name = patient_dict['name']
                    patient_names.append({'name': patient_name})

                options = ''
                for patient in patient_names:
                    options += f'<option value="{patient["name"]}">{patient["name"]}</option>'

                patient_confirm = 'Patient added'
            else:
                patient_error = 'No patient found with that email address'
    #End Add Patients################################################

    #Mood Graph######################################################
    mood_options = ''
    if request.method == 'POST' and 'mood_patient' in request.form:
        
        selected_patient = request.form['mood_patient'] #patient name - want to change to email

        for patient in patient_names:
            if(patient["name"] == selected_patient):
                mood_options += f'<option value="{patient["name"]}" selected>{patient["name"]}</option>'
            else:
                mood_options += f'<option value="{patient["name"]}">{patient["name"]}</option>'
  
    else:   #Incompleted form
        selected_patient = patient_names[0]["name"]
        
        for patient in patient_names:
            mood_options += f'<option value="{patient["name"]}">{patient["name"]}</option>'

    #get patient email from patients list
    for patient_ref in patient_refs:
        patient_dict = patient_ref.get().to_dict()
        if(patient_dict['name'] == selected_patient):
            patient_email = patient_dict['email']   

    moodmap = dbAD.collection('patients').document(patient_email).get().to_dict()["mood"]

    list = [(k, v) for k, v in moodmap.items()]

    list = sorted(list, key = lambda x: datetime.strptime(x[0], '%m/%d/%Y'))

    labels = [row[0] for row in list]
    values = [row[1] for row in list]

    #End Mood Graph##################################################

    #START Calenadar#######################################################
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

    # Retrieve the user's available calendars
    calendar_list = events_service.calendarList().list().execute()
    calendars = calendar_list.get('items', [])

    if request.method == 'POST':
        # Retrieve the selected calendar ID and date from the form data
        selected_calendar_id = request.form.get('calendar_id')
        selected_date_str = request.form.get('selected_date')
        selected_date = datetime.strptime(selected_date_str, '%Y-%m-%d').date()
    else:
        # Use the default calendar ID ('primary') and current date
        selected_calendar_id = 'primary'
        selected_date = datetime.now().date()

    print(selected_date)
    start_of_day = datetime.combine(selected_date, datetime.min.time()) 
    end_of_day = datetime.combine(selected_date, datetime.max.time()) 
    start_of_day_utc = start_of_day.isoformat() + 'Z'
    end_of_day_utc = end_of_day.isoformat() + 'Z'


    print(start_of_day_utc)
    print(end_of_day_utc)

    # Fetch events
    events_result = events_service.events().list(calendarId=selected_calendar_id, timeMin=start_of_day_utc, timeMax=end_of_day_utc, maxResults=10, singleEvents=True, orderBy='startTime').execute()

    events = events_result.get('items', [])
    filtered_events = []

    for event in events:
        start = event.get('start', {}).get('date') or event.get('start', {}).get('dateTime')
        end = event.get('end', {}).get('date') or event.get('end', {}).get('dateTime')

        if start is None or end is None:
            continue

        start_date = datetime.fromisoformat(start).date()
        end_date = datetime.fromisoformat(end).date()

        if start_date == selected_date or (start_date < selected_date and end_date > selected_date):
            filtered_events.append(event)
        print(filtered_events)

    #End Calendar####################################################


    return render_template('dashboard.html', datetime=datetime, userid = user_email, phone=phone, options=options, mood_options=mood_options, labels=labels, values=values, msg_sent = msg_sent, patient_confirm=patient_confirm, patient_error=patient_error, calendars=calendars, selected_calendar_id=selected_calendar_id, selected_date=selected_date, events=filtered_events)


@views.route('/google_auth')
def google_auth():
    flow = google_auth_oauthlib.flow.Flow.from_client_secrets_file(client_key_file_path, scopes=client_scopes)
    flow.redirect_uri = url_callback
    authorization_url, state = flow.authorization_url(access_type="offline", prompt="consent")
    session["state"] = state
    return redirect(authorization_url)


@views.route("/oauth2callback")
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


@views.route('/profile',methods = ['GET', 'POST'])
def profile():
    dbAD = current_app.config['dbAD']
    auth = current_app.config['auth']

    #get current user information from db
    user = auth.current_user
    email = auth.current_user['email']
    #name = dbAD.collection('users').document(email).get().to_dict()['name']
    userid = dbAD.collection('users').document(email).get().to_dict()['userid']
    phone = dbAD.collection('users').document(email).get().to_dict()['phone']
    return render_template('profile.html', email=email, userid=userid, phone=phone)

@views.route('/settings',methods = ['GET', 'POST'])
def settings():
    msg = ''
    return render_template('settings.html', msg = msg)