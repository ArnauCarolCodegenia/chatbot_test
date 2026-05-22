import os
from flask import Flask, request, jsonify, render_template
from google import genai

app = Flask(__name__)

# Set your API key as an environment variable:
#   PowerShell: $env:GEMINI_API_KEY = "YOUR_API_KEY"
client = genai.Client(api_key=os.environ.get("GEMINI_API_KEY"))
MODEL_NAME = "gemini-2.5-flash"
chat = client.chats.create(model=MODEL_NAME)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/chat', methods=['POST'])
def chat_handler():
    user_message = request.json.get('message')
    if not user_message:
        return jsonify({"error": "No message provided"}), 400

    try:
        response = chat.send_message(user_message)
        return jsonify({"response": response.text})
    except Exception as e:
        print(f"Error communicating with Gemini API: {e}")
        return jsonify({"error": "Failed to get response from chatbot"}), 500

if __name__ == '__main__':
    app.run(debug=True)
