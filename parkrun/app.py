from flask import Flask, render_template, request, redirect, url_for, flash
from google.cloud import firestore
import re
import os

app = Flask(__name__)
app.secret_key = os.environ.get('FLASK_SECRET_KEY', 'dev-key-change-this')

# Initialize Firestore
db = firestore.Client()

# Predefined running clubs
RUNNING_CLUBS = [
    "Unattached",
    "City Runners",
    "Marathon Club",
    "Trail Blazers",
    "Speed Demons",
    "Weekend Warriors"
]

def validate_barcode(barcode):
    """Validate Parkrun barcode format (A followed by 6-7 digits)"""
    return re.match(r'^A\d{6,7}$', barcode.upper()) is not None

@app.route('/')
def index():
    return render_template('index.html', clubs=RUNNING_CLUBS)

@app.route('/register', methods=['POST'])
def register():
    name = request.form.get('name', '').strip()
    barcode = request.form.get('barcode', '').strip().upper()
    club = request.form.get('club', '')
    
    # Validation
    if not name:
        flash('Name is required')
        return redirect(url_for('index'))
    
    if not validate_barcode(barcode):
        flash('Invalid barcode format (should be A followed by 6-7 digits)')
        return redirect(url_for('index'))
    
    if club not in RUNNING_CLUBS:
        flash('Please select a valid running club')
        return redirect(url_for('index'))
    
    # Check if barcode already exists
    existing = db.collection('participants').where('barcode', '==', barcode).get()
    if existing:
        flash('This barcode is already registered')
        return redirect(url_for('index'))
    
    # Save to Firestore
    try:
        db.collection('participants').add({
            'name': name,
            'barcode': barcode,
            'club': club,
            'registered_at': firestore.SERVER_TIMESTAMP
        })
        flash('Registration successful!')
    except Exception as e:
        flash('Registration failed. Please try again.')
    
    return redirect(url_for('index'))

@app.route('/participants')
def participants():
    """View all registered participants"""
    participants = db.collection('participants').order_by('registered_at', direction=firestore.Query.DESCENDING).get()
    return render_template('participants.html', participants=participants)

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8080))
    app.run(host='0.0.0.0', port=port)