import os
from flask import session, Flask, render_template, request
from werkzeug.utils import secure_filename
from PIL import Image as PImage
import pytesseract
from pdf2image import convert_from_path, convert_from_bytes
from PyPDF2 import PdfFileWriter, PdfFileReader
from strgen import StringGenerator as SG
import random
import string
import io
import sys
import re
import pandas as pd

# Own module
from model import *

# Seek file path
filepath = os.path.dirname(os.path.abspath(__file__))

# Set up of Flask app
app = Flask(__name__)
app.secret_key = os.urandom(24)


# Deletes cache don't touch it :)
@app.after_request
def after_request(response):
   response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
   response.headers["Expires"] = 0
   response.headers["Pragma"] = "no-cache"
   return response

# Render Frist page
@app.route('/')
def hello():
    '''
    Renders Homepage when main url is called
    '''
    return render_template('layout.html')

# Function for initial reload
@app.route('/upload', methods=['GET', 'POST'])
def upload_file():
    '''
    This is activated after the pdf is submitted, it renders the page and converts the pdf to png.
    '''
    session['mem'] = []
    session['csv'] = {'i':1}
    if request.method == 'POST':

        # Retrive data
        pdf_file = request.files['the_file']
        pagenumber = request.form['pagenum']

        # Format the page number, from string to int index
        if not pagenumber or not pagenumber.isdigit():
            pagenumber = 1
        else:
            pagenumber = int(pagenumber)
        pagenumber -= 1

        # Generate random filename for temp storage
        filename = ''.join(random.choice(string.ascii_uppercase + string.digits) for _ in range(12)).join(".png")
        path = os.path.join(os.path.join(filepath, 'uploads'), filename)
        session["path"] = path
        pdf_file.save(path)

        # Convert to image
        filen = convert_pdf(path, "./static/pngs", pagenumber)

        # Set page number buttons (Stupid way, change later)
        pagenumber += 1
        prevnumber = pagenumber - 2
        if (prevnumber < 0):
            prevnumber = 0

        # Return all the values and render the site.
        return render_template('next.html', img=filen, filename=filename, nextnumber=pagenumber, prevnumber=prevnumber)

@app.route('/page', methods=['GET', 'POST'])
def next_page():
    '''
    Responsible for switching pages, it's a slow way because of the reloading of
    the page withoud cache
    '''
    if request.method == 'POST':
        # Retrive data
        pdf_file = request.form['filename']
        pagenumber = request.form['pagenum']

        # Convert str request to interger
        if not pagenumber:
            pagenumber = 1
        else:
            pagenumber = int(pagenumber)

        # Find path, and convert new page to png
        path = os.path.join(os.path.join(filepath, 'uploads'), pdf_file)
        filen = convert_pdf(path, "./static/pngs", pagenumber)

        # Set page number buttons (Stupid way, change later)
        pagenumber += 1
        prevnumber = pagenumber - 2
        if (prevnumber < 0):
            prevnumber = 0

        # Return all the values and render the site.
        return render_template('next.html', img=filen, filename=pdf_file, nextnumber=pagenumber, prevnumber=prevnumber)

@app.route("/image", methods=["POST"])
def check():
    '''
    If a selection is made, we begin with the OCR. This will, depending on
    the style selection return a total and all the parsed pieces.
    '''
    # Get the coordinates to crop the image
    x1 = request.form.get("x1")
    y1 = request.form.get("y1")
    x2 = request.form.get("x2")
    y2 = request.form.get("y2")

    # fetching file and style
    filename = request.form.get("imgsrc")
    style = request.form.get("style")

    # Exception handeling
    if not x1 or not y1 or not x2 or not y2 or not filename or not style:
        return jsonify({"success": False})

    # Calculate the real pixel values and crop the image
    area = (int(x1) * 2, int(y1) * 2, int(x2) * 2, int(y2) * 2)
    image = crop_image(filename, area)

    # Save the cropped image
    path = os.path.join(os.path.join(filepath, 'uploads'), "out.png")
    image.save(path, "PNG")

    # Get the data needed and return it to the page without auto reload
    if style == 'Mem':
        # Save parsed numbers in the memory
        char_list = read_image(path)
        session['mem'] = session['mem'] + char_list
        display_dict = {'success': True,
                        'total': 0,
                        'totalparsed': 0,
                        'records': session['mem']}
        return jsonify(display_dict)

    else:
        # Normal path
        char_list = read_image(path)

        # If there are numbers in memory, use those
        if session['mem'] == []:
            display_dict = calculate_style(char_list, style=style)
        else:
            display_dict = calculate_style(session['mem'], style=style)
            # The selected value is the expected total
            display_dict['totalparsed'] = char_list[0]
            session['mem'] = []

        # Save to csv
        temp_dict = session['csv']
        temp_dict[f"parsed{temp_dict['i']}"] = [display_dict['total']]+[display_dict['totalparsed']]+display_dict['records']
        temp_dict['i'] += 1
        session['csv']  = temp_dict
        return jsonify(display_dict)

@app.route("/csv", methods=["POST"])
def make_csv():
    name = request.form.get("filename")
    # Create csv from saved values
    data_dict = session['csv']
    data_dict.pop('i', None)
    df = pd.DataFrame()
    df.to_csv(name+'.csv')
    session['csv'] = {'i':1}
    return jsonify({'success':True})
