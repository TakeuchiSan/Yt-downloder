const express = require('express');
const ytdl = require('ytdl-core');
const ffmpeg = require('fluent-ffmpeg');
const fs = require('fs');
const path = require('path');
const { exec } = require('child_process');
const app = express();

// Set EJS as view engine
app.set('view engine', 'ejs');
app.set('views', path.join(__dirname, 'views'));

// Middleware
app.use(express.static('public'));
app.use(express.urlencoded({ extended: true }));

// Routes
app.get('/', (req, res) => {
    res.render('index');
});

app.post('/download', async (req, res) => {
    try {
        const videoUrl = req.body.url;
        const format = req.body.format;
        
        if (!ytdl.validateURL(videoUrl)) {
            return res.status(400).send('URL YouTube tidak valid');
        }

        const info = await ytdl.getInfo(videoUrl);
        const title = info.videoDetails.title.replace(/[^\w\s]/gi, '');
        const tempPath = path.join(__dirname, 'temp', `${Date.now()}_${title.replace(/\s+/g, '_')}`);
        const outputPath = path.join(__dirname, 'public', 'downloads', `${title}.${format}`);

        // Create necessary directories if they don't exist
        [path.join(__dirname, 'temp'), path.join(__dirname, 'public', 'downloads')].forEach(dir => {
            if (!fs.existsSync(dir)) fs.mkdirSync(dir, { recursive: true });
        });

        if (format === 'mp3') {
            // Download audio using child process
            const audioStream = ytdl(videoUrl, { quality: 'highestaudio' });
            const tempAudioPath = `${tempPath}.webm`;
            
            audioStream.pipe(fs.createWriteStream(tempAudioPath))
                .on('finish', () => {
                    // Convert to MP3 using FFmpeg via child process
                    exec(`ffmpeg -i "${tempAudioPath}" -vn -ab 128k -ar 44100 -y "${outputPath}"`, 
                        (error) => {
                            fs.unlinkSync(tempAudioPath);
                            if (error) {
                                console.error(error);
                                return res.status(500).send('Gagal mengkonversi ke MP3');
                            }
                            res.download(outputPath, `${title}.mp3`, () => {
                                fs.unlinkSync(outputPath);
                            });
                        }
                    );
                });
        } else {
            // Download MP4 directly
            const videoStream = ytdl(videoUrl, { quality: 'highest' });
            videoStream.pipe(fs.createWriteStream(outputPath))
                .on('finish', () => {
                    res.download(outputPath, `${title}.mp4`, () => {
                        fs.unlinkSync(outputPath);
                    });
                });
        }
    } catch (error) {
        console.error(error);
        res.status(500).send('Terjadi kesalahan saat mengunduh video');
    }
});

// Start server
const PORT = process.env.PORT || 3000;
app.listen(PORT, () => {
    console.log(`Server berjalan di http://localhost:${PORT}`);
    console.log('Pastikan FFmpeg terinstall di sistem Anda!');
    console.log('Untuk Termux: pkg install ffmpeg');
});
