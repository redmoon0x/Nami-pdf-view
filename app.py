import logging
from flask import Flask, request, send_file, render_template, redirect, url_for
import requests
from urllib.parse import unquote_plus
import io
import time
import secrets
import os

app = Flask(__name__)

# Set up logging
logging.basicConfig(level=logging.DEBUG)

# In-memory token storage (replace with a database in production)
valid_tokens = {}

def generate_token(user_id):
    token = secrets.token_urlsafe()
    valid_tokens[token] = {'user_id': user_id, 'timestamp': time.time()}
    logging.debug(f"Generated token: {token} for user: {user_id}")
    return token

def verify_token(token):
    logging.debug(f"Verifying token: {token}")
    if token in valid_tokens:
        token_data = valid_tokens[token]
        current_time = time.time()
        token_age = current_time - token_data['timestamp']
        logging.debug(f"Token age: {token_age} seconds")
        if token_age < 3600:  # 1 hour expiration
            return True
        else:
            logging.debug(f"Token expired. Age: {token_age} seconds")
            del valid_tokens[token]
    else:
        logging.debug("Token not found in valid_tokens")
    return False

@app.route('/')
def home():
    return "Welcome to the PDF handler application!"

@app.route('/generate_token/<user_id>')
def generate_token_route(user_id):
    token = generate_token(user_id)
    return f"Generated token: {token}"

@app.route('/pdf')
def handle_pdf():
    url = unquote_plus(request.args.get('url', ''))
    token = request.args.get('token', '')
    action = request.args.get('action', 'view')
    
    logging.debug(f"Received request - URL: {url}, Token: {token}, Action: {action}")
    
    if not url or not token:
        return "Missing URL or token", 400
    
    if not verify_token(token):
        return "Invalid or expired token", 403
    
    if action == 'download':
        try:
            response = requests.get(url, stream=True)
            response.raise_for_status()
            return send_file(
                io.BytesIO(response.content),
                mimetype='application/pdf',
                as_attachment=True,
                download_name='document.pdf'  # Changed from attachment_filename
            )
        except requests.RequestException as e:
            logging.error(f"Error downloading PDF: {str(e)}")
            return f"Error downloading PDF: {str(e)}", 500
    else:
        return render_template('index.html', pdf_url=url, token=token)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 5000)), debug=True)
