from flask import Flask, jsonify, request, send_file
from flask_cors import CORS
from yt_dlp import YoutubeDL
import os
import logging
from urllib.parse import unquote

# Initialize Flask app
app = Flask(__name__)
CORS(app)  # Enable CORS
app.logger.setLevel(logging.DEBUG)

# Configuration
DOWNLOAD_FOLDER = 'downloads'
os.makedirs(DOWNLOAD_FOLDER, exist_ok=True)

def sanitize_query(query):
    """Sanitize search query"""
    return unquote(query or '').strip()[:100]

@app.route('/')
def home():
    return jsonify({
        "status": "running",
        "endpoints": {
            "search": "/api/search?q=[query]",
            "download": "/api/download?url=[url]&format=[mp3/mp4]"
        }
    })

@app.route('/api/search')
def search():
    try:
        query = sanitize_query(request.args.get('q'))
        
        if len(query) < 2:
            return jsonify({
                "error": "Query too short",
                "solution": "Use at least 2 characters"
            }), 400

        app.logger.info(f"Searching: '{query}'")

        ydl_opts = {
            'quiet': True,
            'extract_flat': True,
            'default_search': 'ytsearch10:',
            'socket_timeout': 15,
            'extractor_args': {
                'youtube': {
                    'skip': ['dash', 'hls'],
                    'max_results': 10
                }
            }
        }

        with YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(query, download=False)
            
            if not info or not info.get('entries'):
                return jsonify({
                    "error": "No results found",
                    "solution": "Try different keywords"
                }), 404

            videos = []
            for vid in info['entries']:
                if vid:
                    videos.append({
                        'id': vid.get('id', ''),
                        'title': vid.get('title', 'No Title'),
                        'url': f"https://youtu.be/{vid.get('id')}",
                        'thumbnail': (vid.get('thumbnails') or [{}])[-1].get('url', ''),
                        'duration': vid.get('duration_string', '0:00'),
                        'author': vid.get('uploader', 'Unknown')
                    })

            return jsonify(videos)

    except Exception as e:
        app.logger.error(f"Search Error: {str(e)}")
        return jsonify({
            "error": "Search failed",
            "details": str(e)
        }), 500

@app.route('/api/download')
def download():
    try:
        url = unquote(request.args.get('url', ''))
        format = request.args.get('format', 'mp4')

        if not url or not ('youtu.be' in url or 'youtube.com' in url):
            return jsonify({
                "error": "Invalid URL",
                "solution": "Use a valid YouTube URL"
            }), 400

        app.logger.info(f"Downloading: {url} as {format.upper()}")

        ydl_opts = {
            'format': 'bestaudio/best' if format == 'mp3' else 'best[ext=mp4]',
            'outtmpl': f'{DOWNLOAD_FOLDER}/%(title)s.%(ext)s',
            'quiet': True,
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
            }] if format == 'mp3' else []
        }

        with YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            filename = ydl.prepare_filename(info)
            
            if format == 'mp3':
                filename = filename.rsplit('.', 1)[0] + '.mp3'

            return send_file(
                filename,
                as_attachment=True,
                download_name=os.path.basename(filename)
            )

    except Exception as e:
        app.logger.error(f"Download Error: {str(e)}")
        return jsonify({
            "error": "Download failed",
            "details": str(e),
            "solution": "Try another video or check connection"
        }), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=3001, debug=True, threaded=True)
