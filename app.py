from flask import Flask, request, jsonify

app = Flask(__name__)

@app.route('/chat', methods=['POST'])
def chat():
    user_message = request.json.get('message')
    # Here you would integrate your chatbot logic
    # For now, a simple echo response
    bot_response = f"You said: {user_message}"
    return jsonify({'response': bot_response})

@app.route('/')
def index():
    return "Chatbot is running!"

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
