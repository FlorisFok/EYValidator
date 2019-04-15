"""
Routes and views for the flask application.
"""

from datetime import datetime
from flask import render_template, request, url_for
from flaskValidator import app
from werkzeug import *
import os

app.config["UPLOAD_FOLDER"] = "/uploads"

@app.route("/")
def index():
   return redirect("/upload")


@app.route('/upload', methods=['GET', 'POST'])
def upload_file():
   if request.method == "GET":
       return render_template("index.html")
   if request.method == 'POST':
       file = request.files['imgFile']
       filename = secure_filename(file.filename)
       file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
       return "file save complete"