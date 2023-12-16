import os
import pandas as pd

from ftplib import FTP

from pandasql import sqldf
from dotenv import load_dotenv
from flask_sqlalchemy import SQLAlchemy
from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
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

@app.route('/files', methods= ["GET", "POST"])
def index():
    if request.method == "POST":
        try:
            data = request.get_json()
            ftp = FTP(data["ftpHost"])
            ftp.login( user = data["ftpUser"], passwd = data["ftpPasswd"])
            files = [i for i in ftp.nlst() if i.endswith("csv")]
            ftp.quit()
            
            return jsonify({
                "status": 200,
                "message": "Succesful",
                "data": files
            })

        except Exception as e:
            return jsonify({
                "status": 400,
                "message": e,
            })


    return render_template('index.html')

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

@app.route('/processdata')
def process():
    frame_preco_databox = pd.read_csv("PrecoDatabox_16803.csv", encoding='latin-1', delimiter=';')
    frame_stock = pd.read_csv("StockQDatabox_16803.csv", encoding='latin-1', delimiter=';')
    cart_stock = pd.read_csv("CatArtDatabox.csv", encoding='latin-1', delimiter=';', on_bad_lines = "skip")

    query = """
    select       
           preco.PRCUNIT,
           preco.PSC,
           tok.QTDDISP,
           tok.PROXENT,
           cart.*
    from cart_stock cart
    left join frame_preco_databox preco
    on cart.EAN = preco.EAN
    left join frame_stock tok
    on cart.ean = tok.ean
    """
    result_frame = sqldf(query)
    result_frame.to_csv("result.csv")
    return result_frame.iloc[:,:10].head(10).to_json(orient = "records")


def get_value(value):
    if value == "Has Headers":
        return "infer"
    return 1

@app.route('/file/<string:nombre>', methods = ["POST"])
def showfile(nombre: str):
    try:
        data = request.get_json()
        try:
            frame = pd.read_csv(data.get("folderName"), header = get_value(data.get("headers")) , encoding = data.get("encoder"), delimiter = data.get("delimiter"))
            return frame.head(10).iloc[:, :4].to_json(orient = "records")
        except:
            frame = pd.read_csv(data.get("folderName"), header = get_value(data.get("headers")) , encoding = data.get("encoder"), delimiter = data.get("delimiter"), on_bad_lines = "skip")
            return frame.head(10).iloc[:, :4].to_json(orient = "records")
    except Exception as e:
        return {"error": e}

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)
