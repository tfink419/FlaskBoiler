#object that represents the application
from flask import Flask, render_template, request, redirect, url_for, jsonify, Response
from flask_bootstrap import Bootstrap
from flask_sqlalchemy import SQLAlchemy
from flask_security import Security, SQLAlchemyUserDatastore, UserMixin, RoleMixin, login_required, utils as security_utils, current_user
import flask_mail as mail
from flask_social import Social
from flask_social.datastore import SQLAlchemyConnectionDatastore

from os import environ as ENV

# Create app
import psycopg2
from pandas.io import sql
import logging
from logging import handlers

logging.basicConfig(level=logging.DEBUG, format='%(asctime)s [%(levelname)s] %(message)s')

app = Flask(__name__)

app.config['DEBUG'] = True
app.config['SECURITY_PASSWORD_HASH'] = 'sha512_crypt'
app.config['SECURITY_PASSWORD_SALT'] = ENV['SECURITY_PASSWORD_SALT']
app.config['SECRET_KEY'] = ENV['SECRET_KEY']
app.config['SOCIAL_GOOGLE'] = {
    'consumer_key': ENV['GOOGLE_LOGIN_CLIENT_ID'],
    'consumer_secret': ENV['GOOGLE_LOGIN_CLIENT_SECRET']
}
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite://'
# app.config['MAIL_SERVER'] = 'smtp.example.com'
# app.config['MAIL_PORT'] = 465
# app.config['MAIL_USE_SSL'] = True
# app.config['MAIL_USERNAME'] = 'username'
# app.config['MAIL_PASSWORD'] = 'password'
# 
# mail = Mail(app)
db = SQLAlchemy(app)

# Define models
roles_users = db.Table('roles_users',
        db.Column('user_id', db.Integer(), db.ForeignKey('user.id')),
        db.Column('role_id', db.Integer(), db.ForeignKey('role.id')))

class Role(db.Model, RoleMixin):
    id = db.Column(db.Integer(), primary_key=True)
    name = db.Column(db.String(80), unique=True)
    description = db.Column(db.String(255))

class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(255), unique=True)
    password = db.Column(db.String(255))
    active = db.Column(db.Boolean())
    confirmed_at = db.Column(db.DateTime())
    roles = db.relationship('Role', secondary=roles_users,
                            backref=db.backref('users', lazy='dynamic'))
    connections = db.relationship('Connection',
            backref=db.backref('user', lazy='joined'), cascade="all")

class Connection(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    provider_id = db.Column(db.String(255))
    provider_user_id = db.Column(db.String(255))
    access_token = db.Column(db.String(255))
    secret = db.Column(db.String(255))
    display_name = db.Column(db.PickleType)
    full_name = db.Column(db.PickleType)
    profile_url = db.Column(db.String(512))
    image_url = db.Column(db.String(512))
    # rank = db.Column(db.Integer)
    # full_name = db.relationship('FullName',
    #         backref=db.backref('connection', lazy='joined'), cascade="all")
    
class FullName(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    connection_id = db.Column(db.Integer, db.ForeignKey('connection.id'))
    givenName = db.Column(db.String(255))
    familyName = db.Column(db.String(255))

user_datastore = SQLAlchemyUserDatastore(db, User, Role)
security = Security(app, user_datastore)
social_datastore = SQLAlchemyConnectionDatastore(db, Connection)
social = Social(app, social_datastore)

db_user = ENV['DB_USER']
db_pw = ENV['DB_PW']
db_url = ENV['DB_URL']
db_port = ENV['DB_PORT']
db_name = ENV['DB_NAME']

# def redshift_engine():
# 	engine = sqlalchemy.create_engine("""postgresql+psycopg2://""" + db_user + ":" + db_pw + "@" + db_url + ":" + db_port + "/" + db_name)
# 	return engine
# 
# def query_redshift():
# 	query = """
# 	SELECT DISTINCT si.event_table_name
# 	FROM main_production._sync_info si ORDER BY 1;
# 	"""
# 	engine = redshift_engine()
# 	df = sql.read_sql(query, engine) 
# 	return df   

#mock list /db
# shopping_list = ['Item 1', 'Item 2']
logging.debug("pre-query")
# data = query_redshift()
# event_tables = list(data['event_table_name'])
event_tables = ['item1', 'item2']
logging.debug("after event_tables")

@app.route("/protected/",methods=["GET"])
@login_required
def protected():
	return Response(response="Hello Protected World!", status=200)

#decorators 
@app.route('/', methods=['GET', 'POST'])
def index():
	global event_tables
	# return '<h1>Shopping List!</h1>'
	if request.method == 'POST':
		event_tables.append(request.form['item'])
	return render_template('index.html', items=event_tables, len=len)


@app.route('/remove/<name>')
def remove_item(name):
	global event_tables
	if name in event_tables:
		event_tables.remove(name)
	return redirect(url_for('index'))

@app.route('/connect_google')
@login_required
def connect():
    return render_template(
        'connect.html',
        content='Connect Account Page')
        
@app.route('/disconnect_google')
@login_required
def disconnect():
    return render_template(
        'disconnect.html',
        content='Disconnect Account Page',
        conn=social.google.get_connection())

#API interactions 
@app.route('/api/items')
def get_items():
	#jsonify, take a python based structure and convert to JSON format to be consumed by a machine
	global event_tables
	return jsonify({'items': event_tables})

#User for test
@app.before_first_request
def create_user():
    db.create_all()
    user_datastore.create_user(email=ENV['TEST_USER1'], password=ENV['TEST_PW1'])
    user_datastore.create_user(email=ENV['TEST_USER2'], password=ENV['TEST_PW2'])
    user_datastore.create_user(email=ENV['GTEST_USER1'], password=ENV['GTEST_PW1'])
    user_datastore.create_user(email=ENV['GTEST_USER2'], password=ENV['GTEST_PW2'])
    db.session.commit()

if __name__ == '__main__':
	logging.debug("__main__")
	app.run(debug=True)
