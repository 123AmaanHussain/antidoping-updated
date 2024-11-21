from flask import Flask, render_template, request, jsonify, send_file
from flask_pymongo import PyMongo
from flask_cors import CORS
from transformers import AutoModelForCausalLM, AutoTokenizer
from pymongo import MongoClient
from fpdf import FPDF
from newsapi import NewsApiClient
import random
import os
from datetime import datetime, timedelta
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

app = Flask(__name__, static_folder="static")
app.secret_key = os.getenv('FLASK_SECRET_KEY')
CORS(app)

# Initialize News API
newsapi = NewsApiClient(api_key=os.getenv('NEWS_API_KEY'))

# MongoDB configurations
app.config["MONGO_URI"] = os.getenv('MONGO_URI')
mongo = PyMongo(app)
client = MongoClient(os.getenv('MONGO_URI'))
db = client['gamified_quizzes']

# AI model configuration
model_name = "microsoft/DialoGPT-medium"
tokenizer = AutoTokenizer.from_pretrained(model_name)
model = AutoModelForCausalLM.from_pretrained(model_name)

# Certificate configuration
CERTIFICATE_DIR = "certificates"
os.makedirs(CERTIFICATE_DIR, exist_ok=True)

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
        print(f"Error fetching news: {str(e)}")
        import traceback
        print(f"Full error traceback: {traceback.format_exc()}")
        
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

# Quiz related routes
@app.route('/get_quiz/<quiz_id>', methods=['GET'])
def get_quiz(quiz_id):
    quiz = db.quizzes.find_one({"quiz_id": quiz_id}, {"_id": 0})
    if quiz:
        return jsonify(quiz), 200
    return jsonify({"error": "Quiz not found"}), 404

@app.route("/submit_quiz", methods=["POST"])
def submit_quiz():
    data = request.json
    quiz_id = data.get("quiz_id")
    user_id = data.get("user_id")
    answers = data.get("answers")

    if not quiz_id or not user_id or not answers:
        return jsonify({"error": "Missing required fields"}), 400

    quiz = db.quizzes.find_one({"quiz_id": quiz_id})
    if not quiz:
        return jsonify({"error": "Quiz not found"}), 404

    score = 0
    correct_options = [q['correct_option'] for q in quiz["questions"]]
    for idx, correct_option in enumerate(correct_options):
        if idx < len(answers) and answers[idx] == correct_option:
            score += quiz["points_per_question"]

    pass_threshold = len(quiz["questions"]) * quiz["points_per_question"] * 0.8
    if score >= pass_threshold:
        quiz_title = quiz["title"]
        date = "2024-11-21"

        certificate_path = generate_certificate_pdf(
            user_id, quiz_title, score, date, f"{CERTIFICATE_DIR}/{user_id}_{quiz_id}_certificate.pdf"
        )

        db.scores.insert_one({
            "user_id": user_id,
            "quiz_id": quiz_id,
            "score": score,
            "status": "Passed"
        })

        return jsonify({
            "message": "Quiz submitted successfully!",
            "score": score,
            "certificate": f"/download_certificate/{user_id}/{quiz_id}"
        }), 200

    db.scores.insert_one({
        "user_id": user_id,
        "quiz_id": quiz_id,
        "score": score,
        "status": "Failed"
    })
    
    return jsonify({
        "message": "Quiz submitted, but score below passing threshold",
        "score": score
    }), 200

def generate_certificate_pdf(user_id, quiz_title, score, date, filename):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=16)
    pdf.cell(200, 10, txt="Certificate of Completion", ln=1, align='C')
    pdf.set_font("Arial", size=12)
    pdf.cell(200, 10, txt=f"This certifies that {user_id}", ln=1, align='C')
    pdf.cell(200, 10, txt=f"has completed the quiz: {quiz_title}", ln=1, align='C')
    pdf.cell(200, 10, txt=f"with a score of {score}", ln=1, align='C')
    pdf.cell(200, 10, txt=f"Date: {date}", ln=1, align='C')
    pdf.output(filename)
    return filename

@app.route("/download_certificate/<user_id>/<quiz_id>")
def download_certificate(user_id, quiz_id):
    filename = f"{CERTIFICATE_DIR}/{user_id}_{quiz_id}_certificate.pdf"
    return send_file(filename, as_attachment=True)

@app.route("/get_progress/<user_id>")
def get_progress(user_id):
    progress = list(db.scores.find({"user_id": user_id}, {"_id": 0}))
    return jsonify(progress)

@app.route("/anti_doping")
def anti_doping_page():
    return render_template('anti_doping.html')

if __name__ == "__main__":
    app.run(debug=True)
