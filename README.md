# Bilibili Trend Analyst (B站趋势分析仪)

A powerful tool for analyzing Bilibili creators, trends, and video performance. Built with Python (FastAPI) and modern web technologies.

## Features

- 🔍 **Smart Search**: Search for trends/keywords and get a curated list of relevant creators.
- 📊 **Deep Analysis**: Analyze creator performance, weekly update frequency, and average views.
- 🧠 **AI Insight**: Automatic content summarization and audience reaction analysis.
- 📉 **Market Dashboard**: Visualize competition landscape, audience positioning, and market gaps.
- 🛡️ **Robust Fallback**: Advanced anti-scraping bypass and multi-stage fallback mechanisms ensure data availability.

## Setup

1.  **Clone the repository**
2.  **Install dependencies**:
    ```bash
    pip install -r requirements.txt
    ```
3.  **Configuration**:
    - Copy `.env.example` to `.env`
    - Fill in your Bilibili `SESSDATA` (Cookie) for authenticated access (Required for full stats).
4.  **Run the server**:
    ```bash
    python web_app.py
    ```
5.  **Access**: Open `http://localhost:8000`

## Tech Stack

- **Backend**: FastAPI, Requests
- **Frontend**: HTML5, Tailwind CSS (CDN), Jinja2 Templates
- **Design**: Glassmorphism, Neon Dark Mode

## License

MIT
