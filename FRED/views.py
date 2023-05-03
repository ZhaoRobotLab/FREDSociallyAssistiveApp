from flask import Blueprint, render_template, request, current_app
from datetime import datetime
from google.cloud import firestore
#from firebase_admin import auth

views = Blueprint('views', __name__)

@views.route('/')
def home():
    return render_template('home.html')

@views.route('/dashboard',methods = ['GET', 'POST'])
def dashboard():
    dbAD = current_app.config['dbAD']
    auth = current_app.config['auth']
    user = auth.current_user
    user_email = auth.current_user['email']
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


    return render_template('dashboard.html', userid = user_email, phone=phone, options=options, mood_options=mood_options, labels=labels, values=values, msg_sent = msg_sent, patient_confirm=patient_confirm, patient_error=patient_error)

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