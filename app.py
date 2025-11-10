
import yt_dlp
from flask import Flask, render_template, request, redirect, session
import os
import tempfile
import secrets
import re

app = Flask(__name__)
# In a real production app, this should be loaded from an environment variable
app.secret_key = secrets.token_hex(16)

@app.route('/')
def index():
    """Renders the main page and clears any old session data."""
    if 'cookie_file_path' in session:
        if os.path.exists(session['cookie_file_path']):
            os.remove(session['cookie_file_path'])
        session.pop('cookie_file_path', None)
    return render_template('index.html')

@app.route('/download', methods=['POST'])
def download():
    """
    Uses yt-dlp to extract a single, best-quality, direct-downloadable link.
    """
    url = request.form['url']
    if not url:
        return redirect('/')

    cookie_file = request.files.get('cookie_file')
    
    # Clean up any old cookie file from a previous session
    if 'cookie_file_path' in session and os.path.exists(session['cookie_file_path']):
        os.remove(session['cookie_file_path'])
    session.pop('cookie_file_path', None)

    try:
        # This format string is the key. It tells yt-dlp to find the best format
        # that has both video and audio, is not a manifest file, and prefers mp4.
        # It will automatically select the best single file for download.
        ydl_opts = {
            'quiet': True,
            'no_warnings': True,
            'format': 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best',
        }

        if cookie_file and cookie_file.filename:
            fd, path = tempfile.mkstemp(suffix='.txt')
            cookie_file.save(path)
            session['cookie_file_path'] = path
            ydl_opts['cookiefile'] = path

        # We only need to extract the info once. yt-dlp will process the format
        # selector and provide the direct URL for the chosen format.
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            
            video_info = {
                'title': info.get('title', 'No title'),
                'thumbnail': info.get('thumbnail', ''),
                'download_url': info.get('url'), # The single, direct download URL
                'ext': info.get('ext', 'mp4')
            }

            if not video_info['download_url']:
                 return render_template('index.html', error="Could not find a direct downloadable link for this video. It may be a live stream or protected.")

            return render_template('download.html', video=video_info)

    except yt_dlp.utils.DownloadError as e:
        error_str = str(e)
        if 'Sign in to confirm' in error_str or 'nsig extraction' in error_str:
            error_message = "This video is protected. Please try again using the 'Upload cookies.txt' option. See instructions on the homepage."
        else:
            error_message = f"Could not process URL. Please check if it's correct. Error: {error_str}"
        return render_template('index.html', error=error_message)
    except Exception as e:
        return render_template('index.html', error=f"An unexpected error occurred: {e}")
    finally:
        # Clean up cookie file after the request is done
        if 'cookie_file_path' in session:
            cookie_path = session.pop('cookie_file_path', None)
            if cookie_path and os.path.exists(cookie_path):
                os.remove(cookie_path)

if __name__ == '__main__':
    app.run(debug=True)
