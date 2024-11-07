# from flask import flask,redirect,request,jsonify
# from flask_pymongo import PyMongo
# import datetime 

# app = Flask(__name__)

# app.config["MONGO_URI"] = "mongodb+srv://amaanhussain:h5VkBlsEmCReD79E@cluster0.oifmm.mongodb.net/"
# mongo = PyMongo(app)

# @app.route('/')
# def index():
#     return 'Welcome to the Anti Doping Education Platform!'

# @app.route('/add_athlete_data',methods=['POST'])
from flask import Flask
from flask_pymongo import PyMongo
from flask import Flask, render_template

app = Flask(__name__)

# MongoDB Atlas connection string
app.config["MONGO_URI"] = "mongodb+srv://amaanhussain:h5VkBlsEmCReD79E@cluster0.oifmm.mongodb.net/"
mongo = PyMongo(app)

app = Flask(__name__)

@app.route('/')
def home():
    return render_template('home.html')

@app.route('/podcasts')
def podcasts_page():
    return render_template('podcasts.html')

@app.route('/anti_doping')
def anti_doping_page():
    return render_template('anti_doping.html')

if __name__ == '__main__':
    app.run(debug=True)

