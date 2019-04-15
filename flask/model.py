""""
All the Function that do not interact with the Flask app arte placed here
"""
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
import matplotlib.pyplot as plt
import matplotlib.patches as patches
from PIL import Image, ImageDraw, ImageFont
import numpy as np

def convert_pdf(filename, output_path, pagenumber):
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
    try:
        Image.open(f"output{pagenumber}.png")
    except:
        images[0].save(f"output{pagenumber}.png")

    r.close()
    return (image_filename)

def crop_image(filename, area = (400, 400, 800, 800)):
    png_img = PImage.open(filename)
    cropped_img = png_img.crop(area)
    return cropped_img

def draw_rec(area, text, color, page):
    '''
    Draw text and rectacgle over image
    '''
    base = Image.open(f"output{page}.png").convert('RGBA')
    txt = Image.new('RGBA',base.size, (255,255,255,0))

    if color == 'green':
        color_code = (0,255,0,128)
    elif color == 'red':
        color_code = (255,0,0,128)
    else:
        color_code = (255,255,0,128)

    d = ImageDraw.Draw(txt)
    d.rectangle(area, fill=color_code)
    d.text((area[0],area[3]), text, fill=(0,0,0,255))

    out = Image.alpha_composite(base, txt)
    out.save(f"output{page}.png")

def get_numbers(char_list):
    """
    return a list of tuples, orderd, with the first value of the tuple
    representing the number parsed and the second - or +.
    """

    display_dict = {
        'success': True,
        'total': 0,
        'totalparsed': 0,
        'records': []
    }

    # Checks if it's found something
    if len(char_list) < 1:
        return display_dict

    # VERTICAL TEST
    vertical = []
    vertical = [vertical + i.split(' ') for i in char_list]
    # END TEST

    # Let's get the numbers
    number_list = []
    for char in char_list:
        if not char:
            continue
        # Check if its 'minus or plus'
        if is_minus(char):
            symbol = -1
        else:
            symbol = 1

        # Saves the numbers and their symbor +-
        stripped_char = remove_symbols(char)
        int_char = str2int(stripped_char)
        number_list.append((int(int_char) * symbol))

    return number_list

def smart(number_list):
    '''
    Auto detect
    '''
    display_dict = {
        'success': True,
    }

    indexoftotal = [i for i,n in enumerate(number_list) if int(n) == int(sum(number_list)/2)]

    try:
        if len(indexoftotal) < 1:
            indexoftotal = [-1]
        display_dict["totalparsed"] = number_list.pop(indexoftotal[0])
    except:
        display_dict["totalparsed"] = 0

    display_dict["total"] = sum(number_list)
    display_dict['records'] = [i for i in number_list]

    return display_dict

def smart_dev(number_list):
    display_dict = {
        'success': True,
    }

    try:
        display_dict["totalparsed"] = number_list.pop(-1)
    except:
        display_dict["totalparsed"] = 0

    temp_dict = dev_all(number_list)
    display_dict["total"] = temp_dict['total']
    display_dict['records'] = [i for i in number_list]

    return display_dict

def smart_mul(number_list):
    display_dict = {
        'success': True,
    }

    try:
        display_dict["totalparsed"] = number_list.pop(-1)
    except:
        display_dict["totalparsed"] = 0

    temp_dict = mul_all(number_list)
    display_dict["total"] = temp_dict['total']
    display_dict['records'] = [i for i in number_list]

    return display_dict


def sum_all(number_list):
    '''
    Sum
    '''
    display_dict = {
        'success': True,
    }

    display_dict["records"] = [i for i in number_list]
    display_dict["totalparsed"] = 0
    display_dict["total"] = sum(number_list)

    return display_dict

def mul_all(number_list):
    '''
    Multiply
    '''
    display_dict = {
        'success': True,
    }

    display_dict["records"] = [i for i in number_list]
    display_dict["totalparsed"] = 0
    total = 1
    for num in number_list:
        total *= num
    display_dict["total"] = total

    return display_dict

def dev_all(number_list):
    '''
    Multiply
    '''
    display_dict = {
        'success': True,
    }

    display_dict["records"] = [i for i in number_list]
    display_dict["totalparsed"] = 0
    total = number_list[0]
    for num in number_list[1:]:
        total /= num
    display_dict["total"] = round(total, 3)

    return display_dict

def str2int(string_list):
    int_list = [i for i in string_list if i.isdigit()]
    interger = ''.join(i for i in int_list)
    return interger

def remove_symbols(sym_str):
    try:
        return sym_str.replace(',', '').replace(' ', '').replace('.', '')
    except:
        sym_str

def is_minus(stripped_char):
    return (len([i for i in stripped_char if i in '()-']) > 0)

def read_image(filename):

    im = PImage.open(filename)
    text = pytesseract.image_to_string(im, lang = 'eng')
    char_list = text.split('\n')

    char_list = get_numbers(char_list)

    return char_list

def calculate_style(char_list, style, action):
    # styles
    if action == 'result':
        styles = {"Sum": sum_all,
                  "Multiply": mul_all,
                  "Divide": dev_all}
    else:
        styles = {"Sum": smart,
                  "Multiply": smart_mul,
                  "Divide": smart_dev}

    display_dict = styles[style](char_list)
    return display_dict

def save2dict(temp_dict, display_dict):
    '''
    page is still missing
    '''
    temp_dict['total'].append(display_dict['total'])
    temp_dict['totalparsed'].append(display_dict['totalparsed'])
    temp_dict['record'].append(display_dict['records'])
    temp_dict['page'].append(display_dict["page"])
    temp_dict['style'].append(display_dict["style"])
    temp_dict['difference'].append(display_dict['totalparsed']-
                                   display_dict['total'])
    return temp_dict

def color_choice(dic):
    diff = dic['totalparsed']-dic['total']
    if diff == 0:
        color = 'green'
    elif dic['totalparsed'] == 0:
        color = 'yellow'
    else:
        color = 'red'
    return color
