from datetime import datetime
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin

db = SQLAlchemy()

def init_db(app):
    db.init_app(app)

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(128))
    role = db.Column(db.String(20), default='user')  # athlete, coach, admin
    preferred_language = db.Column(db.String(5), default='en')  # Language code
    notifications_enabled = db.Column(db.Boolean, default=True)
    email_notifications = db.Column(db.Boolean, default=True)
    push_notifications = db.Column(db.Boolean, default=True)
    push_subscription = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    last_login = db.Column(db.DateTime)
    
    # Relationships
    notifications = db.relationship('Notification', backref='user', lazy=True)
    progress = db.relationship('UserProgress', backref='user', lazy=True)
    feedback = db.relationship('UserFeedback', backref='user', lazy=True)

class Notification(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    title = db.Column(db.String(200), nullable=False)
    message = db.Column(db.Text, nullable=False)
    type = db.Column(db.String(50))  # news, alert, reminder
    read = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    action_url = db.Column(db.String(500))  # Optional URL for notification action

class UserProgress(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    module = db.Column(db.String(100), nullable=False)
    score = db.Column(db.Float)
    completed = db.Column(db.Boolean, default=False)
    time_spent = db.Column(db.Integer)  # Time spent in seconds
    completed_at = db.Column(db.DateTime)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class UserFeedback(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    content_type = db.Column(db.String(50))  # article, video, quiz, etc.
    content_id = db.Column(db.Integer)
    rating = db.Column(db.Integer)  # 1-5 rating
    comment = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class Translation(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    key = db.Column(db.String(500), nullable=False)
    language = db.Column(db.String(5), nullable=False)  # Language code
    content = db.Column(db.Text, nullable=False)
    context = db.Column(db.String(100))  # Optional context for the translation
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, onupdate=datetime.utcnow)

    __table_args__ = (db.UniqueConstraint('key', 'language', name='unique_translation'),)

class NewsletterSubscription(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    name = db.Column(db.String(100))
    subscribed = db.Column(db.Boolean, default=True)
    preferred_language = db.Column(db.String(5), default='en')
    frequency = db.Column(db.String(20), default='weekly')  # daily, weekly, monthly
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    last_sent_at = db.Column(db.DateTime)

class VideoContent(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    url = db.Column(db.String(500), nullable=False)
    thumbnail_url = db.Column(db.String(500))
    duration = db.Column(db.Integer)  # Duration in seconds
    category = db.Column(db.String(50))
    language = db.Column(db.String(5))
    views = db.Column(db.Integer, default=0)
    likes = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class ForumTopic(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    content = db.Column(db.Text, nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    category = db.Column(db.String(50))
    views = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, onupdate=datetime.utcnow)
    
    # Relationships
    replies = db.relationship('ForumReply', backref='topic', lazy=True)

class ForumReply(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    topic_id = db.Column(db.Integer, db.ForeignKey('forum_topic.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    content = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, onupdate=datetime.utcnow)

class UserAnalytics(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    page_visited = db.Column(db.String(200))
    time_spent = db.Column(db.Integer)  # Time spent in seconds
    interaction_type = db.Column(db.String(50))  # click, scroll, submit, etc.
    device_type = db.Column(db.String(50))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
