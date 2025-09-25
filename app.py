from flask import Flask, render_template, request, redirect, url_for, flash, session
from pymongo import MongoClient
from functools import wraps
from werkzeug.security import generate_password_hash, check_password_hash
import re
import requests
import ssl
import socket
import whois
from datetime import datetime
from urllib.parse import urlparse
import tld
from googlesearch import search

app = Flask(__name__, static_url_path='/static')
app.secret_key = 'your-secret-key'  # Change this to a secure secret key

# MongoDB connection
client = MongoClient('mongodb://localhost:27017/')
db = client['phishing_detector']
users = db['users']
scan_history = db['scan_history']

# Login required decorator
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user' not in session:
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        user = users.find_one({'email': request.form['email']})
        if user and check_password_hash(user['password'], request.form['password']):
            session['user'] = request.form['email']
            return redirect(url_for('dashboard'))
        flash('Invalid credentials')
    return render_template('login.html')

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        if users.find_one({'email': request.form['email']}):
            flash('Email already exists')
        else:
            users.insert_one({
                'email': request.form['email'],
                'password': generate_password_hash(request.form['password'])
            })
            flash('Registration successful')
            return redirect(url_for('login'))
    return render_template('signup.html')

@app.route('/logout')
def logout():
    session.pop('user', None)
    return redirect(url_for('home'))

@app.route('/dashboard')
@login_required
def dashboard():
    history = scan_history.find({'user': session['user']})
    return render_template('dashboard.html', history=history)

def check_phishing_url(url):
    score = 0
    max_score = 10
    parsed_url = urlparse(url)
    domain = parsed_url.netloc
    
    # Check for suspicious URL patterns
    suspicious_patterns = [
        r'paypal.*\.com', r'bank.*\.com', r'login.*\.com', r'secure.*\.com',
        r'account.*\.com', r'update.*\.com', r'verify.*\.com', r'service.*\.com',
        r'confirm.*\.com', r'-', r'@', r'javascript:', r'data:', r'file:',
        r'admin.*\.com', r'server.*\.com', r'client.*\.com', r'setup.*\.com'
    ]
    
    if any(re.search(pattern, url.lower()) for pattern in suspicious_patterns):
        score += 2

    # Check domain age
    try:
        domain_info = whois.whois(domain)
        if domain_info.creation_date:
            creation_date = domain_info.creation_date
            if isinstance(creation_date, list):
                creation_date = creation_date[0]
            domain_age = (datetime.now() - creation_date).days
            if domain_age < 365:  # Domain less than 1 year old
                score += 2
    except:
        score += 1  # If WHOIS lookup fails, consider it suspicious

    # Check SSL certificate
    try:
        ctx = ssl.create_default_context()
        with ctx.wrap_socket(socket.socket(), server_hostname=domain) as s:
            s.connect((domain, 443))
            cert = s.getpeercert()
            if not cert:
                score += 2
    except:
        score += 2  # No SSL or invalid certificate

    # Check for suspicious URL characteristics
    if len(domain) > 30:  # Unusually long domain
        score += 1
    if domain.count('.') > 3:  # Too many subdomains
        score += 1
    if re.search(r'\d{4,}', domain):  # Contains many numbers
        score += 1

    # Check if domain exists in Google search results
    try:
        search_results = list(search(domain, num_results=1))
        if not search_results:
            score += 1
    except:
        score += 1

    # Check for IP address in URL
    if re.search(r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}', url):
        score += 2

    # Check for URL redirects
    try:
        response = requests.get(url, allow_redirects=False, timeout=5)
        if response.status_code in [301, 302]:
            score += 1
    except:
        score += 1

    # Check for uncommon TLD
    try:
        domain_tld = tld.get_tld(url, as_object=True)
        common_tlds = ['.com', '.org', '.net', '.edu', '.gov']
        if domain_tld.extension not in common_tlds:
            score += 1
    except:
        score += 1

    return score >= max_score/2

@app.route('/scan', methods=['POST'])
@login_required
def scan_url():
    url = request.form['url']
    is_phishing = check_phishing_url(url)
    
    # Additional metadata for better reporting
    scan_result = {
        'user': session['user'],
        'url': url,
        'result': 'Phishing' if is_phishing else 'Genuine',
        'timestamp': datetime.now(),
        'scan_score': check_phishing_url(url),
    }
    
    scan_history.insert_one(scan_result)
    return render_template('result.html', url=url, is_phishing=is_phishing, scan_result=scan_result)

if __name__ == '__main__':
    app.run(debug=True)
