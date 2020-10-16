from app import app
from flask import render_template,request, redirect, url_for
import re
import urllib
import html.parser
import string
from base64 import urlsafe_b64decode
from urllib.parse import unquote
maketrans = str.maketrans


def decode_input_url(url):
    match = re.search(r'https://urldefense.*/(v[0-9])/', url)
    if match:
        if match.group(1) == 'v1':
            decoded_url = decodev1(url)
        elif match.group(1) == 'v2':
            decoded_url = decodev2(url)
        elif match.group(1) == 'v3':
            decoded_url = decodev3(url)
        else:
            decoded_url = url
    else:
        decoded_url = url

    return decoded_url


def decodev1(rewrittenurl):
    match = re.search(r'u=(.+?)&k=', rewrittenurl)
    print(match)
    if match:
        urlencodedurl = match.group(1)
        htmlencodedurl = urllib.parse.unquote(urlencodedurl)
        url = html.unescape(htmlencodedurl)
    else:
        url = rewrittenurl

    return url



def decodev2(rewrittenurl):
    match = re.search(r'u=(.+?)&[dc]=', rewrittenurl)
    if match:
        specialencodedurl = match.group(1)
        trans = str.maketrans('-_', '%/')
        urlencodedurl = specialencodedurl.translate(trans)
        htmlencodedurl = urllib.parse.unquote(urlencodedurl)
        url = html.unescape(htmlencodedurl)
    else:
        url = rewrittenurl

    return url


def decodev3(rewrittenurl):
    global dec_bytes

    def replace_token(token):
        current_marker = 0
        if token == '*':
            character = dec_bytes[current_marker]
            current_marker += 1
            return character
        if token.startswith('**'):
            run_length = v3_run_mapping[token[-1]]
            run = dec_bytes[current_marker:current_marker + run_length]
            current_marker += run_length
            return run

    def substitute_tokens(text, start_pos=0):
        v3_token_pattern = re.compile(r"\*(\*.)?")
        match = v3_token_pattern.search(text, start_pos)
        if match:
            start = text[start_pos:match.start()]
            built_string = start
            token = text[match.start():match.end()]
            built_string += replace_token(token)
            built_string += substitute_tokens(text, match.end())
            return built_string
        else:
            return text[start_pos:len(text)]

    v3_run_mapping = {}
    run_values = string.ascii_uppercase + string.ascii_lowercase + string.digits + '-' + '_'
    run_length = 2
    for value in run_values:
        v3_run_mapping[value] = run_length
        run_length += 1

    v3_pattern = re.compile(r'v3/__(?P<url>.+?)__;(?P<enc_bytes>.*?)!')
    match = v3_pattern.search(rewrittenurl)

    if match:
        url = match.group('url')
        encoded_url = unquote(url)
        enc_bytes = match.group('enc_bytes')
        enc_bytes += '=='
        dec_bytes = (urlsafe_b64decode(enc_bytes)).decode('utf-8')
        url = substitute_tokens(encoded_url)
    else:
        url = rewrittenurl
    return url

@app.route('/', methods=['GET', 'POST'])
def index():

    if request.method =='POST':

        url = request.form.get('urlTextArea')
        decode_url = decode_input_url(url)

        if decode_url!="error":
            return render_template('index.html', encode_url=url, decode_url=decode_url)
        else:
            err_message = "check if URL is a proofpoint URL"
            return render_template('index.html', encode_url=url, decode_url=decode_url, err_message=err_message)

    return render_template('index.html')
