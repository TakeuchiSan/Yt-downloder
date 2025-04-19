from flask import Flask, jsonify, request, send_file
from yt_dlp import YoutubeDL
import os
from uuid import uuid4

app = Flask(__name__)
DOWNLOAD_FOLDER = 'downloads'

if not os.path.exists(DOWNLOAD_FOLDER):
    os.makedirs(DOWNLOAD_FOLDER)

@app.route('/api/search', methods=['GET'])
def search():
    query = request.args.get('q')
    if not query:
        return jsonify({'error': 'Query required'}), 400

    with YoutubeDL({'quiet': True}) as ydl:
        try:
            info = ydl.extract_info(f"ytsearch10:{query}", download=False)
            videos = info['entries']
            return jsonify([{
                'id': vid['id'],
                'title': vid['title'],
                'url': vid['url'],
                'thumbnail': vid['thumbnails'][-1]['url'],
                'duration': f"{vid['duration']//60}:{vid['duration']%60:02d}",
                'author': vid['uploader']
            } for vid in videos if vid])
        except Exception as e:
            return jsonify({'error': str(e)}), 500

@app.route('/api/download', methods=['GET'])
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
            'quiet': True
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
        return jsonify({'error': str(e)}), 500
    finally:
        # Cleanup
        if 'filename' in locals():
            if os.path.exists(filename):
                os.remove(filename)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=3001)
