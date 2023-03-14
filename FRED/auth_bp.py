from flask import Blueprint, render_template, redirect, url_for, request, current_app
#from firebase_admin.auth import sign_in_with_email_and_password

import re


auth_bp = Blueprint('auth_bp', __name__)


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