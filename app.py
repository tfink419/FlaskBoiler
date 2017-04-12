#object that represents the application
from flask import Flask, render_template, request, redirect, url_for, jsonify, Response
from flask_bootstrap import Bootstrap 
from flask_sqlalchemy import SQLAlchemy
from flask_security import Security, SQLAlchemyUserDatastore, UserMixin, RoleMixin, login_required, utils as security_utils
import flask_mail as mail

from os import environ as ENV

# Create app
import psycopg2
from pandas.io import sql
import logging
from logging import handlers

logging.basicConfig(level=logging.DEBUG, format='%(asctime)s [%(levelname)s] %(message)s')

print ENV

app = Flask(__name__)

app.config['DEBUG'] = True
app.config['SECURITY_PASSWORD_HASH'] = 'sha512_crypt'
app.config['SECURITY_PASSWORD_SALT'] = ENV['SECURITY_PASSWORD_SALT']
app.config['SECRET_KEY'] = ENV['SECRET_KEY']
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

user_datastore = SQLAlchemyUserDatastore(db, User, Role)
security = Security(app, user_datastore)

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
	return render_template('index.html', items=event_tables)


@app.route('/remove/<name>')
def remove_item(name):
	global event_tables
	if name in event_tables:
		event_tables.remove(name)
	return redirect(url_for('index'))

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
    user_datastore.create_user(email='tyler_fink', password='Pass1234')
    user_datastore.create_user(email='sanj_chakra', password='Pass1234')
    db.session.commit()

if __name__ == '__main__':
	logging.debug("__main__")
	app.run(debug=True)
