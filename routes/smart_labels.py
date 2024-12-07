from flask import Blueprint, request, jsonify
import google.generativeai as genai
from PIL import Image
import io
import json
import time
import logging
from datetime import datetime

smart_labels = Blueprint('smart_labels', __name__)

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

@smart_labels.route('/analyze-product', methods=['POST'])
def analyze_product():
	logger.debug("Received analyze-product request")
	try:
		if 'image' not in request.files:
			logger.debug("No image file in request")
			return jsonify({'status': 'error', 'message': 'No image file provided'})
		
		image_file = request.files['image']
		if not image_file:
			logger.debug("Invalid image file")
			return jsonify({'status': 'error', 'message': 'Invalid image file'})
		
		logger.debug(f"Processing image: {image_file.filename}")
		
		# Read and process the image
		image_bytes = image_file.read()
		image = Image.open(io.BytesIO(image_bytes))
		
		logger.debug("Image opened successfully")
		
		# Initialize Gemini Pro Vision model
		model = genai.GenerativeModel('gemini-pro-vision')
		logger.debug("Gemini model initialized")
		
		# Define the WADA prohibited substances list prompt
		wada_prompt = """You are an expert Anti-Doping analyst. Analyze this product image and identify any ingredients that may be prohibited in sports according to WADA (World Anti-Doping Agency) guidelines.

		Please analyze the following aspects:
		1. Identify all visible ingredients
		2. Cross-reference with WADA prohibited list
		3. Classify each ingredient as:
		   - PROHIBITED: Banned at all times
		   - IN-COMPETITION: Prohibited during competition
		   - THRESHOLD: Permitted but with quantity limits
		   - SAFE: Not on prohibited list
		4. Provide specific warnings for:
		   - Stimulants
		   - Anabolic agents
		   - Hormone modulators
		   - Masking agents
		   - Beta-2 agonists
		   - Peptide hormones
		   - Diuretics
		5. Include competition withdrawal periods if applicable

		Format the response as JSON with:
		{
			"product_name": "detected product name",
			"ingredients_analysis": [
				{
					"name": "ingredient name",
					"status": "PROHIBITED/IN-COMPETITION/THRESHOLD/SAFE",
					"category": "substance category if applicable",
					"warning": "detailed warning message",
					"withdrawal_period": "time period if applicable"
				}
			],
			"overall_assessment": {
				"risk_level": "HIGH/MEDIUM/LOW",
				"competition_status": "PROHIBITED/CAUTION/SAFE",
				"warning_message": "overall warning message"
			},
			"recommendations": [
				"list of specific recommendations"
			]
		}"""
		
		# Analyze with retry logic
		max_retries = 3
		retry_delay = 5
		
		for attempt in range(max_retries):
			try:
				response = model.generate_content([wada_prompt, image])
				
				try:
					# Parse and validate the response
					analysis = json.loads(response.text)
					
					# Add timestamp and confidence level
					analysis['analysis_timestamp'] = datetime.utcnow().isoformat()
					analysis['analysis_version'] = '2.0'
					
					# Store analysis in MongoDB for future reference
					db.product_analyses.insert_one({
						'analysis': analysis,
						'image_filename': image_file.filename,
						'timestamp': datetime.utcnow(),
						'status': 'completed'
					})
					
					return jsonify({
						'status': 'success',
						'analysis': analysis,
						'message': 'Analysis completed successfully'
					})
					
				except json.JSONDecodeError:
					logger.warning(f"Invalid JSON response: {response.text}")
					if attempt < max_retries - 1:
						time.sleep(retry_delay)
						continue
					return jsonify({
						'status': 'error',
						'message': 'Unable to process the response. Please try again.'
					})
					
			except Exception as e:
				error_message = str(e).lower()
				if "rate limit exceeded" in error_message and attempt < max_retries - 1:
					logger.warning(f"Rate limit hit, attempt {attempt + 1}/{max_retries}. Waiting {retry_delay} seconds...")
					time.sleep(retry_delay)
					retry_delay *= 2
					continue
				else:
					raise
		
		return jsonify({
			'status': 'error',
			'message': 'Maximum retry attempts reached. Please try again later.'
		})
		
	except Exception as e:
		logger.error(f"Error analyzing product: {str(e)}")
		return jsonify({
			'status': 'error',
			'message': 'Error analyzing product. Please try again.',
			'error_details': str(e)
		})