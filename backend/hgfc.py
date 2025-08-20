import os
import json
import datetime
import numpy as np
import librosa
import bcrypt
import jwt
import torch
from flask import Flask, request, jsonify , redirect
from flask_cors import CORS
from transformers import Wav2Vec2ForSequenceClassification, AutoFeatureExtractor
from pydub import AudioSegment
import io
import requests
import urllib.parse

# Spotify API Credentials
SPOTIFY_CLIENT_ID = "d5eda56afcbf4ecbafef48fe3db8168c"
SPOTIFY_CLIENT_SECRET = "5694184341e04cd0817da569ad0dc3d8"

# -------------------- Setup --------------------
app = Flask(__name__)

# Enhanced CORS configuration
CORS(app, resources={
    r"/*": {
        "origins": ["http://127.0.0.1:5500", "http://localhost:5500", "http://127.0.0.1:3000", "http://localhost:3000"],
        "methods": ["GET", "POST", "OPTIONS"],
        "allow_headers": ["Content-Type", "Authorization"]
    }
})

app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'your_default_secret_key')
app.config['JWT_SECRET_KEY'] = os.getenv('JWT_SECRET_KEY', 'your_default_jwt_secret_key')

# -------------------- Load Emotion Model --------------------
print(" Loading emotion recognition model...")
try:
    feature_extractor = AutoFeatureExtractor.from_pretrained("ehcalabres/wav2vec2-lg-xlsr-en-speech-emotion-recognition")
    model = Wav2Vec2ForSequenceClassification.from_pretrained("ehcalabres/wav2vec2-lg-xlsr-en-speech-emotion-recognition")
    model.eval()
    print(" Model loaded successfully!")
except Exception as e:
    print(f" Error loading model: {e}")
    print("  Make sure you have transformers and torch installed")

# -------------------- Emotion Mapping & Playlists --------------------
emotion_map = {
    "angry": "angry",
    "disgust": "disgust",
    "fearful": "fearful",
    "happy": "happy",
    "neutral": "neutral",
    "sad": "sad",
    "surprised": "surprised",
    "calm": "calm"
}

# Emotion to playlist mapping
emotion_playlists = {
    "happy": {
        "name": "Feel-Good Hits",
        "url": "https://open.spotify.com/playlist/37i9dQZF1DXdPec7aLTmlC",
    },
    "sad": {
        "name": "Sad Vibes",
        "url": "https://open.spotify.com/playlist/37i9dQZF1DX7qK8ma5wgG1",
    },
    "neutral": {
        "name": "Lo-Fi Chill",
        "url": "https://open.spotify.com/playlist/37i9dQZF1DWSf2RDTDayIx",
    },
    "angry": {
        "name": "Chill Hits",
        "url": "https://open.spotify.com/playlist/37i9dQZF1DX4WYpdgoIcn6",
    },
    "surprised": {
        "name": "Viral Hits",
        "url": "https://open.spotify.com/playlist/37i9dQZF1DXcZDD7cfEKhW",
    },
    "fearful": {
        "name": "Confidence Boost",
        "url": "https://open.spotify.com/playlist/37i9dQZF1DX4fpCWaHOned",
    },
    "disgust": {
        "name": "Mood Booster",
        "url": "https://open.spotify.com/playlist/37i9dQZF1DX3rxVfibe1L0",
    },
    "calm": {
        "name": "Relaxation",
        "url": "https://open.spotify.com/playlist/37i9dQZF1DX4sWSpwq3LiO",
    }
}

# -------------------- CORS Pre-flight Handler --------------------
@app.before_request
def handle_preflight():
    if request.method == "OPTIONS":
        response = jsonify({})
        response.headers.add("Access-Control-Allow-Origin", "*")
        response.headers.add('Access-Control-Allow-Headers', "*")
        response.headers.add('Access-Control-Allow-Methods', "*")
        return response

# -------------------- User Auth --------------------
USER_DB = "users.json"
users = {}

def save_users():
    with open(USER_DB, "w") as f:
        json.dump(users, f, indent=4)

def load_users():
    global users
    if os.path.exists(USER_DB):
        try:
            with open(USER_DB, "r") as f:
                users = json.load(f)
        except json.JSONDecodeError:
            users = {}

load_users()

@app.route('/signup', methods=['POST'])
def signup():
    data = request.json
    username = data.get("username", "").lower()
    password = data.get("password", "")

    if username in users:
        return jsonify({"error": "User already exists"}), 400

    hashed = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
    users[username] = hashed
    save_users()

    return jsonify({"message": "User registered successfully"}), 201

@app.route('/login', methods=['POST'])
def login():
    data = request.json
    username = data.get("username", "").lower()
    password = data.get("password", "")

    stored_hash = users.get(username)
    if not stored_hash or not bcrypt.checkpw(password.encode('utf-8'), stored_hash.encode('utf-8')):
        return jsonify({"error": "Invalid credentials"}), 401

    token = jwt.encode(
        {"username": username, "exp": datetime.datetime.utcnow() + datetime.timedelta(hours=24)},
        app.config['JWT_SECRET_KEY'], algorithm="HS256"
    )

    return jsonify({"message": "Login successful", "token": token})

# -------------------- Emotion Prediction Endpoint --------------------
@app.route('/predict', methods=['POST', 'OPTIONS'])
def predict_emotion():
    # Handle CORS preflight
    if request.method == 'OPTIONS':
        response = jsonify({})
        response.headers.add("Access-Control-Allow-Origin", "*")
        response.headers.add('Access-Control-Allow-Headers', "*")
        response.headers.add('Access-Control-Allow-Methods', "*")
        return response
        
    try:
        print(" Received prediction request")
        print(f" Request origin: {request.headers.get('Origin', 'Unknown')}")
        print(f" Request method: {request.method}")
        print(f" Request headers: {dict(request.headers)}")
        
        if 'audio' not in request.files:
            print(" No audio file in request")
            return jsonify({"error": "No audio uploaded"}), 400

        audio_file = request.files['audio']
        print(f" Audio file received: {audio_file.filename}")
        
        if audio_file.filename == '':
            return jsonify({"error": "No audio file selected"}), 400

        # Read the audio file
        audio_data = audio_file.read()
        print(f" Audio data size: {len(audio_data)} bytes")
        
        if len(audio_data) == 0:
            return jsonify({"error": "Empty audio file"}), 400

        # Convert WebM to WAV using pydub
        try:
            webm_audio = AudioSegment.from_file(io.BytesIO(audio_data), format="webm")
            print(f" WebM audio loaded: duration={len(webm_audio)}ms, frame_rate={webm_audio.frame_rate}")
            
            # Convert to mono and set sample rate to 16kHz
            webm_audio = webm_audio.set_channels(1).set_frame_rate(16000)
            
            # Export to WAV in memory
            wav_io = io.BytesIO()
            webm_audio.export(wav_io, format="wav")
            wav_io.seek(0)
            
        except Exception as e:
            print(f" Error converting audio format: {str(e)}")
            return jsonify({"error": f"Audio format conversion failed: {str(e)}"}), 400

        # Load with librosa
        try:
            signal, sr = librosa.load(wav_io, sr=16000)
            print(f"🔊 Librosa loaded audio: length={len(signal)}, sample_rate={sr}")
            
            if len(signal) == 0:
                return jsonify({"error": "No audio signal detected"}), 400
                
        except Exception as e:
            print(f" Error loading audio with librosa: {str(e)}")
            return jsonify({"error": f"Audio processing failed: {str(e)}"}), 400

        # Feature extraction
        try:
            inputs = feature_extractor(signal, sampling_rate=16000, return_tensors="pt", padding=True)
            print(" Feature extraction completed")
        except Exception as e:
            print(f" Error in feature extraction: {str(e)}")
            return jsonify({"error": f"Feature extraction failed: {str(e)}"}), 400

        # Model prediction
        try:
            with torch.no_grad():
                logits = model(**inputs).logits
                probs = torch.nn.functional.softmax(logits, dim=1)[0]
                top_probs, top_idxs = torch.topk(probs, 3)
                
            print(" Model prediction completed")
        except Exception as e:
            print(f" Error in model prediction: {str(e)}")
            return jsonify({"error": f"Model prediction failed: {str(e)}"}), 500

        # Format results - SIMPLIFIED FORMAT for frontend compatibility
        emotions = []
        for i in range(3):
            idx = top_idxs[i].item()
            prob = top_probs[i].item()
            label = model.config.id2label[idx].lower()
            
            # Map to standardized emotion
            mapped_emotion = emotion_map.get(label, label)
            
            # Simple format: [emotion_name, confidence_score]
            emotions.append([mapped_emotion, round(prob, 3)])
            
        print(f" Emotions detected: {emotions}")
        
        # Return in the format the frontend expects
        response_data = {
            "emotions": emotions,
            "status": "success",
            "message": f"Detected {len(emotions)} emotions"
        }
        
        print(f" Sending response: {response_data}")
        
        # Create response with proper CORS headers
        response = jsonify(response_data)
        response.headers.add("Access-Control-Allow-Origin", "*")
        response.headers.add("Access-Control-Allow-Headers", "Content-Type")
        response.headers.add("Access-Control-Allow-Methods", "POST, OPTIONS")
        
        return response

    except Exception as e:
        print(f" Unexpected error in /predict: {str(e)}")
        import traceback
        traceback.print_exc()
        
        error_response = jsonify({"error": "Internal server error", "details": str(e)})
        error_response.headers.add("Access-Control-Allow-Origin", "*")
        return error_response, 500
    
@app.route('/playlist/<emotion>', methods=['GET'])
def get_playlist(emotion):
    playlist = emotion_playlists.get(emotion, emotion_playlists['neutral'])
    return jsonify(playlist)

# Health check endpoint
@app.route('/health', methods=['GET'])
def health_check():
    return jsonify({"status": "healthy", "message": "Server is running"}), 200

# Test endpoint to verify CORS
@app.route('/test', methods=['GET', 'POST'])
def test_cors():
    response = jsonify({
        "message": "CORS test successful", 
        "method": request.method,
        "origin": request.headers.get('Origin', 'No origin header')
    })
    response.headers.add("Access-Control-Allow-Origin", "*")
    return response

# -------------------- Run --------------------
if __name__ == "__main__":
    if not os.path.exists(USER_DB):
        with open(USER_DB, "w") as f:
            json.dump({}, f)
    
    print(" Starting MoodLift server...")
    print(" Server will be available at: http://127.0.0.1:5000")
    print(" Prediction endpoint: http://127.0.0.1:5000/predict")
    print(" Test endpoint: http://127.0.0.1:5000/test")
    print(" CORS enabled for frontend connections")
    
    # Run with specific host and port
    app.run(debug=True, port=5000, host='127.0.0.1', threaded=True)