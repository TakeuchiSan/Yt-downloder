from flask import Flask, jsonify, request, send_file
from flask_cors import CORS
from yt_dlp import YoutubeDL
import os
import logging
from urllib.parse import unquote

app = Flask(__name__)
CORS(app)  # Enable CORS for cross-origin requests
app.logger.setLevel(logging.DEBUG)

# Configuration
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
        query = unquote(request.args.get('q', '')).strip()
        if not query or len(query) < 2:
            return jsonify({
                "error": "Parameter 'q' diperlukan (minimal 2 karakter)",
                "solution": "Masukkan kata kunci yang valid"
            }), 400

        app.logger.info(f"Mencari video: '{query}'")

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
                    "error": "Tidak ada hasil ditemukan",
                    "solution": "Coba kata kunci lain atau periksa ejaan"
                }), 404

            videos = []
            for vid in info['entries']:
                if vid:  # Filter None entries
                    videos.append({
                        'id': vid.get('id', ''),
                        'title': vid.get('title', 'Tanpa judul'),
                        'url': f"https://youtu.be/{vid.get('id')}",
                        'thumbnail': (vid.get('thumbnails') or [{}])[-1].get('url', ''),
                        'duration': vid.get('duration_string', '0:00'),
                        'author': vid.get('uploader', 'Unknown')
                    })

            app.logger.info(f"Menemukan {len(videos)} hasil untuk '{query}'")
            return jsonify(videos)

    except Exception as e:
        app.logger.error(f"Error Pencarian: {str(e)}")
        return jsonify({
            "error": "Gagal memproses pencarian",
            "details": str(e),
            "solution": "Coba lagi dalam beberapa saat"
        }), 500

@app.route('/api/download')
def download():
    try:
        url = unquote(request.args.get('url', ''))
        format = request.args.get('format', 'mp4')

        if not url or not ('youtu.be' in url or 'youtube.com' in url):
            return jsonify({
                "error": "URL YouTube tidak valid",
                "solution": "Gunakan link YouTube yang benar"
            }), 400

        app.logger.info(f"Memulai download: {url} sebagai {format.upper()}")

        ydl_opts = {
            'format': 'bestaudio/best' if format == 'mp3' else 'best[ext=mp4]',
            'outtmpl': f'{DOWNLOAD_FOLDER}/%(title)s.%(ext)s',
            'quiet': True,
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
            }] if format == 'mp3' else [],
            'socket_timeout': 30
        }

        with YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            filename = ydl.prepare_filename(info)
            
            if format == 'mp3':
                filename = filename.rsplit('.', 1)[0] + '.mp3'

            return send_file(
                filename,
                as_attachment=True,
                download_name=os.path.basename(filename),
                mimetype='audio/mpeg' if format == 'mp3' else 'video/mp4'
            )

    except Exception as e:
        app.logger.error(f"Error Download: {str(e)}")
        return jsonify({
            "error": "Gagal mengunduh",
            "details": str(e),
            "solution": "Coba video lain atau periksa koneksi"
        }), 500

if __name__ == '__main__':
    app.run(
        host='0.0.0.0',
        port=3001,
        debug=True,
        threaded=True
    )
