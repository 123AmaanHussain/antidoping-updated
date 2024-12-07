from flask import session, current_app
from models import Translation, db
from googletrans import Translator
import json
import os

# Supported languages with their codes and names
SUPPORTED_LANGUAGES = {
    'en': 'English',
    'hi': 'हिंदी',  # Hindi
    'bn': 'বাংলা',  # Bengali
    'te': 'తెలుగు',  # Telugu
    'ta': 'தமிழ்',  # Tamil
    'mr': 'मराठी',  # Marathi
    'gu': 'ગુજરાતી',  # Gujarati
    'kn': 'ಕನ್ನಡ',  # Kannada
    'ml': 'മലയാളം',  # Malayalam
    'pa': 'ਪੰਜਾਬੀ',  # Punjabi
}

class TranslationService:
    def __init__(self):
        self.translator = Translator()
        self.cache = {}
        self._load_cache()

    def _load_cache(self):
        """Load translations from database into cache"""
        translations = Translation.query.all()
        for trans in translations:
            cache_key = f"{trans.key}:{trans.language}"
            self.cache[cache_key] = trans.content

    def translate(self, text, target_lang='en', source_lang=None):
        """Translate text to target language"""
        if target_lang == 'en':
            return text

        # Check cache first
        cache_key = f"{text}:{target_lang}"
        if cache_key in self.cache:
            return self.cache[cache_key]

        try:
            # Try to get from database
            translation = Translation.query.filter_by(
                key=text,
                language=target_lang
            ).first()

            if translation:
                self.cache[cache_key] = translation.content
                return translation.content

            # If not in database, use Google Translate
            result = self.translator.translate(text, dest=target_lang, src=source_lang)
            
            # Store in database and cache
            new_translation = Translation(
                key=text,
                language=target_lang,
                content=result.text
            )
            db.session.add(new_translation)
            db.session.commit()

            self.cache[cache_key] = result.text
            return result.text

        except Exception as e:
            current_app.logger.error(f"Translation error: {str(e)}")
            return text  # Return original text if translation fails

    def get_language_name(self, lang_code):
        """Get the display name of a language code"""
        return SUPPORTED_LANGUAGES.get(lang_code, 'Unknown')

    def get_supported_languages(self):
        """Get list of supported languages"""
        return SUPPORTED_LANGUAGES

# Initialize translation service
translation_service = TranslationService()

def translate_text(text, target_lang=None):
    """Utility function to translate text"""
    if target_lang is None:
        target_lang = session.get('language', 'en')
    return translation_service.translate(text, target_lang)

# Template filter for easy translation in templates
def register_template_filters(app):
    @app.template_filter('translate')
    def translate_filter(text):
        return translate_text(text)
