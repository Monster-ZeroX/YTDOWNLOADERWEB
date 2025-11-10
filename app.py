import yt_dlp
from flask import Flask, render_template, request, redirect, session
import os
import tempfile
import secrets
import re

app = Flask(__name__)
# In a real production app, this should be loaded from an environment variable
app.secret_key = secrets.token_hex(16)

def get_formats(video_info):
    """
    Helper function to extract and sort formats, including their direct download URLs.
    """
    formats = []
    for f in video_info.get('formats', []):
        # Only include formats that have a direct URL
        if not f.get('url'):
            continue

        is_video = f.get('vcodec', 'none') != 'none' and f.get('acodec', 'none') != 'none'
        is_audio = f.get('vcodec', 'none') == 'none' and f.get('acodec', 'none') != 'none'

        if is_video:
            resolution = f.get('format_note') or f.get('height')
            if resolution:
                formats.append({
                    'format_id': f['format_id'],
                    'ext': f['ext'],
                    'note': f"{resolution}p, {f['ext']}",
                    'type': 'Video',
                    'url': f['url'] # Include the direct URL
                })
        elif is_audio:
            formats.append({
                'format_id': f['format_id'],
                'ext': f['ext'],
                'note': f"Audio, ~{f.get('abr', 0)}kbps, {f['ext']}",
                'type': 'Audio',
                'url': f['url'] # Include the direct URL
            })

    unique_formats = []
    seen_notes = set()
    # Sort by type (Video first) and then by resolution (higher first)
    for f in sorted(formats, key=lambda x: (x['type'], -int(re.search(r'(\d+)', x['note']).group(1)) if 'p' in x['note'] else 0), reverse=True):
        if f['note'] not in seen_notes:
            unique_formats.append(f)
            seen_notes.add(f['note'])
    
    return unique_formats

@app.route('/')
def index():
    """Renders the main page and clears any old cookie file paths."""
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
    
    if 'cookie_file_path' in session and os.path.exists(session['cookie_file_path']):
        os.remove(session['cookie_file_path'])
    session.pop('cookie_file_path', None)

    try:
        ydl_opts = {
            'quiet': True,
            'no_warnings': True,
            'noplaylist': not download_playlist,
            'format_sort': ['res', 'ext', 'vcodec'], # Prioritize resolution, then extension, then video codec
        }

        if cookie_file and cookie_file.filename:
            fd, path = tempfile.mkstemp(suffix='.txt')
            cookie_file.save(path)
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
        error_str = str(e)
        if 'Sign in to confirm' in error_str or 'nsig extraction' in error_str:
            error_message = "This video is protected. Please try again using the 'Upload cookies.txt' option. See instructions on the homepage."
        else:
            error_message = f"Could not process URL. Please check if it's correct. Error: {error_str}"
        return render_template('index.html', error=error_message)
    except Exception as e:
        return render_template('index.html', error=f"An unexpected error occurred: {e}")

# The /process_download route is no longer needed as direct URLs are provided.
# The cookie file is cleaned up when the session is cleared or overwritten.

if __name__ == '__main__':
    app.run(debug=True)