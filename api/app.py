import os
import time
from flask import Flask, jsonify, request, send_from_directory
from flask_cors import CORS
from dotenv import load_dotenv
import openai
from face_utils import analyze_face

# Initialize Flask app
app = Flask(__name__)
CORS(app, resources={r"/api/*": {"origins": "*"}})  # Allow CORS for all API routes
load_dotenv()

# Configuration
app.config['UPLOAD_FOLDER'] = 'static/uploads'
app.config['MAX_CONTENT_LENGTH'] = 4 * 1024 * 1024  # 4MB file size limit
openai.api_key = os.getenv('OPENAI_API_KEY')

# Ensure upload folder exists
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

def generate_analysis_summary(scores):
    """Generate analysis summary using OpenAI"""
    prompt = f"""Analyze these facial feature scores (1-10 scale):
    {scores}
    
    Provide a constructive summary including:
    1. Overall first impression
    2. Top 2 strengths
    3. 1-2 areas for improvement
    4. Practical beauty tips
    Use friendly, encouraging tone."""
    
    try:
        response = openai.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=300
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        print(f"OpenAI Error: {str(e)}")
        return "Could not generate summary due to an error"

@app.route('/api/upload', methods=['POST'])
def upload_file():
    """Handle file upload and facial analysis"""
    if 'file' not in request.files:
        return jsonify({'error': 'No file uploaded'}), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'Empty filename'}), 400
    
    # Save the file
    filename = f"upload_{int(time.time())}_{file.filename}"
    filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    file.save(filepath)
    
    # Analyze the face
    features = analyze_face(filepath)
    if not features:
        return jsonify({'error': 'Face analysis failed'}), 500
    
    return jsonify({
        'imgPath': f'/static/uploads/{filename}',
        'features': features
    })

@app.route('/api/generate-summary', methods=['POST'])
def generate_summary():
    """Generate summary from facial scores"""
    try:
        data = request.get_json()
        if not data or 'scores' not in data:
            return jsonify({'error': 'Missing scores data'}), 400
            
        summary = generate_analysis_summary(data['scores'])
        return jsonify({'summary': summary})
        
    except Exception as e:
        print(f"Summary Error: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/static/uploads/<path:filename>')
def serve_upload(filename):
    """Serve uploaded files"""
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

if __name__ == '__main__':
    app.run(debug=False)  # Disable debug mode in production