import sys
import os

# Add project root directory to Python path
project_root = os.path.dirname(os.path.abspath(__file__))
if project_root not in sys.path:
    sys.path.append(project_root)

# Flask and Extensions
from flask import Flask, render_template, request, jsonify, send_file, send_from_directory, session, redirect, url_for, flash
from flask_cors import CORS
from flask_socketio import SocketIO
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user

# Database and Models
from models import db, User, Notification, NewsletterSubscription, init_db
from pymongo import MongoClient
from bson import ObjectId

# File Handling
from werkzeug.utils import secure_filename
import mutagen
from mutagen.mp3 import MP3
from fpdf import FPDF

# External APIs
from newsapi import NewsApiClient
import spotipy
from spotipy.oauth2 import SpotifyClientCredentials
from googleapiclient.discovery import build
import google.generativeai as genai

# Web3 and Blockchain
from blockchain_service import BlockchainService
from web3 import Web3

# Data Processing
from bs4 import BeautifulSoup
import feedparser
import xml.etree.ElementTree as ET
import html
from collections import deque

# Project modules
from simulator import *
from utils.notifications import NotificationService

# Standard Library
import os
import json
import time
import random
import string
import logging
import requests
from datetime import datetime, timedelta
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Initialize Flask
app = Flask(__name__, static_folder="static")

# Configure Flask app
app.config.update(
    SECRET_KEY=os.getenv('FLASK_SECRET_KEY', 'default-secret-key-for-development'),
    SQLALCHEMY_DATABASE_URI=os.getenv('DATABASE_URL', 'sqlite:///antidoping.db'),
    SQLALCHEMY_TRACK_MODIFICATIONS=False,
    MONGO_URI=os.getenv('MONGO_URI', 'mongodb://localhost:27017/'),
    NEWS_API_KEY=os.getenv('NEWS_API_KEY'),
    OPENAI_API_KEY=os.getenv('OPENAI_API_KEY'),
    UPLOAD_FOLDER=os.path.join(app.root_path, 'static/uploads'),
    MAX_CONTENT_LENGTH=16 * 1024 * 1024  # 16MB max file size
)

# Ensure upload directory exists
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# Initialize MongoDB for legacy support
try:
    client = MongoClient(app.config['MONGO_URI'])
    mongo_db = client['antidoping']
    client.server_info()  # Test connection
except Exception as e:
    app.logger.warning(f"MongoDB connection failed: {e}")
    mongo_db = None

# Initialize Flask extensions
db.init_app(app)  # SQLAlchemy
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

CORS(app)
socketio = SocketIO(app, cors_allowed_origins="*")

# Initialize services
try:
    notification_service = NotificationService()
except Exception as e:
    app.logger.error(f"Failed to initialize NotificationService: {e}")
    notification_service = None

# Configure logging
logging.basicConfig(
    filename='antidoping.log',
    level=logging.INFO,
    format='%(asctime)s %(levelname)s: %(message)s'
)

@login_manager.user_loader
def load_user(user_id):
    try:
        return User.query.get(int(user_id))
    except Exception as e:
        app.logger.error(f"Error loading user {user_id}: {e}")
        return None

# Get API key from environment variable
GOOGLE_API_KEY = os.getenv('GOOGLE_API_KEY')
print(f"API Key loaded: {'[MASKED]' if GOOGLE_API_KEY else 'None'}")

# Initialize News API
newsapi = NewsApiClient(api_key=os.getenv('NEWS_API_KEY'))

# Initialize blockchain service
try:
    blockchain_service = BlockchainService()
    logging.info("Blockchain service initialized")
except Exception as e:
    logging.warning(f"Failed to initialize blockchain service: {str(e)}")
    blockchain_service = None

# Configure Gemini
genai.configure(api_key=GOOGLE_API_KEY)
model = genai.GenerativeModel('gemini-pro')

# Create certificates directory if it doesn't exist
os.makedirs('certificates', exist_ok=True)

# Configure upload folder for podcasts
UPLOAD_FOLDER = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'static', 'podcasts')
ALLOWED_EXTENSIONS = {'mp3', 'wav', 'ogg'}
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# Podcast categories
PODCAST_CATEGORIES = [
    'Anti-Doping Rules',
    'Athlete Stories',
    'News & Updates',
    'Training & Education',
    'Clean Sport',
    'Health & Wellness'
]

# Sample podcast data
SAMPLE_PODCASTS = [
    {
        'title': 'Understanding Anti-Doping Rules',
        'description': 'A comprehensive guide to anti-doping regulations and their importance in sports.',
        'category': 'Anti-Doping Rules',
        'author': 'Dr. Sarah Johnson',
        'duration': 1800,  # 30 minutes
        'filename': 'understanding_antidoping.mp3',
        'upload_date': datetime.utcnow()
    },
    {
        'title': 'Athlete Stories: Clean Sport Champions',
        'description': 'Listen to inspiring stories from athletes who compete clean and promote fair play.',
        'category': 'Athlete Stories',
        'author': 'Michael Chen',
        'duration': 1200,  # 20 minutes
        'filename': 'clean_sport_champions.mp3',
        'upload_date': datetime.utcnow()
    },
    {
        'title': 'Latest Updates in Anti-Doping Policies',
        'description': 'Stay informed about the latest developments and changes in anti-doping policies.',
        'category': 'News & Updates',
        'author': 'Emma Williams',
        'duration': 900,  # 15 minutes
        'filename': 'policy_updates.mp3',
        'upload_date': datetime.utcnow()
    }
]

def init_sample_podcasts():
    try:
        # Check if podcasts collection exists and is empty
        if 'podcasts' not in mongo_db.list_collection_names() or mongo_db.podcasts.count_documents({}) == 0:
            # Insert sample podcasts
            mongo_db.podcasts.insert_many(SAMPLE_PODCASTS)
            logging.info("Initialized sample podcast data")
    except Exception as e:
        logging.error(f"Error initializing sample podcasts: {str(e)}")

# Initialize sample podcasts when app starts
init_sample_podcasts()

# News cache
news_cache = {
    'last_update': None,
    'data': []
}

# Routes
@app.route("/")
def home():
    return render_template("home.html")

@app.route("/podcasts")
def podcasts():
    return render_template("podcasts.html")

@app.route("/digitaltwin")
def digitaltwin():
    return render_template("digitaltwin.html")

@app.route("/smartlabels")
def smartlabels():
    app.logger.debug("Accessing smart labels page")
    return render_template("smartlabels.html")

@app.route('/antidopingwiki')
def antidopingwiki():
    global news_cache
    current_time = datetime.utcnow()
    
    # Check if we have cached news that's less than 30 minutes old
    if (news_cache['last_update'] and 
        (current_time - news_cache['last_update']).total_seconds() < 1800):
        return render_template('antidopingwiki.html', news=news_cache['data'])
    
    try:
        all_news = []
        
        # Fetch international doping news
        doping_response = newsapi.get_everything(
            q='doping sports athletics',
            language='en',
            sort_by='publishedAt',
            from_param=(datetime.utcnow() - timedelta(days=30)).strftime('%Y-%m-%d'),
            page_size=10
        )
        
        # Fetch local doping news (using country-specific sources)
        local_doping_response = newsapi.get_everything(
            q='doping sports athletics',
            language='en',
            domains='timesofindia.indiatimes.com,hindustantimes.com,indianexpress.com',  # Add more local sources
            sort_by='publishedAt',
            from_param=(datetime.utcnow() - timedelta(days=30)).strftime('%Y-%m-%d'),
            page_size=10
        )
        
        # Fetch general sports news
        sports_response = newsapi.get_top_headlines(
            category='sports',
            language='en',
            page_size=10
        )
        
        # Process international doping news
        if doping_response.get('status') == 'ok' and doping_response.get('articles'):
            for article in doping_response['articles']:
                if article.get('title') and article.get('description'):
                    all_news.append({
                        'title': article.get('title', ''),
                        'description': article.get('description', ''),
                        'url': article.get('url', '#'),
                        'image': article.get('urlToImage', None),
                        'publishedAt': datetime.strptime(article.get('publishedAt', datetime.utcnow().isoformat()), 
                                                       '%Y-%m-%dT%H:%M:%SZ').strftime('%B %d, %Y'),
                        'source': article.get('source', {}).get('name', 'Unknown Source'),
                        'category': 'International Doping News'
                    })
        
        # Process local doping news
        if local_doping_response.get('status') == 'ok' and local_doping_response.get('articles'):
            for article in local_doping_response['articles']:
                if article.get('title') and article.get('description'):
                    all_news.append({
                        'title': article.get('title', ''),
                        'description': article.get('description', ''),
                        'url': article.get('url', '#'),
                        'image': article.get('urlToImage', None),
                        'publishedAt': datetime.strptime(article.get('publishedAt', datetime.utcnow().isoformat()), 
                                                       '%Y-%m-%dT%H:%M:%SZ').strftime('%B %d, %Y'),
                        'source': article.get('source', {}).get('name', 'Unknown Source'),
                        'category': 'Local Doping News'
                    })
            
        # Process sports news
        if sports_response.get('status') == 'ok' and sports_response.get('articles'):
            for article in sports_response['articles']:
                if article.get('title') and article.get('description'):
                    all_news.append({
                        'title': article.get('title', ''),
                        'description': article.get('description', ''),
                        'url': article.get('url', '#'),
                        'image': article.get('urlToImage', None),
                        'publishedAt': datetime.strptime(article.get('publishedAt', datetime.utcnow().isoformat()),
                                                       '%Y-%m-%dT%H:%M:%SZ').strftime('%B %d, %Y'),
                        'source': article.get('source', {}).get('name', 'Unknown Source'),
                        'category': 'Sports News'
                    })
        
        # Add static content for laws, punishments, and real-life cases
        static_content = {
            'laws': {
                'title': 'Anti-Doping Laws and Regulations',
                'sections': [
                    {
                        'title': 'WADA Code',
                        'content': 'The World Anti-Doping Code is the core document that harmonizes anti-doping policies, rules, and regulations within sport organizations and among public authorities around the world.',
                        'link': 'https://www.wada-ama.org/en/what-we-do/world-anti-doping-code'
                    },
                    {
                        'title': 'National Anti-Doping Laws',
                        'content': 'Each country has its own anti-doping laws and regulations that align with the WADA Code while addressing specific national requirements.',
                        'link': 'https://www.nadaindia.org/en/rules-regulations'
                    }
                ]
            },
            'punishments': {
                'title': 'Consequences of Doping',
                'sections': [
                    {
                        'title': 'Sports Sanctions',
                        'content': 'Athletes found guilty of doping violations may face: Competition results voided, Medal/prize forfeitures, Competition bans (2-4 years for first violation, up to lifetime for repeat offenses)',
                    },
                    {
                        'title': 'Legal Consequences',
                        'content': 'Criminal charges in some jurisdictions, Financial penalties, Loss of sponsorships and endorsements'
                    }
                ]
            },
            'cases': {
                'title': 'Notable Doping Cases',
                'sections': [
                    {
                        'title': 'Lance Armstrong Case',
                        'content': 'Seven-time Tour de France winner stripped of titles and banned from cycling for life in 2012 due to systematic doping.',
                        'year': '2012'
                    },
                    {
                        'title': 'Russian Olympic Ban',
                        'content': 'Russia banned from major international sporting events including Olympics due to state-sponsored doping program.',
                        'year': '2019'
                    },
                    {
                        'title': 'Ben Johnson',
                        'content': 'Stripped of 1988 Olympic gold medal after testing positive for stanozolol. Became a landmark case in anti-doping history.',
                        'year': '1988'
                    }
                ]
            }
        }
        
        if all_news:
            # Update cache if we got news successfully
            news_cache['last_update'] = current_time
            news_cache['data'] = all_news
            
    except Exception as e:
        logging.error(f"Error fetching news: {str(e)}")
        import traceback
        logging.error(f"Full error traceback: {traceback.format_exc()}")
        
        # Use cached data if available, otherwise use sample news
        if news_cache['data']:
            all_news = news_cache['data']
        else:
            all_news = [
                {
                    'title': 'Sample International News',
                    'description': 'This is a sample international news article. The news API might be temporarily unavailable.',
                    'url': '#',
                    'image': None,
                    'publishedAt': datetime.utcnow().strftime('%B %d, %Y'),
                    'source': 'Sample Source',
                    'category': 'International Doping News'
                },
                {
                    'title': 'Sample Local News',
                    'description': 'This is a sample local news article. The news API might be temporarily unavailable.',
                    'url': '#',
                    'image': None,
                    'publishedAt': datetime.utcnow().strftime('%B %d, %Y'),
                    'source': 'Sample Source',
                    'category': 'Local Doping News'
                }
            ]
    
    return render_template('antidopingwiki.html', news=all_news, static_content=static_content)

@app.route("/caloriescalculator")
def caloriescalculator():
    return render_template("caloriescalculator.html")

@app.route("/ai-coach-page")
def ai_coach_page():
    return render_template("ai_coach.html")

@app.route("/games")
def games():
    return render_template("games.html")

@app.route('/get_quiz/<quiz_id>')
def get_quiz(quiz_id):
    try:
        logging.info(f"Fetching quiz with ID: {quiz_id}")
        quiz = mongo_db.quizzes.find_one({"quiz_id": quiz_id}, {"_id": 0})
        logging.info(f"Found quiz: {quiz}")
        
        if not quiz:
            # Try to initialize quiz data
            if init_quiz_data():
                quiz = mongo_db.quizzes.find_one({"quiz_id": quiz_id}, {"_id": 0})
        
        if quiz:
            return jsonify({
                "success": True,
                "quiz": quiz
            })
        
        return jsonify({
            "success": False,
            "error": "Quiz not found"
        }), 404
        
    except Exception as e:
        logging.error(f"Error getting quiz: {str(e)}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

class PodcastFetcher:
    def __init__(self):
        """Initialize the podcast fetcher with API clients"""
        # Initialize Spotify client
        self.spotify = spotipy.Spotify(client_credentials_manager=SpotifyClientCredentials())
        
        # Initialize YouTube client
        self.youtube = build('youtube', 'v3', developerKey=os.environ.get('YOUTUBE_API_KEY'))
        
        # Anti-doping related keywords for content filtering
        self.antidoping_keywords = [
            'anti-doping', 'antidoping', 'doping', 'wada', 'usada', 'clean sport',
            'drug testing', 'prohibited substances', 'banned substances', 'athlete integrity',
            'sports integrity', 'fair play', 'clean athlete', 'performance enhancing',
            'drug free sport', 'anti doping violation', 'therapeutic use exemption', 'tue',
            'whereabouts', 'testing pool', 'biological passport', 'prohibited list',
            'anti-doping rule', 'sample collection', 'doping control', 'adams',
            'world anti-doping', 'national anti-doping', 'doping test'
        ]
        
        # Search queries for finding relevant content
        self.search_queries = [
            'anti-doping podcast',
            'clean sport podcast',
            'doping in sports podcast',
            'sports integrity podcast',
            'wada podcast',
            'usada podcast'
        ]
        
        # YouTube channel IDs
        self.youtube_channels = [
            'UCQxkGRRkhVeOQpwR9WEsV3A',  # World Anti-Doping Agency (WADA)
            'UCuJcLm5uNXtXUVHHLs2W_-Q',  # U.S. Anti-Doping Agency (USADA)
            'UC5nU0k_KnOXAwK_6cLvjfDQ'   # UK Anti-Doping (UKAD)
        ]
        
        # Rate limiting attributes
        self.spotify_calls = deque(maxlen=30)  # Track last 30 Spotify API calls
        self.youtube_quota = {
            'daily_limit': 10000,
            'used': 0,
            'reset_time': datetime.now()
        }
        
        # Add iTunes search URL
        self.itunes_search_url = "https://itunes.apple.com/search"
        
    def is_antidoping_content(self, title, description):
        """Check if content is related to sports or anti-doping based on title and description"""
        # Make the filter more lenient by always returning True to get all content
        return True

    def _check_spotify_rate_limit(self):
        """Implement Spotify rate limiting - 30 requests per second"""
        now = time.time()
        # Remove calls older than 1 second
        while self.spotify_calls and self.spotify_calls[0] < now - 1:
            self.spotify_calls.popleft()
        
        if len(self.spotify_calls) >= 30:
            sleep_time = 1 - (now - self.spotify_calls[0])
            if sleep_time > 0:
                time.sleep(sleep_time)
        
        self.spotify_calls.append(now)

    def _check_youtube_quota(self, cost=1):
        """Check YouTube API quota"""
        now = datetime.now()
        
        # Reset quota if it's a new day
        if now.date() > self.youtube_quota['reset_time'].date():
            self.youtube_quota['used'] = 0
            self.youtube_quota['reset_time'] = now
        
        # Check if we have enough quota
        if self.youtube_quota['used'] + cost > self.youtube_quota['daily_limit']:
            raise Exception("YouTube API daily quota exceeded")
        
        self.youtube_quota['used'] += cost

    def fetch_spotify_podcasts(self):
        """Fetch sports and anti-doping related episodes from Spotify using search"""
        podcasts = []
        try:
            logging.info("Starting Spotify podcast search")
            
            # Broader search queries
            search_terms = ['sports', 'athlete', 'olympic', 'fitness', 'training', 'health']
            
            # Search for podcasts using our queries
            for query in search_terms:
                try:
                    self._check_spotify_rate_limit()
                    results = self.spotify.search(q=query, type='show', market='US', limit=10)
                    
                    if not results or 'shows' not in results or 'items' not in results['shows']:
                        continue
                    
                    for show in results['shows']['items']:
                        try:
                            show_id = show['id']
                            show_name = show['name']
                            publisher = show['publisher']
                            
                            episodes = self.spotify.show_episodes(show_id, limit=5, market='US')
                            
                            if not episodes or 'items' not in episodes:
                                continue
                            
                            for episode in episodes['items']:
                                try:
                                    podcast = {
                                        'title': episode['name'],
                                        'description': episode.get('description', '')[:500],
                                        'author': publisher,
                                        'published_date': episode.get('release_date', ''),
                                        'image_url': episode['images'][0]['url'] if episode.get('images') and episode['images'] else None,
                                        'source_url': episode['external_urls']['spotify'] if episode.get('external_urls') else '',
                                        'source_type': 'spotify',
                                        'category': self._categorize_content(episode['name'], episode.get('description', '')),
                                        'language': episode.get('language', 'en'),
                                        'duration_ms': episode.get('duration_ms', 0)
                                    }
                                    
                                    if not any(p['source_url'] == podcast['source_url'] for p in podcasts):
                                        podcasts.append(podcast)
                                        
                                except Exception as episode_error:
                                    continue
                                    
                        except Exception:
                            continue
                            
                except Exception as search_error:
                    if "429" in str(search_error):
                        time.sleep(5)
                    continue
                    
        except Exception as e:
            logging.error(f"Error in fetch_spotify_podcasts: {str(e)}")
        
        return podcasts

    def fetch_youtube_videos(self):
        """Fetch sports and fitness related videos from YouTube"""
        videos = []
        try:
            logging.info("Starting YouTube video fetch")
            
            # Broader search terms
            search_terms = ['sports', 'athlete', 'fitness', 'training', 'olympics']
            
            for term in search_terms:
                try:
                    self._check_youtube_quota(cost=1)
                    
                    search_request = self.youtube.search().list(
                        part="snippet",
                        q=term,
                        maxResults=10,
                        order="date",
                        type="video"
                    ).execute()
                    
                    if not search_request.get('items'):
                        continue
                    
                    for item in search_request['items']:
                        try:
                            snippet = item['snippet']
                            
                            video = {
                                'title': snippet['title'],
                                'description': snippet.get('description', '')[:500],
                                'author': snippet['channelTitle'],
                                'published_date': snippet['publishedAt'],
                                'image_url': snippet.get('thumbnails', {}).get('high', {}).get('url'),
                                'source_url': f"https://www.youtube.com/watch?v={item['id']['videoId']}",
                                'source_type': 'youtube',
                                'category': self._categorize_content(snippet['title'], snippet.get('description', '')),
                                'language': 'en'
                            }
                            
                            if not any(v['source_url'] == video['source_url'] for v in videos):
                                videos.append(video)
                                
                        except Exception:
                            continue
                            
                except Exception as search_error:
                    if "quotaExceeded" in str(search_error):
                        break
                    elif "429" in str(search_error):
                        time.sleep(60)
                    continue
                    
        except Exception as e:
            logging.error(f"Error in fetch_youtube_videos: {str(e)}")
        
        return videos

    def fetch_itunes_podcasts(self):
        """Fetch sports and fitness related podcasts from iTunes"""
        podcasts = []
        try:
            logging.info("Starting iTunes podcast search")
            
            # Broader search terms
            search_terms = ['sports', 'athlete', 'fitness', 'training', 'olympics']
            
            for query in search_terms:
                try:
                    params = {
                        'term': query,
                        'entity': 'podcast',
                        'limit': 20,
                        'media': 'podcast'
                    }
                    
                    response = requests.get(self.itunes_search_url, params=params)
                    if response.status_code == 200:
                        results = response.json()
                        
                        for item in results.get('results', []):
                            try:
                                podcast = {
                                    'title': item.get('collectionName', ''),
                                    'description': item.get('description', '')[:500],
                                    'author': item.get('artistName', ''),
                                    'published_date': datetime.now().strftime('%Y-%m-%d'),
                                    'image_url': item.get('artworkUrl600', ''),
                                    'source_url': item.get('collectionViewUrl', ''),
                                    'source_type': 'itunes',
                                    'category': self._categorize_content(
                                        item.get('collectionName', ''),
                                        item.get('description', '')
                                    ),
                                    'language': 'en'
                                }
                                
                                if not any(p['source_url'] == podcast['source_url'] for p in podcasts):
                                    podcasts.append(podcast)
                                    
                            except Exception:
                                continue
                                
                    time.sleep(1)
                    
                except Exception:
                    continue
                    
        except Exception as e:
            logging.error(f"Error in fetch_itunes_podcasts: {str(e)}")
            
        return podcasts

    def fetch_all_podcasts(self):
        """Fetch podcasts from all available sources"""
        all_podcasts = []
        
        # Try iTunes first as it's more reliable
        itunes_podcasts = self.fetch_itunes_podcasts()
        all_podcasts.extend(itunes_podcasts)
        
        try:
            # Try Spotify if iTunes doesn't return enough results
            if len(all_podcasts) < 20:
                spotify_podcasts = self.fetch_spotify_podcasts()
                all_podcasts.extend(spotcast_podcasts)
        except Exception as spotify_error:
            logging.warning(f"Spotify fetch failed, continuing with iTunes results: {str(spotify_error)}")
        
        try:
            # Add YouTube videos as supplementary content
            youtube_videos = self.fetch_youtube_videos()
            all_podcasts.extend(youtube_videos)
        except Exception as youtube_error:
            logging.warning(f"YouTube fetch failed, continuing with podcast results: {str(youtube_error)}")
        
        return all_podcasts

    def _categorize_content(self, title, description):
        """Categorize content based on title and description"""
        title_lower = title.lower()
        description_lower = description.lower()
        
        # Define category keywords
        categories = {
            'Rules & Compliance': ['rule', 'compliance', 'violation', 'sanction', 'regulation', 'policy'],
            'Testing & Science': ['test', 'sample', 'laboratory', 'biological passport', 'analysis'],
            'Education': ['education', 'learn', 'guide', 'understand', 'awareness'],
            'Athlete Stories': ['story', 'interview', 'experience', 'journey', 'athlete'],
            'Updates & News': ['update', 'news', 'announcement', 'latest', 'change'],
            'Clean Sport': ['clean sport', 'integrity', 'fair play', 'values']
        }
        
        # Check each category
        for category, keywords in categories.items():
            for keyword in keywords:
                if keyword in title_lower or keyword in description_lower:
                    return category
        
        return 'General Anti-Doping'

@app.route('/api/podcasts')
def get_podcasts():
    """API endpoint to get sports and anti-doping podcasts from various sources"""
    try:
        # Initialize podcast fetcher if not already initialized
        if not hasattr(app, 'podcast_fetcher'):
            try:
                app.podcast_fetcher = PodcastFetcher()
            except Exception as init_error:
                logging.error(f"Failed to initialize podcast fetcher: {str(init_error)}")
                return jsonify({
                    'success': False,
                    'error': f"Failed to initialize podcast fetcher: {str(init_error)}"
                }), 500

        # Sample podcasts as fallback
        sample_podcasts = [
            {
                'title': 'Clean Sport Insights',
                'description': 'A podcast about maintaining integrity in sports and understanding anti-doping measures.',
                'author': 'Sports Integrity Unit',
                'published_date': datetime.now().strftime('%Y-%m-%d'),
                'image_url': '/static/images/podcast-placeholder.jpg',
                'source_url': '#',
                'source_type': 'sample',
                'category': 'Education & Prevention',
                'language': 'en'
            },
            {
                'title': 'The Athlete\'s Corner',
                'description': 'Weekly discussions about sports, training, and athlete well-being.',
                'author': 'Sports Network',
                'published_date': datetime.now().strftime('%Y-%m-%d'),
                'image_url': '/static/images/podcast-placeholder.jpg',
                'source_url': '#',
                'source_type': 'sample',
                'category': 'Athlete Stories',
                'language': 'en'
            },
            {
                'title': 'Sports Science Today',
                'description': 'Exploring the latest developments in sports science and performance.',
                'author': 'Science in Sports',
                'published_date': datetime.now().strftime('%Y-%m-%d'),
                'image_url': '/static/images/podcast-placeholder.jpg',
                'source_url': '#',
                'source_type': 'sample',
                'category': 'Testing & Science',
                'language': 'en'
            }
        ]

        all_podcasts = []

        # Try to fetch from each source independently
        try:
            itunes_podcasts = app.podcast_fetcher.fetch_itunes_podcasts()
            if itunes_podcasts:
                all_podcasts.extend(itunes_podcasts)
        except Exception as itunes_error:
            logging.error(f"iTunes fetch failed: {str(itunes_error)}")

        try:
            spotify_podcasts = app.podcast_fetcher.fetch_spotify_podcasts()
            if spotify_podcasts:
                all_podcasts.extend(spotify_podcasts)
        except Exception as spotify_error:
            logging.error(f"Spotify fetch failed: {str(spotify_error)}")

        try:
            youtube_videos = app.podcast_fetcher.fetch_youtube_videos()
            if youtube_videos:
                all_podcasts.extend(youtube_videos)
        except Exception as youtube_error:
            logging.error(f"YouTube fetch failed: {str(youtube_error)}")

        # If no podcasts were found from any source, use sample podcasts
        if not all_podcasts:
            logging.info("No podcasts found from external sources, using sample podcasts")
            all_podcasts = sample_podcasts

        # Return all found podcasts
        return jsonify({
            'success': True,
            'data': all_podcasts
        })

    except Exception as e:
        logging.error(f"Error in get_podcasts: {str(e)}")
        # Return sample podcasts on error
        return jsonify({
            'success': True,
            'data': sample_podcasts
        })

@app.route('/submit_quiz', methods=['POST'])
def submit_quiz():
    try:
        data = request.get_json()
        app.logger.info(f"Received quiz submission: {data}")
        
        # Validate required fields
        required_fields = ['user_id', 'quiz_id', 'answers']
        for field in required_fields:
            if field not in data:
                raise ValueError(f"Missing required field: {field}")

        user_id = data['user_id']
        quiz_id = data['quiz_id']
        answers = data['answers']
        email = data.get('email', '')  # Optional email for blockchain certificate

        if not user_id:
            raise ValueError("User ID is required")

        # Get quiz data
        quiz = mongo_db.quizzes.find_one({"quiz_id": quiz_id}, {"_id": 0})
        if not quiz:
            raise ValueError("Invalid quiz ID")

        # Calculate score
        correct_answers = [q['correct_answer'] for q in quiz['questions']]
        if len(answers) != len(correct_answers):
            raise ValueError("Number of answers does not match number of questions")

        score = calculate_score(answers, correct_answers)
        timestamp = datetime.utcnow()

        # Store quiz result
        quiz_result = {
            'user_id': user_id,
            'quiz_id': quiz_id,
            'score': score,
            'answers': answers,
            'email': email,
            'timestamp': timestamp
        }
        
        # Generate certificate data if passing score
        certificate_data = None
        if score >= 70:
            try:
                token_id = None
                # Attempt to mint blockchain certificate only if email is provided
                if email and blockchain_service:
                    try:
                        token_id = blockchain_service.mint_certificate(
                            recipient_email=email,
                            quiz_title=quiz['title'],
                            score=int(score)
                        )
                    except Exception as e:
                        app.logger.error(f"Error minting blockchain certificate: {str(e)}")
                
                # Generate PDF certificate with token_id if available
                try:
                    pdf_filename = generate_pdf_certificate(user_id, quiz_id, score, timestamp, token_id)
                    app.logger.info(f"Generated certificate PDF: {pdf_filename}")
                    
                    # Store certificate path
                    quiz_result['pdf_certificate'] = pdf_filename
                    
                    # Generate certificate metadata
                    metadata = {
                        'user_id': user_id,
                        'quiz_id': quiz_id,
                        'score': score,
                        'timestamp': timestamp.isoformat(),
                        'token_id': token_id
                    }
                    
                    certificate_data = {
                        'token_id': token_id,
                        'metadata': metadata,
                        'pdf_path': pdf_filename,
                        'user_id': user_id
                    }
                    
                    quiz_result['certificate'] = certificate_data
                    app.logger.info(f"Certificate data prepared: {certificate_data}")
                    
                except Exception as e:
                    app.logger.error(f"Error generating PDF certificate: {str(e)}")
                    raise
                
            except Exception as e:
                app.logger.error(f"Error generating certificate: {str(e)}")
                certificate_data = {'error': str(e)}
        
        # Store result in database
        mongo_db.quiz_results.insert_one(quiz_result)
        app.logger.info(f"Quiz result stored for user {user_id}")

        response_data = {
            'success': True,
            'score': score,
            'certificate': certificate_data,
            'user_id': user_id  # Include user_id in response
        }
        app.logger.info(f"Sending response: {response_data}")
        return jsonify(response_data)

    except Exception as e:
        app.logger.error(f"Error submitting quiz: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/download_certificate/<user_id>/<filename>')
def download_certificate(user_id, filename):
    try:
        # Validate input parameters
        if not user_id or not filename:
            app.logger.error("Missing user_id or filename")
            return jsonify({
                'success': False,
                'error': "Invalid request parameters"
            }), 400

        # Log request details
        app.logger.info(f"Certificate download requested - User: {user_id}, File: {filename}")
        
        # Security check: ensure filename belongs to the user (check both formats)
        if not (filename.startswith(f"{user_id}_") or filename.startswith(f"certificate_{user_id}_")):
            app.logger.warning(f"Invalid certificate access attempt - User: {user_id}, File: {filename}")
            return jsonify({
                'success': False,
                'error': "Invalid certificate access"
            }), 403
            
        certificate_dir = os.path.join(os.path.dirname(__file__), 'certificates')
        app.logger.info(f"Looking for certificate in: {certificate_dir}")
        
        # Ensure certificate directory exists
        if not os.path.exists(certificate_dir):
            os.makedirs(certificate_dir)
            app.logger.info(f"Created certificates directory: {certificate_dir}")
        
        certificate_path = os.path.join(certificate_dir, filename)
        if not os.path.exists(certificate_path):
            app.logger.error(f"Certificate file not found: {filename}")
            return jsonify({
                'success': False,
                'error': f"Certificate file not found: {filename}"
            }), 404
            
        # Check if the file is actually a PDF
        if not filename.lower().endswith('.pdf'):
            app.logger.error(f"Invalid certificate file type: {filename}")
            return jsonify({
                'success': False,
                'error': "Invalid certificate file type"
            }), 400
            
        return send_from_directory(
            certificate_dir, 
            filename,
            as_attachment=True,
            download_name=f"antidoping_certificate_{user_id}.pdf"
        )
    except Exception as e:
        app.logger.error(f"Error downloading certificate: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route("/get_progress/<user_id>")
def get_progress(user_id):
    try:
        scores = list(mongo_db.scores.find({"user_id": user_id}, {"_id": 0}))
        return jsonify(scores), 200
    except Exception as e:
        logging.error(f"Error getting progress: {str(e)}")
        return jsonify({"error": "Internal server error"}), 500

@app.route("/anti_doping")
def anti_doping_page():
    return render_template('anti_doping.html')

@app.route('/ai-nutrition-planner')
def ai_nutrition_planner():
    return render_template('ai_nutrition_planner.html')

@app.route('/generate-nutrition-plan', methods=['POST'])
def generate_nutrition_plan():
    try:
        data = request.json
        # Construct the prompt for the model
        prompt = f"""As a professional sports nutritionist, create a detailed weekly nutrition plan for an athlete with the following details:
        Sport: {data['sport']}
        Age: {data['age']}
        Weight: {data['weight']} kg
        Height: {data['height']} cm
        Gender: {data['gender']}
        Training Phase: {data['trainingPhase']}
        Dietary Restrictions: {data['dietaryRestrictions']}
        Goals: {data['goals']}
        
        Please provide a comprehensive nutrition plan including:
        1. Daily caloric needs
        2. Macronutrient distribution
        3. Meal timing around training
        4. Specific food recommendations
        5. Pre and post-workout nutrition
        6. Hydration guidelines
        7. Supplement recommendations (if necessary)
        
        Format the response in a clear, structured way with sections and bullet points."""

        # Generate response using Gemini
        response = model.generate_content(prompt)
        
        # Get the generated text
        nutrition_plan = response.text
        return jsonify({"plan": nutrition_plan})
    except Exception as e:
        print(f"Error in generate_nutrition_plan: {str(e)}")
        return jsonify({"error": str(e)}), 500

@app.route('/save-nutrition-plan', methods=['POST'])
def save_nutrition_plan():
    try:
        data = request.json
        # Add timestamp and generate unique ID
        data['created_at'] = datetime.utcnow()
        data['_id'] = str(ObjectId())
        
        # Save to MongoDB
        nutrition_plans.insert_one(data)
        return jsonify({'success': True, 'message': 'Nutrition plan saved successfully', 'plan_id': data['_id']})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/get-saved-plans', methods=['GET'])
def get_saved_plans():
    try:
        # Retrieve all saved plans, sorted by creation date
        saved_plans = list(nutrition_plans.find().sort('created_at', -1))
        # Convert ObjectId to string for JSON serialization
        for plan in saved_plans:
            plan['_id'] = str(plan['_id'])
            plan['created_at'] = plan['created_at'].isoformat()
        return jsonify({'success': True, 'plans': saved_plans})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/delete-nutrition-plan/<plan_id>', methods=['DELETE'])
def delete_nutrition_plan(plan_id):
    try:
        # Delete the plan from MongoDB
        result = nutrition_plans.delete_one({'_id': plan_id})
        if result.deleted_count > 0:
            return jsonify({'success': True, 'message': 'Plan deleted successfully'})
        else:
            return jsonify({'success': False, 'message': 'Plan not found'}), 404
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

# Import digital twin service
from digital_twin_service import DigitalTwin, monitor_athlete
import asyncio
from asgiref.sync import async_to_sync

# Initialize digital twin service
digital_twin = DigitalTwin()

# Digital Twin Routes
@app.route('/digital-twin', methods=['GET', 'POST'])
def digital_twin_route():
    if request.method == 'GET':
        return render_template('digital_twin.html')
        
    if request.method == 'POST':
        try:
            # Get action from JSON data
            data = request.get_json()
            if not data:
                return jsonify({"status": "error", "message": "No JSON data received"})
                
            action = data.get('action')
            if not action:
                return jsonify({"status": "error", "message": "No action specified"})
            
            logger.info(f"Digital Twin action received: {action}")
            
            if action == 'scan':
                scan_result = async_to_sync(digital_twin.scan_devices)()
                logger.info(f"Scan result: {scan_result}")
                return jsonify(scan_result)
                
            elif action == 'connect':
                device_address = data.get('device_address')
                if not device_address:
                    return jsonify({"status": "error", "message": "No device address provided"})
                    
                logger.info(f"Connecting to device: {device_address}")
                connect_result = async_to_sync(digital_twin.connect_device)(device_address)
                logger.info(f"Connect result: {connect_result}")
                return jsonify(connect_result)
                
            elif action == 'get_data':
                if not digital_twin.connected_device:
                    return jsonify({"status": "error", "message": "No device connected"})
                    
                duration = int(data.get('duration', 60))
                logger.info(f"Getting data for duration: {duration}s")
                data_result = async_to_sync(digital_twin.get_monitoring_data)(duration)
                return jsonify(data_result)
                
            elif action == 'disconnect':
                disconnect_result = async_to_sync(digital_twin.disconnect_current_device)()
                logger.info(f"Disconnect result: {disconnect_result}")
                return jsonify(disconnect_result)
                
            return jsonify({"status": "error", "message": "Invalid action"})
            
        except Exception as e:
            logger.error(f"Error in digital twin route: {str(e)}")
            return jsonify({"status": "error", "message": str(e)})

@app.route('/api/digital-twin/scan', methods=['GET'])
def scan_devices():
    """Scan for available fitness devices."""
    try:
        digital_twin = DigitalTwin()
        devices = async_to_sync(digital_twin.device_manager.scan_devices)()
        return jsonify({
            'status': 'success',
            'devices': devices
        })
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

@app.route('/api/digital-twin/connect', methods=['POST'])
def connect_device():
    """Connect to a specific fitness device."""
    try:
        data = request.get_json()
        device_address = data.get('device_address')
        
        if not device_address:
            return jsonify({
                'status': 'error',
                'message': 'Device address is required'
            }), 400
        
        digital_twin = DigitalTwin()
        async_to_sync(digital_twin.initialize)(device_address)
        
        return jsonify({
            'status': 'success',
            'message': 'Connected to device'
        })
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

@app.route('/api/digital-twin/monitor', methods=['POST'])
def start_monitoring():
    """Start monitoring athlete's data."""
    try:
        data = request.get_json()
        duration = data.get('duration', 60)  # Default 60 seconds
        
        insights = async_to_sync(monitor_athlete)(duration)
        
        if insights:
            return jsonify({
                'status': 'success',
                'data': insights
            })
        else:
            return jsonify({
                'status': 'error',
                'message': 'Failed to collect data'
            }), 500
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

# AI Coach configuration
AI_COACH_PROMPT = """You are an expert AI Sports Coach and Anti-Doping Assistant. Your role is to provide personalized guidance for athletes.

Current language: {language}
Previous conversation:
{context}

User's message: {message}

Please provide a response that:
1. Is clear, concise, and actionable
2. Uses appropriate language and tone for {language}
3. Includes specific training or anti-doping advice when relevant
4. Maintains a supportive and motivating tone
5. References scientific/medical facts when appropriate
6. Emphasizes safety and compliance with anti-doping regulations

Response:"""

@app.route('/chat')
def chat():
    """Render the chat interface"""
    return render_template('chat.html')

@app.route('/ai-coach', methods=['POST'])
def ai_coach_api():
    """Handle AI coach API requests with improved context and error handling"""
    try:
        # Validate request data
        if not request.is_json:
            return jsonify({
                'error': 'Request must be JSON',
                'success': False
            }), 400

        data = request.json
        user_message = data.get('message', '').strip()
        language = data.get('language', 'en')
        context = data.get('context', [])

        # Validate input
        if not user_message:
            return jsonify({
                'error': 'Message cannot be empty',
                'success': False
            }), 400

        # Process conversation context
        context_summary = ""
        if context:
            # Take last 3 interactions for context
            recent_context = context[-6:]  # Last 3 exchanges (user + coach)
            context_summary = "\n".join([
                f"{'User' if item['role'] == 'user' else 'Coach'}: {item['content']}"
                for item in recent_context
            ])

        # Map language codes to full names for better context
        language_names = {
            'en': 'English',
            'es': 'Spanish',
            'fr': 'French',
            'de': 'German',
            'it': 'Italian',
            'pt': 'Portuguese',
            'hi': 'Hindi',
            'zh': 'Chinese'
        }

        # Format the prompt
        formatted_prompt = AI_COACH_PROMPT.format(
            language=language_names.get(language, 'English'),
            context=context_summary,
            message=user_message
        )

        try:
            # Generate response using Gemini
            response = model.generate_content(formatted_prompt)
            coach_response = response.text

            # Translate if needed
            if language != 'en':
                translation_prompt = f"""Translate this sports coaching response to {language_names.get(language, 'English')}.
                Maintain the professional and supportive tone.
                Preserve technical terms, numbers, and proper names.
                
                Original text: {coach_response}
                
                Translation:"""
                
                translation = model.generate_content(translation_prompt)
                coach_response = translation.text

            return jsonify({
                'response': coach_response,
                'success': True
            })

        except Exception as e:
            logging.error(f"Gemini API error: {str(e)}")
            return jsonify({
                'error': 'An error occurred while generating the response. Please try again.',
                'success': False
            }), 500

    except Exception as e:
        logging.error(f"AI coach error: {str(e)}")
        return jsonify({
            'error': 'An unexpected error occurred. Please try again.',
            'success': False
        }), 500

@app.route('/smart-labels')
def smart_labels():
    app.logger.debug("Accessing smart labels page")
    return render_template('smart_labels.html')

import numpy as np
from sklearn.ensemble import RandomForestClassifier, GradientBoostingRegressor
from sklearn.preprocessing import StandardScaler
import joblib
import os

# Initialize ML models
def initialize_ml_models():
    """Initialize or load ML models"""
    models_dir = os.path.join(os.path.dirname(__file__), 'models')
    os.makedirs(models_dir, exist_ok=True)
    
    # Supplement Safety Model
    supplement_model_path = os.path.join(models_dir, 'supplement_safety_model.joblib')
    if os.path.exists(supplement_model_path):
        supplement_classifier = joblib.load(supplement_model_path)
    else:
        # Initialize with basic training data
        supplement_classifier = RandomForestClassifier(n_estimators=100)
        # Example training data structure
        X_supp = np.array([
            # [protein_content, stimulant_level, hormone_level, synthetic_compounds]
            [80, 0, 0, 0],  # Whey Protein
            [0, 5, 0, 1],   # Pre-workout
            [0, 0, 90, 1],  # Anabolic steroid
            [20, 0, 0, 0],  # BCAA
        ])
        y_supp = np.array(['safe', 'caution', 'prohibited', 'safe'])
        supplement_classifier.fit(X_supp, y_supp)
        joblib.dump(supplement_classifier, supplement_model_path)

    # Athlete Performance Model
    performance_model_path = os.path.join(models_dir, 'performance_model.joblib')
    if os.path.exists(performance_model_path):
        performance_predictor = joblib.load(performance_model_path)
    else:
        # Initialize with basic training data
        performance_predictor = GradientBoostingRegressor(n_estimators=100)
        # Example training data structure
        X_perf = np.array([
            # [sleep_hours, training_intensity, stress_level, recovery_score]
            [8, 7, 3, 90],
            [6, 8, 6, 70],
            [7, 6, 4, 85],
            [5, 9, 8, 60],
        ])
        y_perf = np.array([95, 75, 85, 65])  # Performance scores
        performance_predictor.fit(X_perf, y_perf)
        joblib.dump(performance_predictor, performance_model_path)

    return supplement_classifier, performance_predictor

# Initialize models at startup
supplement_classifier, performance_predictor = initialize_ml_models()
scaler = StandardScaler()

@app.route('/api/supplements/analyze', methods=['POST'])
def analyze_supplement_ml():
    """Analyze supplement using ML model"""
    try:
        data = request.json
        
        # Extract features from Gemini analysis
        ingredients_response = model.generate_content(f"""
        Analyze this supplement and provide numerical values for:
        1. Protein content (0-100)
        2. Stimulant level (0-100)
        3. Hormone level (0-100)
        4. Synthetic compounds presence (0 or 1)

        Supplement: {data.get('name', '')}

        Please provide a response in this JSON format:
        {{
            "protein_content": float,
            "stimulant_level": float,
            "hormone_level": float,
            "synthetic_compounds": int
        }}
        """)
        
        try:
            features = json.loads(ingredients_response.text)
            X = np.array([[
                features['protein_content'],
                features['stimulant_level'],
                features['hormone_level'],
                features['synthetic_compounds']
            ]])
            
            # Get ML prediction
            ml_prediction = supplement_classifier.predict(X)[0]
            ml_proba = supplement_classifier.predict_proba(X)[0]
            
            return jsonify({
                'success': True,
                'ml_analysis': {
                    'prediction': ml_prediction,
                    'confidence': float(max(ml_proba)),
                    'features': features
                }
            })
        except Exception as e:
            return jsonify({
                'success': False,
                'error': f'ML analysis error: {str(e)}'
            })

    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/athlete/analyze-performance', methods=['POST'])
def analyze_performance_ml():
    """Analyze athlete performance using ML model"""
    try:
        data = request.json
        
        # Extract features
        X = np.array([[
            float(data.get('sleep_hours', 0)),
            float(data.get('training_intensity', 0)),
            float(data.get('stress_level', 0)),
            float(data.get('recovery_score', 0))
        ]])
        
        # Get ML prediction
        performance_score = performance_predictor.predict(X)[0]
        
        # Get feature importance
        feature_importance = dict(zip(
            ['sleep', 'training', 'stress', 'recovery'],
            performance_predictor.feature_importances_
        ))
        
        # Generate personalized recommendations
        recommendations = []
        if X[0][0] < 7:  # sleep hours
            recommendations.append({
                'factor': 'sleep',
                'message': 'Increase sleep duration to improve recovery and performance'
            })
        if X[0][2] > 7:  # stress level
            recommendations.append({
                'factor': 'stress',
                'message': 'Consider stress management techniques to optimize performance'
            })
        if X[0][3] < 70:  # recovery score
            recommendations.append({
                'factor': 'recovery',
                'message': 'Focus on recovery protocols to prevent overtraining'
            })
        
        return jsonify({
            'success': True,
            'ml_analysis': {
                'performance_score': float(performance_score),
                'feature_importance': feature_importance,
                'recommendations': recommendations,
                'training_load_status': 'High' if X[0][1] > 7 else 'Moderate' if X[0][1] > 4 else 'Low'
            }
        })

    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/supplements/check', methods=['POST'])
def check_supplement():
    """Check supplement safety using Gemini AI and ML"""
    try:
        data = request.json
        supplement_name = data.get('name', '')
        
        # First get ML analysis
        ml_response = analyze_supplement_ml()
        ml_data = ml_response.json
        
        # Then get Gemini analysis
        ingredients_prompt = f"""As a supplement expert, analyze this supplement and list its typical ingredients:

Supplement Name: {supplement_name}

Please provide:
1. Common ingredients found in this supplement
2. Active ingredients and their typical amounts
3. Other ingredients (excipients, fillers, etc.)

Format the response as a JSON object with these fields:
{{
    "active_ingredients": [
        {{
            "name": "ingredient name",
            "typical_amount": "amount with unit",
            "purpose": "brief purpose description"
        }}
    ],
    "other_ingredients": ["list of other ingredients"],
    "supplement_type": "category of supplement",
    "common_forms": ["list of common forms (tablets, powder, etc.)"]
}}"""

        ingredients_response = model.generate_content(ingredients_prompt)
        try:
            ingredients_text = ingredients_response.text
            ingredients_data = json.loads(ingredients_text)
        except (json.JSONDecodeError, AttributeError):
            ingredients_data = {
                "active_ingredients": [{"name": "Unknown", "typical_amount": "N/A", "purpose": "Unable to determine"}],
                "other_ingredients": ["Unknown"],
                "supplement_type": "Unknown",
                "common_forms": ["Unknown"]
            }

        # Format ingredients for safety analysis
        active_ingredients = ", ".join([f"{ing['name']} ({ing['typical_amount']})" for ing in ingredients_data['active_ingredients']])
        other_ingredients = ", ".join(ingredients_data['other_ingredients'])
        
        # Include ML prediction in the prompt
        safety_prompt = f"""As an anti-doping expert, analyze this supplement for safety and competition compliance:

Supplement: {supplement_name}
Type: {ingredients_data['supplement_type']}
Active Ingredients: {active_ingredients}
Other Ingredients: {other_ingredients}
ML Safety Prediction: {ml_data.get('ml_analysis', {}).get('prediction', 'Unknown')}
ML Confidence: {ml_data.get('ml_analysis', {}).get('confidence', 0):.2f}

Provide a detailed analysis including:
1. Overall safety assessment
2. Competition compliance status
3. Ingredient analysis
4. Potential risks
5. Recommendations for athletes

Format the response as a JSON object with these fields:
{{
    "safety_status": "Safe/Caution/Prohibited",
    "competition_safe": true/false,
    "analysis": "Detailed safety analysis",
    "key_concerns": ["List of key concerns if any"],
    "risks": ["Potential risks"],
    "recommendations": ["Specific recommendations"],
    "wada_compliance": "WADA compliance status",
    "confidence_level": "High/Medium/Low",
    "alternatives": ["Safer alternatives if needed"]
}}"""

        safety_response = model.generate_content(safety_prompt)
        try:
            safety_text = safety_response.text
            safety_data = json.loads(safety_text)
        except (json.JSONDecodeError, AttributeError):
            safety_data = {
                "safety_status": "Caution",
                "competition_safe": False,
                "analysis": "Unable to determine safety with confidence",
                "key_concerns": ["Unable to verify ingredients"],
                "risks": ["Unknown ingredients may be present"],
                "recommendations": [
                    "Consult with sports nutritionist",
                    "Verify with your sports organization",
                    "Check WADA prohibited substances list"
                ],
                "wada_compliance": "Unable to determine",
                "confidence_level": "Low",
                "alternatives": ["Consider certified supplements"]
            }

        # Combine all analyses
        return jsonify({
            'success': True,
            'data': {
                'ingredients': ingredients_data,
                'safety': safety_data,
                'ml_analysis': ml_data.get('ml_analysis', {})
            }
        })

    except Exception as e:
        logging.error(f"Error in supplement check: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/analyze-product', methods=['POST'])
def analyze_product():
    try:
        app.logger.info("Starting product analysis")
        if 'image' not in request.files:
            return jsonify({'status': 'error', 'message': 'No image file provided'})

        image_file = request.files['image']
        if not image_file or not allowed_file(image_file.filename):
            return jsonify({'status': 'error', 'message': 'Invalid image file'})

        # Process image
        image_bytes = image_file.read()
        image = Image.open(io.BytesIO(image_bytes))
        
        # Generate hash for caching
        image_hash = hashlib.md5(image_bytes).hexdigest()
        cache_path = os.path.join(app.config['CACHE_DIR'], f'{image_hash}.json')

        # Check cache
        if os.path.exists(cache_path):
            app.logger.info(f"Cache hit for image {image_hash}")
            with open(cache_path, 'r') as f:
                return jsonify({'status': 'success', 'analysis': json.load(f)})

        # Prepare image for Gemini
        img_byte_arr = io.BytesIO()
        image.save(img_byte_arr, format=image.format or 'JPEG')
        img_byte_arr = img_byte_arr.getvalue()

        try:
            # Try OCR first for better text extraction
            text_from_image = pytesseract.image_to_string(image)
            app.logger.info("OCR completed")
        except Exception as e:
            app.logger.warning(f"OCR failed: {str(e)}")
            text_from_image = ""

        # Prepare Gemini model
        model = genai.GenerativeModel('gemini-pro-vision')
        
        # Enhanced prompt for better analysis
        prompt = f"""
        Analyze this product label image for athletes. Focus on:
        1. Product name and type
        2. Ingredients list
        3. Potential banned or controlled substances
        4. Competition status (prohibited, allowed, threshold)
        5. Risk assessment

        Additional context from OCR: {text_from_image}

        Provide a detailed analysis in this JSON format:
        {{
            "product_name": "Product name",
            "overall_assessment": {{
                "risk_level": "LOW/MEDIUM/HIGH",
                "competition_status": "SAFE/CAUTION/PROHIBITED",
                "warning_message": "Any specific warnings"
            }},
            "ingredients_analysis": [
                {{
                    "name": "Ingredient name",
                    "status": "SAFE/CAUTION/PROHIBITED",
                    "category": "Stimulant/Protein/etc",
                    "warning": "Specific warning if any"
                }}
            ],
            "recommendations": [
                "Specific recommendations for the athlete"
            ]
        }}

        Focus on WADA prohibited list and common sports supplements.
        """

        try:
            # Generate response from Gemini
            response = model.generate_content([prompt, genai.types.Image.from_bytes(img_byte_arr)])
            analysis = json.loads(response.text)
            app.logger.info("Gemini analysis completed")
            
            # Cache the result
            os.makedirs(app.config['CACHE_DIR'], exist_ok=True)
            with open(cache_path, 'w') as f:
                json.dump(analysis, f)
            
            return jsonify({'status': 'success', 'analysis': analysis})

        except Exception as e:
            app.logger.error(f"Gemini analysis failed: {str(e)}")
            # Fallback to basic analysis
            basic_analysis = {
                "product_name": "Unknown Product",
                "overall_assessment": {
                    "risk_level": "MEDIUM",
                    "competition_status": "CAUTION",
                    "warning_message": "Unable to perform detailed analysis. Please consult with your sports physician."
                },
                "ingredients_analysis": [
                    {
                        "name": "Unknown Ingredients",
                        "status": "CAUTION",
                        "category": "Unknown",
                        "warning": "Could not analyze ingredients. Please check with your team doctor."
                    }
                ],
                "recommendations": [
                    "Consult with your sports physician or team doctor",
                    "Check the product against WADA's prohibited list manually",
                    "Consider using a certified alternative product"
                ],
                "source": "fallback"
            }
            
            if text_from_image:
                basic_analysis["ocr_text"] = text_from_image

            return jsonify({'status': 'success', 'analysis': basic_analysis})

    except Exception as e:
        app.logger.error(f"Analysis error: {str(e)}")
        return jsonify({'status': 'error', 'message': str(e)})

@app.route('/api/podcasts/upload', methods=['POST'])
def upload_podcast():
    try:
        if 'audio_file' not in request.files:
            return jsonify({'success': False, 'error': 'No audio file provided'}), 400
            
        file = request.files['audio_file']
        if file.filename == '':
            return jsonify({'success': False, 'error': 'No selected file'}), 400
            
        if not file.filename.endswith('.mp3'):
            return jsonify({'success': False, 'error': 'Only MP3 files are supported'}), 400
        
        # Secure the filename
        filename = secure_filename(file.filename)
        
        # Create uploads directory if it doesn't exist
        upload_dir = os.path.join(app.root_path, 'static', 'podcasts')
        os.makedirs(upload_dir, exist_ok=True)
        
        # Save the file
        file_path = os.path.join(upload_dir, filename)
        file.save(file_path)
        
        # Get audio duration using mutagen
        try:
            audio = MP3(file_path)
            duration = int(audio.info.length)
        except Exception as e:
            duration = 0
            logging.error(f"Error getting audio duration: {str(e)}")
        
        # Create podcast document
        podcast = {
            'title': request.form.get('title', 'Untitled Podcast'),
            'description': request.form.get('description', ''),
            'category': request.form.get('category', 'Training & Education'),
            'author': request.form.get('author', 'Anonymous'),
            'filename': filename,
            'duration': duration,
            'upload_date': datetime.utcnow(),
            'language': request.form.get('language', 'en'),
            'tags': request.form.get('tags', '').split(',') if request.form.get('tags') else []
        }
        
        # Save to MongoDB
        result = mongo_db.podcasts.insert_one(podcast)
        podcast['_id'] = str(result.inserted_id)
        
        return jsonify({
            'success': True,
            'message': 'Podcast uploaded successfully',
            'podcast': podcast
        })
        
    except Exception as e:
        logging.error(f"Error uploading podcast: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/podcasts/<podcast_id>', methods=['DELETE'])
def delete_podcast(podcast_id):
    try:
        # Find the podcast
        podcast = mongo_db.podcasts.find_one({'_id': ObjectId(podcast_id)})
        if not podcast:
            return jsonify({'success': False, 'error': 'Podcast not found'}), 404
            
        # Delete the audio file
        file_path = os.path.join(app.root_path, 'static', 'podcasts', podcast['filename'])
        if os.path.exists(file_path):
            os.remove(file_path)
            
        # Delete from MongoDB
        mongo_db.podcasts.delete_one({'_id': ObjectId(podcast_id)})
        
        return jsonify({'success': True, 'message': 'Podcast deleted successfully'})
        
    except Exception as e:
        logging.error(f"Error deleting podcast: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/podcasts/<podcast_id>', methods=['PUT'])
def update_podcast(podcast_id):
    try:
        # Get the podcast
        podcast = mongo_db.podcasts.find_one({'_id': ObjectId(podcast_id)})
        if not podcast:
            return jsonify({'success': False, 'error': 'Podcast not found'}), 404
            
        # Update fields
        update_data = {
            'title': request.form.get('title', podcast['title']),
            'description': request.form.get('description', podcast['description']),
            'category': request.form.get('category', podcast['category']),
            'author': request.form.get('author', podcast['author']),
            'language': request.form.get('language', podcast.get('language', 'en')),
            'tags': request.form.get('tags', '').split(',') if request.form.get('tags') else podcast.get('tags', [])
        }
        
        # Update audio file if provided
        if 'audio_file' in request.files:
            file = request.files['audio_file']
            if file.filename != '' and file.filename.endswith('.mp3'):
                # Delete old file
                old_file_path = os.path.join(app.root_path, 'static', 'podcasts', podcast['filename'])
                if os.path.exists(old_file_path):
                    os.remove(old_file_path)
                
                # Save new file
                filename = secure_filename(file.filename)
                file_path = os.path.join(app.root_path, 'static', 'podcasts', filename)
                file.save(file_path)
                
                # Update duration
                try:
                    audio = MP3(file_path)
                    update_data['duration'] = int(audio.info.length)
                except Exception as e:
                    logging.error(f"Error getting audio duration: {str(e)}")
                
                update_data['filename'] = filename
        
        # Update in MongoDB
        mongo_db.podcasts.update_one(
            {'_id': ObjectId(podcast_id)},
            {'$set': update_data}
        )
        
        return jsonify({
            'success': True,
            'message': 'Podcast updated successfully',
            'podcast': {**podcast, **update_data, '_id': str(podcast['_id'])}
        })
        
    except Exception as e:
        logging.error(f"Error updating podcast: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500

def calculate_score(user_answers, correct_answers):
    """Calculate the percentage score for a quiz"""
    if len(user_answers) != len(correct_answers):
        raise ValueError("Answer length mismatch")
    
    correct_count = sum(1 for user_ans, correct_ans in zip(user_answers, correct_answers) if user_ans == correct_ans)
    return (correct_count / len(correct_answers)) * 100

def fetch_sports_podcasts():
    """Fetch sports and anti-doping related podcasts from multiple sources"""
    all_podcasts = []
    
    # List of RSS feeds for sports and anti-doping content
    rss_feeds = [
        {
            'url': 'https://feeds.megaphone.fm/EMPOW3391357123',  # Sports Integrity Podcast
            'category': 'Sports Integrity'
        },
        {
            'url': 'https://anchor.fm/s/1f8af31c/podcast/rss',  # Play True Podcast
            'category': 'Anti-Doping'
        },
        {
            'url': 'https://feeds.buzzsprout.com/1052198.rss',  # Clean Sport Collective
            'category': 'Clean Sport'
        },
        {
            'url': 'https://feeds.soundcloud.com/users/soundcloud:users:307223250/sounds.rss',  # UKAD Podcast
            'category': 'Anti-Doping'
        },
        {
            'url': 'https://www.listennotes.com/c/r/37a1c7f7e0e246d8a8696a95c7c93d62',  # The Doping Podcast
            'category': 'Anti-Doping Education'
        }
    ]
    
    # YouTube channels and playlists for anti-doping content
    youtube_sources = [
        'https://www.youtube.com/user/wadamovies/videos',  # WADA's YouTube channel
        'https://www.youtube.com/user/cleansport/videos',  # Clean Sport
        'https://www.youtube.com/c/antidoping/videos'  # Anti-Doping Channel
    ]
    
    try:
        # Fetch from RSS feeds
        for feed_info in rss_feeds:
            try:
                feed = feedparser.parse(feed_info['url'])
                for entry in feed.entries[:5]:  # Get latest 5 episodes
                    try:
                        # Extract audio URL from enclosures or content
                        audio_url = ''
                        if hasattr(entry, 'enclosures') and entry.enclosures:
                            audio_url = next((e['href'] for e in entry.enclosures 
                                            if e.get('type', '').startswith('audio/')), '')
                        
                        # Get the largest image from media content or thumbnail
                        image_url = ''
                        if hasattr(entry, 'media_content'):
                            images = [m['url'] for m in entry.media_content 
                                    if m.get('type', '').startswith('image/')]
                            if images:
                                image_url = max(images, key=lambda x: int(x.get('width', 0)))
                        elif hasattr(entry, 'media_thumbnail'):
                            image_url = entry.media_thumbnail[0]['url']
                        
                        podcast = {
                            'title': entry.get('title', 'Untitled Episode'),
                            'description': BeautifulSoup(entry.get('description', ''), 'html.parser').get_text()[:500],
                            'published_date': entry.get('published', ''),
                            'duration': entry.get('itunes_duration', ''),
                            'audio_url': audio_url,
                            'image_url': image_url,
                            'source_url': entry.get('link', ''),
                            'author': entry.get('author', feed.feed.get('title', 'Unknown')),
                            'category': feed_info['category'],
                            'language': entry.get('language', 'en'),
                            'source_type': 'rss'
                        }
                        all_podcasts.append(podcast)
                        logging.info(f"Added podcast: {podcast['title']} from {feed_info['url']}")
                    except Exception as entry_error:
                        logging.error(f"Error processing entry from {feed_info['url']}: {str(entry_error)}")
                        continue
            except Exception as feed_error:
                logging.error(f"Error fetching feed {feed_info['url']}: {str(feed_error)}")
                continue
        
        # Fetch from YouTube (if API key is available)
        youtube_api_key = os.getenv('YOUTUBE_API_KEY')
        if youtube_api_key:
            for source in youtube_sources:
                try:
                    channel_id = source.split('/')[-2]
                    url = f"https://www.googleapis.com/youtube/v3/search"
                    params = {
                        'key': youtube_api_key,
                        'channelId': channel_id,
                        'part': 'snippet',
                        'order': 'date',
                        'maxResults': 5,
                        'type': 'video'
                    }
                    response = requests.get(url, params=params)
                    if response.status_code == 200:
                        data = response.json()
                        for item in data.get('items', []):
                            video = {
                                'title': item['snippet']['title'],
                                'description': item['snippet']['description'][:500],
                                'published_date': item['snippet']['publishedAt'],
                                'image_url': item['snippet']['thumbnails']['high']['url'],
                                'source_url': f"https://www.youtube.com/watch?v={item['id']['videoId']}",
                                'author': item['snippet']['channelTitle'],
                                'category': 'Anti-Doping Education',
                                'language': 'en',
                                'source_type': 'youtube'
                            }
                            all_podcasts.append(video)
                except Exception as yt_error:
                    logging.error(f"Error fetching YouTube content from {source}: {str(yt_error)}")
                    continue
        
        # Sort all podcasts by published date
        all_podcasts.sort(key=lambda x: x.get('published_date', ''), reverse=True)
        return all_podcasts
        
    except Exception as e:
        logging.error(f"Error in fetch_sports_podcasts: {str(e)}")
        return []

# Sample athlete data
athlete_data = {
    'profile': {
        'name': 'John Doe',
        'sport': 'Track and Field',
        'age': 24,
        'height': '180 cm',
        'weight': '75 kg',
        'training_level': 'Professional'
    },
    'metrics': {
        'recent_training': {
            'weekly_hours': 15,
            'intensity_level': 'High',
            'recovery_status': 'Good'
        },
        'performance': {
            'vo2_max': '58.5 ml/kg/min',
            'resting_heart_rate': '52 bpm',
            'training_zones': {
                'zone1': '120-140 bpm',
                'zone2': '140-160 bpm',
                'zone3': '160-180 bpm'
            }
        },
        'wellness': {
            'sleep_quality': 'Good',
            'stress_level': 'Low',
            'fatigue_index': 'Normal'
        }
    },
    'recommendations': [
        {
            'category': 'Training',
            'text': 'Consider increasing endurance training sessions based on your recent performance metrics.'
        },
        {
            'category': 'Recovery',
            'text': 'Your sleep quality is good. Maintain your current sleep schedule for optimal recovery.'
        },
        {
            'category': 'Nutrition',
            'text': 'Pre-competition nutrition plan suggested: focus on complex carbohydrates 3 hours before events.'
        }
    ]
}

# Supplement database with safety information
supplement_database = {
    'whey_protein': {
        'name': 'Whey Protein Isolate',
        'category': 'Protein',
        'status': 'Safe',
        'competition_safe': True,
        'description': 'Common and well-researched protein supplement.',
        'recommendations': 'Safe for competition use. Check for quality certification.',
        'common_brands': ['Brand A', 'Brand B', 'Brand C']
    },
    'creatine': {
        'name': 'Creatine Monohydrate',
        'category': 'Performance',
        'status': 'Safe',
        'competition_safe': True,
        'description': 'One of the most researched supplements in sports nutrition.',
        'recommendations': 'Follow recommended loading and maintenance doses.',
        'common_brands': ['Brand X', 'Brand Y', 'Brand Z']
    },
    'pre_workout': {
        'name': 'Pre-Workout Supplement',
        'category': 'Performance',
        'status': 'Caution',
        'competition_safe': False,
        'description': 'May contain prohibited substances. Check ingredients carefully.',
        'recommendations': 'Verify all ingredients against WADA prohibited list.',
        'warning': 'High risk of contamination with prohibited substances.'
    }
}

@app.route('/api/athlete/dashboard')
def get_athlete_dashboard():
    """Get athlete's dashboard data including metrics and recommendations"""
    return jsonify(athlete_data)

# @app.route('/api/supplements/check', methods=['POST'])
# def check_supplement():
#     """Check supplement safety using Gemini AI"""
#     try:
#         data = request.json
#         supplement_name = data.get('name', '')
        
#         # First prompt to get supplement ingredients
#         ingredients_prompt = f"""As a supplement expert, analyze this supplement and list its typical ingredients:

# Supplement Name: {supplement_name}

# Please provide:
# 1. Common ingredients found in this supplement
# 2. Active ingredients and their typical amounts
# 3. Other ingredients (excipients, fillers, etc.)

# Format the response as a JSON object with these fields:
# {{
#     "active_ingredients": [
#         {{
#             "name": "ingredient name",
#             "typical_amount": "amount with unit",
#             "purpose": "brief purpose description"
#         }}
#     ],
#     "other_ingredients": ["list of other ingredients"],
#     "supplement_type": "category of supplement",
#     "common_forms": ["list of common forms (tablets, powder, etc.)"]
# }}"""

#         # Get ingredients from Gemini
#         ingredients_response = model.generate_content(ingredients_prompt)
        
#         try:
#             # Extract the text content from Gemini response
#             ingredients_text = ingredients_response.text
#             # Parse the response as JSON
#             ingredients_data = json.loads(ingredients_text)
#         except (json.JSONDecodeError, AttributeError):
#             ingredients_data = {
#                 "active_ingredients": [{"name": "Unknown", "typical_amount": "N/A", "purpose": "Unable to determine"}],
#                 "other_ingredients": ["Unknown"],
#                 "supplement_type": "Unknown",
#                 "common_forms": ["Unknown"]
#             }

#         # Format ingredients for safety analysis
#         active_ingredients = ", ".join([f"{ing['name']} ({ing['typical_amount']})" for ing in ingredients_data['active_ingredients']])
#         other_ingredients = ", ".join(ingredients_data['other_ingredients'])
        
#         # Second prompt for safety analysis
#         safety_prompt = f"""As an anti-doping expert, analyze this supplement for safety and competition compliance:

# Supplement: {supplement_name}
# Type: {ingredients_data['supplement_type']}
# Active Ingredients: {active_ingredients}
# Other Ingredients: {other_ingredients}

# Provide a detailed analysis including:
# 1. Overall safety assessment
# 2. Competition compliance status
# 3. Ingredient analysis
# 4. Potential risks
# 5. Recommendations for athletes

# Format the response as a JSON object with these fields:
# {{
#     "safety_status": "Safe/Caution/Prohibited",
#     "competition_safe": true/false,
#     "analysis": "Detailed safety analysis",
#     "key_concerns": ["List of key concerns if any"],
#     "risks": ["Potential risks"],
#     "recommendations": ["Specific recommendations"],
#     "wada_compliance": "WADA compliance status",
#     "confidence_level": "High/Medium/Low",
#     "alternatives": ["Safer alternatives if needed"]
# }}"""

#         # Get safety analysis from Gemini
#         safety_response = model.generate_content(safety_prompt)
        
#         try:
#             # Extract the text content from Gemini response
#             safety_text = safety_response.text
#             # Parse the response as JSON
#             safety_data = json.loads(safety_text)
#         except (json.JSONDecodeError, AttributeError):
#             safety_data = {
#                 "safety_status": "Caution",
#                 "competition_safe": False,
#                 "analysis": "Unable to determine safety with confidence",
#                 "key_concerns": ["Unable to verify ingredients"],
#                 "risks": ["Unknown ingredients may be present"],
#                 "recommendations": [
#                     "Consult with sports nutritionist",
#                     "Verify with your sports organization",
#                     "Check WADA prohibited substances list"
#                 ],
#                 "wada_compliance": "Unable to determine",
#                 "confidence_level": "Low",
#                 "alternatives": ["Consider certified supplements"]
#             }

#         # Combine both analyses
#         return jsonify({
#             'success': True,
#             'data': {
#                 'ingredients': ingredients_data,
#                 'safety': safety_data
#             }
#         })

#     except Exception as e:
#         logging.error(f"Error in supplement check: {str(e)}")
#         return jsonify({
#             'success': False,
#             'error': str(e)
#         }), 500

@app.route('/api/athlete/analyze', methods=['POST'])
def analyze_athlete_data():
    """Analyze athlete's training data using Gemini AI"""
    try:
        data = request.json
        
        # Construct prompt for Gemini
        prompt = f"""As a professional sports performance analyst, analyze this athlete's data and provide recommendations:

Training Data:
- Daily Steps: {data.get('steps')}
- Heart Rate: {data.get('heart_rate')} bpm
- Sleep Hours: {data.get('sleep_hours')}
- Training Type: {data.get('training_type')}
- Training Intensity: {data.get('intensity')}
- Training Duration: {data.get('duration')} minutes
- Stress Level: {data.get('stress_level')}
- Muscle Soreness: {data.get('soreness')}

Please analyze this data and provide:
1. Training load assessment
2. Recovery status evaluation
3. Performance analysis
4. Specific recommendations

Format the response as a JSON object with these fields:
{{
    "training_load": "Current training load status",
    "intensity_analysis": "Analysis of training intensity",
    "volume_status": "Training volume assessment",
    "recovery_score": "Recovery score out of 100",
    "sleep_quality": "Sleep quality assessment",
    "readiness": "Training readiness status",
    "performance_level": "Current performance level",
    "trend": "Performance trend (improving/stable/declining)",
    "focus_areas": "Key areas to focus on",
    "recommendations": [
        {{
            "category": "Training/Recovery/Nutrition",
            "text": "Specific recommendation"
        }}
    ]
}}"""

        # Get response from Gemini
        response = model.generate_content(prompt)
        
        try:
            # Parse the response as JSON
            analysis = json.loads(response.text)
            return jsonify(analysis)
        except json.JSONDecodeError:
            # Fallback response if AI response isn't proper JSON
            return jsonify({
                "training_load": "Moderate",
                "intensity_analysis": "Consider your current intensity level",
                "volume_status": "Review training volume",
                "recovery_score": "70",
                "sleep_quality": "Adequate",
                "readiness": "Ready for light training",
                "performance_level": "Maintaining",
                "trend": "Stable",
                "focus_areas": "Recovery and stress management",
                "recommendations": [
                    {
                        "category": "Training",
                        "text": "Monitor your training intensity and adjust based on recovery status"
                    },
                    {
                        "category": "Recovery",
                        "text": "Ensure adequate rest between sessions"
                    }
                ]
            })

    except Exception as e:
        logging.error(f"Error in athlete analysis: {str(e)}")
        return jsonify({
            'error': str(e)
        }), 500

import os
from datetime import datetime
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from reportlab.lib.units import inch
from reportlab.lib.colors import HexColor

def generate_pdf_certificate(user_id, quiz_id, score, timestamp, token_id=None):
    """Generate a PDF certificate for the user."""
    try:
        # Create certificates directory if it doesn't exist
        certificate_dir = os.path.join(os.path.dirname(__file__), 'certificates')
        if not os.path.exists(certificate_dir):
            os.makedirs(certificate_dir)
            
        # Generate unique filename
        filename = f"{user_id}_{quiz_id}_{int(timestamp.timestamp())}.pdf"
        filepath = os.path.join(certificate_dir, filename)
        
        # Create PDF
        c = canvas.Canvas(filepath, pagesize=letter)
        width, height = letter
        
        # Set background color
        c.setFillColor(HexColor('#f8f9fa'))
        c.rect(0, 0, width, height, fill=True)
        
        # Add certificate title
        c.setFillColor(HexColor('#212529'))
        c.setFont("Helvetica-Bold", 24)
        c.drawCentredString(width/2, height-2*inch, "Certificate of Completion")
        
        # Add anti-doping education details
        c.setFont("Helvetica", 16)
        c.drawCentredString(width/2, height-3*inch, "This is to certify that")
        
        # Add user name/ID
        c.setFont("Helvetica-Bold", 20)
        c.drawCentredString(width/2, height-3.5*inch, user_id)
        
        # Add completion text
        c.setFont("Helvetica", 16)
        c.drawCentredString(width/2, height-4*inch, 
            f"has successfully completed the Anti-Doping Education Quiz")
        c.drawCentredString(width/2, height-4.5*inch, 
            f"with a score of {score}%")
            
        # Add date
        c.setFont("Helvetica", 14)
        date_str = timestamp.strftime("%B %d, %Y")
        c.drawCentredString(width/2, height-5.5*inch, f"Date: {date_str}")
        
        # Add blockchain verification if available
        if token_id:
            c.setFont("Helvetica", 10)
            c.drawCentredString(width/2, 2*inch, 
                f"Blockchain Verification Token: {token_id}")
        
        # Save the PDF
        c.save()
        app.logger.info(f"Generated certificate: {filename}")
        return filename
        
    except Exception as e:
        app.logger.error(f"Error generating certificate PDF: {str(e)}")
        raise

from simulator import FitnessSimulator

# Initialize simulator
simulator = FitnessSimulator(socketio)

# Digital Twin Routes
@app.route('/api/athlete/start_simulation/<athlete_id>', methods=['POST'])
def start_simulation(athlete_id):
    try:
        simulator.start_simulation(athlete_id)
        return jsonify({
            'success': True,
            'message': f'Started simulation for athlete {athlete_id}'
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/athlete/metrics/<athlete_id>', methods=['GET'])
def get_athlete_metrics(athlete_id):
    try:
        data = simulator.athlete_data.get(athlete_id)
        if not data:
            return jsonify({
                'success': False,
                'error': 'Athlete not found'
            }), 404
            
        return jsonify({
            'success': True,
            'data': {
                'heart_rate': round(data['heart_rate']),
                'hrv': round(data['hrv']),
                'steps': int(data['steps']),
                'sleep_hours': round(data['sleep_hours'], 1),
                'activity': data['current_activity'],
                'calories_burned': int(data['calories_burned']),
                'stress_level': round(data['stress_level']),
                'recovery_score': round(data['recovery_score']),
                'hydration_level': round(data['hydration_level']),
                'is_sleeping': data['is_sleeping']
            }
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/digital_twin/<athlete_id>')
def digital_twin_dashboard(athlete_id):
    return render_template('digital_twin.html', athlete_id=athlete_id)

# Language and Notification Routes
@app.route('/change-language', methods=['POST'])
@login_required
def change_language():
    data = request.get_json()
    language = data.get('language')
    if language in ['en', 'es', 'fr', 'de', 'it', 'pt', 'hi', 'zh']:
        session['language'] = language
    return jsonify({'status': 'success'})

@app.route('/mark-notifications-read', methods=['POST'])
@login_required
def mark_notifications_read():
    try:
        notifications = Notification.query.filter_by(
            user_id=current_user.id,
            read=False
        ).all()
        
        for notification in notifications:
            notification.read = True
        
        db.session.commit()
        return jsonify({'status': 'success'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/register-push', methods=['POST'])
@login_required
def register_push():
    try:
        subscription_json = request.get_json()
        user = User.query.get(current_user.id)
        user.push_subscription = json.dumps(subscription_json)
        db.session.commit()
        return jsonify({'status': 'success'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/toggle-high-contrast', methods=['POST'])
@login_required
def toggle_high_contrast():
    session['high_contrast'] = not session.get('high_contrast', False)
    return jsonify({'status': 'success'})

@app.route('/toggle-large-text', methods=['POST'])
@login_required
def toggle_large_text():
    session['large_text'] = not session.get('large_text', False)
    return jsonify({'status': 'success'})

# Context Processors
@app.context_processor
def inject_notifications():
    if current_user.is_authenticated:
        notifications = Notification.query.filter_by(
            user_id=current_user.id
        ).order_by(Notification.created_at.desc()).limit(10).all()
        
        unread_count = Notification.query.filter_by(
            user_id=current_user.id,
            read=False
        ).count()
        
        return {
            'notifications': notifications,
            'unread_notifications_count': unread_count
        }
    return {}

@app.context_processor
def inject_languages():
    return {'supported_languages': ['en', 'es', 'fr', 'de', 'it', 'pt', 'hi', 'zh']}

if __name__ == "__main__":
    with app.app_context():
        db.create_all()  # Create all database tables
    app.run(debug=True)