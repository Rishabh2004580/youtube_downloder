import os
from pathlib import Path

import yt_dlp
from flask import Flask, render_template, request, send_from_directory

app = Flask(__name__)

DOWNLOAD_FOLDER = "downloads"
os.makedirs(DOWNLOAD_FOLDER, exist_ok=True)


def build_format_string(media_type: str, quality: str) -> str:
    if media_type == "audio":
        return "bestaudio[ext=m4a]/bestaudio/best"

    quality_formats = {
        "best": "best[acodec!=none][vcodec!=none]/best[ext=mp4][acodec!=none][vcodec!=none]/best[ext=mkv][acodec!=none][vcodec!=none]",
        "1080": "best[height<=1080][acodec!=none][vcodec!=none]/best[ext=mp4][height<=1080][acodec!=none][vcodec!=none]/best[acodec!=none][vcodec!=none]",
        "720": "best[height<=720][acodec!=none][vcodec!=none]/best[ext=mp4][height<=720][acodec!=none][vcodec!=none]/best[acodec!=none][vcodec!=none]",
        "480": "best[height<=480][acodec!=none][vcodec!=none]/best[ext=mp4][height<=480][acodec!=none][vcodec!=none]/best[acodec!=none][vcodec!=none]",
    }
    return quality_formats.get(quality, quality_formats["best"])


@app.route('/')
def home():
    return render_template(
        'index.html',
        message=None,
        message_type=None,
        download_file=None,
        url_value='',
        media_type='video',
        quality='best'
    )


@app.route('/downloads/<path:filename>')
def serve_download(filename: str):
    return send_from_directory(DOWNLOAD_FOLDER, filename, as_attachment=True)


@app.route('/download', methods=['POST'])
def download():
    url = request.form.get('url', '').strip()
    media_type = request.form.get('media_type', 'video').strip().lower()
    quality = request.form.get('quality', 'best').strip().lower()

    if media_type not in {'video', 'audio'}:
        media_type = 'video'

    if quality not in {'best', '1080', '720', '480'}:
        quality = 'best'

    if not url:
        return render_template(
            'index.html',
            message='Please paste a YouTube URL.',
            message_type='error',
            download_file=None,
            url_value=url,
            media_type=media_type,
            quality=quality
        ), 400

    if 'youtube.com' not in url and 'youtu.be' not in url:
        return render_template(
            'index.html',
            message='Please enter a valid YouTube link.',
            message_type='error',
            download_file=None,
            url_value=url,
            media_type=media_type,
            quality=quality
        ), 400

    format_string = build_format_string(media_type, quality)
    ydl_opts = {
        'format': format_string,
        'outtmpl': f'{DOWNLOAD_FOLDER}/%(title)s.%(ext)s',
        'noplaylist': True,
        'quiet': True,
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            title = info.get('title', 'video')
            file_path = Path(ydl.prepare_filename(info))

            download_file = file_path.name if file_path.exists() else None

        return render_template(
            'index.html',
            message=f'Download completed: {title}',
            message_type='success',
            download_file=download_file,
            url_value=url,
            media_type=media_type,
            quality=quality
        )
    except Exception as e:
        return render_template(
            'index.html',
            message=f'Download failed: {e}',
            message_type='error',
            download_file=None,
            url_value=url,
            media_type=media_type,
            quality=quality
        ), 400

if __name__ == '__main__':
    app.run(debug=True)