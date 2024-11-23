from flask import Flask, render_template, request, jsonify, send_file, send_from_directory
from flask_cors import CORS
from pymongo import MongoClient
from fpdf import FPDF
from newsapi import NewsApiClient
import random
import os
from datetime import datetime, timedelta
from blockchain_service import BlockchainService
from web3 import Web3
import json
from dotenv import load_dotenv
import logging
import time
import requests
import google.generativeai as genai
from bson import ObjectId

# Load environment variables
load_dotenv()

# Directly set the API key
GOOGLE_API_KEY = "AIzaSyAKVHyZrJB36-fa1t_nXO_-BcCyUJlO88g"
print(f"API Key loaded: {'[MASKED]' if GOOGLE_API_KEY else 'None'}")

app = Flask(__name__, static_folder="static")
app.secret_key = os.getenv('FLASK_SECRET_KEY', 'your-secret-key-here')
CORS(app)

client = MongoClient(os.getenv('MONGO_URI', 'mongodb://localhost:27017/'))
db = client['gamified_quizzes']
nutrition_plans = db.nutrition_plans

# Initialize logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[
        logging.FileHandler('antidoping.log'),
        logging.StreamHandler()
    ]
)

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

# Initialize MongoDB with quiz data
def init_quiz_data():
    try:
        # Drop existing quiz data to ensure clean state
        db.quizzes.drop()
        
        sample_quiz = {
            "quiz_id": "quiz1",
            "title": "Anti-Doping Basics",
            "questions": [
                {
                    "text": "What is WADA?",
                    "options": [
                        "World Athletics Development Association",
                        "World Anti-Doping Agency",
                        "World Athletics Doping Authority",
                        "World Agency for Doping Analysis"
                    ],
                    "correct_answer": 1
                },
                {
                    "text": "Which of these is a prohibited substance?",
                    "options": [
                        "Vitamin C",
                        "Caffeine",
                        "Anabolic Steroids",
                        "Protein Powder"
                    ],
                    "correct_answer": 2
                },
                {
                    "text": "How often should athletes check the prohibited substances list?",
                    "options": [
                        "Once a year",
                        "Every 6 months",
                        "Only when prescribed new medication",
                        "Regularly, as it's updated frequently"
                    ],
                    "correct_answer": 3
                }
            ]
        }
        
        result = db.quizzes.insert_one(sample_quiz)
        logging.info(f"Initialized quiz data with ID: {result.inserted_id}")
        return True
    except Exception as e:
        logging.error(f"Error initializing quiz data: {str(e)}")
        return False

# Initialize quiz data
if not init_quiz_data():
    logging.error("Failed to initialize quiz data")

# Quiz data - you can expand this with more questions
QUIZ_DATA = {
    'quiz': {
        'quiz_id': 'antidoping_basics',
        'title': 'Anti-Doping Basics Quiz',
        'questions': [
            {
                'text': 'What is the main purpose of anti-doping regulations?',
                'options': [
                    'To ensure fair competition and protect athlete health',
                    'To make sports more entertaining',
                    'To increase athletic performance',
                    'To reduce sports participation'
                ],
                'correct': 0
            },
            {
                'text': 'Which organization is responsible for the World Anti-Doping Code?',
                'options': [
                    'FIFA',
                    'IOC',
                    'WADA',
                    'UEFA'
                ],
                'correct': 2
            },
            {
                'text': 'What is a "prohibited substance"?',
                'options': [
                    'Any substance that enhances performance',
                    'Substances listed on the WADA Prohibited List',
                    'Illegal drugs only',
                    'Substances chosen by sports federations'
                ],
                'correct': 1
            },
            {
                'text': 'How often is the WADA Prohibited List updated?',
                'options': [
                    'Monthly',
                    'Every six months',
                    'Annually',
                    'Every two years'
                ],
                'correct': 2
            },
            {
                'text': 'What is a TUE in anti-doping?',
                'options': [
                    'Technical Use Exemption',
                    'Therapeutic Use Exemption',
                    'Temporary Use Exception',
                    'Training Under Examination'
                ],
                'correct': 1
            }
        ]
    }
}

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
    return render_template("smartlabels.html")

@app.route('/antidopingwiki')
def antidopingwiki():
    global news_cache
    current_time = datetime.now()
    
    # Check if we have cached news that's less than 30 minutes old
    if (news_cache['last_update'] and 
        news_cache['data'] and 
        (current_time - news_cache['last_update']).total_seconds() < 1800):
        return render_template('antidopingwiki.html', news=news_cache['data'])
    
    # Get news about sports and doping
    all_news = []
    try:
        # Get news about doping in sports
        doping_news = newsapi.get_everything(
            q='doping sports athletics',
            language='en',
            sort_by='publishedAt',
            from_param=(datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d'),
            page_size=10
        )
        
        # Get general sports news
        sports_news = newsapi.get_top_headlines(
            category='sports',
            language='en',
            page_size=10
        )
        
        # Process doping news
        if doping_news.get('status') == 'ok' and doping_news.get('articles'):
            for article in doping_news['articles']:
                if article.get('title') and article.get('description'):
                    all_news.append({
                        'title': article.get('title', ''),
                        'description': article.get('description', ''),
                        'url': article.get('url', '#'),
                        'image': article.get('urlToImage', None),
                        'publishedAt': datetime.strptime(article.get('publishedAt', datetime.now().isoformat()), 
                                                       '%Y-%m-%dT%H:%M:%SZ').strftime('%B %d, %Y'),
                        'source': article.get('source', {}).get('name', 'Unknown Source'),
                        'category': 'Doping News'
                    })
            
        # Process sports news
        if sports_news.get('status') == 'ok' and sports_news.get('articles'):
            for article in sports_news['articles']:
                if article.get('title') and article.get('description'):
                    all_news.append({
                        'title': article.get('title', ''),
                        'description': article.get('description', ''),
                        'url': article.get('url', '#'),
                        'image': article.get('urlToImage', None),
                        'publishedAt': datetime.strptime(article.get('publishedAt', datetime.now().isoformat()),
                                                       '%Y-%m-%dT%H:%M:%SZ').strftime('%B %d, %Y'),
                        'source': article.get('source', {}).get('name', 'Unknown Source'),
                        'category': 'Sports News'
                    })
        
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
                    'title': 'Sample Sports News',
                    'description': 'This is a sample sports news article. The news API might be temporarily unavailable.',
                    'url': '#',
                    'image': None,
                    'publishedAt': datetime.now().strftime('%B %d, %Y'),
                    'source': 'Sample Source',
                    'category': 'Sports News'
                },
                {
                    'title': 'Sample Doping News',
                    'description': 'This is a sample doping news article. The news API might be temporarily unavailable.',
                    'url': '#',
                    'image': None,
                    'publishedAt': datetime.now().strftime('%B %d, %Y'),
                    'source': 'Sample Source',
                    'category': 'Doping News'
                }
            ]
    
    return render_template('antidopingwiki.html', news=all_news)

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
        logging.info(f"Fetching quiz with ID: {quiz_id}")  # Debug log
        quiz = db.quizzes.find_one({"quiz_id": quiz_id}, {"_id": 0})
        logging.info(f"Found quiz: {quiz}")  # Debug log
        
        if not quiz:
            # Try to initialize quiz data
            if init_quiz_data():
                quiz = db.quizzes.find_one({"quiz_id": quiz_id}, {"_id": 0})
        
        if quiz:
            return jsonify(quiz)
        return jsonify({"error": "Quiz not found"}), 404
    except Exception as e:
        logging.error(f"Error getting quiz: {str(e)}")
        return jsonify({"error": str(e)}), 500

def generate_pdf_certificate(user_id, quiz_id, score, timestamp):
    """Generate a PDF certificate for quiz completion"""
    try:
        # Create certificates directory if it doesn't exist
        certificate_dir = os.path.join(os.path.dirname(__file__), 'certificates')
        os.makedirs(certificate_dir, exist_ok=True)
        
        # Initialize PDF
        pdf = FPDF()
        pdf.add_page()
        
        # Add certificate styling
        pdf.set_font("Arial", "B", 24)
        pdf.set_text_color(44, 62, 80)  # Dark blue color
        pdf.cell(0, 30, "Certificate of Achievement", ln=True, align='C')
        
        # Add logo if exists
        logo_path = os.path.join(os.path.dirname(__file__), 'static', 'images', 'logo.png')
        if os.path.exists(logo_path):
            pdf.image(logo_path, x=85, y=50, w=40)
        
        # Certificate content
        pdf.set_font("Arial", "", 16)
        pdf.ln(60)  # Add some space after logo
        pdf.cell(0, 10, "This is to certify that", ln=True, align='C')
        
        pdf.set_font("Arial", "B", 18)
        pdf.cell(0, 15, f"User ID: {user_id}", ln=True, align='C')
        
        pdf.set_font("Arial", "", 16)
        pdf.cell(0, 10, "has successfully completed the", ln=True, align='C')
        pdf.cell(0, 10, "Anti-Doping Awareness Quiz", ln=True, align='C')
        pdf.cell(0, 10, f"with a score of {score}%", ln=True, align='C')
        
        # Add date
        pdf.set_font("Arial", "I", 14)
        pdf.cell(0, 20, f"Date: {timestamp.strftime('%B %d, %Y')}", ln=True, align='C')
        
        # Add verification text
        pdf.set_font("Arial", "", 10)
        pdf.set_text_color(128, 128, 128)  # Gray color
        pdf.cell(0, 10, "This certificate's authenticity can be verified on the blockchain", ln=True, align='C')
        
        # Generate unique filename
        filename = f"{user_id}_{quiz_id}_{timestamp.strftime('%Y%m%d_%H%M%S')}.pdf"
        filepath = os.path.join(certificate_dir, filename)
        
        # Save PDF
        pdf.output(filepath)
        return filepath
        
    except Exception as e:
        app.logger.error(f"Error generating PDF certificate: {str(e)}")
        raise

@app.route('/submit_quiz', methods=['POST'])
def submit_quiz():
    try:
        data = request.get_json()
        
        # Validate required fields
        required_fields = ['user_id', 'quiz_id', 'answers', 'wallet_address']
        for field in required_fields:
            if field not in data:
                raise ValueError(f"Missing required field: {field}")

        user_id = data['user_id']
        quiz_id = data['quiz_id']
        answers = data['answers']
        wallet_address = data['wallet_address']

        # Get quiz data
        quiz = db.quizzes.find_one({"quiz_id": quiz_id}, {"_id": 0})
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
            'wallet_address': wallet_address,
            'timestamp': timestamp
        }
        
        # Generate certificate data if passing score
        certificate_data = None
        if score >= 70:
            try:
                # Generate PDF certificate
                pdf_path = generate_pdf_certificate(user_id, quiz_id, score, timestamp)
                
                # Store certificate path
                quiz_result['pdf_certificate'] = os.path.basename(pdf_path)
                
                # Generate certificate metadata
                metadata = {
                    'user_id': user_id,
                    'quiz_id': quiz_id,
                    'score': score,
                    'timestamp': timestamp.isoformat()
                }
                
                # Attempt to mint blockchain certificate
                token_id = None
                try:
                    token_id = blockchain_service.mint_certificate(
                        recipient_address=wallet_address,
                        quiz_title=quiz['title'],
                        score=int(score)
                    )
                except Exception as e:
                    app.logger.error(f"Error minting blockchain certificate: {str(e)}")
                
                certificate_data = {
                    'token_id': token_id,
                    'metadata': metadata,
                    'pdf_path': os.path.basename(pdf_path)
                }
                
                quiz_result['certificate'] = certificate_data
                
            except Exception as e:
                app.logger.error(f"Error generating certificate: {str(e)}")
                certificate_data = {'error': str(e)}
        
        # Store result in database
        db.quiz_results.insert_one(quiz_result)

        return jsonify({
            'success': True,
            'score': score,
            'certificate': certificate_data
        })

    except Exception as e:
        app.logger.error(f"Error submitting quiz: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/download_certificate/<user_id>/<filename>')
def download_certificate(user_id, filename):
    try:
        # Security check: ensure filename belongs to the user
        if not filename.startswith(f"{user_id}_"):
            raise ValueError("Invalid certificate access")
            
        certificate_dir = os.path.join(os.path.dirname(__file__), 'certificates')
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
        scores = list(db.scores.find({"user_id": user_id}, {"_id": 0}))
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

def calculate_score(user_answers, correct_answers):
    """Calculate the percentage score for a quiz"""
    if len(user_answers) != len(correct_answers):
        raise ValueError("Answer length mismatch")
    
    correct_count = sum(1 for user_ans, correct_ans in zip(user_answers, correct_answers) if user_ans == correct_ans)
    return (correct_count / len(correct_answers)) * 100

if __name__ == "__main__":
    app.run(debug=True)
