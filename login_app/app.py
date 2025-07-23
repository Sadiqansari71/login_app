from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime, timedelta
import jwt
import random
import string

# Create the Flask app
app = Flask(__name__)
app.config['SECRET_KEY'] = 'your-secret-key-123'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///users.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Initialize database
db = SQLAlchemy(app)

# User Model
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(100), unique=True, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f'<User {self.email}>'

# OTP Model
class OTP(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(100), nullable=False)
    code = db.Column(db.String(6), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    used = db.Column(db.Boolean, default=False)
    
    def is_expired(self):
        """Check if OTP is expired (5 minutes)"""
        return datetime.utcnow() - self.created_at > timedelta(minutes=5)

# Helper Functions
def generate_otp():
    """Generate 6-digit OTP"""
    return ''.join(random.choices(string.digits, k=6))

def create_token(email):
    """Create JWT token for user"""
    payload = {
        'email': email,
        'exp': datetime.utcnow() + timedelta(hours=24),
        'iat': datetime.utcnow()
    }
    return jwt.encode(payload, app.config['SECRET_KEY'], algorithm='HS256')

def send_otp_mock(email, otp_code):
    """Mock email service - prints OTP"""
    print(f"\n{'='*50}")
    print(f"MOCK EMAIL SERVICE")
    print(f"{'='*50}")
    print(f"To: {email}")
    print(f"Subject: Your Login Code")
    print(f"Message: Your verification code is: {otp_code}")
    print(f"This code expires in 5 minutes.")
    print(f"{'='*50}\n")

# API Endpoints

@app.route('/api/register', methods=['POST'])
def register():
    """Register new user"""
    try:
        data = request.get_json()
        email = data.get('email', '').lower().strip()
        
        # Validate email
        if not email or '@' not in email:
            return jsonify({
                'success': False,
                'message': 'Valid email is required'
            }), 400
        
        # Check if user exists
        if User.query.filter_by(email=email).first():
            return jsonify({
                'success': False,
                'message': 'User with this email already exists'
            }), 400
        
        # Create new user
        new_user = User(email=email)
        db.session.add(new_user)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Registration successful. Please verify your email.'
        }), 201
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': 'Registration failed'
        }), 500

@app.route('/api/request-otp', methods=['POST'])
def request_otp():
    """Request OTP for login"""
    try:
        data = request.get_json()
        email = data.get('email', '').lower().strip()
        
        # Check if user exists
        user = User.query.filter_by(email=email).first()
        if not user:
            return jsonify({
                'success': False,
                'message': 'User not found'
            }), 404
        
        # Generate OTP
        otp_code = generate_otp()
        
        # Invalidate old OTPs
        OTP.query.filter_by(email=email, used=False).update({'used': True})
        
        # Create new OTP
        new_otp = OTP(email=email, code=otp_code)
        db.session.add(new_otp)
        db.session.commit()
        
        # Send OTP (mock)
        send_otp_mock(email, otp_code)
        
        return jsonify({
            'success': True,
            'message': 'OTP sent to your email'
        }), 200
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': 'Failed to send OTP'
        }), 500

@app.route('/api/verify-otp', methods=['POST'])
def verify_otp():
    """Verify OTP and login"""
    try:
        data = request.get_json()
        email = data.get('email', '').lower().strip()
        otp_code = data.get('otp', '').strip()
        
        # Validate input
        if not email or not otp_code:
            return jsonify({
                'success': False,
                'message': 'Email and OTP are required'
            }), 400
        
        # Find valid OTP
        otp = OTP.query.filter_by(
            email=email, 
            code=otp_code, 
            used=False
        ).first()
        
        if not otp:
            return jsonify({
                'success': False,
                'message': 'Invalid OTP'
            }), 400
        
        # Check if expired
        if otp.is_expired():
            return jsonify({
                'success': False,
                'message': 'OTP has expired'
            }), 400
        
        # Mark OTP as used
        otp.used = True
        db.session.commit()
        
        # Create token
        token = create_token(email)
        
        return jsonify({
            'success': True,
            'message': 'Login successful',
            'token': token
        }), 200
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': 'Verification failed'
        }), 500

@app.route('/api/profile', methods=['GET'])
def get_profile():
    """Get user profile (protected)"""
    try:
        # Get token from header
        auth_header = request.headers.get('Authorization')
        if not auth_header or not auth_header.startswith('Bearer '):
            return jsonify({
                'success': False,
                'message': 'Authorization token required'
            }), 401
        
        token = auth_header.split(' ')[1]
        
        # Decode token
        payload = jwt.decode(
            token, 
            app.config['SECRET_KEY'], 
            algorithms=['HS256']
        )
        email = payload['email']
        
        # Get user
        user = User.query.filter_by(email=email).first()
        if not user:
            return jsonify({
                'success': False,
                'message': 'User not found'
            }), 404
        
        return jsonify({
            'success': True,
            'user': {
                'id': user.id,
                'email': user.email,
                'created_at': user.created_at.isoformat()
            }
        }), 200
        
    except jwt.ExpiredSignatureError:
        return jsonify({
            'success': False,
            'message': 'Token has expired'
        }), 401
    except jwt.InvalidTokenError:
        return jsonify({
            'success': False,
            'message': 'Invalid token'
        }), 401
    except Exception as e:
        return jsonify({
            'success': False,
            'message': 'Failed to get profile'
        }), 500

@app.route('/', methods=['GET'])
def home():
    """API Info endpoint"""
    return jsonify({
        'message': 'User Login API with Email & OTP',
        'version': '1.0',
        'endpoints': {
            'POST /api/register': 'Register new user',
            'POST /api/request-otp': 'Request OTP',
            'POST /api/verify-otp': 'Verify OTP and login',
            'GET /api/profile': 'Get user profile (requires token)'
        }
    })

# Initialize database
with app.app_context():
    db.create_all()
    print("Database tables created successfully!")

if __name__ == '__main__':
    print("Starting User Login API Server...")
    print("Server URL: http://127.0.0.1:5000")
    print("API Documentation: http://127.0.0.1:5000")
    print("Check terminal for OTP codes when testing")
    app.run(debug=True, host='127.0.0.1', port=5000)
