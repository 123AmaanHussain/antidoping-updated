from flask import Flask, render_template, request, jsonify, send_file, send_from_directory
from flask_cors import CORS
from pymongo import MongoClient
from transformers import AutoModelForCausalLM, AutoTokenizer
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

# Load environment variables
load_dotenv()

app = Flask(__name__, static_folder="static")
app.secret_key = os.getenv('FLASK_SECRET_KEY', 'your-secret-key-here')
CORS(app)

client = MongoClient(os.getenv('MONGO_URI', 'mongodb://localhost:27017/'))
db = client['gamified_quizzes']

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
    logging.error(f"Failed to initialize blockchain service: {str(e)}")
    raise

# AI model configuration
model_name = "microsoft/DialoGPT-medium"
tokenizer = AutoTokenizer.from_pretrained(model_name)
model = AutoModelForCausalLM.from_pretrained(model_name)

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

# Response templates for AI coach
RESPONSE_TEMPLATES = {
    "anti_doping": [
        "As your anti-doping advisor, it's important to avoid substances on the WADA (World Anti-Doping Agency) prohibited list. Always consult the latest resources and check your supplements carefully. If you're unsure about an ingredient, consider talking to an expert.",
        "Avoid supplements with unfamiliar ingredients, as they might contain banned substances. Staying informed and regularly checking the WADA website can help you stay compliant and protect your career.",
        "An athlete's career can be affected by accidental doping violations. Stick to trusted supplements, and avoid any that aren't thoroughly researched or that have unknown ingredients.",
        "Always stay informed about banned substances. Consult with a medical professional or a doping advisor to ensure all supplements you use are safe and legal."
    ],
    "fitness": [
        "For effective fitness training, balance cardio with strength exercises. Include endurance training, but also dedicate time to strength work to build core stability and power.",
        "To build endurance, try interval training or long-distance running. Combine this with weight training to enhance your overall athletic ability.",
        "Aim to work out at least three times a week, and don't forget to stretch before and after your sessions. Stretching helps with flexibility and can prevent injuries.",
        "Remember to allow for rest days between intense workouts. Rest days are crucial for muscle recovery and long-term progress. Pacing yourself will prevent burnout and help you stay consistent."
    ],
    "health": [
        "A balanced diet is crucial for peak performance. Focus on high-quality proteins, complex carbohydrates, and healthy fats to fuel your body effectively.",
        "Stay hydrated, especially during intense training periods. Dehydration can impair performance, so keep a water bottle handy throughout the day.",
        "Good mental health is essential. Consider incorporating practices like mindfulness, meditation, or journaling to manage stress and improve focus.",
        "Sleep is one of the most important factors in recovery. Aim for 7-9 hours of quality sleep each night to allow your body to repair and prepare for the next training session."
    ],
    "motivation": [
        "Staying motivated as an athlete can be challenging. Set small, achievable goals and celebrate each accomplishment to keep yourself encouraged.",
        "Focus on the reasons why you started. Visualize your long-term goals and remind yourself of the progress you've made to stay motivated.",
        "Surround yourself with supportive people, whether teammates, friends, or family. A positive environment can boost your motivation and make training enjoyable.",
        "Consistency is key to success. Even on days when motivation is low, sticking to your routine will help you stay on track and achieve your goals over time."
    ],
    "general": [
        "I'm here to assist you with fitness, health, anti-doping, and motivation. You can ask specific questions in any of these areas!",
        "Ask me about fitness training, dietary advice, motivation tips, or guidance on anti-doping best practices for athletes.",
        "I can help with tips on fitness, health, anti-doping, and motivation. Let me know which area you're interested in!"
    ]
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

@app.route("/ai_coach")
def ai_coach():
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

# AI Coach response generation
def generate_response(user_input):
    if "doping" in user_input or "substance" in user_input:
        response = random.choice(RESPONSE_TEMPLATES["anti_doping"])
    elif "fitness" in user_input or "training" in user_input:
        response = random.choice(RESPONSE_TEMPLATES["fitness"])
    elif "health" in user_input or "nutrition" in user_input or "diet" in user_input:
        response = random.choice(RESPONSE_TEMPLATES["health"])
    elif "motivate" in user_input or "goal" in user_input or "discouraged" in user_input:
        response = random.choice(RESPONSE_TEMPLATES["motivation"])
    else:
        response = random.choice(RESPONSE_TEMPLATES["general"])
    return response

@app.route("/get_response", methods=["POST"])
def get_response():
    user_text = request.form["msg"]
    response = generate_response(user_text)
    return jsonify(response)

def calculate_score(user_answers, correct_answers):
    """Calculate the percentage score for a quiz"""
    if len(user_answers) != len(correct_answers):
        raise ValueError("Answer length mismatch")
    
    correct_count = sum(1 for user_ans, correct_ans in zip(user_answers, correct_answers) if user_ans == correct_ans)
    return (correct_count / len(correct_answers)) * 100

if __name__ == "__main__":
    app.run(debug=True)
