import os
from flask import Flask
from flask import redirect,flash,url_for
from flask import render_template
from flask import request
from datetime import datetime
from flask_sqlalchemy import SQLAlchemy
from flask_login import login_user, current_user, logout_user, login_required
from flask_login import LoginManager
from flask_bcrypt import Bcrypt 
from flask_login import UserMixin
#from forms import RegistrationForm, LoginForm


#----------------------
# config
#----------------------
app = Flask(__name__)
# database
project_dir = os.path.dirname(os.path.abspath(__file__))
database_file = "sqlite:///{}".format(os.path.join(project_dir, "meal_prep_database_backup.db")) # file-based database
app.config["SQLALCHEMY_DATABASE_URI"] = database_file
db = SQLAlchemy(app)
# register, login, logout
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, BooleanField
from wtforms.validators import DataRequired, Length, Email, EqualTo

class RegistrationForm(FlaskForm):
    """
    variable name will be called as a key in the html, and input name of field will be represented in the Browser
    """
    username = StringField('Username',
                           validators=[DataRequired(), Length(min=2, max=20)])
    email = StringField('Email',
                        validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired()])
    confirm_password = PasswordField('Confirm Password',
                                     validators=[DataRequired(), EqualTo('password')])
    submit = SubmitField('Sign Up')

    def validate_username(self, username):
        """
        Create a custome validation funtion to check if this username existed in our database already.

        Note:
            flask_wtf extention makes using custom logic to to validate a form 
            very easy since you can hook into the whole validation process:
            """
        user = User.query.filter_by(username=username.data).first()
        if user:
            # if user is not None
            raise ValidationError('That username is taken. Please choose a different one.')

    def validate_email(self, email):
        user = User.query.filter_by(email=email.data).first()
        if user:
            raise ValidationError('That email is taken. Please choose a different one.')

class LoginForm(FlaskForm):
    # we choose use email and password as required login information 
    email = StringField('Email',
                        validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired()])
    remember = BooleanField('Remember Me')
    submit = SubmitField('Login')

app.config['SECRET_KEY'] = '2dfc013cd636382d0dd9f6a09672c052'
# login extention
login_manager = LoginManager(app)
# get better display on browser for flash message using bootstrap
login_manager.login_view = 'login'
login_manager.login_message_category = 'info'
# hash password 
bcrypt = Bcrypt(app)


# table1 : for saving weekly tdeelogin_manager
class Tdee_target(db.Model):
    # how to solve schema conflict

    # We always need an id in the table
    id = db.Column(db.Integer, primary_key=True)
    # A tdee_target has target calories, protien, carb and fat:
    t_tdee = db.Column(db.Float,nullable=False)
    t_protein = db.Column(db.Float,nullable=False)
    t_carb = db.Column(db.Float,nullable=False)
    t_fat = db.Column(db.Float,nullable=False)
    # track date
    t_tdee_date = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    # here is primary key of user
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

    def __repr__(self):
        return "<Tdee_target: {} on {}, and your target macros is {}P{}C{}F>".format(
            self.t_tdee,
            self.t_tdee_date,
            self.t_protein,
            self.t_carb,
            self.t_fat,
            )
# table2 : for food macros
class Food_macros(db.Model):
    # We always need an id in the table
    id = db.Column(db.Integer, primary_key=True)
    # food macros
    f_name = db.Column(db.String(120),nullable=False)
    f_weight = db.Column(db.Float,nullable=False)
    f_protein = db.Column(db.Float,nullable=False)
    f_carb = db.Column(db.Float,nullable=False)
    f_fat = db.Column(db.Float,nullable=False)
    f_cal = db.Column(db.Float,nullable=False)
    # track date
    f_date = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    # here is primary key of user
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

    def __repr__(self):
        return "<food name: {}, weight {}, calories {}, and the macros is {}P{}C{}F>".format(
            self.f_name,
            self.f_weight,
            self.f_cal,
            self.f_protein,
            self.f_carb,
            self.f_fat,
            )

@login_manager.user_loader
def load_user(user_id):
    # Getting user by primary key, return an instance
    return User.query.get(int(user_id))

# table3: User information
class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(20), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    image_file = db.Column(db.String(20), nullable=False, default='default.jpg')
    password = db.Column(db.String(60), nullable=False)
    #  db.relationship() helps us to build relationship between Post table. Noted: it's relationship instead of columns called foods or tdeetargets 
    foods = db.relationship('Food_macros', backref='author', lazy=True) # one user can have many foods (1-to-many relationship)
    tdeetargets  = db.relationship('Tdee_target', backref='author', lazy=True) # one user can have many tdee targets (1-to-many relationship)

    def __repr__(self):
        return f"User('{self.username}', '{self.email}', '{self.image_file}')"

@app.route('/', methods=["GET", "POST"])
def home():
    return render_template("home.html")

@app.route('/today_macros', methods=["GET", "POST"])
def today_macros():
    foods = None
    user_id = current_user.id
    username = current_user.username
    #print ('user_id', current_user.id)
    # check if someone just submitted the form
    if request.form:
        # If they did, we can access the data that they submitted through the request.form
        # request.form return a dict with (key=field name that you assign in html, value = user's input) pair
        # Noted: the key has nothing to do with database
        try:
            # Get the incoming data from the request.form dictionary.
            food_name = request.form.get("food_name")
            weight = request.form.get("gram")
            cal = request.form.get("calorie")
            p = request.form.get("protein")
            c = request.form.get("carb")
            f = request.form.get("fat")
            # get user through query
            user = User.query.filter_by(username=username).first()
            # add this instance into database
            food = Food_macros(
                f_name = food_name,
                f_weight = weight,
                f_cal = cal,
                f_protein = p,
                f_carb = c,
                f_fat = f,
                user_id = user.id
                )
            db.session.add(food)
            db.session.commit()
        except Exception as e:
            print("Failed to add food macros into database")
            print(e)
    # retrieve all of the foods out of this specific user 
    # version1: 列出這個使用者DB所有的foods
    # version3: 保留前一天的紀錄, 有選單你可以看到你的過去歷史紀錄, 然後往內加。
    # version2: 24小時後更新一次, 每天都是空的, 有選單你可以看到你的過去歷史紀錄, 然後往內加。
    foods = Food_macros.query.filter_by(user_id=user_id).all() # return a list, each element inside the list is a Food_macros class and each of instance has key name u designed in the table
    #------------------
    # retrieve the latest tdee target 
    #------------------
    print (Tdee_target.query.filter_by(user_id=user_id).all())
    try:
        tdee_target = Tdee_target.query.filter_by(user_id=user_id).all()[-1]
    except:
        tdee_target = Tdee_target.query.filter_by(user_id=user_id).first()
    #-----------------
    # calculation
    #-----------------
    # get total
    try:
        total_p = sum([f.f_protein for f in foods])
    except:
        print ('User may input wrong format for db')
        total_p = []
        for f in foods:
            try:
                tmp = float(f.f_protein)
            except:
                tmp = 0
            total_p.append(tmp)
        total_p = sum(total_p)
    try:
        total_c = sum([f.f_carb for f in foods])
    except:
        print ('User may input wrong format for db')
        total_c = []
        for f in foods:
            try:
                tmp = float(f.f_carb)
            except:
                tmp = 0
            total_c.append(tmp)
        total_c = sum(total_c)
    try:
        total_f = sum([f.f_fat for f in foods])
    except:
        print ('User may input wrong format for db')
        total_f = []
        for f in foods:
            try:
                tmp = float(f.f_fat)
            except:
                tmp = 0
            total_f.append(tmp)
        total_f = sum(total_f)
    try:
        total_cal = sum([f.f_cal for f in foods])    
    except:
        print ('User may input wrong format for db')
        total_cal = []
        for f in foods:
            try:
                tmp = float(f.f_cal)
            except:
                tmp = 0
            total_cal.append(tmp)
        total_cal = sum(total_cal)
    # we should separate home.html and today_macros.html
    return render_template("today_macros.html", 
        foods = foods, 
        tdee_target = tdee_target, 
        total_p=total_p, 
        total_c = total_c,
        total_f = total_f,
        total_cal = total_cal
        )

@app.route("/tdee", methods=["GET","POST"])
def tdee():
    try:
        if request.method == 'GET':
            return render_template('add_tdee_target.html')
        # Get the incoming data from the request.form dictionary.
        tdee = request.form.get("tdee")
        tdee_p = request.form.get("tdee_p")
        tdee_c = request.form.get("tdee_c")
        tdee_f = request.form.get("tdee_f")
        username = current_user.username
        #print ('username', current_user.username)
        # get user through query
        user = User.query.filter_by(username=username).first()
        # add this instance into database
        TDEE = Tdee_target(
            t_tdee = tdee,
            t_protein = tdee_p,
            t_carb = tdee_c,
            t_fat = tdee_f,
            user_id = user.id
            )
        db.session.add(TDEE)
        db.session.commit()
    except Exception as e:
        print("Couldn't update tdee target")
        print(e)
    return redirect(url_for("today_macros"))

@app.route("/update", methods=["POST"])
def update():
    """
    provide updating existing data functionality
    """
    try:
        print ('update',request.form)
        newtitle = request.form.get("newtitle")
        oldtitle = request.form.get("oldtitle")
        # etches the book with the old title from the database 
        book = Book.query.filter_by(title=oldtitle).first() # Return the first result of this Query or None if the result doesn’t contain any row.
        # Updates that book's title to the new title
        book.title = newtitle
        db.session.commit()
    except Exception as e:
        # for the case what if new title is existed in database allready.
        # since we set title in our database is unique field
        print("Couldn't update book title")
        print(e)
    return redirect(url_for("today_macros"))

@app.route("/delete", methods=["POST"])
def delete():
    """
    provide updating existing data functionality
    """
    f_name = request.form.get("food_name_deleted")
    food = Food_macros.query.filter_by(f_name=f_name).first()
    db.session.delete(food)
    db.session.commit()
    return redirect(url_for("today_macros"))


@app.route("/register", methods=['GET', 'POST'])
def register():
     # check if the user is currently logged in, to avoid them can go back to register page after he logged in already
    if current_user.is_authenticated:
        return redirect(url_for('home'))
    form = RegistrationForm()
    if form.validate_on_submit():
        hashed_password = bcrypt.generate_password_hash(form.password.data).decode('utf-8')
        # add this user who just registered into database
        user = User(username=form.username.data, email=form.email.data, password=hashed_password)
        db.session.add(user)
        db.session.commit()
        flash('Your account has been created! You are now able to log in', category = 'success')
        # after registraction, go to login page
        return redirect(url_for('login'))
    return render_template('register.html', form=form)


@app.route("/login", methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        # check if the user is currently logged in
        # if a user is already logged in, and they try to go to the login and register page, it's kind of wierd.
        # so we redirect them into home page
        return redirect(url_for('home'))
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user and bcrypt.check_password_hash(user.password, form.password.data):
            # if user is existed and password is correct
            # we simply use login_user to help this user login
            login_user(user, remember=form.remember.data)
            # get next parameter from URL if it exists
            next_page = request.args.get('next') # request.args returns a dictionary
            return redirect(next_page) if next_page else redirect(url_for('home'))
        else:
            flash('Login Unsuccessful. Please check email and password', 'danger')
    return render_template('login.html', form=form)

@app.route("/logout")
def logout():
    logout_user()
    return redirect(url_for('home'))
    
if __name__ == "__main__":
    app.run(debug=True, port=1030)













