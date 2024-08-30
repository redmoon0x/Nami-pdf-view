from flask import Flask, request, send_file, render_template, redirect
import requests
from urllib.parse import unquote_plus
import io
import time
from flask import abort
import secrets
import os

app = Flask(__name__)



# In-memory token storage (replace with a database in production)
valid_tokens = {}

def generate_token(user_id):
    token = secrets.token_urlsafe()
    valid_tokens[token] = {'user_id': user_id, 'timestamp': time.time()}
    return token

def verify_token(token):
    if token in valid_tokens:
        token_data = valid_tokens[token]
        if time.time() - token_data['timestamp'] < 3600:  # 1 hour expiration
            return True
        else:
            del valid_tokens[token]
    return False

# Use this in your route
@app.route('/')
def home():
    return "Welcome to the PDF handler application!"

@app.route('/pdf')
def handle_pdf():
    url = unquote_plus(request.args.get('url', ''))
    token = request.args.get('token', '')
    action = request.args.get('action', 'view')

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
                attachment_filename='document.pdf'
            )
        except requests.RequestException as e:
            return f"Error downloading PDF: {str(e)}", 500
    else:
        return render_template('index.html', pdf_url=url, token=token)
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 5000)))

