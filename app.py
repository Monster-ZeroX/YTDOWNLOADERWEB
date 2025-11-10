
import yt_dlp
from flask import Flask, render_template, request, redirect, session
import os
import tempfile
import secrets

app = Flask(__name__)
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
    Uses yt-dlp to extract a single, direct download URL.
    """
    url = request.form['url']
    if not url:
        return redirect('/')

    cookie_file = request.files.get('cookie_file')
    
    # Clean up any previous cookie file from the session
    if 'cookie_file_path' in session and os.path.exists(session['cookie_file_path']):
        os.remove(session['cookie_file_path'])
    session.pop('cookie_file_path', None)

    try:
        # This format string prefers a single, pre-merged MP4 file.
        # It's the most reliable format for direct browser downloads.
        ydl_opts = {
            'quiet': True,
            'no_warnings': True,
            'format': 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best',
        }

        if cookie_file and cookie_file.filename:
            # Save the cookie file to a temporary location
            fd, path = tempfile.mkstemp(suffix='.txt')
            cookie_file.save(path)
            session['cookie_file_path'] = path
            ydl_opts['cookiefile'] = path

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            
            # We need to find the URL of the requested format after extraction
            download_url = info.get('url')

            if not download_url:
                 return render_template('index.html', error="Could not find a direct download link for this video. It might only be available as a protected stream.")

            video_info = {
                'title': info.get('title', 'No title'),
                'thumbnail': info.get('thumbnail', ''),
                'download_url': download_url,
                'ext': info.get('ext', 'mp4')
            }

            return render_template('download.html', video=video_info)

    except yt_dlp.utils.DownloadError as e:
        error_str = str(e)
        if 'Sign in to confirm' in error_str or 'nsig extraction' in error_str:
            error_message = "This video is protected. Please try again using the 'Upload cookies.txt' option."
        else:
            error_message = f"Could not process URL. Please check if it's correct. Error: {error_str}"
        return render_template('index.html', error=error_message)
    except Exception as e:
        return render_template('index.html', error=f"An unexpected error occurred: {e}")
    finally:
        # Clean up the cookie file after the request is done
        if 'cookie_file_path' in session:
            cookie_path = session.pop('cookie_file_path', None)
            if cookie_path and os.path.exists(cookie_path):
                os.remove(cookie_path)

if __name__ == '__main__':
    app.run(debug=True)
