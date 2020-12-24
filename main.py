from flask import Flask, render_template, request, session, redirect
from flask_sqlalchemy import SQLAlchemy
from werkzeug.utils import secure_filename
# from flask_mail import Mail
import json
import os
import math
from datetime import datetime


with open('config.json', 'r') as c:
    param = json.load(c)['params']

local_server = True
app = Flask(__name__, template_folder='template')
app.secret_key = 'super-secret-key'
app.config['UPLOAD_FOLDER'] = param['upload_location']
# app.config.update(
#     MAIL_SERVER = 'smtp.gmail.com',
#     MAIL_PORT = '465',
#     MAIL_USE_SSL = True,
#     MAIL_USERNAME = param['gmail_user'],
#     MAIL_PASSWORD = param['gmail_password']
# )
# mail = Mail(app)
if (local_server):
    app.config['SQLALCHEMY_DATABASE_URI'] = param['local_uri']
else:
    app.config['SQLALCHEMY_DATABASE_URI'] = param['prod_uri']

db = SQLAlchemy(app)

class Contacts(db.Model):
    # SNo, Name, Email, Phone_num, Msg, Date
    Sno = db.Column(db.Integer, primary_key=True)
    Name = db.Column(db.String(80), nullable=False)
    Email = db.Column(db.String(20),  nullable=False)
    Phone_num = db.Column(db.String(20), nullable=False)
    Msg = db.Column(db.String(120), nullable=False)
    Date = db.Column(db.String(50), nullable=False)

class Posts(db.Model):
    # SNo, Slug, Title, Content, Date
    Sno = db.Column(db.Integer, primary_key=True)
    Slug = db.Column(db.String(21), nullable=False)
    Title = db.Column(db.String(20),  nullable=False)
    Tag_line = db.Column(db.String(20),  nullable=False)
    Content = db.Column(db.String(120), nullable=False)
    Date = db.Column(db.String(50), nullable=False)
    Img_file = db.Column(db.String(50), nullable=False)



@app.route("/")
def home():

    posts = Posts.query.filter_by().all()#[0:param['no_of_posts']]
    last = math.ceil(len(posts)/int(param['no_of_posts']))
    # Pagination Logic
    page = request.args.get('page')
    if (not str(page).isnumeric()):
        page = 1
    page = int(page)
    posts = posts[(page-1)*int(param['no_of_posts']): (page-1)*int(param['no_of_posts']) + int(param['no_of_posts']) ]
    # First -> prev = #, # next = page+1
    if (page==1):
            prev = '#'
            next = '/?page='+ str(page+1)
    # Last -> prev = page-1, next = #
    elif (page == last):
            prev = '/?page='+ str(page-1)
            next = '#'
    # Middle -> prev  page-1, next = page+1
    else:
            prev = '/?page='+ str(page-1)
            next = '/?page='+ str(page+1)
    
    return render_template('index.html', params=param, posts=posts, prev=prev, next=next)

@app.route('/about')
def about():
    return render_template('about.html', params=param)

@app.route('/dashboard', methods=['GET','POST'])
def dashboard():

    if ('user' in session and session['user'] == param['admin_user']):
        post = Posts.query.all()
        return render_template('dashboard.html', params=param, posts=post)

    if request.method == 'POST':
        username = request.form.get('uname')
        userpass = request.form.get('pass')
        if (username == param['admin_user'] and userpass == param['admin_password']):
            # SET THE SESSION VARIABLE
            session['user'] = username
            post = Posts.query.all()
            return render_template('dashboard.html', params=param, posts=post)

    return render_template('signIn.html', params=param)

@app.route('/edit/<string:sno>', methods=['GET','POST'])
def edit(sno):
    if ('user' in session and session['user'] == param['admin_user']):
        if(request.method == 'POST'):
            box_title = request.form.get('title')
            box_tline = request.form.get('tline')
            box_slug = request.form.get('slug')
            box_content = request.form.get('content')
            box_img_file = request.form.get('img_file')
            box_date = datetime.now()

            if sno == '0':
                post = Posts(Title=box_title, Slug=box_slug, Tag_line=box_tline, Content=box_content, Img_file=box_img_file, Date=box_date)
                db.session.add(post)
                db.session.commit()
            else:
                post = Posts.query.filter_by(Sno=sno).first()
                post.Title = box_title
                post.Slug = box_slug
                post.Tag_line = box_tline
                post.Content = box_content
                post.Img_file = box_img_file
                post.Date = box_date        
                db.session.commit()
                return redirect('/edit/'+sno)

        post = Posts.query.filter_by(Sno=sno).first()
        return render_template('edit.html', params=param, post=post, Sno=sno)


@app.route("/uploader", methods=['GET', 'POST'])
def uploader():
    if ('user' in session and session['user'] == param['admin_user']):
        if (request.method == 'POST'):
            f = request.files['file1']
            f.save(os.path.join(app.config['UPLOAD_FOLDER'], secure_filename(f.filename)))
            return "Uploaded Successfully..."


@app.route("/logout")
def logout():
    session.pop('user')
    return redirect('/dashboard')

@app.route("/delete/<string:sno>", methods = ['GET', 'POST'])
def delete(sno):
    if ('user' in session and session['user'] == param['admin_user']):
        post = Posts.query.filter_by(Sno=sno).first()
        db.session.delete(post)
        db.session.commit()
        return redirect('/dashboard')

@app.route("/contact", methods=['GET', 'POST'])
def contact():
    if (request.method == 'POST'):
# Add Entry to the database        
        name=request.form.get('name')
        email=request.form.get('email')
        phone=request.form.get('phone')
        msg=request.form.get('msg')

        entry = Contacts(Name=name, Email=email, Phone_num=phone, Msg=msg, Date=datetime.now())
        db.session.add(entry)
        db.session.commit()
        # mail.send_message('New message from ' + name, sender=email, recipients=[param['gmail_user']], body=msg + "\n" + phone)

    return render_template('contact.html', params=param)

@app.route("/signin")
def signin():
    return render_template('signIn.html', params=param)

@app.route('/post/<string:post_slug>', methods=['GET'])
def post_rout(post_slug):
    post =  Posts.query.filter_by(Slug=post_slug).first()
    return render_template('post.html', params=param, posts=post)

@app.route('/bootstrap')
def bootstrap():
    return render_template('bootstrap.html')

app.run(debug=True)