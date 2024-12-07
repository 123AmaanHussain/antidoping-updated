from flask import current_app
from models import db, Notification, User, NewsletterSubscription
from datetime import datetime, timedelta
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import json
import requests
import os
from threading import Thread
import logging

class NotificationService:
    def __init__(self):
        # Email configuration
        self.smtp_server = os.getenv('SMTP_SERVER', 'smtp.gmail.com')
        self.smtp_port = int(os.getenv('SMTP_PORT', 587))
        self.smtp_username = os.getenv('SMTP_USERNAME')
        self.smtp_password = os.getenv('SMTP_PASSWORD')
        
        # Firebase configuration for push notifications
        self.firebase_api_key = os.getenv('FIREBASE_API_KEY')
        self.firebase_project_id = os.getenv('FIREBASE_PROJECT_ID')
        
        # Initialize logging
        self.logger = logging.getLogger(__name__)
        
        # Test configurations
        self._test_configurations()
    
    def _test_configurations(self):
        """Test all configurations and log warnings for missing ones"""
        if not all([self.smtp_username, self.smtp_password]):
            self.logger.warning("Email configuration incomplete. Email notifications will be disabled.")
        
        if not all([self.firebase_api_key, self.firebase_project_id]):
            self.logger.warning("Firebase configuration incomplete. Push notifications will be disabled.")
    
    def send_notification(self, user_id, title, message, notification_type='info', action_url=None):
        """Send a notification to a user through all enabled channels"""
        try:
            # Create notification record
            notification = Notification(
                user_id=user_id,
                title=title,
                message=message,
                type=notification_type,
                action_url=action_url
            )
            db.session.add(notification)
            
            # Get user preferences
            user = User.query.get(user_id)
            if not user:
                return False

            # Send through enabled channels
            if user.email_notifications:
                Thread(target=self._send_email_async,
                      args=(user.email, title, message)).start()

            if user.push_notifications:
                Thread(target=self._send_push_notification,
                      args=(user_id, title, message)).start()

            db.session.commit()
            return True

        except Exception as e:
            self.logger.error(f"Notification error: {str(e)}")
            db.session.rollback()
            return False

    def send_bulk_notification(self, user_ids, title, message, notification_type='info', action_url=None):
        """Send notification to multiple users"""
        for user_id in user_ids:
            Thread(target=self.send_notification,
                  args=(user_id, title, message, notification_type, action_url)).start()

    def send_newsletter(self, frequency='daily'):
        """Send newsletter to subscribed users"""
        try:
            subscribers = NewsletterSubscription.query.filter_by(
                subscribed=True,
                frequency=frequency
            ).all()

            for subscriber in subscribers:
                if self._should_send_newsletter(subscriber):
                    content = self._generate_newsletter_content(subscriber.preferred_language)
                    Thread(target=self._send_email_async,
                          args=(subscriber.email,
                                "Your Anti-Doping Newsletter",
                                content,
                                True)).start()
                    
                    subscriber.last_sent_at = datetime.utcnow()

            db.session.commit()
            return True

        except Exception as e:
            self.logger.error(f"Newsletter error: {str(e)}")
            return False

    def _should_send_newsletter(self, subscriber):
        """Check if newsletter should be sent based on frequency"""
        if not subscriber.last_sent_at:
            return True

        time_diff = datetime.utcnow() - subscriber.last_sent_at
        
        if subscriber.frequency == 'daily':
            return time_diff.days >= 1
        elif subscriber.frequency == 'weekly':
            return time_diff.days >= 7
        elif subscriber.frequency == 'monthly':
            return time_diff.days >= 30
        
        return False

    def _generate_newsletter_content(self, language):
        """Generate newsletter content based on user's language"""
        # TODO: Implement newsletter content generation
        return "Newsletter content placeholder"

    def _send_email_async(self, recipient, subject, body, is_html=False):
        """Send email asynchronously"""
        if not all([self.smtp_username, self.smtp_password]):
            self.logger.warning("Email configuration incomplete. Skipping email notification.")
            return
        
        def send_email():
            try:
                msg = MIMEMultipart()
                msg['From'] = self.smtp_username
                msg['To'] = recipient
                msg['Subject'] = subject
                
                if is_html:
                    msg.attach(MIMEText(body, 'html'))
                else:
                    msg.attach(MIMEText(body, 'plain'))
                
                with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                    server.starttls()
                    server.login(self.smtp_username, self.smtp_password)
                    server.send_message(msg)
                    
            except Exception as e:
                self.logger.error(f"Error sending email: {str(e)}")
        
        Thread(target=send_email).start()

    def _send_push_notification(self, user_id, title, message):
        """Send push notification"""
        if not all([self.firebase_api_key, self.firebase_project_id]):
            self.logger.warning("Firebase configuration incomplete. Skipping push notification.")
            return
        
        try:
            # Get user's FCM token
            user = User.query.get(user_id)
            if not user or not hasattr(user, 'fcm_token'):
                return False

            headers = {
                'Authorization': f'key={self.firebase_api_key}',
                'Content-Type': 'application/json'
            }
            
            data = {
                'to': user.fcm_token,
                'notification': {
                    'title': title,
                    'body': message,
                    'click_action': 'FLUTTER_NOTIFICATION_CLICK',
                    'icon': 'notification_icon'
                }
            }

            response = requests.post(
                'https://fcm.googleapis.com/fcm/send',
                headers=headers,
                data=json.dumps(data)
            )

            if response.status_code != 200:
                self.logger.error(f"Push notification failed: {response.text}")
                
        except Exception as e:
            self.logger.error(f"Error sending push notification: {str(e)}")

# Initialize notification service
notification_service = NotificationService()
