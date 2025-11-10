
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

This application is ready to be deployed to Heroku.

### Prerequisites

-   A free Heroku account.
-   The [Heroku CLI](https://devcenter.heroku.com/articles/heroku-cli) installed.
-   [Git](https://git-scm.com/downloads) installed.

### Steps

1.  **Log in to Heroku from your terminal:**
    ```bash
    heroku login
    ```

2.  **Navigate to the project directory and create a new Heroku app:**
    ```bash
    cd YTDOWNLOADERWEB
    heroku create your-unique-app-name
    ```
    If you omit a name, Heroku will generate a random one.

3.  **Add a non-Python buildpack for FFmpeg (optional but recommended):**
    `yt-dlp` sometimes relies on FFmpeg for processing certain formats. Adding this buildpack prevents potential issues.
    ```bash
    heroku buildpacks:add --index 1 heroku-community/ffmpeg
    ```

4.  **Push your code to Heroku:**
    This command will push the `main` branch of your repository to the `heroku` remote, which will trigger a build and deployment.
    ```bash
    git push heroku main
    ```

5.  **Open your application:**
    ```bash
    heroku open
    ```
    Your YouTube Downloader website is now live!

---

## Disclaimer

This project is intended for educational purposes only. Downloading copyrighted content without the owner's permission may be illegal in your country. Please respect copyright laws and the terms of service of YouTube. The developers of this project do not condone piracy and are not responsible for any misuse of this tool.
