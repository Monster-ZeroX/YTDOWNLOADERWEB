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
    """Renders the main page."""
    return render_template('index.html')

@app.route('/download', methods=['POST'])
def download():
    """
    Fetches video/playlist info, passing cookie data to the template.
    """
    url = request.form['url']
    if not url:
        return redirect('/')

    cookie_file = request.files.get('cookie_file')
    download_playlist = request.form.get('download_playlist') == 'yes'
    
    cookie_data_string = ""
    if cookie_file and cookie_file.filename:
        cookie_data_string = cookie_file.read().decode('utf-8')

    cookie_temp_file = None
    try:
        ydl_opts = {
            'quiet': True,
            'no_warnings': True,
            'noplaylist': not download_playlist,
        }

        if cookie_data_string:
            fd, path = tempfile.mkstemp(suffix='.txt')
            cookie_temp_file = path
            with os.fdopen(fd, 'w', encoding='utf-8') as tmp:
                tmp.write(cookie_data_string)
            ydl_opts['cookiefile'] = cookie_temp_file

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            
            # Pass cookie data to the template for the next step
            if 'entries' in info and info['entries']:
                for entry in info['entries']:
                    if entry:
                        entry['formats'] = get_formats(entry)
                        entry['original_url'] = entry.get('webpage_url')
                return render_template('download.html', video=info, cookie_data=cookie_data_string)
            else:
                unique_formats = get_formats(info)
                video_info = {
                    'title': info.get('title', 'No title'),
                    'thumbnail': info.get('thumbnail', ''),
                    'formats': unique_formats,
                    'original_url': info.get('webpage_url')
                }
                return render_template('download.html', video=video_info, cookie_data=cookie_data_string)

    except yt_dlp.utils.DownloadError as e:
        return render_template('index.html', error=f"Could not process URL. Please check if it's correct. Error: {e}")
    except Exception as e:
        return render_template('index.html', error=f"An unexpected error occurred: {e}")
    finally:
        if cookie_temp_file and os.path.exists(cookie_temp_file):
            os.remove(cookie_temp_file)

@app.route('/process_download', methods=['POST'])
def process_download():
    """
    Gets the direct download URL using cookies if provided.
    """
    url = request.form.get('url')
    format_id = request.form.get('format_id')
    cookie_data = request.form.get('cookie_data')

    if not url or not format_id:
        return redirect('/')

    cookie_temp_file = None
    try:
        ydl_opts = {
            'format': format_id,
            'quiet': True,
        }

        if cookie_data:
            fd, path = tempfile.mkstemp(suffix='.txt')
            cookie_temp_file = path
            with os.fdopen(fd, 'w', encoding='utf-8') as tmp:
                tmp.write(cookie_data)
            ydl_opts['cookiefile'] = cookie_temp_file

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
        if cookie_temp_file and os.path.exists(cookie_temp_file):
            os.remove(cookie_temp_file)

if __name__ == '__main__':
    app.run(debug=True)