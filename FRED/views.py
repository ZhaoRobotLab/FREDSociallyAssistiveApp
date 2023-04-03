from flask import Blueprint, render_template, request, current_app
#from firebase_admin import auth


views = Blueprint('views', __name__)



@views.route('/')
def home():
    msg = ''
    return render_template('index.html', msg=msg)

@views.route('/dashboard',methods = ['GET', 'POST'])
def dashboard():
    msg = ''
    auth = current_app.config['auth']

    #get current user
    user = auth.current_user
    userid = auth.current_user['displayName']
    
    return render_template('dashboard.html', userid = userid)

@views.route('/profile',methods = ['GET', 'POST'])
def profile():
    dbAD = current_app.config['dbAD']
    auth = current_app.config['auth']

    #get current user information from db
    user = auth.current_user
    email = auth.current_user['email']
    name = dbAD.collection('users').document(email).get().to_dict()['name']
    userid = dbAD.collection('users').document(email).get().to_dict()['userid']
    phone = dbAD.collection('users').document(email).get().to_dict()['phone']
    return render_template('profile.html', email=email, name=name, userid=userid, phone=phone)

@views.route('/settings',methods = ['GET', 'POST'])
def settings():
    msg = ''
    return render_template('settings.html', msg = msg)

@views.route('/patients',methods = ['GET', 'POST'])
def patients():
    if request.method == 'POST':
        ID = request.form['ID']
        dbAD = current_app.config['dbAD']
        auth = current_app.config['auth']
        try:
            patients = dbAD.collection('FREDs').document(ID).get().to_dict()['Patient']
            patient_names = []
            msg = 'If these are the correct patients, then confirm connection of your account to FRED #' + ID + ": "
            for i, patient in enumerate(patients):
                patient_name = (patient.get()).to_dict().get('name')
                patient_names.append(patient_name)

            patient_names = ", ".join(patient_names)
            msg = msg + patient_names
            return render_template('patients.html', msg = msg)
        except:
            return render_template('patients.html', msg = 'FRED ID invalid')
    else:
        return render_template('patients.html')
    
@views.route('/notification',methods = ['GET', 'POST'])
def notification():
    dbAD = current_app.config['dbAD']
    auth = current_app.config['auth']
    user = auth.current_user
    email = auth.current_user['email']

    # Get the patient data from Firestore
    caretaker_ref = dbAD.collection('users').document(email)
    caretaker_dict = caretaker_ref.get().to_dict()
    patient_refs = caretaker_dict['patients']
    patients = []
    for patient_ref in patient_refs:
        patient_dict = patient_ref.get().to_dict()
        patient_email = patient_dict['email']
        patient_name = patient_dict['name']
        patients.append({'name': patient_name})

    options = ''
    for patient in patients:
        options += f'<option value="{patient["name"]}">{patient["name"]}</option>'

    if request.method == 'POST' and 'patient' in request.form and 'message' in request.form:
        patient = request.form['patient'] #patient name - want to change to email
        message = request.form['message'] #message for patient

        print(patient)
        print(message)

        return render_template('notification.html', options=options) 
    #Incompleted form
    else:
        return render_template('notification.html', options=options)    