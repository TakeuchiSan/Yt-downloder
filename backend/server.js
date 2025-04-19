const express = require('express');
const ytdl = require('ytdl-core');
const cors = require('cors');
const app = express();
const PORT = process.env.PORT || 5000;

app.use(cors());
app.use(express.json());

// Rute untuk root URL
app.get('/', (req, res) => {
    res.send('YouTube Downloader API is running. Use /search to get video info.');
});

// Endpoint untuk mencari video
app.get('/search', async (req, res) => {
    const { url } = req.query;
    if (!url) {
        return res.status(400).send('URL is required');
    }

    try {
        const info = await ytdl.getInfo(url);
        const formats = ytdl.filterFormats(info.formats, 'audioandvideo');
        const results = formats.map(format => ({
            title: info.videoDetails.title,
            thumbnail: info.videoDetails.thumbnails[0].url,
            url: format.url,
            quality: format.qualityLabel,
            type: format.mimeType.includes('audio') ? 'mp3' : 'mp4'
        }));
        res.json(results);
    } catch (error) {
        res.status(500).send('Error fetching video info');
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
