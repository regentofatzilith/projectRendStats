# Boss Wave Detection & Lab Package Feature

## Overview

The simulation now includes boss wave detection and the "Package After Boss" lab upgrade functionality. Bosses appear every N waves (configurable from 4 to 10 waves), and when the lab upgrade is active, a package is automatically granted after defeating each boss.

## Features

### 1. **Boss Wave Detection**
- Bosses spawn at regular intervals (default: every 10 waves)
- Configurable interval from 4 to 10 waves
- Boss waves are automatically tracked: wave 10, 20, 30, etc.

### 2. **Lab Package After Boss**
- Simulates the "Package After Boss" lab upgrade
- Grants a recovery package after each boss is defeated
- Package arrives at the moment the boss wave ends
- Cooldown reduction works the same as regular packages

### 3. **Boss Package Callback**
- Optional callback function triggered when boss packages are collected
- Useful for logging, analytics, or UI updates
- Receives `(time_s, wave_idx)` as parameters

## Usage

### Basic Example

```python
from functions.simulation import UltimateWeaponSimulator

# Create simulator with boss wave detection
sim = UltimateWeaponSimulator(
    duration_s=1800,
    game_mode="farming",
    boss_wave_interval=10,      # Boss every 10 waves (default)
    lab_package_after_boss=True, # Enable lab upgrade
)

sim.run()

# Access results
components = sim.get_components()
print(f"Boss waves: {components['boss_waves']}")
print(f"Boss packages: {len(components['boss_package_times'])}")
```

### With Callback

```python
def on_boss_defeated(time_s, wave_idx):
    print(f"Boss defeated at wave {wave_idx} (t={time_s}s)")

sim = UltimateWeaponSimulator(
    duration_s=1800,
    boss_wave_interval=10,
    lab_package_after_boss=True,
    on_boss_package_callback=on_boss_defeated,
)

sim.run()
```

### Using Wrapper Function

```python
from functions.simulation import compute_multiplier_simulation

df, avg_mult, components = compute_multiplier_simulation(
    duration_s=1800,
    game_mode="farming",
    boss_wave_interval=8,        # Boss every 8 waves
    lab_package_after_boss=True,
)

print(f"Boss packages: {len(components['boss_package_times'])}")
```

## Parameters

### Constructor Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `boss_wave_interval` | int | 10 | Boss spawn frequency (4-10 waves) |
| `lab_package_after_boss` | bool | False | Enable "Package After Boss" lab |
| `on_boss_package_callback` | Callable | None | Optional callback function |

### Callback Signature

```python
def callback(time_s: int, wave_idx: int) -> None:
    """
    Args:
        time_s: Time in seconds when package was collected
        wave_idx: Wave number where boss was defeated
    """
    pass
```

## Results Access

The simulation results include boss wave information:

```python
components = sim.get_components()

# Boss wave data
boss_waves = components['boss_waves']              # List[int] - wave numbers
boss_package_times = components['boss_package_times']  # List[int] - collection times (seconds)
boss_interval = components['boss_wave_interval']   # int - configured interval
lab_enabled = components['lab_package_after_boss']  # bool - lab status

# Example: [10, 20, 30, 40, 50]
print(f"Boss waves: {boss_waves}")

# Example: [301, 603, 904, 1206, 1508]
print(f"Package times: {boss_package_times}")
```

## Wave Timing

Boss waves occur at predictable intervals:

| Interval | Boss Waves (first 5) | Example Times (farming) |
|----------|---------------------|------------------------|
| 4 waves | 4, 8, 12, 16, 20 | 121s, 241s, 362s, 482s, 603s |
| 5 waves | 5, 10, 15, 20, 25 | 151s, 301s, 452s, 603s, 754s |
| 10 waves | 10, 20, 30, 40, 50 | 301s, 603s, 904s, 1206s, 1508s |

**Note:** Wave duration is 30.140s in farming mode, 28.070s in other modes.

## Performance Impact

The "Package After Boss" lab provides consistent performance benefits through additional cooldown reduction:

| Configuration | Boss Packages (30 min) | Multiplier Improvement |
|---------------|------------------------|----------------------|
| Interval 4 | ~9 packages | +8-10% |
| Interval 5 | ~7 packages | +7-9% |
| Interval 10 | ~5 packages | +5-6% |

*Values assume Galaxy Compressor (Ancestral) with 20s reduction per package*

## Integration Examples

### Dashboard Integration

```python
boss_log = []

def track_boss_packages(time_s, wave_idx):
    boss_log.append({
        'wave': wave_idx,
        'time': time_s,
        'timestamp': datetime.now()
    })

sim = UltimateWeaponSimulator(
    duration_s=3600,
    lab_package_after_boss=True,
    on_boss_package_callback=track_boss_packages,
)
sim.run()

# Display in dashboard
for entry in boss_log:
    print(f"Wave {entry['wave']}: {entry['timestamp']}")
```

### Analytics & Optimization

```python
# Compare different boss intervals
results = {}
for interval in [4, 5, 6, 8, 10]:
    sim = UltimateWeaponSimulator(
        duration_s=1800,
        boss_wave_interval=interval,
        lab_package_after_boss=True,
    )
    sim.run()
    results[interval] = {
        'packages': len(sim.boss_package_times),
        'multiplier': sim.average_multiplier
    }

# Find optimal interval
best = max(results.items(), key=lambda x: x[1]['multiplier'])
print(f"Best interval: {best[0]} waves")
```

## Technical Notes

### Boss Wave Detection Logic

- Boss waves start at multiples of `boss_wave_interval` (10, 20, 30...)
- Wave 0 is not a boss wave (first boss is at wave 10 by default)
- Package is collected when the boss wave ends (next wave starts)

### Cooldown Reduction

- Boss packages trigger the same cooldown reduction as regular packages
- Works with Galaxy Compressor generator module
- Reduction amount depends on generator rarity:
  - Epic: 10s
  - Legendary: 13s
  - Mythic: 17s
  - Ancestral: 20s

### Compatibility

- Works with all armor modules and rarities
- Compatible with all generator modules
- Boss packages and random packages stack (both can occur)
- Golden Bot is excluded from package cooldown reduction (by design)

## Related Files

- `myproject/SimulationClass.py` - Core simulation implementation
- `myproject/Simulation.py` - Wrapper function
- `test_boss_wave.py` - Unit tests
- `example_boss_wave.py` - Usage examples

## See Also

- Ultimate Weapon Simulation documentation
- Galaxy Compressor mechanics
- Recovery Package system
