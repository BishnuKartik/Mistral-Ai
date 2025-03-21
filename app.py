from flask import Flask, render_template, request, send_file
import requests
import os
from werkzeug.utils import secure_filename

app = Flask(__name__)

# Mistral AI Configuration
MISTRAL_API_KEY = "zdyXrsjZSVYMWlqSfYwVvUIquitVaMPB"  # Your Mistral API key
MISTRAL_API_URL = "https://api.mistral.ai/v1/chat/completions"
YOUR_NAME = "Bishnu Sah"  # Your name as the creator

# Background Remover API Configuration (remove.bg)
BG_REMOVER_API_KEY = "BHNR7xEYsk4fP9MttgNM4hSU"  # Your remove.bg API key
BG_REMOVER_API_URL = "https://api.remove.bg/v1.0/removebg"  # remove.bg endpoint
UPLOAD_FOLDER = 'uploads'  # Folder to store uploaded images
OUTPUT_FOLDER = 'outputs'  # Folder for processed images
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg'}  # Allowed image types

# Create folders if they don’t exist
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(OUTPUT_FOLDER, exist_ok=True)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['OUTPUT_FOLDER'] = OUTPUT_FOLDER

# Check if file extension is allowed
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# Function to ask Mistral AI or process background removal
def ask_mistral(question, file=None):
    # List of creator-related questions (case-insensitive)
    creator_questions = [
        "who is your creator", "who creates you", "who made you",
        "who built you", "who developed you"
    ]
    # Background removal trigger phrases
    bg_remove_triggers = [
        "remove background", "delete background", "clear background",
        "remove bg", "background off"
    ]

    question_lower = question.lower().strip()

    # Check if it’s a creator question
    if any(q in question_lower for q in creator_questions):
        return f"I am created by {YOUR_NAME}."

    # Check if it’s a background removal request
    elif any(trigger in question_lower for trigger in bg_remove_triggers) and file:
        if not allowed_file(file.filename):
            return "Please upload a valid image (PNG, JPG, JPEG)!"
        
        # Save the uploaded file
        filename = secure_filename(file.filename)
        input_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(input_path)

        # Call remove.bg API
        headers = {
            "X-API-Key": BG_REMOVER_API_KEY,
        }
        with open(input_path, 'rb') as image_file:
            try:
                response = requests.post(
                    BG_REMOVER_API_URL,
                    headers=headers,
                    files={'image_file': image_file},
                    data={'size': 'auto'},  # Optional: adjust size as needed
                    timeout=10
                )
                if response.status_code == 200:
                    # Save the processed image
                    output_filename = f"processed_{filename}"
                    output_path = os.path.join(app.config['OUTPUT_FOLDER'], output_filename)
                    with open(output_path, 'wb') as out_file:
                        out_file.write(response.content)
                    return f"Background removed! Download your image: <a href='/download/{output_filename}' download>Click here</a>"
                else:
                    return f"Error with background remover: {response.status_code} - {response.text}"
            except Exception as e:
                return f"Background removal failed: {str(e)}"
    elif any(trigger in question_lower for trigger in bg_remove_triggers) and not file:
        return "Please attach an image to remove its background!"

    # Normal Mistral AI response
    else:
        headers = {
            "Authorization": f"Bearer {MISTRAL_API_KEY}",
            "Content-Type": "application/json"
        }
        data = {
            "model": "mistral-medium",
            "messages": [
                {"role": "system", "content": f"You are an AI created by {YOUR_NAME}. If asked about your creator, say '{YOUR_NAME}'."},
                {"role": "user", "content": question}
            ],
            "temperature": 0.8,
            "max_tokens": 200,
            "top_p": 0.95
        }
        try:
            response = requests.post(MISTRAL_API_URL, headers=headers, json=data, timeout=10)
            if response.status_code == 200:
                answer = response.json()["choices"][0]["message"]["content"]
                if "Mistral" in answer or "mistral" in answer.lower():
                    answer = answer.replace("Mistral AI", YOUR_NAME).replace("Mistral", YOUR_NAME).replace("mistral", YOUR_NAME)
                return answer
            else:
                return f"Error: API returned status code {response.status_code}"
        except Exception as e:
            return f"API Error: {str(e)}"

# Route to display the webpage
@app.route('/')
def index():
    return render_template('index.html')

# Route to handle questions and file uploads
@app.route('/ask', methods=['POST'])
def ask():
    question = request.form.get('question', '').strip()
    file = request.files.get('attachment')
    if not question and not file:
        return "Hey, type something or attach an image!"
    response = ask_mistral(question, file)
    return response

# Route to download processed images
@app.route('/download/<filename>')
def download_file(filename):
    return send_file(os.path.join(app.config['OUTPUT_FOLDER'], filename), as_attachment=True)

if __name__ == "__main__":
    app.run(debug=True)