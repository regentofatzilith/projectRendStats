# Quick Reference Guide - New Package Structure

## Package Organization

### functions.data
**Purpose**: Data handling, JSON processing, and data storage

**Key Modules**:
- `DataStore.py` - Singleton data store for user data
- `ImportJSON.py` - JSON parsing and data extraction
- `ConvertNumbers.py` - Number conversion utilities

**Common Imports**:
```python
from functions import user_data_store
from functions.data import Import_JSON_record, cleanupJSON
from functions.data import extract_combined_ultimate_weapons_data
from functions.data import time_to_decimal_hours
```

---

### functions.geometry
**Purpose**: Tower geometry, layout calculations, and spatial analysis

**Key Modules**:
- `TowerGeometry.py` - Tower layout and positioning functions

**Common Imports**:
```python
from functions.geometry import get_combined_ultimate_weapons_table
from functions.geometry import tower_layout_figure_with_kpis
from functions.geometry import golden_bot_figure_with_kpis
```

---

### functions.graphs
**Purpose**: Visualization, plotting, and optimization graphics

**Key Modules**:
- `Graphs.py` - Main graphing and visualization functions
- `Optimizer.py` - Optimization algorithms and tables

**Common Imports**:
```python
from functions.graphs import combined_metrics_figure
from functions.graphs import makeTable, optimize_figure, optimize_table
from functions.graphs import continuous_metrics_figure
from functions.graphs import get_smoothed_daily_data
from functions.graphs import get_color_for_metric, display_name, colors
```

---

### functions.simulation
**Purpose**: Game mechanics simulation and multiplier calculations

**Key Modules**:
- `Simulation.py` - Core simulation functions
- `SimulationClass.py` - Object-oriented simulator class

**Common Imports**:
```python
from functions.simulation import compute_multiplier_simulation
from functions.simulation import UltimateWeaponSimulator
```

---

### functions.statistics
**Purpose**: Statistical analysis and forecasting

**Key Modules**:
- `Statistics.py` - Time series statistics
- `forecast_stats.py` - Forecasting algorithms

**Common Imports**:
```python
from functions.statistics import TimeSeriesStats
from functions.statistics import forecast_metric
```

---

## Migration Cheat Sheet

| Old Import | New Import |
|------------|------------|
| `from myproject import user_data_store` | `from functions import user_data_store` |
| `from myproject.ImportJSON import ...` | `from functions.data import ...` |
| `from myproject.DataStore import UserDataStore` | `from functions.data import UserDataStore` |
| `from myproject.ConvertNumbers import ...` | `from functions.data import ...` |
| `from myproject.TowerGeometry import ...` | `from functions.geometry import ...` |
| `from myproject.Graphs import ...` | `from functions.graphs import ...` |
| `from myproject.Optimizer import ...` | `from functions.graphs import ...` |
| `from myproject.Simulation import ...` | `from functions.simulation import ...` |
| `from myproject.SimulationClass import ...` | `from functions.simulation import ...` |
| `from myproject.Statistics import ...` | `from functions.statistics import ...` |
| `from myproject.forecast_stats import ...` | `from functions.statistics import ...` |

---

## Directory Structure Summary

```
ProjectAtzi/
├── functions/          # Main business logic
│   ├── data/          # Data handling
│   ├── geometry/      # Spatial calculations
│   ├── graphs/        # Visualization
│   ├── simulation/    # Game simulation
│   └── statistics/    # Statistical analysis
├── pages/             # Dash application pages
├── tests_debug/       # All tests and debug scripts
├── assets/            # Static resources
└── deploy_render/     # Deployment configurations
```

---

## Testing Imports

Quick verification script:
```python
# Test all imports
from functions import user_data_store
from functions.data import Import_JSON_record
from functions.geometry import tower_layout_figure_with_kpis
from functions.graphs import combined_metrics_figure
from functions.simulation import UltimateWeaponSimulator
from functions.statistics import TimeSeriesStats

print("✓ All imports successful!")
```

---

## Next Steps

1. **Remove myproject folder** (optional, after confirming everything works)
   ```powershell
   Remove-Item -Recurse -Force myproject
   ```

2. **Update any external documentation** that references `myproject`

3. **Update deployment scripts** if they reference old paths

4. **Run full test suite** to verify all functionality
   ```powershell
   python -m pytest tests_debug/
   ```
