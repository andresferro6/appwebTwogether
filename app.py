import os
import pandas as pd

from ftplib import FTP
from dotenv import load_dotenv
from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your_secret_key'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///users.db'
db = SQLAlchemy(app)

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password = db.Column(db.String(120), nullable=False)

# Replace the following with your FTP server details
ftp_host = "195.23.61.65"
ftp_user = "AntonioFrancisco_16803"
ftp_passwd = "S5lOvr6"

@app.route('/', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        
        username = request.form['username']
        password = request.form['password']

        user = User.query.filter_by(username=username).first()

        if user and check_password_hash(user.password, password):
            flash('Login successful', 'success')
            return redirect(url_for('index'))
        else:
            flash('Invalid username or password', 'danger')
            return redirect(url_for('login'))
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        # Check if the username already exists
        if User.query.filter_by(username=username).first():
            flash('Username already exists. Please choose another.', 'danger')
        else:
            # Hash the password before storing it
            hashed_password = generate_password_hash(password)

            # Create a new user
            new_user = User(username=username, password=hashed_password)
            db.session.add(new_user)
            db.session.commit()

            flash('Registration successful. You can now log in.', 'success')
            return redirect(url_for('login'))
    return render_template('register.html')


@app.route('/files')
def index():
    ftp = FTP(ftp_host)
    ftp.login( user = ftp_user, passwd = ftp_passwd)
    files = [i for i in ftp.nlst() if i.endswith("csv")]
    ftp.quit()
    return render_template('index.html', files = files)

@app.route('/update/<string:nombre>', methods = ["POST"])
def get_file(nombre: str):

    data = request.get_json()

    try:
        ftp = FTP(data.get("ftpHost"))
        ftp.login( user = data.get("ftpUser"), passwd = data.get("ftpPasswd"))
        with open(nombre, 'wb') as local_file:
            ftp.retrbinary('RETR ' + nombre, local_file.write)
            ftp.quit()
            return jsonify({"status": 200,
                    "message": "Success"})

    except Exception as e:
        ftp.quit()
        return jsonify({"status": 400,
                    "message": f"Caught a generic exception: {e}"})


if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)
