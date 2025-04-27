# Social Media Comment Analyzer API

A FastAPI application for extracting and analyzing comments from Instagram and YouTube.

## Features

- Extract metadata from Instagram posts
- Extract comments and metadata from YouTube videos
- Sentiment analysis on comments
- Background processing of requests
- API endpoints to submit URLs and check analysis status
- File download endpoints for results

## Project Structure

```
social-media-analyzer/
├── app/
│   ├── __init__.py
│   ├── main.py               # FastAPI application entry point
│   ├── routers/
│   │   ├── __init__.py
│   │   └── analyze.py        # API route handlers
│   ├── services/
│   │   ├── __init__.py
│   │   ├── instagram.py      # Instagram extraction logic
│   │   ├── youtube.py        # YouTube extraction logic
│   │   └── sentiment.py      # Sentiment analysis functionality
│   └── utils/
│       ├── __init__.py
│       ├── file_manager.py   # File saving/handling utilities
│       └── url_parser.py     # Functions to parse different URL formats
├── output/                   # Directory for generated files
├── .env.example              # Example environment variables
├── .gitignore                # Git ignore file
├── requirements.txt          # Project dependencies
└── README.md                 # Project documentation
```

## Installation

1. Clone this repository
2. Create a virtual environment: `python -m venv venv`
3. Activate the virtual environment:
   - Windows: `venv\Scripts\activate`
   - macOS/Linux: `source venv/bin/activate`
4. Install dependencies: `pip install -r requirements.txt`

## Configuration

1. Copy `.env.example` to `.env` and update with your YouTube API key
2. By default, output files are saved to an `output` directory which will be created automatically

## Running the API

```
uvicorn app.main:app --reload
```

The API will be available at http://127.0.0.1:8000

## API Documentation

FastAPI automatically generates API documentation:
- OpenAPI UI: http://127.0.0.1:8000/docs
- ReDoc: http://127.0.0.1:8000/redoc

## API Endpoints

### Submit a URL for analysis
```
POST /api/analyze
```
Request body:
```json
{
  "url": "https://www.youtube.com/watch?v=VIDEO_ID"
}
```
Response:
```json
{
  "request_id": "req_20250421235959_abc123",
  "status": "processing"
}
```

### Check analysis status
```
GET /api/status/{request_id}
```
Response (processing):
```json
{
  "request_id": "req_20250421235959_abc123",
  "status": "processing"
}
```
Response (completed):
```json
{
  "request_id": "req_20250421235959_abc123",
  "status": "completed",
  "file_urls": {
    "comments_csv": "/api/files/yt_comments_req_20250421235959_abc123_20250422000005.csv",
    "sentiment_csv": "/api/files/yt_sentiment_req_20250421235959_abc123_20250422000005.csv",
    "metadata_txt": "/api/files/yt_metadata_req_20250421235959_abc123_20250422000005.txt"
  }
}
```

### Download analysis files
```
GET /api/files/{filename}
```

## Notes

- Instagram API access is limited: this API can extract post metadata but cannot extract comments without user authentication
- YouTube API requires a valid API key and has rate limits
- In a production environment, consider:
  - Adding proper authentication to the API
  - Using a database to store jobs instead of in-memory storage
  - Setting up proper file serving with expiration policies