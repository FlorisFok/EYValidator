import os
from flask import request
from flask import render_template
from flask import Flask
from flask import session
from werkzeug.utils import secure_filename
from PIL import Image as PImage
import pytesseract
from pdf2image import convert_from_path, convert_from_bytes
from PyPDF2 import PdfFileWriter, PdfFileReader
from strgen import StringGenerator as SG
from flask import jsonify
import random
import string
import io
import sys
import re

filepath = os.path.dirname(os.path.abspath(__file__))
app = Flask(__name__)
app.secret_key = os.urandom(24)

@app.after_request
def after_request(response):
   response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
   response.headers["Expires"] = 0
   response.headers["Pragma"] = "no-cache"
   return response

def convert_pdf(filename, output_path, pagenumber):
    input_file = 'diditwork'
    print("Start")
    print("Done")

    inp = PdfFileReader(filename, "rb")
    page = inp.getPage(pagenumber)

    wrt = PdfFileWriter()
    wrt.addPage(page)

    r = io.BytesIO()
    wrt.write(r)

    image_filename = os.path.splitext(os.path.basename(filename))[0]
    image_filename = '{}.png'.format(image_filename)
    image_filename = os.path.join(output_path, image_filename)

    images = convert_from_bytes(r.getvalue())
    images[0].save(image_filename)


    print("Done, your cover photo has been saved as {}.".format(input_file+".png"))
    r.close()
    return (image_filename)

def crop_image(filename, area = (400, 400, 800, 800)):
    png_img = PImage.open(filename)
    cropped_img = png_img.crop(area)
    return cropped_img

def pos_neg_calc(list):
    display_dict = {
        'success': True,
        'total': 0,
        'totalparsed': 0,
        'records': []
    }
    for e in list[:-1]:
        if e:
            f = e.replace(',', '').replace(' ', '').replace('.', '')
            if ("(" in f and ")" in f) or "-" in f:
                f = f.replace('(', '').replace(')', '').replace('-', '')
                display_dict['total'] -= int(f)
                display_dict['records'].append(-int(f))
            else:
                display_dict['total'] += int(f)
                display_dict['records'].append(int(f))
    last = list[-1]
    if last:
        l = last.replace(',', '').replace(' ', '').replace('.', '')
        if ("(" in l and ")" in l) or "-" in l:
            l = l.replace('(', '').replace(')', '').replace('-', '')
            display_dict['totalparsed'] = -int(l)
        else:
            display_dict['totalparsed'] = int(l)
    return display_dict

def read_image(filename, point=False):
    im = PImage.open(filename)
    text = pytesseract.image_to_string(im, lang = 'eng')
    display_dict = pos_neg_calc(text.split('\n'))
    print(text)
    print("---------- PARSED DATA ----------")
    for d in display_dict['records']:
        print(d)
    print("-------------- +")
    print("Parsed total:		", display_dict['totalparsed'])
    print("Calculated total:	", display_dict['total'])
    print("-----------------------------------")
    return display_dict

@app.route('/')
def hello():
    return render_template('layout.html')

# def pagechecker():
#     reader = PyPDF2.PdfFileReader(open(session["path"]))
#     print (reader.getNumPages())

@app.route('/upload', methods=['GET', 'POST'])
def upload_file():
    if request.method == 'POST':
        f = request.files['the_file']
        pagenumber = request.form['pagenum']
        if not pagenumber:
            pagenumber = 1
        else:
            pagenumber = int(pagenumber)
        pagenumber -= 1
        filename = ''.join(random.choice(string.ascii_uppercase + string.digits) for _ in range(12)).join(".png")
        path = os.path.join(os.path.join(filepath, 'uploads'), filename)
        session["path"] = path
        f.save(path)
        filen = convert_pdf(path, "./static/pngs", pagenumber)
        pagenumber += 1
        prevnumber = pagenumber - 2
        if (prevnumber < 0):
            prevnumber = 0
        return render_template('next.html', img=filen, filename=filename, nextnumber=pagenumber, prevnumber=prevnumber)

@app.route('/page', methods=['GET', 'POST'])
def next_page():
    if request.method == 'POST':
        f = request.form['filename']
        pagenumber = request.form['pagenum']
        if not pagenumber:
            pagenumber = 1
        else:
            pagenumber = int(pagenumber)
        filename = f
        path = os.path.join(os.path.join(filepath, 'uploads'), filename)
        filen = convert_pdf(path, "./static/pngs", pagenumber)
        pagenumber += 1
        prevnumber = pagenumber - 2
        if (prevnumber < 0):
            prevnumber = 0
        return render_template('next.html', img=filen, filename=filename, nextnumber=pagenumber, prevnumber=prevnumber)

@app.route("/image", methods=["POST"])
def check():

    x1 = request.form.get("x1")
    y1 = request.form.get("y1")
    x2 = request.form.get("x2")
    y2 = request.form.get("y2")

    filename = request.form.get("imgsrc")
    style = request.form.get("style")
    print("TEST")
    print(style)

    if x1 and y1 and x2 and y2 and filename:

        area = (int(x1) * 2, int(y1) * 2, int(x2) * 2, int(y2) * 2)
        image = crop_image(filename, area)
        path = os.path.join(os.path.join(filepath, 'uploads'), "out.png")
        image.save(path, "PNG")
        display_dict = read_image(path)
        return jsonify(display_dict)
    else:
        return jsonify({"success": False})
