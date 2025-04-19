const express = require('express');
const ytdl = require('ytdl-core');
const ytsr = require('ytsr');
const ffmpeg = require('fluent-ffmpeg');
const ffmpegPath = require('ffmpeg-static');
const fs = require('fs');
const path = require('path');
const cors = require('cors');
const app = express();

// Konfigurasi
const PORT = process.env.PORT || 3001;
const DOWNLOAD_FOLDER = path.join(__dirname, 'downloads');

// Buat folder downloads jika belum ada
if (!fs.existsSync(DOWNLOAD_FOLDER)) {
    fs.mkdirSync(DOWNLOAD_FOLDER);
}

// Middleware
app.use(cors());
app.use(express.json());

// Endpoint untuk pencarian YouTube
app.get('/api/search', async (req, res) => {
    try {
        const { query } = req.query;
        if (!query) {
            return res.status(400).json({ error: 'Query pencarian diperlukan' });
        }

        const filters = await ytsr.getFilters(query);
        const filter = filters.get('Type').get('Video');
        const options = {
            limit: 15, // Tampilkan 15 hasil
            nextpageRef: filter.url
        };

        const searchResults = await ytsr(null, options);
        
        const videos = searchResults.items
            .filter(item => item.type === 'video')
            .map(item => ({
                id: item.id,
                title: item.title,
                url: item.url,
                thumbnail: item.bestThumbnail.url,
                duration: item.duration,
                author: item.author.name
            }));

        res.json(videos);
    } catch (error) {
        console.error(error);
        res.status(500).json({ error: 'Gagal melakukan pencarian' });
    }
});

// Endpoint untuk mendapatkan info video
app.get('/api/video-info', async (req, res) => {
    try {
        const { url } = req.query;
        if (!ytdl.validateURL(url)) {
            return res.status(400).json({ error: 'URL YouTube tidak valid' });
        }

        const info = await ytdl.getInfo(url);
        res.json({
            title: info.videoDetails.title,
            thumbnail: info.videoDetails.thumbnails[info.videoDetails.thumbnails.length - 1].url,
            duration: info.videoDetails.lengthSeconds,
            formats: info.formats.filter(f => f.hasVideo || f.hasAudio)
        });
    } catch (error) {
        console.error(error);
        res.status(500).json({ error: 'Gagal mendapatkan info video' });
    }
});

// Endpoint untuk download
app.get('/api/download', async (req, res) => {
    try {
        const { url, format } = req.query;
        
        if (!ytdl.validateURL(url)) {
            return res.status(400).json({ error: 'URL YouTube tidak valid' });
        }

        const info = await ytdl.getInfo(url);
        const title = info.videoDetails.title.replace(/[^\w\s]/gi, '');
        const filePath = path.join(DOWNLOAD_FOLDER, `${title}.${format}`);

        if (format === 'mp3') {
            const audioStream = ytdl(url, { quality: 'highestaudio' });
            
            ffmpeg(audioStream)
                .setFfmpegPath(ffmpegPath)
                .audioBitrate(128)
                .save(filePath)
                .on('end', () => {
                    res.download(filePath, `${title}.mp3`, (err) => {
                        if (err) console.error(err);
                        fs.unlinkSync(filePath);
                    });
                });
        } else {
            const videoStream = ytdl(url, { quality: 'highest' });
            videoStream.pipe(fs.createWriteStream(filePath))
                .on('finish', () => {
                    res.download(filePath, `${title}.mp4`, (err) => {
                        if (err) console.error(err);
                        fs.unlinkSync(filePath);
                    });
                });
        }
    } catch (error) {
        console.error(error);
        res.status(500).json({ error: 'Gagal mengunduh video' });
    }
});

// Jalankan server
app.listen(PORT, () => {
    console.log(`Server backend berjalan di http://localhost:${PORT}`);
});
