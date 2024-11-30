from flask import Flask
from flask_cors import CORS
from pymongo import MongoClient
import os
from dotenv import load_dotenv
import logging

# Import all route blueprints
from routes.main_routes import main_bp
from routes.podcast_routes import podcast_bp
from routes.quiz_routes import quiz_bp
from routes.wiki_routes import wiki_bp
from routes.game_routes import game_bp
from routes.ai_coach_routes import ai_coach_bp
from routes.nutrition_routes import nutrition_bp
from routes.news_routes import news_bp

# Load environment variables
load_dotenv()

app = Flask(__name__, static_folder="static")
app.secret_key = os.getenv('FLASK_SECRET_KEY', 'your-secret-key-here')
CORS(app)

# Initialize MongoDB connection with error handling
try:
    client = MongoClient(os.getenv('MONGO_URI', 'mongodb://localhost:27017/'), serverSelectionTimeoutMS=5000)
    client.server_info()  # This will raise an exception if MongoDB is not running
    db = client['gamified_quizzes']
    logging.info("Successfully connected to MongoDB")
except Exception as e:
    logging.error(f"Failed to connect to MongoDB: {str(e)}")
    # Create an in-memory quiz storage as fallback
    class InMemoryQuizDB:
        def __init__(self):
            self.quizzes = {}
            self.quiz_results = {}
            self.podcasts = {}

        def find_one(self, query, projection=None):
            return self.quizzes.get(query.get('_id'))

        def insert_one(self, document):
            self.quizzes[document['_id']] = document

        def drop(self):
            self.quizzes.clear()
            self.quiz_results.clear()
            self.podcasts.clear()

    db = type('obj', (object,), {
        'quizzes': InMemoryQuizDB(),
        'quiz_results': {},
        'podcasts': {}
    })

# Register all blueprints
app.register_blueprint(main_bp)
app.register_blueprint(podcast_bp, url_prefix='/podcasts')
app.register_blueprint(quiz_bp, url_prefix='/quiz')
app.register_blueprint(wiki_bp, url_prefix='/wiki')
app.register_blueprint(game_bp, url_prefix='/games')
app.register_blueprint(ai_coach_bp, url_prefix='/chat')
app.register_blueprint(nutrition_bp, url_prefix='/nutrition')
app.register_blueprint(news_bp, url_prefix='/news')

if __name__ == "__main__":
    app.run(debug=True)
