
import yt_dlp
from flask import Flask, render_template, request, redirect
import os
import tempfile
from werkzeug.utils import secure_filename

app = Flask(__name__)

def get_formats(video_info):
    """Helper function to extract and sort formats for a single video."""
    formats = []
    for f in video_info.get('formats', []):
        # Include only formats with both video and audio, or audio-only
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

    # Remove duplicate notes for a cleaner presentation
    unique_formats = []
    seen_notes = set()
    # Sort by type (Video first) and then by resolution (higher first)
    for f in sorted(formats, key=lambda x: (x['type'], -int(x['note'].split('p')[0]) if 'p' in x['note'] else 0), reverse=True):
        if f['note'] not in seen_notes:
            unique_formats.append(f)
            seen_notes.add(f['note'])
    return unique_formats

@app.route('/')
def index():
    """Renders the main page."""
    return render_template('index.html')

@app.route('/download', methods=['POST'])
def download():
    """
    Fetches video/playlist info and formats using yt-dlp.
    Handles cookie files and playlist options.
    """
    url = request.form['url']
    if not url:
        return redirect('/')

    cookie_file = request.files.get('cookie_file')
    download_playlist = request.form.get('download_playlist') == 'yes'
    
    cookie_temp_file = None
    
    try:
        ydl_opts = {
            'quiet': True,
            'no_warnings': True,
            'noplaylist': not download_playlist,
        }

        # Securely handle the cookie file
        if cookie_file and cookie_file.filename:
            # Save the uploaded file to a temporary file
            fd, path = tempfile.mkstemp(suffix='.txt')
            cookie_temp_file = path
            with os.fdopen(fd, 'wb') as tmp:
                cookie_file.save(tmp)
            ydl_opts['cookiefile'] = cookie_temp_file

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            
            # If it's a playlist
            if 'entries' in info and info['entries']:
                for entry in info['entries']:
                    if entry: # Some entries can be None if deleted
                        entry['formats'] = get_formats(entry)
                        entry['original_url'] = entry.get('webpage_url')
                return render_template('download.html', video=info)
            
            # If it's a single video
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
    finally:
        # Ensure the temporary cookie file is always deleted
        if cookie_temp_file and os.path.exists(cookie_temp_file):
            os.remove(cookie_temp_file)


@app.route('/process_download')
def process_download():
    """
    Gets the direct download URL for the selected format and redirects the user.
    This avoids server-side downloading, saving bandwidth.
    """
    url = request.args.get('url')
    format_id = request.args.get('format_id')
    if not url or not format_id:
        return redirect('/')

    # Note: Cookies are not passed here. This can be a limitation.
    # For most cases, the direct URL is accessible without cookies once obtained.
    # If direct link access also requires cookies, this part would need enhancement
    # (e.g., passing a token to retrieve the cookie file path).
    ydl_opts = {
        'format': format_id,
        'quiet': True,
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            download_url = info.get('url')
            if download_url:
                return redirect(download_url)
            else:
                return render_template('index.html', error="Could not get direct download link. Please try another format.")
    except Exception as e:
        return render_template('index.html', error=f"An error occurred while processing the download: {e}")


if __name__ == '__main__':
    app.run(debug=True)
