const express = require('express');
const { spawn } = require('child_process');
const app = express();
const PORT = 8080;

app.use(express.json());

// 1) Search endpoint
app.get('/search', (req, res) => {
  const query = req.query.q;
  if (!query) return res.status(400).json({ error: 'Missing query parameter' });

  const ytdlp = spawn('yt-dlp', [`ytsearch5:${query}`, '--skip-download', '--print-json']);
  let output = '';

  ytdlp.stdout.on('data', chunk => { output += chunk.toString(); });
  ytdlp.stderr.on('data', err => console.error(`yt-dlp stderr: ${err}`));

  ytdlp.on('close', code => {
    if (code !== 0) return res.status(500).json({ error: `yt-dlp exited with code ${code}` });
    const videos = output
      .trim()
      .split('\n')
      .map(line => JSON.parse(line))
      .map(v => ({
        id: v.id,
        title: v.title,
        thumbnail: v.thumbnail,
        url: v.webpage_url
      }));
    res.json(videos);
  });
});

// 2) Download MP4
app.get('/download/mp4/:id', (req, res) => {
  const id = req.params.id;
  const url = `https://www.youtube.com/watch?v=${id}`;
  const args = ['-f', 'best[ext=mp4]+bestaudio[ext=m4a]/best', '-o', '-', url];
  const ytdlp = spawn('yt-dlp', args);

  res.setHeader('Content-Disposition', `attachment; filename="${id}.mp4"`);
  ytdlp.stdout.pipe(res);
  ytdlp.stderr.on('data', err => console.error(`yt-dlp stderr: ${err}`));
});

// 3) Download MP3
app.get('/download/mp3/:id', (req, res) => {
  const id = req.params.id;
  const url = `https://www.youtube.com/watch?v=${id}`;
  const args = ['-f', 'bestaudio', '--extract-audio', '--audio-format', 'mp3', '-o', '-', url];
  const ytdlp = spawn('yt-dlp', args);

  res.setHeader('Content-Disposition', `attachment; filename="${id}.mp3"`);
  ytdlp.stdout.pipe(res);
  ytdlp.stderr.on('data', err => console.error(`yt-dlp stderr: ${err}`));
});

app.listen(PORT, () => console.log(`🚀 Backend running on port ${PORT}`));
