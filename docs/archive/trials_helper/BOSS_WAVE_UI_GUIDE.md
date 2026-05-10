# Boss Wave UI Integration - Quick Guide

## What Was Added

The boss wave functionality is now fully integrated into the Simulation page UI!

## Location

Navigate to: **Simulation** page (http://127.0.0.1:8050/simulation)

## New Controls

You'll find two new controls added to the top configuration section, right next to the "Package Chance" slider:

### 1. Boss Wave Interval (Dropdown)
- **Location**: Top section, next to Package Chance slider
- **Options**:
  - Every 4 waves
  - Every 5 waves
  - Every 6 waves
  - Every 8 waves
  - Every 10 waves (default)

### 2. Lab: Package After Boss (Toggle Switch)
- **Location**: Right next to Boss Wave Interval
- **Label**: "Lab: Package After Boss"
- **Type**: Switch/Toggle
- **Default**: Disabled (unchecked)

## How to Use

1. **Set Boss Wave Interval**
   - Choose how frequently bosses appear (default is every 10 waves)
   - More frequent bosses = more potential packages

2. **Enable Lab Upgrade**
   - Toggle "Lab: Package After Boss" to ON
   - This simulates having the lab upgrade active

3. **Run Simulation**
   - The simulation automatically updates when you change these settings
   - Works in both:
     - **3600s Multiplier Simulation** (main section)
     - **Enhancement Planner** (override section)

## What You'll See

When the lab is enabled and bosses are spawning:
- Boss packages are collected after each boss wave
- These packages trigger Galaxy Compressor cooldown reductions
- Average multiplier increases due to more frequent ultimate weapon activations
- The effect is most noticeable with:
  - Galaxy Compressor (Ancestral rarity for 20s reduction)
  - Shorter boss intervals (4-6 waves)

## Example Performance Impact

Based on 30-minute simulations with Galaxy Compressor (Ancestral):

| Boss Interval | Boss Packages | Multiplier Improvement |
|---------------|---------------|------------------------|
| Every 4 waves | ~9 packages   | +8-10% |
| Every 5 waves | ~7 packages   | +7-9% |
| Every 10 waves| ~5 packages   | +5-6% |

## Tips

- **Combine with Random Packages**: The lab packages stack with regular random packages (from Package Chance slider)
- **Test Different Intervals**: Try different intervals to see which gives you the best performance
- **Enhancement Planner**: Use the planner section to test "what if" scenarios with modified cooldowns

## Technical Details

- Boss waves occur at predictable intervals: 10, 20, 30, 40, 50... (for interval=10)
- Package is collected at the moment the boss wave ends
- Galaxy Compressor cooldown reduction applies the same as regular packages
- Works in both Tournament and Farming game modes

## Troubleshooting

If you don't see the controls:
1. Refresh the page (Ctrl+F5 or Cmd+Shift+R)
2. Make sure you're on the Simulation page (/simulation)
3. Check that your browser has loaded the latest version

If boss packages don't seem to work:
1. Make sure the toggle is switched ON (should be green/checked)
2. Verify you have Galaxy Compressor selected as Generator Module
3. Check that the simulation duration is long enough to see boss waves (need at least 301s for first boss at interval 10)
