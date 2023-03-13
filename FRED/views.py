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
    msg = ''
    dbAD = current_app.config['dbAD']
    auth = current_app.config['auth']


    #retrieve from db groups including current user as caretaker
    groups = dbAD.collection('groups').where('caretaker', '==', auth.current_user['email']).get()
    #list name of group documents in groups
    msg = []
    for group in groups:
        msg.append(group.id)
    if request.method == 'POST' and 'patient' in request.form:
        patientName = request.form['patient']
    #db.child("patients").order_by_child("name").equal_to(10).get()
    return render_template('patients.html', msg = msg)
