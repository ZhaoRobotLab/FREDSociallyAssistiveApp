import firebase_admin
import os
from flask import Flask, request, jsonify
from firebase_admin import credentials, firestore, initialize_app

app = Flask(__name__)

@app.route('/')
def home():
    return 'FRED FRED FRED'
    
@app.route('/greet', methods=['GET'])
def greet():
    name = request.args.get('name')
    return f'Hello, {name}!'

if __name__ == '__main__':
    cred = credentials.Certificate("key.json")
    firebase_admin.initialize_app(cred)
    db = firestore.client()
    app.run(debug=True,host='0.0.0.0',port=int(os.environ.get('PORT', 8080)))
    
