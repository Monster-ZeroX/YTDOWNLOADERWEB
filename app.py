
import yt_dlp
from flask import Flask, render_template, request, redirect

app = Flask(__name__)

@app.route('/')
def index():
    """Renders the main page."""
    return render_template('index.html')

@app.route('/download', methods=['POST'])
def download():
    """
    Fetches video info and formats using yt-dlp.
    Renders a page for the user to select a download format.
    """
    url = request.form['url']
    if not url:
        return redirect('/')

    ydl_opts = {
        'noplaylist': True,
        'quiet': True,
        'no_warnings': True,
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            
            # Filter and sort formats
            formats = []
            for f in info.get('formats', []):
                # Include only formats with both video and audio, or audio-only/video-only
                if f.get('acodec') != 'none' and f.get('vcodec') != 'none':
                    resolution = f.get('format_note') or f.get('height')
                    if resolution:
                        formats.append({
                            'format_id': f['format_id'],
                            'ext': f['ext'],
                            'note': f"{resolution}p, {f['ext']}",
                            'type': 'Video'
                        })
                elif f.get('acodec') != 'none' and f.get('vcodec') == 'none':
                     formats.append({
                        'format_id': f['format_id'],
                        'ext': f['ext'],
                        'note': f"Audio only, ~{f.get('abr', 0)}kbps, {f['ext']}",
                        'type': 'Audio'
                    })

            # Remove duplicate notes for cleaner presentation
            unique_formats = []
            seen_notes = set()
            for f in sorted(formats, key=lambda x: (x['type'], x.get('height', 0)), reverse=True):
                if f['note'] not in seen_notes:
                    unique_formats.append(f)
                    seen_notes.add(f['note'])

            video_info = {
                'title': info.get('title', 'No title'),
                'thumbnail': info.get('thumbnail', ''),
                'formats': unique_formats,
                'original_url': info.get('webpage_url')
            }
            return render_template('download.html', video=video_info)

    except yt_dlp.utils.DownloadError as e:
        # Handle cases where the URL is invalid or the video is unavailable
        return render_template('index.html', error=f"Could not process URL. Please check if it's correct. Error: {e}")
    except Exception as e:
        return render_template('index.html', error=f"An unexpected error occurred: {e}")


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
                # Fallback if direct URL is not found
                return render_template('index.html', error="Could not get direct download link. Please try another format.")
    except Exception as e:
        return render_template('index.html', error=f"An error occurred while processing the download: {e}")


if __name__ == '__main__':
    app.run(debug=True)
