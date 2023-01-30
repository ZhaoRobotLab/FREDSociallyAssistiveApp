import firebase_admin
from flask import Flask, request
from firebase_admin import credentials

app = Flask(__name__)

@app.route('/')
def home():
    return 'FRED FRED FRED'
    
@app.route('/greet', methods=['GET'])
def greet():
    name = request.args.get('name')
    return f'Hello, {name}!'


if __name__ == '__main__':
    app.run()
    cred = credentials.Certificate("key.json")
    firebase_admin.initialize_app(cred)
    db = firestore.client()
    
