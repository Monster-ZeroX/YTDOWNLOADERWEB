
import yt_dlp
from flask import Flask, render_template, request, redirect, session, Response
import os
import tempfile
import secrets
import requests

app = Flask(__name__)
app.secret_key = secrets.token_hex(16)

def cleanup_session_cookie():
    """Removes any temporary cookie file stored in the session."""
    if 'cookie_file_path' in session:
        cookie_path = session.pop('cookie_file_path', None)
        if cookie_path and os.path.exists(cookie_path):
            try:
                os.remove(cookie_path)
            except OSError as e:
                app.logger.error(f"Error removing cookie file {cookie_path}: {e}")

@app.route('/')
def index():
    """Renders the main page."""
    cleanup_session_cookie()
    return render_template('index.html')

@app.route('/select', methods=['POST'])
def select_formats():
    """
    Fetches all available formats for a URL and presents them to the user
    on a selection page.
    """
    url = request.form['url']
    if not url:
        return redirect('/')

    cookie_file = request.files.get('cookie_file')
    cleanup_session_cookie()

    ydl_opts = {
        'quiet': True,
        'no_warnings': True,
    }

    if cookie_file and cookie_file.filename:
        fd, path = tempfile.mkstemp(suffix='.txt')
        cookie_file.save(path)
        session['cookie_file_path'] = path
        ydl_opts['cookiefile'] = path

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)

        print(f"yt-dlp info['formats']: {info.get('formats', [])}") # Debug log

        video_formats = []
        audio_formats = []

        for f in info.get('formats', []):
            print(f"  Format: id={f.get('format_id')}, protocol={f.get('protocol')}, vcodec={f.get('vcodec')}, acodec={f.get('acodec')}, ext={f.get('ext')}, url={f.get('url')}") # Debug log
            # Prioritize HLS and DASH protocols for adaptive streams
            if f.get('protocol') in ['m3u8_native', 'https', 'http']:
                # Video-only formats
                if f.get('vcodec') != 'none' and f.get('acodec') == 'none':
                    video_formats.append({
                        'format_id': f.get('format_id'),
                        'ext': f.get('ext'),
                        'resolution': f.get('resolution'),
                        'fps': f.get('fps'),
                        'url': f.get('url'),
                        'note': f.get('format_note', 'Video')
                    })
                # Audio-only formats
                elif f.get('acodec') != 'none' and f.get('vcodec') == 'none':
                    audio_formats.append({
                        'format_id': f.get('format_id'),
                        'ext': f.get('ext'),
                        'abr': f.get('abr'),
                        'url': f.get('url'),
                        'note': f.get('format_note', 'Audio')
                    })
        
        # Sort by quality (resolution for video, bitrate for audio)
        video_formats.sort(key=lambda v: v.get('resolution', '0x0').split('x')[1], reverse=True)
        audio_formats.sort(key=lambda a: a.get('abr', 0), reverse=True)

        if not video_formats or not audio_formats:
            return render_template('index.html', error="Could not find separate video and audio streams for quality selection. The video might be in an unsupported format.")

        return render_template('select_quality.html', 
                               video_formats=video_formats, 
                               audio_formats=audio_formats,
                               title=info.get('title', 'Unknown Title'),
                               thumbnail=info.get('thumbnail', ''))

    except Exception as e:
        return render_template('index.html', error=f"An error occurred: {e}")

@app.route('/process', methods=['POST'])
def process_download():
    """
    Receives the selected format URLs and passes them to the download page.
    """
    video_url = request.form.get('video_url')
    audio_url = request.form.get('audio_url')
    title = request.form.get('title')

    if not video_url or not audio_url:
        return render_template('index.html', error="You must select both a video and an audio quality.")

    video_info = {
        'title': title,
        'video_manifest_url': video_url,
        'audio_manifest_url': audio_url,
        'ext': 'mp4'
    }
    return render_template('download.html', video=video_info)


@app.route('/proxy')
def proxy():
    """
    A proxy to fetch cross-origin resources to bypass browser CORS restrictions.
    """
    url = request.args.get('url')
    if not url:
        return "No URL provided", 400

    try:
        req = requests.get(url, stream=True)
        return Response(req.iter_content(chunk_size=1024), content_type=req.headers['content-type'])
    except Exception as e:
        return f"Failed to proxy request: {e}", 500

if __name__ == '__main__':
    app.run(debug=True)
