from flask import Flask, render_template, request, session, redirect
from flask_sqlalchemy import SQLAlchemy
from werkzeug.utils import secure_filename
from flask_mail import Mail,Message
import json
import os
import math
from datetime import datetime
from random import *

otp = randint(000000,999999)
with open('config.json', 'r') as c:
    params = json.load(c)["params"]

success = False
local_server = True
app = Flask(__name__)
app.secret_key = os.urandom(24)

app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['UPLOAD_FOLDER'] = params['upload_location']
app.config.update(
    MAIL_SERVER = 'smtp.gmail.com',
    MAIL_PORT = '465',
    MAIL_USE_SSL = True,
    MAIL_USERNAME = params['gmail-user'],
    MAIL_PASSWORD=  params['gmail-password']
)
mail = Mail(app)
if(local_server):
    app.config['SQLALCHEMY_DATABASE_URI'] = params['local_uri']
else:
    app.config['SQLALCHEMY_DATABASE_URI'] = params['prod_uri']
db = SQLAlchemy(app)


class Contacts(db.Model):
    sno = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80), nullable=False)
    phone_num = db.Column(db.String(12), nullable=False)
    msg = db.Column(db.String(120), nullable=False)
    date = db.Column(db.String(12), nullable=True)
    email = db.Column(db.String(20), nullable=False)


class Posts(db.Model):
    sno = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(80), nullable=False)
    slug = db.Column(db.String(50), nullable=False)
    content = db.Column(db.String(200), nullable=False)
    tagline = db.Column(db.String(120), nullable=False)
    date = db.Column(db.String(20), nullable=True)
    img_file = db.Column(db.String(50), nullable=True)

class Users(db.Model):
	user_id = db.Column(db.Integer,primary_key=True)
	name = db.Column(db.String(80),nullable=False)
	email = db.Column(db.String(100), nullable=False)
	password = db.Column(db.String(100), nullable=False)


@app.route('/')
def login():
	if(('user_email' in session and 'user_pass' in session) or ('user' in session and session['user'] == params['admin_user'])):
		return redirect('/home')
	else:
		return render_template("ulogin.html",params=params)

@app.route('/register')
def regis():
    return render_template('register.html',params=params)

	
@app.route('/login_validation',methods = ['POST'])
def login_validation():
	try:
		email = request.form.get('email')
		password = request.form.get('password')
		users = Users.query.filter_by(email=email).first()
		if (email.lower() == str(users.email).lower() and password == str(users.password)):
			session['user_email'] = users.email
			session['user_pass'] = users.password
			return redirect('/home')
		else:
			return redirect('/')
	except:
		return redirect('/')

@app.route('/verify',methods = ["POST"])  
def verify():  
	email = request.form["uemail"]
	name = request.form['uname']
	password = request.form['upassword']
	global user_details 
	user_details= {'name':name,'email':email,'password':password} 
	msg = Message('OTP',sender = params['gmail-user'], recipients = [email])  
	msg.body = str(otp)  
	mail.send(msg)  
	return render_template('verify.html')

@app.route('/validate',methods=["POST"])   
def validate():  
	user_otp = request.form['otp']
	if otp == int(user_otp): 
		name = user_details['name']
		email = user_details['email']
		password = user_details['password']
		user_input = Users(name=name,email=email,password=password)
		db.session.add(user_input)
		db.session.commit()
		myuser = Users.query.filter_by(email=email).first()
		session['user_email'] = myuser.email
		session['user_pass'] = myuser.password
		return redirect('/home') 
	return render_template("reVerifyOTP.html")

@app.route('/ulogout')
def ulogout():
	try:
		session.pop('user_email')
		session.pop('user_pass')
		return redirect('/')
	except:
		session.pop('user')
		return redirect('/')
	
@app.route("/home/")
def home():
	try:
		if(('user_email' in session and 'user_pass' in session) or ('user' in session and session['user'] == params['admin_user']) or success):
		    posts = Posts.query.filter_by().all()
		    last = math.ceil(len(posts)/int(params['no_of_posts']))
		    #[0: params['no_of_posts']]
		    #posts = posts[]
		    page = request.args.get('page')
		    if(not str(page).isnumeric()):
		        page = 1
		    page= int(page)
		    posts = posts[(page-1)*int(params['no_of_posts']): (page-1)*int(params['no_of_posts'])+ int(params['no_of_posts'])]
		    if (page==1):
		        prev = "#"
		        next = "/home?page="+ str(page+1)
		    elif(page==last):
		        prev = "/home?page=" + str(page - 1)
		        next = "#"
		    else:
		        prev = "/home?page=" + str(page - 1)
		        next = "/home?page=" + str(page + 1)

		    return render_template('index.html', params=params, posts=posts, prev=prev, next=next)
		else:
			return redirect('/')
	except:
		return redirect('/')

@app.route("/post/<string:post_slug>", methods=['GET'])
def post_route(post_slug):
    if(('user_email' in session and 'user_pass' in session) or ('user' in session and session['user'] == params['admin_user'])):
        post = Posts.query.filter_by(slug=post_slug).first()
        return render_template('post.html', params=params, post=post)
    else:
        return redirect('/')

@app.route("/about")
def about():
	if(('user_email' in session and 'user_pass' in session) or ('user' in session and session['user'] == params['admin_user'])):
		return render_template('about.html', params=params)
	return redirect('/')

@app.route("/dashboard", methods=['GET', 'POST'])
def dashboard():
	try:
	    if ('user' in session and session['user'] == params['admin_user']):
	        posts = Posts.query.all()
	        return render_template('dashboard.html', params=params, posts = posts)
	    if request.method=='POST':
	        username = request.form.get('uname')
	        userpass = request.form.get('pass')
	        if (username == params['admin_user'] and userpass == params['admin_password']):
	            session['user'] = username
	            posts = Posts.query.all()
	            global success
	            success = True
	            return render_template('dashboard.html', params=params, posts = posts)

	    return render_template('login.html', params=params)
	except:
		return redirect('/')

@app.route("/edit/<string:sno>", methods = ['GET', 'POST'])
def edit(sno):
    if ('user' in session and session['user'] == params['admin_user']):
        if request.method == 'POST':
            box_title = request.form.get('title')
            tline = request.form.get('tline')
            slug = request.form.get('slug')
            content = request.form.get('content')
            img_file = request.form.get('img_file')
            date = datetime.now()

            if sno=='0':
                post = Posts(title=box_title, slug=slug, content=content, tagline=tline, img_file=img_file, date=date)
                db.session.add(post)
                db.session.commit()
            else:
                post = Posts.query.filter_by(sno=sno).first()
                post.title = box_title
                post.slug = slug
                post.content = content
                post.tagline = tline
                post.img_file = img_file
                post.date = date
                db.session.commit()
                return redirect('/edit/'+sno)
        post = Posts.query.filter_by(sno=sno).first()
        return render_template('edit.html', params=params, post=post, sno=sno)

@app.route("/uploader", methods = ['GET', 'POST'])
def uploader():	
    if ('user' in session and session['user'] == params['admin_user']):
        if (request.method == 'POST'):
            f= request.files['file1']
            f.save(os.path.join(app.config['UPLOAD_FOLDER'], secure_filename(f.filename) ))
            return redirect('/dashboard')

@app.route("/logout")
def logout():
    session.pop('user')
    return redirect('/')

@app.route("/delete/<string:sno>", methods = ['GET', 'POST'])
def delete(sno):
    if ('user' in session and session['user'] == params['admin_user']):
        post = Posts.query.filter_by(sno=sno).first()
        db.session.delete(post)
        db.session.commit()
    return redirect('/dashboard')

@app.route("/contact", methods = ['GET', 'POST'])
def contact():
    if(('user_email' in session and 'user_pass' in session) or ('user' in session and session['user'] == params['admin_user'])):
        if(request.method=='POST'):
            name = request.form.get('name')
            email = request.form.get('email')
            phone = request.form.get('phone')
            message = request.form.get('message')
            entry = Contacts(name=name, phone_num = phone, msg = message, date= datetime.now(),email = email )
            db.session.add(entry)
            db.session.commit()
            mail.send_message('New message from ' + name,
                              sender=email,
                              recipients = [params['gmail-user']],
                              body = message + "\n" + phone + "\n" + email
                              )
        return render_template('contact.html', params=params)
    else:
        return redirect('/')


if __name__ =='__main__':
    app.run(debug=True)

