# Medical Note Generator 🏥

A web app that turns doctor-patient conversations into structured medical notes. Upload an audio recording, pick a template, and get a properly formatted medical note in under a minute.

## What It Does

Instead of spending 10 minutes typing up consultation notes, you:

1. **Upload audio** of your conversation (or paste text)
2. **Select a template** (SOAP note, Cardiology consult, etc.)
3. **Get a formatted note** ready to copy or download as Word doc

The app handles transcription, cleanup, and structuring everything according to medical standards.

## Key Features

- **Audio to Text** - Transcribes recordings using Google Gemini AI (no model downloads needed)
- **Smart Formatting** - Understands medical terminology and structures information properly
- **Custom Templates** - Upload any PDF/Word medical form and it learns the format
- **Template Library** - Save frequently used note templates in SQLite database
- **Export to Word** - Download notes as `.docx` files
- **Rate Limit Protection** - Automatically tries 4 different AI models if one hits quota

## Technology

**Backend:**
- FastAPI (Python web framework)
- Google Gemini 2.5 Flash (AI for transcription and processing)
- SQLite (template storage)
- PyMuPDF & python-docx (document handling)

**Frontend:**
- Plain HTML, CSS, JavaScript (no React complexity)
- Professional blue medical theme

## Getting Started

### What You Need
- Python 3.9+
- Google Gemini API key (https://aistudio.google.com/app/apikey))
### Installation

**1. Clone and enter the project**
```bash
git clone <your-repo-url>
cd medical-note-generator
```

**2. Set up Python environment**
```bash
python -m venv venv

# Windows:
venv\Scripts\activate

# Mac/Linux:
source venv/bin/activate
```

**3. Install packages**
```bash
pip install -r requirements.txt
```

**4. Add your API keys**

Create a `.env` file in the project root:

```bash
GEMINI_API_KEY=your_api_key_here
```

**5. Start the server**
```bash
python main.py
```

Open browser: `http://localhost:8000`

## How to Use

### Generate a Medical Note

1. Go to **"Generate Note"** tab
2. Upload audio file (mp3, wav, m4a) or paste text
3. Select a template from dropdown
4. Click **"Generate Note"**
5. Download as Word doc or copy HTML

### Create Your Own Template

1. Go to **"Create Template"** tab
2. Upload a PDF or Word document (any medical form you use)
3. Name your template
4. Click **"Create Template"**
5. The app analyzes and saves the structure
6. Now available in the template dropdown

### Manage Templates

View all templates:
```bash
curl http://localhost:8000/templates
```

## Configuration

### Environment Variables (.env)

```bash
# Required
GEMINI_API_KEY=your_key          # From Google AI Studio


# Optional (defaults shown)
APP_ENV=production               # or "development"
HOST=0.0.0.0                    # Server address
PORT=8000                       # Server port
DB_PATH=templates.db            # Database location
ALLOWED_ORIGINS=*               # CORS (set to your domain in production)
```

### AI Model Fallback System

The app tries 4 models in order if rate limits hit:

1. `gemini-2.5-flash` (primary - fast and accurate you can use any other model)
2. `gemini-2.5-flash-lite` (fallback 1)
3. `gemini-2.5-flash` (fallback 2 - alternative endpoint)
4. `gemini-3.0-flash` (fallback 3 - last resort)

This means free tier users rarely see quota errors.

## API Endpoints

| Endpoint | Method | What It Does |
|----------|--------|-------------|
| `/` | GET | Web interface |
| `/health` | GET | Health check |
| `/transcribe-and-clean` | POST | Upload audio → get clean text |
| `/generate-note` | POST | Text + template → structured note |
| `/create-template` | POST | PDF/DOCX → extract template |
| `/templates` | GET | List all templates |
| `/templates/{name}` | DELETE | Remove a template |
| `/download-template` | POST | Template as Word doc |
| `/download-note` | POST | Note as Word doc |

## Project Structure

```
medical-note-generator/
├── main.py                      # FastAPI server
├── requirements.txt             # 12 Python packages
├── .env                         # API keys (not in git)
├── templates.db                 # SQLite database
│
├── backend/
│   ├── config.py               # App settings
│   ├── database.py             # Template storage
│   ├── transcription.py        # Audio → text
│   ├── text_cleaner.py         # Clean transcriptions
│   ├── note_generator.py       # Generate notes
│   ├── template_generator.py   # Extract templates
│   ├── note_formatter.py       # Format output
│   ├── prompts.py              # AI prompts
│   │
│   └── LLM/
│       ├── config.py           # AI settings
│       └── gemini.py           # Gemini API wrapper
│
├── frontend/
│   ├── public/
│   │   ├── index.html          # Main UI
│   │   └── styles.css          # Blue theme
│   └── static/
│       └── static.js           # Frontend logic
│
└── deployment/
    └── render.yaml             # Deployment config
```

## Deploying to Render.com

### Quick Deploy Steps

**1. Push to GitHub**
```bash
git add .
git commit -m "Deploy"
git push
```

**2. Create Render Service**
- Go to [render.com](https://render.com)
- New+ → Web Service
- Connect GitHub repo
- Auto-detects `render.yaml`

**3. Add Secrets**
In Render dashboard:
- `GEMINI_API_KEY`: Your API key

**4. Deploy**
Click "Create" - you'll get `https://your-app.onrender.com`

**5. Lock Down CORS**
After deploy, update in Render:
```
ALLOWED_ORIGINS=https://your-app.onrender.com
```

### How Storage Works

**Persistent Disk Setup:**
```
Deploy #1: Template saved → /data/templates.db ✓
Deploy #2: Git push → /data untouched ✓
Template still there!
```

Render mounts a 200MB disk at `/data` that survives redeployments. Your templates never get deleted unless you manually remove the service.

## Development Mode

Run with auto-reload:

```bash
# In .env:
APP_ENV=development
RELOAD=true

python main.py
```

Code changes apply automatically.

## Troubleshooting

**Import errors in VS Code:**
```bash
pip install -r requirements.txt
# Reload VS Code: Ctrl+Shift+P → "Developer: Reload Window"
```

**Rate limit errors:**
- Wait a few minutes (free tier: 15 req/min)
- App auto-tries 4 models, so this is rare
- Upgrade API plan if needed


**Templates not saving:**
- Check `templates.db` exists
- On Render: verify `/data` disk mounted
- Check logs for database errors

## Performance

Typical response times:
- Transcription: 10-30 seconds (depends on audio length)
- Text cleaning: 2-5 seconds
- Note generation: 5-10 seconds
- Template creation: 10-20 seconds

Total: About 1 minute from upload to formatted note.


## What's Not Included

This is a single-user note generation tool. It doesn't have:

- User authentication
- Patient database
- HIPAA compliance certification
- Real-time collaboration
- Native mobile app (web UI is responsive though)

Good candidates for future additions if needed.

## Contributing

Found a bug? Have an idea?

1. Fork the repo
2. Create a branch
3. Make changes
4. Submit a PR

Code is straightforward (< 2000 lines total).

## License

See `LICENSE` file.

---

**That's everything.** Five-minute setup, add your API key, start generating medical notes.

