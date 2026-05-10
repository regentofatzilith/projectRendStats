# Tower Conquest Analytics

A comprehensive analytics dashboard for Tower Conquest game data.

## Features

- 📊 **Metrics Dashboard** - Track coins, cells, reroll shards, and efficiency metrics
- 🔮 **Forecasting** - Predict future performance with multiple models (exponential, sigmoidal, ensemble)
- ⚙️ **Simulation** - Test tower configurations and strategies
- 📈 **Guardian Performance** - Analyze guardian effectiveness
- 🎲 **Chance Calculators** - Calculate probabilities for various game mechanics
- 🗼 **Tower Layout** - Visualize and optimize tower configurations
- 💎 **Perma Calc** - Calculate permanent upgrade costs and benefits

## Quick Start

### For Users (No Python Required)

1. Download `TowerConquestAnalytics.exe`
2. Double-click to run
3. Browser opens automatically at `http://localhost:8050`
4. Go to **Settings** page
5. Load your `userData.json` file (usually in `%USERPROFILE%\AppData\LocalLow\Boolba Games\Tower Conquest`)
6. Explore the analytics!

**Note:** The console window shows status - don't close it or the app will stop.

### For Developers

#### Installation
```bash
# Clone repository
git clone <repository-url>
cd ProjectAtzi

# Install dependencies
pip install -r requirements.txt

# Run the app
python app.py
```

#### Building Executable
```bash
# Automated build (Windows)
build.bat

# Manual build
pip install pyinstaller
pyinstaller build_exe.spec
```

See [BUILD_INSTRUCTIONS.md](BUILD_INSTRUCTIONS.md) for detailed build information.

## System Requirements

- **OS:** Windows 10/11
- **RAM:** 2GB minimum, 4GB recommended
- **Storage:** 500MB for app + data
- **Browser:** Any modern browser (Chrome, Firefox, Edge)

## Data Privacy

- ✅ All data stays on **your local machine**
- ✅ No data is sent to any servers
- ✅ No internet connection required (except for initial download)
- ✅ Your `userData.json` is only read, never modified

## Forecast Models

### Auto-select (Recommended)
Automatically chooses the best model based on R² score.

### Ensemble (Hybrid)
Combines multiple models with weighted averaging for robust predictions.

### Exponential
Best for consistently accelerating growth.

### Sigmoidal (S-curve)
Best for growth that plateaus near a capacity limit.

### Polynomial
Best for growth with multiple inflection points.

### Linear
Best for steady, consistent growth.

## Tips

- **Daily Results Window:** Controls smoothing for charts (2 days recommended)
- **Historical Lookback:** How far back to use for forecasts (60 days recommended)
- **Forecast Smoothing:** Reduces noise in predictions (14 days recommended)
- **Confidence Intervals:** Shaded area shows uncertainty (widens further into future)

## Troubleshooting

### App won't start
- Check Windows Defender isn't blocking the .exe
- Run from command line to see error messages

### Browser doesn't open
- Manually open browser and go to `http://localhost:8050`

### Can't find userData.json
Default location:
```
C:\Users\<YourName>\AppData\LocalLow\Boolba Games\Tower Conquest\userData.json
```

Or search for `userData.json` in File Explorer.

### Charts not showing
- Ensure you've loaded a valid `userData.json` file
- Check the Settings page for error messages
- Try refreshing the page (F5)

## Credits

Developed for the Tower Conquest community.

## License

[Add your license here]

## Version

Current version: 1.0.0
