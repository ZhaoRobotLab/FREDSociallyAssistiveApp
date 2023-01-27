from flask import Flask, request
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