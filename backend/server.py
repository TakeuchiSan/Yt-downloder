from flask import Flask, jsonify, request, send_file
from flask_cors import CORS  # Import CORS
from yt_dlp import YoutubeDL
import os
import logging
from urllib.parse import unquote

app = Flask(__name__)
CORS(app)  # Enable CORS for all routes
app.logger.setLevel(logging.DEBUG)

DOWNLOAD_FOLDER = 'downloads'
os.makedirs(DOWNLOAD_FOLDER, exist_ok=True)

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
        query = request.args.get('q')
        if not query:
            return jsonify({"error": "Parameter 'q' diperlukan"}), 400

        app.logger.info(f"Mencari video: {query}")

        ydl_opts = {
            'quiet': True,
            'extract_flat': True,
            'default_search': 'ytsearch10:',
            'socket_timeout': 15  # Add timeout
        }

        with YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(query, download=False)
            
            if not info or 'entries' not in info:
                return jsonify({"error": "Tidak ada hasil"}), 404

            videos = []
            for vid in info['entries']:
                if not vid:
                    continue
                videos.append({
                    'id': vid.get('id'),
                    'title': vid.get('title', 'Tanpa judul'),
                    'url': vid.get('url'),
                    'thumbnail': vid.get('thumbnails', [{}])[-1].get('url'),
                    'duration': vid.get('duration_string', '0:00'),
                    'author': vid.get('uploader', 'Unknown')
                })

            app.logger.info(f"Menemukan {len(videos)} video")
            return jsonify(videos)

    except Exception as e:
        app.logger.error(f"Search Error: {str(e)}")
        return jsonify({"error": "Gagal melakukan pencarian", "details": str(e)}), 500

@app.route('/api/download')
def download():
    try:
        url = unquote(request.args.get('url'))
        format = request.args.get('format', 'mp4')

        if not url:
            return jsonify({"error": "Parameter 'url' diperlukan"}), 400

        app.logger.info(f"Download: {url} sebagai {format}")

        ydl_opts = {
            'format': 'bestaudio/best' if format == 'mp3' else 'best[ext=mp4]',
            'outtmpl': f'{DOWNLOAD_FOLDER}/%(title)s.%(ext)s',
            'quiet': True,
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
            }] if format == 'mp3' else [],
            'socket_timeout': 30  # Add timeout
        }

        with YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            filename = ydl.prepare_filename(info)
            
            if format == 'mp3':
                filename = filename.rsplit('.', 1)[0] + '.mp3'
            
            # Clean filename for safe download
            safe_filename = os.path.basename(filename)
            app.logger.info(f"Berhasil didownload: {safe_filename}")
            
            return send_file(
                filename,
                as_attachment=True,
                download_name=safe_filename,
                mimetype='audio/mpeg' if format == 'mp3' else 'video/mp4'
            )

    except Exception as e:
        app.logger.error(f"Download Error: {str(e)}")
        return jsonify({
            "error": "Gagal mengunduh",
            "details": str(e),
            "solution": "Coba lagi atau gunakan URL berbeda"
        }), 500

if __name__ == '__main__':
    app.run(
        host='0.0.0.0',
        port=3001,
        debug=True,
        threaded=True  # Enable threading for multiple requests
    )
