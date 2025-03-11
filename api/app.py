import os
import time
from flask import Flask, jsonify, request, send_from_directory
from flask_cors import CORS
from dotenv import load_dotenv
import openai
from face_utils import analyze_face

app = Flask(__name__)
CORS(app)
load_dotenv()

app.config['UPLOAD_FOLDER'] = 'static/uploads'
openai.api_key = os.getenv('OPENAI_API_KEY')

def generate_analysis_summary(scores):
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
@app.route('/api/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return jsonify({'error': 'No file uploaded'}), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'Empty filename'}), 400
    
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
    filename = f"upload_{int(time.time())}_{file.filename}"
    filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    file.save(filepath)
    
    features = analyze_face(filepath)
    if not features:
        return jsonify({'error': 'Face analysis failed'}), 500
    
    return jsonify({
        'imgPath': f'/static/uploads/{filename}',
        'features': features
    })

@app.route('/api/generate-summary', methods=['POST'])
def generate_summary():
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
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

if __name__ == '__main__':
    app.run(debug=True)