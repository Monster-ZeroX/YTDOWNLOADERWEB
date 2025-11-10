
import yt_dlp
from flask import Flask, render_template, request, redirect, session
import os
import tempfile
from werkzeug.utils import secure_filename
import secrets

app = Flask(__name__)
# In a real production app, this should be loaded from an environment variable
app.secret_key = secrets.token_hex(16)

def get_formats(video_info):
    """Helper function to extract and sort formats for a single video."""
    formats = []
    for f in video_info.get('formats', []):
        is_video = f.get('vcodec') != 'none' and f.get('acodec') != 'none'
        is_audio = f.get('vcodec') == 'none' and f.get('acodec') != 'none'

        if is_video:
            resolution = f.get('format_note') or f.get('height')
            if resolution:
                formats.append({
                    'format_id': f['format_id'],
                    'ext': f['ext'],
                    'note': f"{resolution}p, {f['ext']}",
                    'type': 'Video'
                })
        elif is_audio:
            formats.append({
                'format_id': f['format_id'],
                'ext': f['ext'],
                'note': f"Audio, ~{f.get('abr', 0)}kbps, {f['ext']}",
                'type': 'Audio'
            })

    unique_formats = []
    seen_notes = set()
    for f in sorted(formats, key=lambda x: (x['type'], -int(x['note'].split('p')[0]) if 'p' in x['note'] else 0), reverse=True):
        if f['note'] not in seen_notes:
            unique_formats.append(f)
            seen_notes.add(f['note'])
    return unique_formats

@app.route('/')
def index():
    """Renders the main page and clears any old cookie file paths."""
    # Clean up any lingering session data
    if 'cookie_file_path' in session:
        if os.path.exists(session['cookie_file_path']):
            os.remove(session['cookie_file_path'])
        session.pop('cookie_file_path', None)
    return render_template('index.html')

@app.route('/download', methods=['POST'])
def download():
    """
    Fetches video/playlist info, saving cookie file path in session.
    """
    url = request.form['url']
    if not url:
        return redirect('/')

    cookie_file = request.files.get('cookie_file')
    download_playlist = request.form.get('download_playlist') == 'yes'
    
    # Clear any old cookie file path from the session
    if 'cookie_file_path' in session and os.path.exists(session['cookie_file_path']):
        os.remove(session['cookie_file_path'])
    session.pop('cookie_file_path', None)

    try:
        ydl_opts = {
            'quiet': True,
            'no_warnings': True,
            'noplaylist': not download_playlist,
        }

        if cookie_file and cookie_file.filename:
            fd, path = tempfile.mkstemp(suffix='.txt')
            cookie_file.save(path)
            # Store the path in the session
            session['cookie_file_path'] = path
            ydl_opts['cookiefile'] = path

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            
            if 'entries' in info and info['entries']:
                for entry in info['entries']:
                    if entry:
                        entry['formats'] = get_formats(entry)
                        entry['original_url'] = entry.get('webpage_url')
                return render_template('download.html', video=info)
            else:
                unique_formats = get_formats(info)
                video_info = {
                    'title': info.get('title', 'No title'),
                    'thumbnail': info.get('thumbnail', ''),
                    'formats': unique_formats,
                    'original_url': info.get('webpage_url')
                }
                return render_template('download.html', video=video_info)

    except yt_dlp.utils.DownloadError as e:
        return render_template('index.html', error=f"Could not process URL. Please check if it's correct. Error: {e}")
    except Exception as e:
        return render_template('index.html', error=f"An unexpected error occurred: {e}")

@app.route('/process_download')
def process_download():
    """
    Gets the direct download URL using the cookie path from the session.
    """
    url = request.args.get('url')
    format_id = request.args.get('format_id')

    if not url or not format_id:
        return redirect('/')

    cookie_path = session.get('cookie_file_path')
    
    try:
        ydl_opts = {
            'format': format_id,
            'quiet': True,
        }

        if cookie_path and os.path.exists(cookie_path):
            ydl_opts['cookiefile'] = cookie_path

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            download_url = info.get('url')
            if download_url:
                return redirect(download_url)
            else:
                return render_template('index.html', error="Could not get direct download link. Please try another format.")
    except Exception as e:
        return render_template('index.html', error=f"An error occurred while processing the download: {e}")
    finally:
        # Clean up the cookie file after the first use
        if cookie_path and os.path.exists(cookie_path):
            os.remove(cookie_path)
            session.pop('cookie_file_path', None)

if __name__ == '__main__':
    app.run(debug=True)
