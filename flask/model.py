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

    r.close()
    return (image_filename)

def crop_image(filename, area = (400, 400, 800, 800)):
    png_img = PImage.open(filename)
    cropped_img = png_img.crop(area)
    return cropped_img

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
    print(vertical[0])

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
    print(number_list)
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
        display_dict["totalparsed"] = number_list.pop(indexoftotal[0])
    except:
        display_dict["totalparsed"] = 0

    display_dict["total"] = sum(number_list)
    display_dict['records'] = number_list

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
    display_dict["total"] = total

    return display_dict

def pos_neg_calc(char_list):
    """
    Auto SUM
    """
    display_dict = {
        'success': True,
        'total': 0,
        'totalparsed': 0,
        'records': []
    }

    if len(char_list) < 1:
        return display_dict

    for char in char_list[:-1]:

        if not char:
            continue

        stripped_char =  remove_symbols(char)
        if ("(" in stripped_char and ")" in stripped_char) or "-" in stripped_char:
            int_char = str2int(stripped_char)
            display_dict['total'] -= int(int_char)
            display_dict['records'].append(-int(int_char))
        else:
            int_char = str2int(stripped_char)
            display_dict['total'] += int(int_char)
            display_dict['records'].append(int(int_char))

    if char_list[-1]:
        stripped_char = remove_symbols(char_list[-1])
        if ("(" in stripped_char and ")" in stripped_char) or "-" in stripped_char:
            int_char = str2int(stripped_char)
            display_dict['totalparsed'] = -int(int_char)
        else:
            int_char = str2int(stripped_char)
            display_dict['totalparsed'] = int(int_char)
    return display_dict

def sum_pos_neg(char_list):
    """
    SUM
    """
    display_dict = {
        'success': True,
        'total': 0,
        'totalparsed': 0,
        'records': []
    }

    if len(char_list) < 1:
        return display_dict

    for char in char_list:
        if not char:
            continue
        stripped_char =  remove_symbols(char)
        if ("(" in stripped_char and ")" in stripped_char) or "-" in stripped_char:
            int_char = str2int(stripped_char)
            display_dict['total'] -= int(int_char)
            display_dict['records'].append(-int(int_char))
        else:
            int_char = str2int(stripped_char)
            display_dict['total'] += int(int_char)
            display_dict['records'].append(int(int_char))
    return display_dict

def multi_pos(char_list):
    """
    Multiply
    """
    display_dict = {
        'success': True,
        'total': 1,
        'totalparsed': 0,
        'records': []
    }
    if len(char_list) < 1:
        return display_dict

    for char in char_list:
        if not char:
            continue
        stripped_char =  remove_symbols(char)
        int_char = str2int(stripped_char)
        display_dict['total'] *= int(int_char)
        display_dict['records'].append(int(int_char))

    return display_dict


def devide_pos(char_list):
    """
    Devide
    """
    display_dict = {
        'success': True,
        'total': 0,
        'totalparsed': 0,
        'records': []
    }
    if len(char_list) < 1:
        return display_dict

    first = True
    for char in char_list:
        if not char:
            continue
        stripped_char =  remove_symbols(char)
        int_char = str2int(stripped_char)

        if first:
            display_dict['total'] = int(int_char)
            first = False

        display_dict['total'] /= int(int_char)
        display_dict['records'].append(int(int_char))

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
    return len([i for i in stripped_char if i in ['()-']]) > 0

def read_image(filename):

    im = PImage.open(filename)
    text = pytesseract.image_to_string(im, lang = 'eng')
    char_list = text.split('\n')

    char_list = get_numbers(char_list)

    return char_list

def calculate_style(char_list, style):
    # styles
    styles = {"ASum": smart,
              "Sum": sum_all,
              "Multiply": mul_all,
              "Divide": dev_all}


    display_dict = styles[style](char_list)

    return display_dict
