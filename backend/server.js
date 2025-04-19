const express = require('express');
const ytdl = require('ytdl-core');
const ytDlp = require('yt-dlp');
const cors = require('cors');
const app = express();
const PORT = process.env.PORT || 5000;

app.use(cors());
app.use(express.json());

// Rute untuk root URL
app.get('/', (req, res) => {
  res.send('YouTube Downloader API is running. Use /search to get video info.');
});

// Endpoint untuk mencari video berdasarkan judul menggunakan yt-dlp
app.get('/search', async (req, res) => {
  const { query } = req.query;
  if (!query) {
    return res.status(400).send('Query is required');
  }

  try {
    // Melakukan pencarian menggunakan yt-dlp
    const searchResults = await ytDlp.exec(['ytsearch:' + query, '--max-results', '5']);

    // Memproses hasil pencarian
    const videoResults = searchResults.map(result => ({
      title: result.title,
      thumbnail: result.thumbnail,
      url: result.url,
    }));

    res.json(videoResults);
  } catch (error) {
    res.status(500).send('Error fetching search results');
  }
});

// Endpoint untuk mendownload video
app.get('/download', (req, res) => {
  const { url } = req.query;
  if (!url) {
    return res.status(400).send('URL is required');
  }

  res.header('Content-Disposition', 'attachment; filename="video.mp4"');
  ytdl(url).pipe(res);
});

app.listen(PORT, () => {
  console.log(`Server is running on http://localhost:${PORT}`);
});
