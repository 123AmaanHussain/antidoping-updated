# Anti-Doping Educational Platform - Project Overview 🎯

## Project Summary
Our team has developed an innovative anti-doping educational platform that combines podcasts, AI coaching, and interactive features to make anti-doping education more engaging and accessible.

## Core Features Implemented

### 1. Podcast Management System 🎧
- **Multi-Source Integration:**
  - Fetches podcasts from Spotify, YouTube, and iTunes
  - Unified search across all platforms
  - Smart categorization of content

- **Modern User Interface:**
  - Clean, responsive design
  - Easy-to-use search and filters
  - Gradient-based modern styling
  - Mobile-friendly layout

### 2. AI Coach System 🤖
- Interactive chat interface
- Personalized responses
- Anti-doping knowledge base
- Real-time assistance

### 3. Digital Twin System 👤
- User profile management
- Progress tracking
- Personalized learning paths
- Achievement system

### 4. Digital Twin Athlete Monitoring
The Digital Twin system provides real-time athlete monitoring and health tracking:

#### Technical Implementation
- **Backend Service**: `digital_twin_service.py`
  - Bluetooth Low Energy (BLE) device connectivity
  - Real-time data collection and processing
  - Anomaly detection and health monitoring
  - Support for multiple fitness device brands

#### Key Features
- Real-time health metrics monitoring
  - Heart rate tracking
  - Step counting
  - Activity duration measurement
  - Performance analytics

#### Device Support
- Fitbit devices
- Mi Band series
- Garmin devices
- Apple Watch
- Samsung Galaxy Watch

#### User Interface
- Responsive design for all devices
- Real-time data visualization
- Interactive device management
- Dark mode support
- Animated alerts and notifications

## Technical Implementation

### Backend Architecture
```
Python Flask Application
│
├── MongoDB Database
│   ├── User Data
│   ├── Podcast Information
│   └── Learning Progress
│
├── External APIs
│   ├── Spotify
│   ├── YouTube
│   └── iTunes
│
└── AI Services
    ├── Coach System
    └── Digital Twin
```

### Frontend Structure
- Modern HTML5/CSS3
- Vanilla JavaScript
- Responsive Design
- Interactive UI Components

## Environment Setup and Dependencies

### 1. Virtual Environment Setup
```bash
# Create virtual environment
python -m venv venv

# Activate virtual environment
# Windows
venv\Scripts\activate
# Unix/MacOS
source venv/bin/activate
```

### 2. Required Environment Variables
```python
# .env file structure
FLASK_APP=app.py
FLASK_ENV=development
MONGODB_URI=mongodb://localhost:27017/antidoping_db
SECRET_KEY=your_secret_key_here
SPOTIFY_CLIENT_ID=your_spotify_client_id
SPOTIFY_CLIENT_SECRET=your_spotify_client_secret
YOUTUBE_API_KEY=your_youtube_api_key
```

### 3. Dependencies List (requirements.txt)
```text
# Web Framework
Flask==2.0.1
flask-cors==3.0.10
Werkzeug==2.0.1

# Database
pymongo==3.12.0
flask-pymongo==2.3.0

# Authentication
PyJWT==2.1.0
bcrypt==3.2.0

# External APIs
spotipy==2.19.0
google-api-python-client==2.15.0
requests==2.26.0

# File Handling
python-magic==0.4.24
mutagen==1.45.1

# Validation
marshmallow==3.13.0

# Environment Variables
python-dotenv==0.19.0

# Testing
pytest==6.2.5
pytest-cov==2.12.1

# Utilities
python-dateutil==2.8.2

# Digital Twin Requirements
bleak==0.21.1
asyncio==3.4.3
pandas==1.5.3
numpy==1.24.3
scikit-learn==1.3.0
```

### 4. Development Tools Configuration

#### VSCode Settings (settings.json)
```json
{
    "python.linting.enabled": true,
    "python.linting.pylintEnabled": true,
    "python.formatting.provider": "black",
    "editor.formatOnSave": true,
    "python.testing.pytestEnabled": true,
    "python.testing.unittestEnabled": false,
    "python.testing.nosetestsEnabled": false,
    "python.testing.pytestArgs": [
        "tests"
    ]
}
```

#### Git Configuration (.gitignore)
```text
# Virtual Environment
venv/
env/

# Environment Variables
.env
.env.*

# Python
__pycache__/
*.py[cod]
*$py.class
*.so

# Distribution/Packaging
dist/
build/
*.egg-info/

# Testing
.coverage
htmlcov/
.pytest_cache/

# IDE
.vscode/
.idea/

# Project Specific
uploads/
logs/
*.log
```

### 5. Installation Instructions

```bash
# 1. Clone repository
git clone [repository-url]
cd SIHAntidoping

# 2. Create and activate virtual environment
python -m venv venv
source venv/bin/activate  # Unix/MacOS
# or
venv\Scripts\activate  # Windows

# 3. Install dependencies
pip install -r requirements.txt

# 4. Set up environment variables
cp .env.example .env
# Edit .env with your actual values

# 5. Initialize database
python init_db.py

# 6. Run the application
flask run
```

### 6. Common Issues and Solutions

#### MongoDB Connection Issues
```python
# Check if MongoDB is running
def check_mongo_connection():
    try:
        client = MongoClient(os.getenv('MONGODB_URI'), serverSelectionTimeoutMS=2000)
        client.server_info()
        print("MongoDB connection successful")
    except Exception as e:
        print(f"MongoDB connection failed: {str(e)}")
```

#### API Rate Limiting
```python
# Implement rate limiting
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

limiter = Limiter(
    app,
    key_func=get_remote_address,
    default_limits=["200 per day", "50 per hour"]
)

@app.route("/api/search")
@limiter.limit("1 per second")
def search():
    # Your code here
    pass
```

#### File Upload Size Limits
```python
# Configure maximum file size
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max-limit
```

## Basic Implementation Syntax Guide

### 1. Flask Application Setup
```python
# app.py
from flask import Flask, render_template, request, jsonify
from flask_cors import CORS
from pymongo import MongoClient

app = Flask(__name__)
CORS(app)

# MongoDB connection
client = MongoClient('mongodb://localhost:27017/')
db = client['antidoping_db']

# Basic route
@app.route('/')
def home():
    return render_template('home.html')

# API endpoint example
@app.route('/api/podcasts/search', methods=['GET'])
def search_podcasts():
    query = request.args.get('query', '')
    results = fetch_podcasts(query)
    return jsonify(results)

if __name__ == '__main__':
    app.run(debug=True)
```

### 2. HTML Template Structure
```html
<!-- base.html -->
<!DOCTYPE html>
<html>
<head>
    <title>{% block title %}{% endblock %}</title>
    <link rel="stylesheet" href="{{ url_for('static', filename='css/style.css') }}">
</head>
<body>
    <nav>
        <!-- Navigation items -->
    </nav>
    
    {% block content %}{% endblock %}
    
    <script src="{{ url_for('static', filename='js/main.js') }}"></script>
</body>
</html>

<!-- podcasts.html -->
{% extends "base.html" %}
{% block content %}
<div class="podcast-container">
    <div class="search-bar">
        <input type="text" id="searchInput" placeholder="Search podcasts...">
    </div>
    <div id="podcastList" class="podcast-grid">
        <!-- Podcasts will be loaded here -->
    </div>
</div>
{% endblock %}
```

### 3. CSS Styling
```css
/* style.css */
:root {
    --primary-color: #4a90e2;
    --secondary-color: #f5f5f5;
    --text-color: #333;
}

.podcast-container {
    max-width: 1200px;
    margin: 0 auto;
    padding: 20px;
}

.podcast-grid {
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
    gap: 20px;
}

.podcast-card {
    background: white;
    border-radius: 8px;
    box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    transition: transform 0.3s ease;
}

.podcast-card:hover {
    transform: translateY(-5px);
}
```

### 4. JavaScript Functions
```javascript
// podcast.js
// Debounced search function
function debounce(func, wait) {
    let timeout;
    return function executedFunction(...args) {
        const later = () => {
            clearTimeout(timeout);
            func(...args);
        };
        clearTimeout(timeout);
        timeout = setTimeout(later, wait);
    };
}

// Fetch podcasts
async function fetchPodcasts(query) {
    try {
        const response = await fetch(`/api/podcasts/search?query=${query}`);
        const data = await response.json();
        return data;
    } catch (error) {
        console.error('Error:', error);
        showError('Failed to fetch podcasts');
    }
}

// Display podcasts
function displayPodcasts(podcasts) {
    const container = document.getElementById('podcastList');
    container.innerHTML = podcasts.map(podcast => `
        <div class="podcast-card">
            <img src="${podcast.thumbnail}" alt="${podcast.title}">
            <h3>${podcast.title}</h3>
            <p>${podcast.description}</p>
        </div>
    `).join('');
}
```

### 5. MongoDB Operations
```python
# database.py
from pymongo import MongoClient
from datetime import datetime

class Database:
    def __init__(self):
        self.client = MongoClient('mongodb://localhost:27017/')
        self.db = self.client['antidoping_db']
    
    def save_podcast(self, podcast_data):
        return self.db.podcasts.insert_one({
            'title': podcast_data['title'],
            'description': podcast_data['description'],
            'source': podcast_data['source'],
            'created_at': datetime.now()
        })
    
    def get_podcasts(self, query=None, limit=10):
        filter_query = {}
        if query:
            filter_query = {
                '$or': [
                    {'title': {'$regex': query, '$options': 'i'}},
                    {'description': {'$regex': query, '$options': 'i'}}
                ]
            }
        return list(self.db.podcasts.find(filter_query).limit(limit))
```

### 6. API Integration
```python
# spotify_service.py
import spotipy
from spotipy.oauth2 import SpotifyClientCredentials

class SpotifyService:
    def __init__(self):
        self.client = spotipy.Spotify(
            client_credentials_manager=SpotifyClientCredentials(
                client_id='YOUR_CLIENT_ID',
                client_secret='YOUR_CLIENT_SECRET'
            )
        )
    
    def search_podcasts(self, query):
        results = self.client.search(
            q=query,
            type='show',
            market='US',
            limit=20
        )
        return self._format_results(results)
    
    def _format_results(self, results):
        shows = results['shows']['items']
        return [{
            'title': show['name'],
            'description': show['description'],
            'thumbnail': show['images'][0]['url'] if show['images'] else None,
            'source': 'spotify'
        } for show in shows]
```

### 7. Error Handling
```python
# error_handler.py
from flask import jsonify

class APIError(Exception):
    def __init__(self, message, status_code=400):
        self.message = message
        self.status_code = status_code

def handle_error(error):
    response = {
        'error': error.message,
        'status': error.status_code
    }
    return jsonify(response), error.status_code

# Usage in routes
@app.route('/api/podcasts')
def get_podcasts():
    try:
        # Your code here
        if something_wrong:
            raise APIError('Invalid request', 400)
    except APIError as e:
        return handle_error(e)
    except Exception as e:
        return handle_error(APIError('Internal server error', 500))
```

### 8. Authentication
```python
# auth.py
from functools import wraps
from flask import request, jsonify
import jwt

def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = request.headers.get('Authorization')
        if not token:
            return jsonify({'message': 'Token is missing'}), 401
        
        try:
            data = jwt.decode(token, app.config['SECRET_KEY'])
            current_user = User.get_by_id(data['user_id'])
        except:
            return jsonify({'message': 'Token is invalid'}), 401
        
        return f(current_user, *args, **kwargs)
    return decorated

# Usage in routes
@app.route('/protected')
@token_required
def protected_route(current_user):
    return jsonify({'message': 'This is protected'})
```

### 9. Testing
```python
# test_app.py
import unittest
from app import app

class TestPodcastAPI(unittest.TestCase):
    def setUp(self):
        self.app = app.test_client()
        self.app.testing = True
    
    def test_search_podcasts(self):
        response = self.app.get('/api/podcasts/search?query=doping')
        data = response.get_json()
        
        self.assertEqual(response.status_code, 200)
        self.assertIsInstance(data, list)
        self.assertTrue(len(data) > 0)
    
    def test_invalid_search(self):
        response = self.app.get('/api/podcasts/search')
        self.assertEqual(response.status_code, 400)

if __name__ == '__main__':
    unittest.main()
```

## Project Imports Explanation

### 1. Flask and Extensions
```python
from flask import Flask, render_template, request, jsonify, session, redirect, url_for
from flask_cors import CORS
from flask_pymongo import PyMongo
```
- `Flask`: Core framework for building web applications
- `render_template`: Renders HTML templates with Jinja2
- `request`: Handles HTTP requests and form data
- `jsonify`: Converts Python dictionaries to JSON responses
- `session`: Manages user sessions
- `redirect`: Handles URL redirections
- `url_for`: Generates URLs for routes
- `CORS`: Handles Cross-Origin Resource Sharing
- `PyMongo`: MongoDB integration for Flask

### 2. Database and Authentication
```python
from pymongo import MongoClient
from werkzeug.security import generate_password_hash, check_password_hash
import jwt
from functools import wraps
```
- `MongoClient`: Direct MongoDB connection client
- `generate_password_hash`: Securely hashes passwords
- `check_password_hash`: Verifies hashed passwords
- `jwt`: JSON Web Token for authentication
- `wraps`: Preserves function metadata in decorators

### 3. External API Services
```python
import spotipy
from spotipy.oauth2 import SpotifyClientCredentials
from googleapiclient.discovery import build
import requests
```
- `spotipy`: Spotify API client library
- `SpotifyClientCredentials`: Handles Spotify authentication
- `build`: Creates YouTube API service
- `requests`: Makes HTTP requests to external APIs

### 4. Data Processing and Utilities
```python
import json
import datetime
from bson import ObjectId
import os
from dotenv import load_dotenv
import logging
```
- `json`: JSON data encoding/decoding
- `datetime`: Date and time handling
- `ObjectId`: MongoDB document ID handling
- `os`: Operating system interface
- `load_dotenv`: Loads environment variables
- `logging`: System logging

### 5. File Handling
```python
from werkzeug.utils import secure_filename
import mutagen
from pathlib import Path
```
- `secure_filename`: Sanitizes uploaded filenames
- `mutagen`: Audio file metadata handling
- `Path`: Cross-platform file path handling

### 6. Error Handling and Validation
```python
from marshmallow import Schema, fields, validate
from werkzeug.exceptions import HTTPException
```
- `Schema`: Data validation schemas
- `fields`: Schema field types
- `validate`: Custom validation rules
- `HTTPException`: HTTP error handling

### 7. Testing
```python
import unittest
from unittest.mock import patch, MagicMock
import pytest
```
- `unittest`: Standard testing framework
- `patch`: Mocks objects for testing
- `MagicMock`: Creates mock objects
- `pytest`: Advanced testing framework

### Import Usage Examples

#### 1. Flask Route with MongoDB
```python
@app.route('/api/podcasts', methods=['GET'])
def get_podcasts():
    try:
        # Using PyMongo to fetch data
        podcasts = mongo.db.podcasts.find()
        
        # Converting ObjectId to string for JSON
        podcast_list = [{
            'id': str(podcast['_id']),
            'title': podcast['title'],
            'description': podcast['description']
        } for podcast in podcasts]
        
        return jsonify(podcast_list)
    except Exception as e:
        logging.error(f"Error fetching podcasts: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500
```

#### 2. Authentication Decorator
```python
def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = request.headers.get('Authorization')
        
        if not token:
            return jsonify({'message': 'Token missing'}), 401
            
        try:
            # Decode JWT token
            data = jwt.decode(token, app.config['SECRET_KEY'])
            current_user = User.get_by_id(data['user_id'])
        except:
            return jsonify({'message': 'Invalid token'}), 401
            
        return f(current_user, *args, **kwargs)
    return decorated
```

#### 3. Spotify API Integration
```python
def fetch_spotify_podcasts(query):
    spotify = spotipy.Spotify(
        client_credentials_manager=SpotifyClientCredentials(
            client_id=os.getenv('SPOTIFY_CLIENT_ID'),
            client_secret=os.getenv('SPOTIFY_CLIENT_SECRET')
        )
    )
    
    try:
        results = spotify.search(q=query, type='show', limit=20)
        return format_spotify_results(results)
    except Exception as e:
        logging.error(f"Spotify API error: {str(e)}")
        return []
```

#### 4. File Upload Handling
```python
@app.route('/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return jsonify({'error': 'No file part'}), 400
        
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No selected file'}), 400
        
    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(file_path)
        
        # Get audio metadata
        audio = mutagen.File(file_path)
        
        return jsonify({
            'message': 'File uploaded successfully',
            'filename': filename,
            'duration': audio.info.length if audio else None
        })
```

#### 5. Data Validation
```python
class PodcastSchema(Schema):
    title = fields.Str(required=True, validate=validate.Length(min=1))
    description = fields.Str(required=True)
    duration = fields.Float(required=True)
    source = fields.Str(required=True)

@app.route('/api/podcasts', methods=['POST'])
def create_podcast():
    try:
        # Validate incoming data
        schema = PodcastSchema()
        data = schema.load(request.json)
        
        # Save to database
        result = mongo.db.podcasts.insert_one(data)
        
        return jsonify({
            'message': 'Podcast created successfully',
            'id': str(result.inserted_id)
        }), 201
    except ValidationError as e:
        return jsonify({'error': e.messages}), 400
```

These imports and their usage patterns form the backbone of our application's functionality. Each import serves a specific purpose and helps maintain clean, modular, and maintainable code. Understanding these imports is crucial for:

1. Debugging issues
2. Adding new features
3. Maintaining code
4. Writing tests
5. Handling security
6. Managing dependencies

## Detailed Implementation Process

### 1. Podcast System Implementation
- **Database Structure:**
  ```
  podcasts_collection:
    - id: unique identifier
    - title: podcast title
    - description: content description
    - source: [spotify/youtube/itunes]
    - duration: length in minutes
    - thumbnail: image URL
    - category: anti-doping category
  ```

- **API Integration Flow:**
  1. User initiates search
  2. System queries multiple sources simultaneously
  3. Results are normalized and merged
  4. Content is filtered and ranked
  5. Results displayed in unified format

- **Search Implementation:**
  - Real-time search with debouncing
  - Smart filtering by source/category
  - Relevance-based sorting
  - Error handling for failed API calls

### 2. Frontend Architecture
- **Component Structure:**
  ```
  templates/
    ├── base.html (common layout)
    ├── podcasts.html (podcast interface)
    ├── coach.html (AI coach interface)
    └── profile.html (user dashboard)
  ```

- **Styling Framework:**
  - Custom CSS with CSS Variables
  - Responsive Grid System
  - Modern Animation Effects
  - Consistent Color Scheme

### 3. Backend Services
- **Route Structure:**
  ```
  /api/
    ├── /podcasts
    │   ├── GET /search
    │   ├── GET /categories
    │   └── GET /recommendations
    │
    ├── /coach
    │   ├── POST /query
    │   └── GET /history
    │
    └── /user
        ├── GET /progress
        └── POST /update
  ```

- **Error Handling:**
  - Graceful API failure recovery
  - User-friendly error messages
  - Detailed server-side logging
  - Rate limit protection

### 4. Development Workflow
1. **Local Development:**
   - Setup virtual environment
   - Install dependencies
   - Configure environment variables
   - Run development server

2. **Testing Process:**
   - Unit tests for API endpoints
   - Integration tests for external services
   - UI/UX testing
   - Performance benchmarking

3. **Deployment Steps:**
   - Environment configuration
   - Database migration
   - Static file optimization
   - Server setup and deployment

### 5. Key Features Implementation

#### Podcast Management:
```python
# Pseudo-code for podcast fetching
def fetch_podcasts(query):
    results = []
    # Parallel API calls
    spotify_results = fetch_from_spotify(query)
    youtube_results = fetch_from_youtube(query)
    itunes_results = fetch_from_itunes(query)
    
    # Merge and normalize results
    results = merge_results([
        spotify_results,
        youtube_results,
        itunes_results
    ])
    
    return format_response(results)
```

#### Search System:
```javascript
// Frontend search implementation
const handleSearch = debounce(async (query) => {
    try {
        const results = await fetchPodcasts(query);
        updateUI(results);
    } catch (error) {
        showErrorMessage(error);
    }
}, 300);
```

### 6. Database Operations
- **MongoDB Queries:**
  ```python
  # Example database operations
  def save_podcast(podcast_data):
      return db.podcasts.insert_one({
          'title': podcast_data['title'],
          'source': podcast_data['source'],
          'url': podcast_data['url'],
          'timestamp': datetime.now()
      })

  def get_user_history(user_id):
      return db.history.find({
          'user_id': user_id
      }).sort('timestamp', -1)
  ```

### 7. Security Implementation
- **Authentication Flow:**
  1. User login request
  2. Credential verification
  3. JWT token generation
  4. Session management
  5. Secure cookie handling

- **Data Protection:**
  - Password hashing
  - API key encryption
  - CORS configuration
  - XSS prevention

### 8. Performance Optimizations
- **Caching Strategy:**
  ```python
  # Cache implementation
  CACHE_DURATION = 3600  # 1 hour

  def get_cached_data(key):
      cached = redis_client.get(key)
      return json.loads(cached) if cached else None

  def set_cached_data(key, data):
      redis_client.setex(key, CACHE_DURATION, json.dumps(data))
  ```

- **Load Time Optimization:**
  - Image lazy loading
  - Code splitting
  - Minification
  - Compression

### 9. Monitoring and Logging
- **System Metrics:**
  - API response times
  - Error rates
  - User engagement
  - Resource utilization

- **Log Management:**
  ```python
  # Logging configuration
  logging.config.dictConfig({
      'version': 1,
      'handlers': {
          'file': {
              'class': 'logging.FileHandler',
              'filename': 'app.log'
          }
      },
      'root': {
          'level': 'INFO',
          'handlers': ['file']
      }
  })
  ```

## Key Technologies Used
- **Backend:** Python Flask
- **Database:** MongoDB
- **Frontend:** HTML5, CSS3, JavaScript
- **APIs:** Spotify, YouTube, iTunes
- **AI/ML:** TensorFlow, PyTorch

## Project Workflow

1. **User Journey:**
   - Login/Registration
   - Browse Podcasts
   - Interact with AI Coach
   - Track Progress
   - Earn Certificates

2. **Content Delivery:**
   - Real-time podcast fetching
   - Smart content filtering
   - Personalized recommendations
   - Interactive learning materials

## Security Features
- Secure authentication
- API rate limiting
- Data encryption
- Safe file handling

## Performance Optimizations
- Efficient database queries
- Content caching
- Optimized API calls
- Fast page loading

## Future Enhancements
1. Advanced recommendation system
2. More interactive games
3. Enhanced AI capabilities
4. Mobile application
5. Offline content access

## Team Structure
1. **Backend Developer:**
   - Core API development
   - Database management
   - Server configuration

2. **API Integration Specialist:**
   - External API integrations
   - Service connections
   - Data synchronization

3. **Frontend Lead:**
   - UI/UX design
   - Responsive layouts
   - Visual components

4. **JavaScript Specialist:**
   - Client-side functionality
   - Interactive features
   - Dynamic content

5. **AI/ML Specialist:**
   - AI coach implementation
   - Digital twin system
   - Smart features

6. **QA & Documentation:**
   - Testing
   - Documentation
   - Deployment support

## Project Benefits
1. **For Athletes:**
   - Easy access to anti-doping information
   - Interactive learning experience
   - Personalized guidance

2. **For Organizations:**
   - Streamlined education delivery
   - Progress tracking
   - Compliance monitoring

3. **For Administrators:**
   - Easy content management
   - User progress monitoring
   - System analytics

## Current Status
- ✅ Core platform implemented
- ✅ Podcast system complete
- ✅ Basic AI features working
- 🟡 Advanced features in progress
- 🟡 Testing ongoing

## Technical Requirements
- Python 3.8+
- MongoDB
- Modern web browser
- Internet connection
- API access keys

This project represents a modern approach to anti-doping education, combining technology and user experience to create an effective learning platform.
