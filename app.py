import yt_dlp
from flask import Flask, render_template, request, redirect, session
import os
import tempfile
import secrets

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
    Uses yt-dlp to extract the HLS manifest URL (.m3u8) for client-side processing.
    """
    url = request.form['url']
    if not url:
        return redirect('/')

    cookie_file = request.files.get('cookie_file')
    
    if 'cookie_file_path' in session and os.path.exists(session['cookie_file_path']):
        os.remove(session['cookie_file_path'])
    session.pop('cookie_file_path', None)

    try:
        # This format string specifically asks for the HLS manifest
        ydl_opts = {
            'quiet': True,
            'no_warnings': True,
            'format': 'bestvideo[protocol=m3u8_native]+bestaudio[protocol=m3u8_native]/best[protocol=m3u8_native]',
        }

        if cookie_file and cookie_file.filename:
            fd, path = tempfile.mkstemp(suffix='.txt')
            cookie_file.save(path)
            session['cookie_file_path'] = path
            ydl_opts['cookiefile'] = path

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            
            video_info = {
                'title': info.get('title', 'No title'),
                'thumbnail': info.get('thumbnail', ''),
                'manifest_url': info.get('url'), # The HLS manifest URL
                'ext': 'mp4' # We will be creating an mp4 file
            }

            if not video_info['manifest_url']:
                 return render_template('index.html', error="Could not find a suitable HLS stream for this video. It may be a live stream or protected in a way that is not supported.")

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