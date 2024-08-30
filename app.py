import logging
from flask import Flask, request, send_file, render_template
import requests
from urllib.parse import unquote_plus
import io
import os
import psycopg2
from datetime import datetime
from psycopg2.extras import DictCursor

app = Flask(__name__)

# Set up logging
logging.basicConfig(level=logging.DEBUG)

# PostgreSQL connection string
DATABASE_URL = os.environ['postgresql://tokens_q0zt_user:NaKCtK3QIJGNL3D4dVpcJuxA0q3ZfigA@dpg-cr8q3156l47c73bnbbqg-a.oregon-postgres.render.com/tokens_q0zt']

def get_db_connection():
    return psycopg2.connect(DATABASE_URL, sslmode='require')

def verify_token(token):
    logging.debug(f"Verifying token: {token}")
    conn = get_db_connection()
    with conn.cursor(cursor_factory=DictCursor) as cur:
        cur.execute("SELECT expiry FROM tokens WHERE token = %s", (token,))
        result = cur.fetchone()
        if result:
            expiry = result['expiry']
            if expiry > datetime.now():
                logging.debug(f"Token {token} verified successfully")
                return True
            else:
                cur.execute("DELETE FROM tokens WHERE token = %s", (token,))
                conn.commit()
                logging.debug(f"Token {token} expired and deleted")
        else:
            logging.debug(f"Token {token} not found in database")
    conn.close()
    return False

@app.route('/')
def home():
    return "Welcome to the PDF handler application!"

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
                download_name='document.pdf'
            )
        except requests.RequestException as e:
            logging.error(f"Error downloading PDF: {str(e)}")
            return f"Error downloading PDF: {str(e)}", 500
    else:
        return render_template('index.html', pdf_url=url, token=token)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 5000)), debug=True)
