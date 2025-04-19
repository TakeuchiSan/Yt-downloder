from flask import Flask, jsonify, request, send_file
from yt_dlp import YoutubeDL
import os

app = Flask(__name__)
DOWNLOAD_FOLDER = 'downloads'

# Pastikan folder download ada
os.makedirs(DOWNLOAD_FOLDER, exist_ok=True)

# Root endpoint
@app.route('/')
def home():
    return jsonify({"status": "running", "service": "yt-dlp backend"})

# Search endpoint
@app.route('/api/search')
def search():
    query = request.args.get('q')
    if not query:
        return jsonify({"error": "Parameter 'q' diperlukan"}), 400
    
    try:
        with YoutubeDL({'quiet': True}) as ydl:
            info = ydl.extract_info(f"ytsearch10:{query}", download=False)
            return jsonify(info['entries'])
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# Download endpoint
@app.route('/api/download')
def download():
    url = request.args.get('url')
    format = request.args.get('format', 'mp4')
    
    try:
        ydl_opts = {
            'format': 'bestaudio/best' if format == 'mp3' else 'best',
            'outtmpl': f'{DOWNLOAD_FOLDER}/%(title)s.%(ext)s',
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
            }] if format == 'mp3' else [],
        }
        
        with YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            filename = ydl.prepare_filename(info)
            if format == 'mp3':
                filename = filename.rsplit('.', 1)[0] + '.mp3'
            
            return send_file(filename, as_attachment=True)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=3001, debug=True)
