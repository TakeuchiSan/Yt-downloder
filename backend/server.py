from flask import Flask, jsonify, request, send_file
from yt_dlp import YoutubeDL
import os
import logging
import math

app = Flask(__name__)
app.logger.setLevel(logging.DEBUG)

DOWNLOAD_FOLDER = 'downloads'
os.makedirs(DOWNLOAD_FOLDER, exist_ok=True)

def format_duration(seconds):
    if not seconds:
        return "0:00"
    minutes = int(seconds) // 60
    secs = int(seconds) % 60
    return f"{minutes}:{secs:02}"

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
            'default_search': 'ytsearch10',
        }

        with YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(query, download=False)
            
            if not info or 'entries' not in info:
                return jsonify({"error": "Tidak ada hasil"}), 404

            results = []
            for vid in info['entries']:
                if not vid:
                    continue
                results.append({
                    'id': vid.get('id'),
                    'title': vid.get('title', 'Tanpa judul'),
                    'url': vid.get('webpage_url'),
                    'thumbnail': vid.get('thumbnails', [{}])[-1].get('url'),
                    'duration': format_duration(vid.get('duration')),
                    'author': vid.get('uploader', 'Unknown')
                })

            app.logger.info(f"Menemukan {len(results)} video")
            return jsonify(results)

    except Exception as e:
        app.logger.error(f"Error: {str(e)}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/download')
def download():
    try:
        url = request.args.get('url')
        format = request.args.get('format', 'mp4')

        if not url:
            return jsonify({"error": "Parameter 'url' diperlukan"}), 400

        app.logger.info(f"Download: {url} sebagai {format}")

        ydl_opts = {
            'format': 'bestaudio/best' if format == 'mp3' else 'best',
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

            app.logger.info(f"Berhasil didownload: {filename}")
            return send_file(filename, as_attachment=True, download_name=os.path.basename(filename))

    except Exception as e:
        app.logger.error(f"Download error: {str(e)}")
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=3001, debug=True)
