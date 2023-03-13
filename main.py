from FRED import create_app
import os
from firebase_admin import credentials, initialize_app, firestore
import pyrebase


firebaseConfig = {
    "apiKey": "AIzaSyAp9sn0EJli86ELaO9idVcqLEGqckdFHYw",
    "authDomain": "fredsocialbot.firebaseapp.com",
    "databaseURL": "https://fredsocialbot.firebaseio.com",
    "storageBucket": "fredsocialbot.appspot.com",
}

#Admin API
key_file_path = os.path.join(os.path.dirname(__file__), 'FRED', 'key', 'key.json')
cred = credentials.Certificate(key_file_path)
firebaseAD = initialize_app(cred)
dbAD = firestore.client()

#User API
firebase = pyrebase.initialize_app(firebaseConfig)
auth = firebase.auth()
db = firebase.database()

app = create_app()
app.config['firebaseAD'] = firebaseAD
app.config['dbAD'] = dbAD
app.config['firebase'] = firebase
app.config['auth'] = auth
app.config['db'] = db
    


#Main function
if __name__ == '__main__':
    #Run app
    app.run(debug=True,host='0.0.0.0',port=int(os.environ.get('PORT', 8080)))
