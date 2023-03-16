from flask import Flask



def create_app():
    app = Flask(__name__)
    app.config['SECRET_KEY'] = 'secretkey' #figure out
    
    from .views import views
    from .auth_bp import auth_bp

    app.register_blueprint(views, url_prefix='/')
    app.register_blueprint(auth_bp, url_prefix='/')

    return app