
# YouTube Downloader Web App

A simple, clean, and modern web application to download YouTube videos and audio. Built with Python (Flask) and `yt-dlp`, and designed with an iOS-inspired aesthetic.

![Screenshot of the App](https://via.placeholder.com/680x400.png?text=App+Screenshot+Goes+Here)

## Features

-   **Simple Interface:** Just paste a YouTube URL and go.
-   **Format Selection:** Choose from available video and audio-only formats.
-   **Direct Downloads:** Links redirect straight to the file, saving server bandwidth.
-   **iOS-Inspired UI:** Clean, modern, and responsive design.
-   **Deployable on Heroku:** Includes all necessary files for a one-click deployment.

## Tech Stack

-   **Backend:** Python 3, Flask
-   **YouTube Interaction:** `yt-dlp`
-   **WSGI Server:** Gunicorn
-   **Frontend:** HTML5, CSS3 (No JavaScript needed for core functionality)
-   **Hosting:** Heroku

---

## Local Development Setup

To run this application on your local machine, follow these steps.

### Prerequisites

-   Python 3.7+
-   `pip` (Python package installer)

### Installation

1.  **Clone the repository:**
    ```bash
    git clone https://github.com/YOUR_USERNAME/YTDOWNLOADERWEB.git
    cd YTDOWNLOADERWEB
    ```

2.  **Create a virtual environment (recommended):**
    ```bash
    # For macOS/Linux
    python3 -m venv venv
    source venv/bin/activate

    # For Windows
    python -m venv venv
    .\venv\Scripts\activate
    ```

3.  **Install the dependencies:**
    ```bash
    pip install -r requirements.txt
    ```

4.  **Run the Flask application:**
    ```bash
    flask run
    ```
    The application will be available at `http://127.0.0.1:5000`.

---

## Deployment to Heroku

Once you have pushed this repository to your own GitHub account, you can deploy it to Heroku by clicking the button below.

[![Deploy to Heroku](https://www.herokucdn.com/deploy/button.svg)](https://heroku.com/deploy?template=https://github.com/Monster-ZeroX/YTDOWNLOADERWEB)

**Note:** Remember to replace `YOUR_USERNAME` in the button's link within the `README.md` file with your actual GitHub username for the button to work correctly from your repository. The `app.json` file will handle the rest of the setup automatically.

---

## Disclaimer

This project is intended for educational purposes only. Downloading copyrighted content without the owner's permission may be illegal in your country. Please respect copyright laws and the terms of service of YouTube. The developers of this project do not condone piracy and are not responsible for any misuse of this tool.
