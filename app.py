import os
import re
import requests
from flask import Flask, render_template, request, redirect

app = Flask(__name__)

def extract_video_id(url):
    """Extracts the YouTube video ID from a URL."""
    patterns = [
        r'(?:https?:\/\/)?(?:www\.)?youtube\.com\/watch\?v=([a-zA-Z0-9_-]{11})',
        r'(?:https?:\/\/)?(?:www\.)?youtu\.be\/([a-zA-Z0-9_-]{11})',
        r'(?:https?:\/\/)?(?:www\.)?youtube\.com\/embed\/([a-zA-Z0-9_-]{11})',
        r'(?:https?:\/\/)?(?:www\.)?youtube\.com\/v\/([a-zA-Z0-9_-]{11})'
    ]
    for pattern in patterns:
        match = re.search(pattern, url)
        if match:
            return match.group(1)
    return None

@app.route('/')
def index():
    """Renders the main page."""
    return render_template('index.html')

@app.route('/download', methods=['POST'])
def download():
    """
    Fetches video info from the RapidAPI endpoint.
    """
    video_url = request.form['url']
    video_id = extract_video_id(video_url)

    if not video_id:
        return render_template('index.html', error="Invalid YouTube URL provided.")

    # Securely get the API key from an environment variable
    api_key = os.environ.get('RAPIDAPI_KEY')
    if not api_key:
        return render_template('index.html', error="API Key is not configured on the server.")

    api_url = "https://youtube-media-downloader.p.rapidapi.com/v2/video/details"
    querystring = {"videoId": video_id}
    headers = {
        "x-rapidapi-key": api_key,
        "x-rapidapi-host": "youtube-media-downloader.p.rapidapi.com"
    }

    try:
        response = requests.get(api_url, headers=headers, params=querystring)
        response.raise_for_status()  # Raise an exception for bad status codes
        data = response.json()

        if not data.get('ok') or not data.get('result'):
            return render_template('index.html', error=f"API returned an error: {data.get('message', 'Unknown error')}")

        result = data['result']
        
        # --- Transform API data to the structure our template expects ---
        formats = []
        # Process videos
        for video_format in result.get('videos', []):
            formats.append({
                'url': video_format.get('url'),
                'note': f"{video_format.get('quality')}, {video_format.get('size')}",
                'type': 'Video',
                'ext': video_format.get('ext')
            })
        
        # Process audios
        for audio_format in result.get('audios', []):
             formats.append({
                'url': audio_format.get('url'),
                'note': f"Audio only, {audio_format.get('ext')}, {audio_format.get('size')}",
                'type': 'Audio',
                'ext': audio_format.get('ext')
            })

        video_info = {
            'title': result.get('title', 'No title'),
            'thumbnail': result.get('thumbnails', [{}])[0].get('url', ''),
            'formats': formats
        }
        
        return render_template('download.html', video=video_info)

    except requests.exceptions.RequestException as e:
        return render_template('index.html', error=f"Failed to connect to the download API. Error: {e}")
    except Exception as e:
        return render_template('index.html', error=f"An unexpected error occurred: {e}")

if __name__ == '__main__':
    # For local testing:
    # Ensure you have a .env file with RAPIDAPI_KEY="your_key"
    # Or run: export RAPIDAPI_KEY="your_key"
    app.run(debug=True)