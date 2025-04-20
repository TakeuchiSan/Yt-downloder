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
      font-family: 'Segoe UI', sans-serif;
      background: #f0f2f5;
      margin: 0;
      padding: 20px;
    }
    .container {
      max-width: 800px;
      margin: auto;
      background: #ffffff;
      padding: 30px;
      border-radius: 12px;
      box-shadow: 0 4px 10px rgba(0,0,0,0.1);
    }
    h1 {
      text-align: center;
      margin-bottom: 20px;
      color: #333;
    }
    input[type="text"] {
      width: 100%;
      box-sizing: border-box;
      padding: 15px;
      font-size: 16px;
      border: 1px solid #ccc;
      border-radius: 8px;
      margin-bottom: 10px;
    }
    button {
      padding: 10px 18px;
      font-size: 16px;
      margin: 5px 5px 15px 0;
      border: none;
      border-radius: 8px;
      background-color: #007bff;
      color: white;
      cursor: pointer;
    }
    button:hover {
      background-color: #0056b3;
    }
    .video {
      display: flex;
      align-items: flex-start;
      gap: 10px;
      margin-bottom: 20px;
      border-bottom: 1px solid #eee;
      padding-bottom: 10px;
    }
    .thumbnail {
      width: 160px;
      border-radius: 6px;
    }
    .info {
      flex: 1;
    }
    .info strong {
      font-size: 18px;
      display: block;
      margin-bottom: 5px;
    }
    .info em {
      color: #777;
      font-size: 14px;
    }
    .search-status {
      font-style: italic;
      color: #555;
      font-size: 16px;
      animation: pulse 1.2s infinite;
    }
    @keyframes pulse {
      0% { opacity: 0.2; }
      50% { opacity: 1; }
      100% { opacity: 0.2; }
    }
  </style>
</head>
<body>
  <div class="container">
    <h1>YouTube Downloader</h1>
    <input type="text" id="query" placeholder="Masukkan judul atau link video YouTube..." />
    <button onclick="search()">Cari</button>
    <div id="results"></div>
  </div>

  <script>
    async function search() {
      const query = document.getElementById('query').value;
      const resultsDiv = document.getElementById('results');
      resultsDiv.innerHTML = '<p class="search-status">Mencari...</p>';

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
              <strong>${video.title}</strong>
              <em>${video.author}</em><br>
              <button onclick="download('${video.url}', 'mp3')">Download MP3</button>
              <button onclick="download('${video.url}', 'mp4')">Download MP4</button>
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
