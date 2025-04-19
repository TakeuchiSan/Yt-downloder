from flask import Flask, jsonify, request, send_file, render_template_string
from yt_dlp import YoutubeDL
import os
import logging

app = Flask(__name__)
app.logger.setLevel(logging.DEBUG)

DOWNLOAD_FOLDER = 'downloads'
os.makedirs(DOWNLOAD_FOLDER, exist_ok=True)

HTML_TEMPLATE = '''
<!DOCTYPE html>
<html lang="id">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0"/>
  <title>YouTube MP3/MP4 Downloader</title>
  <style>
    body {
      font-family: Arial, sans-serif;
      background: #f5f5f5;
      padding: 20px;
      max-width: 700px;
      margin: auto;
    }
    h1 {
      text-align: center;
    }
    input[type="text"] {
      width: 100%;
      padding: 12px;
      margin-bottom: 10px;
      font-size: 16px;
    }
    button {
      padding: 10px 15px;
      font-size: 16px;
      margin-right: 10px;
      cursor: pointer;
    }
    .video {
      border: 1px solid #ccc;
      padding: 10px;
      margin-top: 10px;
      background: #fff;
    }
    .thumbnail {
      max-width: 120px;
      float: left;
      margin-right: 10px;
    }
    .info {
      overflow: hidden;
    }
  </style>
</head>
<body>
  <h1>YouTube Downloader</h1>
  <input type="text" id="query" placeholder="Cari video YouTube..." />
  <button onclick="search()">Cari</button>
  <div id="results"></div>

  <script>
    async function search() {
      const query = document.getElementById('query').value;
      const resultsDiv = document.getElementById('results');
      resultsDiv.innerHTML = 'Mencari...';

      try {
        const res = await fetch(`/api/search?q=${encodeURIComponent(query)}`);
        const data = await res.json();

        if (res.status !== 200) {
          resultsDiv.innerHTML = `<p>Error: ${data.error}</p>`;
          return;
        }

        resultsDiv.innerHTML = '';
        data.forEach(video => {
          const div = document.createElement('div');
          div.className = 'video';
          div.innerHTML = `
            <img class="thumbnail" src="${video.thumbnail}" />
            <div class="info">
              <strong>${video.title}</strong><br>
              <em>${video.author}</em><br>
              Durasi: ${video.duration}<br>
              <button onclick="download('${video.url}', 'mp3')">MP3</button>
              <button onclick="download('${video.url}', 'mp4')">MP4</button>
            </div>
          `;
          resultsDiv.appendChild(div);
        });
      } catch (err) {
        resultsDiv.innerHTML = `<p>Error: ${err.message}</p>`;
      }
    }

    function download(url, format) {
      const a = document.createElement('a');
      a.href = `/api/download?url=${encodeURIComponent(url)}&format=${format}`;
      a.click();
    }
  </script>
</body>
</html>
'''

@app.route('/')
def index():
    return render_template_string(HTML_TEMPLATE)

@app.route('/api/search')
def search():
    try:
        query = request.args.get('q')
        if not query:
            return jsonify({"error": "Parameter 'q' diperlukan"}), 400

        app.logger.info(f"Mencari video: {query}")

        ydl_opts = {
            'quiet': True,
            'extract_flat': 'in_playlist',
            'default_search': 'ytsearch10:'
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
                    'url': vid.get('url'),
                    'thumbnail': vid.get('thumbnails', [{}])[-1].get('url'),
                    'duration': vid.get('duration_string', '0:00'),
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
            return send_file(filename, as_attachment=True)

    except Exception as e:
        app.logger.error(f"Download error: {str(e)}")
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=3001, debug=True)
