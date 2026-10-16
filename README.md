# EduClip-Ai — AI-Powered Educational Video Content Curator

EduClip-Ai is a web application that helps users discover educational topics, curate relevant video content, generate timestamped transcripts, and prepare short-form educational clips.

The project combines a React frontend, Django REST backend, AI-powered transcription, and video-processing tools in a single workflow.

## Features

- **AI Topic Generation:** Generate and browse educational topics.
- **Video Curation:** Browse and manage educational video records.
- **YouTube Transcription:** Generate timestamped transcripts from supported YouTube videos.
- **Caption Import:** Import existing subtitle or caption files.
- **Transcript Management:** View and manage transcript segments.
- **Clip Creation:** Select transcript portions for short-form video creation.
- **Narrated Videos:** View and manage generated narrated MP4 files.
- **Web Interface:** Access project functionality through a React-based interface.

Feature availability depends on the current implementation, configuration, and external service access.

## Technology Stack

### Frontend
- React
- JavaScript
- Vite
- Axios
- React Router
- HTML and CSS

### Backend
- Python
- Django
- Django REST Framework
- SQLite

### AI and Media Processing
- Faster-Whisper for speech transcription
- yt-dlp for supported YouTube media processing
- FFmpeg-compatible media processing
- Configured AI services for supported AI features

## Project Structure

```text
EduClip-Ai/
├── backend/
│   ├── config/
│   ├── core/
│   └── manage.py
├── frontend/
│   ├── public/
│   ├── src/
│   ├── package.json
│   └── vite.config.js
├── requirements.txt
├── .gitignore
└── README.md
```

## Prerequisites

- Python
- Node.js and npm
- Git
- FFmpeg or a compatible media-processing setup for features that require it
- API credentials for any configured external AI services

## Installation and Setup

### 1. Clone the repository

Replace `YOUR_USERNAME` with your GitHub username.

```bash
git clone https://github.com/YOUR_USERNAME/EduClip-Ai.git
cd EduClip-Ai
```

### 2. Set up the Python environment

From the project root, run these commands in Windows PowerShell:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

### 3. Configure environment variables

Create a local `frontend/.env` file containing the frontend API configuration:

```env
VITE_API_BASE_URL=http://127.0.0.1:8000/api
```

Use the actual API base URL expected by the existing frontend. If your application uses a different URL, retain that configuration.

Create any additional backend environment variables required by your implementation. Keep credentials and private configuration out of GitHub.

### 4. Start the Django backend

Open a terminal in the project root and run:

```powershell
cd backend
python manage.py migrate
python manage.py runserver
```

The default Django development server address is:

`http://127.0.0.1:8000/`

### 5. Start the React frontend

Open a second terminal in the project root:

```powershell
cd frontend
npm install
npm run dev
```

Open the local URL displayed by Vite in your terminal.

## Application Workflow

1. Generate or browse educational topics.
2. Select relevant educational video content.
3. Generate or import a transcript.
4. Review timestamped transcript segments.
5. Select content for clip creation.
6. Generate and manage supported video outputs.

The exact workflow depends on the implemented features and available media-processing tools.

## Security and Repository Guidelines

- Never commit API keys, passwords, or private environment files.
- Keep `.env` files out of version control.
- Do not commit virtual environments or `node_modules`.
- Avoid committing local databases and large generated media files.
- Review staged files before pushing to GitHub.

## Project Status

**Development status:** Paused at the current implementation stage.

This repository represents the existing development project. It is not a claim that every feature has been fully tested or deployed to a public production server.

## License

No open-source license has been specified. Add a license if you intend to permit public reuse or redistribution.
