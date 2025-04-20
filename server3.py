from flask import Flask, jsonify, request, send_file, render_template_string
from yt_dlp import YoutubeDL
import os, logging, random

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
    body { font-family: 'Segoe UI', sans-serif; background: #f0f2f5; margin: 0; padding: 20px; }
    .container { max-width: 800px; margin: auto; background: #fff; padding: 30px; border-radius: 12px;
                 box-shadow: 0 4px 10px rgba(0,0,0,0.1); }
    h1 { text-align: center; margin-bottom: 20px; color: #333; }
    input[type="text"] { width: 100%; box-sizing: border-box; padding: 15px; font-size: 16px;
                           border: 1px solid #ccc; border-radius: 8px; margin-bottom: 5px; }
    button { padding: 10px 18px; font-size: 16px; margin: 10px 0; border: none; border-radius: 8px;
             background-color: #007bff; color: white; cursor: pointer; }
    button:hover { background-color: #0056b3; }
    .video { display: flex; align-items: flex-start; gap: 10px; margin-bottom: 20px;
             border-bottom: 1px solid #eee; padding-bottom: 10px; }
    .thumbnail { width: 160px; border-radius: 6px; }
    .info { flex: 1; }
    .info strong { font-size: 18px; display: block; margin-bottom: 5px; }
    .info em { color: #777; font-size: 14px; }
    .search-status { font-style: italic; color: #555; font-size: 16px;
                     animation: pulse 1.2s infinite; margin-top: 10px; }
    .suggestions, .random-suggestions { border: 1px solid #ccc; padding: 10px; border-radius: 8px;
                   background: #fff; box-shadow: 0 4px 6px rgba(0,0,0,0.1); margin-top: 20px;
                   max-height: 200px; overflow-y: auto; }
    .suggestions div, .random-suggestions .suggestion-video { padding: 5px; cursor: pointer; }
    .suggestions div:hover, .random-suggestions .suggestion-video:hover { background: #f1f1f1; }
    .random-suggestions h2 { text-align: center; color: #333; margin-bottom: 10px; }
    .suggestion-video { display: flex; align-items: center; gap: 15px; margin-bottom: 10px; }
    .suggestion-thumbnail { width: 120px; height: 90px; border-radius: 6px; }
    @keyframes pulse { 0% { opacity: 0.2; } 50% { opacity: 1; } 100% { opacity: 0.2; } }
  </style>
</head>
<body>
  <div class="container">
    <h1>YouTube Downloader</h1>
    <input type="text" id="query" placeholder="Masukkan judul atau link YouTube..." oninput="suggest()" />
    <button onclick="search()">Cari</button>

    <div id="suggestions" class="suggestions" style="display:none;"></div>
    <div id="results"></div>

    <div class="random-suggestions">
      <h2>Video Saran</h2>
      <div id="random-suggestions"></div>
    </div>
  </div>

  <script>
    let suggestTimeout;
    function suggest() {
      clearTimeout(suggestTimeout);
      const q = document.getElementById('query').value;
      const sugDiv = document.getElementById('suggestions');
      if (q.length < 3) { sugDiv.style.display = 'none'; return; }
      suggestTimeout = setTimeout(async () => {
        try {
          const res = await fetch(`/api/suggest?q=${encodeURIComponent(q)}`);
          const data = await res.json();
          if (res.ok) {
            sugDiv.innerHTML = data.map(item => `<div onclick="pickSuggest('${item.replace(/'/g, "\\'")}')">${item}</div>`).join('');
            sugDiv.style.display = 'block';
          }
        } catch (e) { console.error(e); }
      }, 300);
    }
    function pickSuggest(val) {
      document.getElementById('query').value = val;
      document.getElementById('suggestions').style.display = 'none';
      search();
    }
    async function search() {
      document.getElementById('suggestions').style.display = 'none';
      const q = document.getElementById('query').value;
      const resDiv = document.getElementById('results');
      resDiv.innerHTML = '<p class="search-status">Mencari...</p>';
      try {
        const res = await fetch(`/api/search?q=${encodeURIComponent(q)}`);
        const data = await res.json();
        if (!res.ok) return resDiv.innerHTML = `<p>Error: ${data.error}</p>`;
        resDiv.innerHTML = '';
        data.forEach(v => {
          const dv = document.createElement('div'); dv.className = 'video';
          dv.innerHTML = `
            <img class=\"thumbnail\" src=\"${v.thumbnail}\" />
            <div class=\"info\"> 
              <strong>${v.title}</strong>
              <em>${v.author}</em><br>
              <button onclick=\"download('${v.url}','mp3')\">MP3</button>
              <button onclick=\"download('${v.url}','mp4')\">MP4</button>
            </div>`;
          resDiv.appendChild(dv);
        });
      } catch (e) { resDiv.innerHTML = `<p>Error: ${e.message}</p>`; }
    }
    function download(url, fmt) {
      const a = document.createElement('a');
      a.href = `/api/download?url=${encodeURIComponent(url)}&format=${fmt}`;
      a.click();
    }

    async function loadRandomSuggestions() {
      const rndDiv = document.getElementById('random-suggestions');
      try {
        const res = await fetch('/api/random_suggestions');
        const data = await res.json();
        if (!res.ok) { rndDiv.innerHTML = '<p>Gagal memuat saran.</p>'; return; }
        rndDiv.innerHTML = '';
        data.forEach(v => {
          const dv = document.createElement('div'); dv.className = 'suggestion-video';
          dv.innerHTML = `
            <img class=\"suggestion-thumbnail\" src=\"${v.thumbnail}\" />
            <div class=\"suggestion-info\"> 
              <strong>${v.title}</strong><br>
              <em>${v.author}</em><br>
              <button onclick=\"download('${v.url}','mp3')\">MP3</button>
              <button onclick=\"download('${v.url}','mp4')\">MP4</button>
            </div>`;
          rndDiv.appendChild(dv);
        });
      } catch {
        rndDiv.innerHTML = '<p>Error loading suggestions.</p>';
      }
    }
    // load random suggestions on page load
    window.onload = () => loadRandomSuggestions();
  </script>
</body>
</html>
'''

@app.route('/')
def index():
    return render_template_string(HTML_TEMPLATE)

@app.route('/api/suggest')
def suggest():
    q = request.args.get('q')
    if not q:
        return jsonify({ 'error': "Parameter 'q' diperlukan" }), 400
    try:
        ydl_opts = { 'quiet': True, 'extract_flat': 'in_playlist', 'default_search': 'ytsearch5:' }
        with YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(q, download=False)
            titles = [e.get('title','') for e in info.get('entries',[]) if e]
        return jsonify(titles)
    except Exception as e:
        return jsonify({ 'error': str(e) }), 500

@app.route('/api/random_suggestions')
def random_suggestions():
    try:
        query = 'music'
        ydl_opts = { 'quiet': True, 'extract_flat': 'in_playlist', 'default_search': 'ytsearch10:' }
        with YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(query, download=False)
            entries = info.get('entries',[]) or []
            results = [
                {'id': v.get('id'), 'title': v.get('title','Tanpa judul'),
                 'url': v.get('url'), 'thumbnail': v.get('thumbnails',[{}])[-1].get('url'),
                 'author': v.get('uploader','Unknown')} for v in entries if v
            ]
        sample = random.sample(results, 3) if len(results)>=3 else results
        return jsonify(sample)
    except Exception as e:
        app.logger.error(f"Error random: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/search')
def search():
    q = request.args.get('q')
    if not q:
        return jsonify({ 'error': "Parameter 'q' diperlukan" }), 400
    try:
        app.logger.info(f"Mencari video: {q}")
        ydl_opts = { 'quiet': True, 'extract_flat': 'in_playlist', 'default_search': 'ytsearch10:' }
        with YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(q, download=False)
            entries = info.get('entries',[]) or []
            results = [
                {'id': v.get('id'), 'title': v.get('title','Tanpa judul'),
                 'url': v.get('url'), 'thumbnail': v.get('thumbnails',[{}])[-1].get('url'),
                 'author': v.get('uploader','Unknown')} for v in entries if v
            ]
        return jsonify(results)
    except Exception as e:
        return jsonify({ 'error': str(e) }), 500

@app.route('/api/download')
def download_file():
    url = request.args.get('url')
    fmt = request.args.get('format','mp4')
    if not url:
        return jsonify({ 'error': "Parameter 'url' diperlukan" }), 400
    try:
        app.logger.info(f"Downloading: {url} as {fmt}")
        ydl_opts = {
            'format': 'bestaudio/best' if fmt=='mp3' else 'best',
            'outtmpl': f'{DOWNLOAD_FOLDER}/%(title)s.%(ext)s',
            'quiet': True,
            'postprocessors': [{ 'key':'FFmpegExtractAudio','preferredcodec':'mp3' }] if fmt=='mp3' else []
        }
        with YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            filename = ydl.prepare_filename(info)
            if fmt=='mp3': filename = filename.rsplit('.',1)[0] + '.mp3'
        return send_file(filename, as_attachment=True)
    except Exception as e:
        return jsonify({ 'error': str(e) }), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=3001, debug=True)
