import os
import pandas as pd

from ftplib import FTP
from dotenv import load_dotenv
from flask import Flask, render_template, jsonify

app = Flask(__name__)


# Replace the following with your FTP server details
ftp_host = os.getenv("FTP_HOST")
ftp_user = os.getenv("FTP_USER")
ftp_passwd = os.getenv("FTP_PASSWD")

@app.route('/')
def index():
    ftp = FTP(ftp_host)
    ftp.login( user = ftp_user, passwd = ftp_passwd)
    files = [i for i in ftp.nlst() if i.endswith("csv")]
    
    ftp.quit()
    return render_template('index.html', files = files)

@app.route('/update/<string:nombre>')
def get_file(nombre: str):
    ftp = FTP(ftp_host)
    ftp.login( user = ftp_user, passwd = ftp_passwd)

    try:
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
    app.run(debug=True)
