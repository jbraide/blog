import os
from flask import Flask, render_template, redirect, url_for, request, session
from wtforms import StringField, TextAreaField, PasswordField, Form, validators
from flask_sqlalchemy import SQLAlchemy
from passlib.hash import sha256_crypt
from datetime import datetime
from functools import wraps


def is_logged_in(f):
    @wraps(f)
    def wrap(*args, **kwargs):
        if 'logged_in' in session:
            return f(*args,**kwargs)
        else:
            flash('Unauthorized, Please Login','danger')
            return redirect(url_for('login'))
    return wrap

project_dir = os.path.dirname(os.path.abspath(__file__))
database_file = "sqlite:///{}".format(os.path.join(project_dir,"blog.db"))

#instantiate flask app
app = Flask(__name__)
#configure flask-sqlalchemy
app.config['SQLALCHEMY_DATABASE_URI'] = database_file

# Blogpost form class
class BlogPostForm(Form):
    title = StringField('Title',[validators.Length(min=1, max=200)])
    subtitle = StringField('Subtitle',[validators.Length(min=1, max=200)])
    author = StringField('Author', [validators.Length(min=1, max=100)])
    content = TextAreaField('Content', [validators.Length(min=300)])

# Admin registration class
class  RegisterForm(Form):
    name = StringField('Name',[validators.Length(min=1, max=30)])
    username = StringField('Username',[validators.Length(min=4, max=25)])
    email =  StringField('Email', [validators.Length(min=6, max=50)])
    password = PasswordField('Password',[
    validators.DataRequired(),
    validators.EqualTo('confirm', message = 'Passwords do not match')
    ])
    confirm = PasswordField('Confirm Password')



# initialize database
db = SQLAlchemy(app)

#blog post database model class
class BlogPost(db.Model):
    id = db.Column(db.Integer,primary_key=True)
    title = db.Column(db.String(50))
    subtitle = db.Column(db.String(50))
    author = db.Column(db.String(20))
    date_posted = db.Column(db.DateTime)
    content = db.Column(db.Text)

#admin databases model class
class Admin(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50))
    username = db.Column(db.String(50))
    email = db.Column(db.String(50))
    password = db.Column(db.String(50))




@app.route('/')
def index():
    posts = BlogPost.query.order_by(BlogPost.date_posted.desc()).all()
    return render_template('index.html', posts=posts)

@app.route('/about')
def about():
    return render_template('about.html')


@app.route('/post/<string:id>/', methods=['GET'])
def post(id):
    post = BlogPost.query.filter_by(id=id).one()

    return render_template('post.html',post=post)
@app.route('/dashboard')
@is_logged_in
def dashboard():
    posts = BlogPost.query.all()
    return render_template('dashboard.html', posts=posts)

@app.route('/add',methods=['GET','POST'])
@is_logged_in
def add():
    form = BlogPostForm(request.form)

    if request.method == 'POST' and form.validate():
        title = form.title.data
        subtitle = form.subtitle.data
        author = form.author.data
        content = form.content.data
        post = BlogPost(title=title, subtitle = subtitle, author=author, content=content)
        db.session.add(post)
        db.session.commit()

        return redirect(url_for('index'))


    return render_template('add.html', form=form)

@app.route('/edit/<string:id>',methods=['GET','POST'])
@is_logged_in
def edit(id):
    post = BlogPost.query.filter_by(id=id).one()
    form = BlogPostForm(request.form)

    #Populate post form fields
    form.title.data = post.title
    form.subtitle.data = post.subtitle
    form.author.data = post.author
    form.content.data = post.content

    if request.method == 'POST' and form.validate():
        title = request.form['title']
        subtitle = request.form['subtitle']
        author = request.form['author']
        content = request.form['content']


        post.title = title
        post.subtitle = subtitle
        post.author = author
        post.content = content

        db.session.commit()

        return redirect(url_for('index'))
    return render_template('edit.html',form=form)



@app.route('/delete/<string:id>/', methods=['GET','POST'])
@is_logged_in
def delete(id):

    post = BlogPost.query.filter_by(id=id).one()

    db.session.delete(post)
    db.session.commit()
    return redirect(url_for('index'))


@app.route('/register', methods=['GET','POST'])
def register():
    form = RegisterForm(request.form)
    if request.method == 'POST' and form.validate():
        name = form.name.data
        username = form.username.data
        email = form.email.data
        password = sha256_crypt.encrypt(str(form.password.data))

        admin = Admin(name=name, username=username, email=email, password=password)
        db.session.add(admin)
        db.session.commit()

        return redirect(url_for('login'))
    return render_template('register.html', form=form)

@app.route('/login', methods=['GET','POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password_candidate = request.form['password']

        result = Admin.query.filter_by(username=username).one()

        password = result.password

        if sha256_crypt.verify(password_candidate, password):
            session['logged_in'] = True
            session['username'] = username

            return redirect(url_for('dashboard'))
        else:
            error = 'Invalid Login'
            return render_template('login.html', error=error)

    return render_template('login.html')




    return render_template('login.html')

@app.route('/logout')
@is_logged_in
def logout():
    session.clear()
    return redirect(url_for('login'))

@app.route('/contact')
def contact():
    return render_template('contact.html')



if __name__ == '__main__':
    app.secret_key = 'Secret1234'
    app.run(debug=True)
