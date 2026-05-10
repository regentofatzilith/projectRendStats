# UW PermaCalc - Standalone Usage Guide

## Running Standalone

The UW PermaCalc page can run as a standalone application without the main app.

### How to Run

```bash
python pages/perma_calc_new.py
```

Then open your browser to: **http://127.0.0.1:8050**

### Sharing the Calculator

To share this calculator with others, they need:

1. **Required Files:**
   - `pages/perma_calc_new.py`
   - `requirements.txt` (or at minimum: `dash`, `dash-bootstrap-components`, `plotly`, `pandas`, `numpy`)

2. **Installation Steps:**
   ```bash
   # Install dependencies
   pip install dash dash-bootstrap-components plotly pandas numpy
   
   # Run the calculator
   python perma_calc_new.py
   ```

3. **Self-Contained Version:**
   The file is already self-contained - it includes all necessary logic and doesn't depend on other project files.

### Features Included

- ✅ All 5 Ultimate Weapons (Black Hole, Golden Tower, Death Wave, Chrono Field, Golden Bot)
- ✅ Play Mode selection (Tournament/Farming)
- ✅ Wave Accelerator Card levels
- ✅ Boss Waves configuration
- ✅ Package After Boss setting
- ✅ Battle Condition cooldown bonus
- ✅ Galaxy Compressor tiers
- ✅ Multiverse Nexus synchronization
- ✅ Farming perks for BH, DW, CF
- ✅ Interactive charts with package visualization
- ✅ Statistics cards for each UW
- ✅ Detailed UW analysis chart
- ✅ Synchronized overview chart

### Port Configuration

Default port: **8050**

To change the port, edit line 1345:
```python
app.run(debug=True, host='127.0.0.1', port=8050)
```

### Notes

- The calculator uses dark theme (DARKLY) by default
- All calculations run client-side in the browser after initial page load
- Simulates 3600 seconds (1 hour) by default

---

## Sharing Without Python Installation

### Option 1: PyInstaller (Windows Executable)

Package the app as a standalone `.exe` file:

```bash
# Install PyInstaller
pip install pyinstaller

# Create executable (from project root)
pyinstaller --onefile --add-data "pages;pages" --hidden-import=dash --hidden-import=dash_bootstrap_components pages/perma_calc_new.py

# The executable will be in dist/perma_calc_new.exe
```

**Share:** Just send the `perma_calc_new.exe` file. Users double-click it and open `http://127.0.0.1:8050` in their browser.

**Note:** The executable is ~100-200MB due to bundled Python + dependencies.

### Option 2: Deploy to Free Cloud Service

Deploy to a web server so users access via URL (no installation needed):

#### Render.com (Recommended - Free Tier)
1. Create a `requirements.txt` with dependencies
2. Create a new Web Service on Render
3. Connect your GitHub repo or upload files
4. Set build command: `pip install -r requirements.txt`
5. Set start command: `gunicorn perma_calc_new:server`
6. Add `gunicorn` to requirements.txt

**Share:** Give users the Render URL (e.g., `https://your-app.onrender.com`)

#### Railway.app
1. Upload `perma_calc_new.py` and `requirements.txt`
2. Railway auto-detects Python and deploys
3. Get shareable URL

#### PythonAnywhere
1. Upload files to PythonAnywhere
2. Configure web app with Dash
3. Get URL like `https://yourusername.pythonanywhere.com`

### Option 3: Docker Container

Create a `Dockerfile`:

```dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY perma_calc_new.py .
RUN pip install dash dash-bootstrap-components plotly pandas numpy
EXPOSE 8050
CMD ["python", "perma_calc_new.py"]
```

Build and share:
```bash
docker build -t uw-permacalc .
docker run -p 8050:8050 uw-permacalc
```

**Share:** Provide Docker image or Dockerfile. Users run with Docker Desktop.

### Option 4: Online IDE (Easiest for Quick Sharing)

#### Replit
1. Create account at replit.com
2. Upload `perma_calc_new.py` and `requirements.txt`
3. Click "Run"
4. Share the Repl link

**Share:** Users click link, click "Run" button, app opens in browser.

#### Google Colab (Limited)
Works but less ideal for web apps since sessions are temporary.

---

## Comparison

| Method | Pros | Cons | Best For |
|--------|------|------|----------|
| **PyInstaller** | No server needed, runs locally | Large file size (~200MB) | Windows users, offline use |
| **Render/Railway** | Professional URL, always online | Free tier has cold starts | Permanent sharing |
| **Replit** | Easiest, instant sharing | Sessions may timeout | Quick demos |
| **Docker** | Consistent environment | Requires Docker installed | Technical users |

---

## Recommended Approach

**For non-technical users:** Deploy to **Render.com** or **Replit** - just share a URL, they click and use.

**For technical users:** Share **PyInstaller executable** - they download, run, no installation needed.

**For developers:** Share the **Python file** with `pip install` instructions.
