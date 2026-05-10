"""
Configuration module for Ultimate Weapons lookup tables.

This module centralizes all upgrade level -> value lookup tables for ultimate weapons,
labs research bonuses, and other game mechanics lookups.

Architecture:
- Lookup tables are defined here for easy maintenance and reference
- ImportJSON.py imports these for data extraction and calculation
- UltimateWeapons.py imports these for value lookups and combination

TODO:
- Added lookups for Ultimate Weapon unique module effects and submodule stats per rarity. => Remove GC_Labs?
- Create manual tables (UW, Bots, Guardians) to identify labs, uw bonus, modules, relic contributions to each parameter.
- Added Assist Mods lookups for UW substats and modules.
- How to include Standard Values for not unlocked UWs?
"""

# ============================================================================
# NUMBER SCALE LOOKUPS
# ============================================================================

scale={
        "K": 10**3, "M": 10**6, "B": 10**9, "T": 10**12,
        "q": 10**15, "Q": 10**18, "s": 10**21, "S": 10**24,
        "O": 10**27, "N": 10**30, "D": 10**33,
        "aa": 10**36, "ab": 10**39, "ac": 10**42,
        "":10**0
    }

# ============================================================================
# GOLDEN TOWER LOOKUPS
# ============================================================================

GOLDEN_TOWER_LUT = {
    "Levels": {
        "Coin Bonus": {
            0: 5.0, 1: 5.8, 2: 6.6, 3: 7.4, 4: 8.2, 5: 9.0, 6: 9.8, 7: 10.6, 8: 11.4, 9: 12.2,
            10: 13.0, 11: 13.8, 12: 14.6, 13: 15.4, 14: 16.2, 15: 17.0, 16: 17.8, 17: 18.6,
            18: 19.4, 19: 20.2, 20: 21.0
        },
        "Duration": {
            0: 15, 1: 16, 2: 17, 3: 18, 4: 19, 5: 20, 6: 21, 7: 22, 8: 23, 9: 24,
            10: 25, 11: 26, 12: 27, 13: 28, 14: 29, 15: 30, 16: 31, 17: 32, 18: 33, 19: 34,
            20: 35, 21: 36, 22: 37, 23: 38, 24: 39, 25: 40, 26: 41, 27: 42, 28: 43, 29: 44,
            30: 45, 31: 46, 32: 47, 33: 48, 34: 49, 35: 50, 36: 51, 37: 52, 38: 53
        },
        "Cooldown": {
            0: 300, 1: 290, 2: 280, 3: 270, 4: 260, 5: 250, 6: 240, 7: 230, 8: 220, 9: 210,
            10: 200, 11: 190, 12: 180, 13: 170, 14: 160, 15: 150, 16: 140, 17: 130, 18: 120,
            19: 110, 20: 100
        },
    },
    "Labs": {
        "Duration": {
            0: 0, 1: 1, 2: 2, 3: 3, 4: 4, 5: 5, 6: 6, 7: 7, 8: 8, 9: 9, 10: 10,
            11: 11, 12: 12, 13: 13, 14: 14, 15: 15, 16: 16, 17: 17, 18: 18, 19: 19, 20: 20
        },
        "Coin Bonus": {
            0: 0, 1: 0.15, 2: 0.30, 3: 0.45, 4: 0.60, 5: 0.75, 6: 0.90, 7: 1.05, 8: 1.20, 9: 1.35, 10: 1.50,
            11: 1.65, 12: 1.80, 13: 1.95, 14: 2.10, 15: 2.25, 16: 2.40, 17: 2.55, 18: 2.70, 19: 2.85, 20: 3.00,
            21: 3.15, 22: 3.30, 23: 3.45, 24: 3.60, 25: 3.75
        },
    },
    "Modules":    None,
    "Submodules": {
        "Coin Bonus": "Golden Tower Coin Bonus",
        "Duration": "Golden Tower Duration [s]",
        "Cooldown": "Golden Tower Cooldown [s]",
    },
    "Relics":     None,
}

GOLDEN_TOWER_DURATION_LABS_LOOKUP = GOLDEN_TOWER_LUT["Labs"]["Duration"]
GOLDEN_TOWER_COIN_BONUS_LABS_LOOKUP = GOLDEN_TOWER_LUT["Labs"]["Coin Bonus"]

# Map weapon type + parameter to lookup table [UW, Labs, Relics, Modules, Assist Mods]
GOLDEN_TOWER_LOOKUPS = {
    "Coin Bonus": GOLDEN_TOWER_LUT["Levels"]["Coin Bonus"],
    "Duration":   GOLDEN_TOWER_LUT["Levels"]["Duration"],
    "Cooldown":   GOLDEN_TOWER_LUT["Levels"]["Cooldown"],
}

GOLDEN_TOWER_LOOKUP = GOLDEN_TOWER_LOOKUPS

# ============================================================================
# BLACK HOLE LOOKUPS
# ============================================================================

BLACK_HOLE_LUT = {
    "Levels": {
        "Size": {
            0: 30, 1: 32, 2: 34, 3: 36, 4: 38, 5: 40, 6: 42, 7: 44, 8: 46, 9: 48,
            10: 50, 11: 52, 12: 54, 13: 56, 14: 58, 15: 60, 16: 62, 17: 64, 18: 66, 19: 68,
            20: 70
        },
        "Duration": {
            0: 15, 1: 16, 2: 17, 3: 18, 4: 19, 5: 20, 6: 21, 7: 22, 8: 23, 9: 24,
            10: 25, 11: 26, 12: 27, 13: 28, 14: 29, 15: 30, 16: 31, 17: 32, 18: 33, 19: 34,
            20: 35, 21: 36, 22: 37, 23: 38
        },
        "Cooldown": {
            0: 200, 1: 190, 2: 180, 3: 170, 4: 160, 5: 150, 6: 140, 7: 130, 8: 120, 9: 110,
            10: 100, 11: 90, 12: 80, 13: 70, 14: 60, 15: 50
        },
    },
    "Labs": {
        "Damage Mult": {
            0: 0.000, 1: 0.002, 2: 0.004, 3: 0.006, 4: 0.008, 5: 0.010, 6: 0.012, 7: 0.014, 8: 0.016, 9: 0.018, 10: 0.020
        },
        "Coin Bonus": {
            0: 0, 1: 1.50, 2: 2.00, 3: 2.50, 4: 3.00, 5: 3.50, 6: 4.00, 7: 4.50, 8: 5.00, 9: 5.50, 10: 6.00,
            11: 6.50, 12: 7.00, 13: 7.50, 14: 8.00, 15: 8.50, 16: 9.00, 17: 9.50, 18: 10.00, 19: 10.50, 20: 11.00
        },
        "Extra Black Hole": {
            0: False, 1: True
        },
        "Black Hole Disable Ranged Enemies": {
            0: False, 1: True
        },
    },
    "Modules":    None,
    "Submodules": {
        "Size": "Black Hole - Size [m]",
        "Duration": "Black Hole - Duration [s]",
        "Cooldown": "Black Hole - Cooldown [s]",
        },
    "Relics":     None,
}

BLACK_HOLE_COIN_BONUS_LABS_LOOKUP = BLACK_HOLE_LUT["Labs"]["Coin Bonus"]

BLACK_HOLE_LOOKUPS = {
    "Size":     BLACK_HOLE_LUT["Levels"]["Size"],
    "Duration": BLACK_HOLE_LUT["Levels"]["Duration"],
    "Cooldown": BLACK_HOLE_LUT["Levels"]["Cooldown"],
}

BLACK_HOLE_LOOKUP = BLACK_HOLE_LOOKUPS

# ============================================================================
# DEATH WAVE LOOKUPS
# ============================================================================

DEATH_WAVE_LUT = {
    "Levels": {
        "Damage Mult": {
            0: 2, 1: 3, 2: 5, 3: 9, 4: 14, 5: 22, 6: 32, 7: 46, 8: 63, 9: 85,
            10: 113, 11: 148, 12: 191, 13: 244, 14: 309, 15: 387, 16: 482, 17: 596, 18: 723, 19: 877,
            20: 1064, 21: 1290, 22: 1569, 23: 1916, 24: 2356, 25: 2919, 26: 3637, 27: 4544, 28: 5678, 29: 7078,
            30: 9119
        },
        "Quantity": {
            0: 1, 1: 2, 2: 3, 3: 4, 4: 5
        },
        "Cooldown": {
            0: 300, 1: 290, 2: 280, 3: 270, 4: 260, 5: 250, 6: 240, 7: 230, 8: 220, 9: 210,
            10: 200, 11: 190, 12: 180, 13: 170, 14: 160, 15: 150, 16: 140, 17: 130, 18: 120, 19: 110,
            20: 100, 21: 90, 22: 80, 23: 70, 24: 60, 25: 50
        },
    },
    "Labs": {
        "Death Wave Health": {
            0: 0, 1: 5.25, 2: 5.50, 3: 5.75, 4: 6.00, 5: 6.25, 6: 6.50, 7: 6.75, 8: 7.00, 9: 7.25, 10: 7.50,
            11: 7.75, 12: 8.00, 13: 8.25, 14: 8.50, 15: 8.75, 16: 9.00, 17: 9.25, 18: 9.50, 19: 9.75, 20: 10.00,
            21: 10.25, 22: 10.50, 23: 10.75, 24: 11.00, 25: 11.25, 26: 11.50, 27: 11.75, 28: 12.00, 29: 12.25, 30: 12.50
        },
        "Coins Bonus": {
            0: 0, 1: 1.55, 2: 1.60, 3: 1.65, 4: 1.70, 5: 1.75, 6: 1.80, 7: 1.85, 8: 1.90, 9: 1.95, 10: 2.00,
            11: 2.05, 12: 2.10, 13: 2.15, 14: 2.20, 15: 2.25, 16: 2.30, 17: 2.35, 18: 2.40, 19: 2.45, 20: 2.50
        },
        "Cells Bonus": {
            0: 0, 1: 1.10, 2: 1.20, 3: 1.30, 4: 1.40, 5: 1.50, 6: 1.60, 7: 1.70, 8: 1.80, 9: 1.90, 10: 2.00,
            11: 2.10, 12: 2.20, 13: 2.30, 14: 2.40, 15: 2.50, 16: 2.60, 17: 2.70, 18: 2.80, 19: 2.90, 20: 3.00
        },
        "Damage Amplifier": {
            0: 0, 1: 6.50, 2: 8.00, 3: 9.50, 4: 11.00, 5: 12.50, 6: 14.00, 7: 15.50, 8: 17.00, 9: 18.50, 10: 20.00,
            11: 21.50, 12: 23.00, 13: 24.50, 14: 26.00, 15: 27.50, 16: 29.00, 17: 30.50, 18: 32.00, 19: 33.50, 20: 35.00,
            21: 36.50, 22: 38.00, 23: 39.50, 24: 41.00, 25: 42.50, 26: 44.00, 27: 45.50, 28: 47.00, 29: 48.50, 30: 50.00
        },
        "Armor Stripping": {
            0: 0, 1: 1, 2: 2, 3: 3, 4: 4, 5: 5, 6: 6, 7: 7, 8: 8, 9: 9, 10: 10
        },
    },
    "Modules":    None,
    "Submodules": {
        "Damage Mult": "Death Wave - Damage [x]",
        "Quantity": "Death Wave - Quantity",
        "Cooldown": "Death Wave - Cooldown [s]",
    },
    "Relics":     {
        "Damage Mult": "Ultimate Damage"    
    }
}

DEATH_WAVE_DAMAGE_LOOKUP     = DEATH_WAVE_LUT["Levels"]["Damage Mult"]
DEATH_WAVE_BONUS_LOOKUP      = DEATH_WAVE_LUT["Levels"]["Damage Mult"]  # alias for Damage
DEATH_WAVE_QUANTITY_LOOKUP   = DEATH_WAVE_LUT["Levels"]["Quantity"]
DEATH_WAVE_COOLDOWN_LOOKUP   = DEATH_WAVE_LUT["Levels"]["Cooldown"]
DEATH_WAVE_COIN_BONUS_LABS_LOOKUP = DEATH_WAVE_LUT["Labs"].get("Coin Bonus", DEATH_WAVE_LUT["Labs"].get("Coins Bonus", {}))

DEATH_WAVE_LOOKUPS = {
    "Damage":   DEATH_WAVE_LUT["Levels"]["Damage Mult"],
    "Bonus":    DEATH_WAVE_LUT["Levels"]["Damage Mult"],  # alias for Damage
    "Quantity": DEATH_WAVE_LUT["Levels"]["Quantity"],
    "Cooldown": DEATH_WAVE_LUT["Levels"]["Cooldown"],
}

DEATH_WAVE_LOOKUP = DEATH_WAVE_LOOKUPS

# ============================================================================
# SPOTLIGHT LOOKUPS
# ============================================================================

SPOTLIGHT_LUT = {
    "Levels": {
        "Damage Mult": {
            0: 8.0, 1: 9.4, 2: 10.8, 3: 12.2, 4: 13.6, 5: 15.0, 6: 16.4, 7: 17.8, 8: 19.2, 9: 20.6,
            10: 22.0, 11: 23.4, 12: 24.8, 13: 26.2, 14: 27.6, 15: 29.0, 16: 30.4, 17: 31.8, 18: 33.2, 19: 34.6,
            20: 36.0, 21: 37.4, 22: 38.8, 23: 40.2, 24: 41.6, 25: 43.0
        },
        "Angle": {
            0: 30, 1: 31, 2: 32, 3: 33, 4: 34, 5: 35, 6: 36, 7: 37, 8: 38, 9: 39,
            10: 40, 11: 41, 12: 42, 13: 43, 14: 44, 15: 45, 16: 46, 17: 47, 18: 48, 19: 49,
            20: 50, 21: 51, 22: 52, 23: 53, 24: 54, 25: 55, 26: 56, 27: 57, 28: 58, 29: 59,
            30: 60, 31: 61, 32: 62, 33: 63, 34: 64, 35: 65, 36: 66, 37: 67, 38: 68, 39: 69,
            40: 70, 41: 71, 42: 72, 43: 73, 44: 74, 45: 75, 46: 76, 47: 77, 48: 78, 49: 79,
            50: 80, 51: 81, 52: 82, 53: 83, 54: 84, 55: 85, 56: 86, 57: 87, 58: 88, 59: 89,
            60: 90
        },
        "Quantity": {
            0: 1, 1: 2, 2: 3, 3: 4
        },
    },
    "Labs": {
        "Spotlight Missiles": {
            0: 0, 1: 19, 2: 18, 3: 17, 4: 16, 5: 15, 6: 14, 7: 13, 8: 12, 9: 11, 10: 10,
            11: 9, 12: 8, 13: 7, 14: 6, 15: 5, 16: 4, 17: 3, 18: 2
        },
        "Coin Bonus": {
            0: 0, 1: 1.10, 2: 1.20, 3: 1.30, 4: 1.40, 5: 1.50, 6: 1.60, 7: 1.70, 8: 1.80, 9: 1.90, 10: 2.00,
            11: 2.10, 12: 2.20, 13: 2.30, 14: 2.40, 15: 2.50, 16: 2.60, 17: 2.70, 18: 2.80, 19: 2.90, 20: 3.00
        },
    },
    "Modules":    None,
    "Submodules": {
        "Damage Mult": "Spotlight - Bonus",
        "Angle": "Spotlight - Angle",
    },
    "Relics":     {
        "Damage Mult": "Ultimate Damage"    
    }
}

SPOTLIGHT_DAMAGE_MULT_LOOKUP = SPOTLIGHT_LUT["Levels"]["Damage Mult"]
SPOTLIGHT_ANGLE_LOOKUP       = SPOTLIGHT_LUT["Levels"]["Angle"]
SPOTLIGHT_QUANTITY_LOOKUP    = SPOTLIGHT_LUT["Levels"]["Quantity"]
SPOTLIGHT_COIN_BONUS_LABS_LOOKUP  = SPOTLIGHT_LUT["Labs"]["Coin Bonus"]

SPOTLIGHT_LOOKUPS = {
    "Bonus":       SPOTLIGHT_LUT["Levels"]["Damage Mult"],  # alias for Damage Mult
    "Damage Mult": SPOTLIGHT_LUT["Levels"]["Damage Mult"],
    "Angle":       SPOTLIGHT_LUT["Levels"]["Angle"],
    "Quantity":    SPOTLIGHT_LUT["Levels"]["Quantity"],
}

SPOTLIGHT_LOOKUP = SPOTLIGHT_LOOKUPS

# ============================================================================
# CHRONO FIELD LOOKUPS
# ============================================================================

CHRONO_FIELD_LUT = {
    "Levels": {
        "Duration": {
            0: 5, 1: 6, 2: 7, 3: 8, 4: 9, 5: 10, 6: 11, 7: 12, 8: 13, 9: 14,
            10: 15, 11: 16, 12: 17, 13: 18, 14: 19, 15: 20, 16: 21, 17: 22, 18: 23, 19: 24,
            20: 25, 21: 26, 22: 27, 23: 28, 24: 29, 25: 30, 26: 31, 27: 32, 28: 33, 29: 34,
            30: 35, 31: 36, 32: 37, 33: 38, 34: 39, 35: 40
        },
        "Cooldown": {
            0: 180, 1: 170, 2: 160, 3: 150, 4: 140, 5: 130, 6: 120, 7: 110, 8: 100, 9: 90,
            10: 80, 11: 70, 12: 60
        },
        "Slow %": {
            0: 20, 1: 25, 2: 30, 3: 35, 4: 40, 5: 45, 6: 50, 7: 55, 8: 60, 9: 65,
            10: 70, 11: 75
        },
    },
    "Labs": {
        "Duration": {
            0: 0, 1: 1, 2: 2, 3: 3, 4: 4, 5: 5, 6: 6, 7: 7, 8: 8, 9: 9, 10: 10,
            11: 11, 12: 12, 13: 13, 14: 14, 15: 15, 16: 16, 17: 17, 18: 18, 19: 19, 20: 20,
            21: 21, 22: 22, 23: 23, 24: 24, 25: 25, 26: 26, 27: 27, 28: 28, 29: 29, 30: 30
        },
        "Damage Reduction": {
            0: False, 1: True
        },
        "Damage Reduction %": {
            0: 0, 1: 0.1050, 2: 0.1100, 3: 0.1150, 4: 0.1200, 5: 0.1250, 6: 0.1300, 7: 0.1350, 8: 0.1400, 9: 0.1450, 10: 0.1500,
            11: 0.1550, 12: 0.1600, 13: 0.1650, 14: 0.1700, 15: 0.1750, 16: 0.1800, 17: 0.1850, 18: 0.1900, 19: 0.1950, 20: 0.2000,
            21: 0.2050, 22: 0.2100, 23: 0.2150, 24: 0.2200, 25: 0.2250, 26: 0.2300, 27: 0.2350, 28: 0.2400, 29: 0.2450, 30: 0.2500
        },
        "Range": {
            0: 0, 1: 3, 2: 6, 3: 9, 4: 12, 5: 15, 6: 18, 7: 21, 8: 24, 9: 27, 10: 30,
            11: 33, 12: 36, 13: 39, 14: 42, 15: 45, 16: 48, 17: 51, 18: 54, 19: 57, 20: 60
        },
    },
    "Modules":    None,
    "Submodules": {
        "Duration": "Chrono Field - Duration [s]",
        "Cooldown": "Chrono Field - Cooldown [s]",
        "Slow %": "Chrono Field - Speed Reduction [%]",
    },
    "Relics":     None,
}

CHRONO_FIELD_DURATION_LOOKUP      = CHRONO_FIELD_LUT["Levels"]["Duration"]
CHRONO_FIELD_COOLDOWN_LOOKUP      = CHRONO_FIELD_LUT["Levels"]["Cooldown"]
CHRONO_FIELD_SLOW_LOOKUP          = CHRONO_FIELD_LUT["Levels"]["Slow %"]
CHRONO_FIELD_DURATION_LABS_LOOKUP = CHRONO_FIELD_LUT["Labs"]["Duration"]

CHRONO_FIELD_LOOKUPS = {
    "Duration": CHRONO_FIELD_LUT["Levels"]["Duration"],
    "Cooldown": CHRONO_FIELD_LUT["Levels"]["Cooldown"],
    "Slow %":   CHRONO_FIELD_LUT["Levels"]["Slow %"],
}

CHRONO_FIELD_LOOKUP = CHRONO_FIELD_LOOKUPS

# Canonical ultimate-weapon level lookup map.
ULTIMATE_WEAPON_LOOKUPS = {
    "Golden Tower": GOLDEN_TOWER_LOOKUP,
    "Black Hole": BLACK_HOLE_LOOKUP,
    "Death Wave": DEATH_WAVE_LOOKUP,
    "Spotlight": SPOTLIGHT_LOOKUP,
    "Chrono Field": CHRONO_FIELD_LOOKUP,
}

# ============================================================================
# SMART MISSILES LOOKUPS
# ============================================================================

SMART_MISSILE_LUT = {
    "Levels": {
        "Damage Mult": {
            0: 10, 1: 11, 2: 12, 3: 13, 4: 14, 5: 20, 6: 26, 7: 34, 8: 43, 9: 55, 10: 69,
            11: 87, 12: 108, 13: 134, 14: 164, 15: 200, 16: 243, 17: 293, 18: 352, 19: 421, 20: 502,
            21: 597, 22: 708, 23: 838, 24: 989, 25: 1165, 26: 1370, 27: 1608, 28: 1886, 29: 2209, 30: 2585,
            31: 3028
        },
        "Quantity": {
            0: 5, 1: 6, 2: 7, 3: 8, 4: 9, 5: 10, 6: 11, 7: 12, 8: 13, 9: 14, 10: 15,
            11: 16, 12: 17, 13: 18, 14: 19, 15: 20
        },
        "Cooldown": {
            0: 180, 1: 170, 2: 160, 3: 150, 4: 140, 5: 130, 6: 120, 7: 110, 8: 100, 9: 90,
            10: 80, 11: 70, 12: 60, 13: 50, 14: 40, 15: 30, 16: 20
        },
    },
    "Labs": {
        "Missile Despawn Time": {
            0: 0, 1: 1, 2: 2, 3: 3, 4: 4, 5: 5, 6: 6, 7: 7, 8: 8, 9: 9, 10: 10,
            11: 11, 12: 12, 13: 13, 14: 14, 15: 15, 16: 16, 17: 17, 18: 18, 19: 19, 20: 20
        },
        "Missile Amplifier": {
            0: 0, 1: 2.50, 2: 4.00, 3: 5.50, 4: 7.00, 5: 8.50, 6: 10.00, 7: 11.50, 8: 13.00, 9: 14.50, 10: 16.00,
            11: 17.50, 12: 19.00, 13: 20.50, 14: 22.00, 15: 23.50, 16: 25.00, 17: 26.50, 18: 28.00, 19: 29.50, 20: 31.00,
            21: 32.50, 22: 34.00, 23: 35.50, 24: 37.00, 25: 38.50
        },
        "Missiles Explosion": {
            0: False, 1: True
        },
        "Missile Radius": {
            0: 0, 1: 0.35, 2: 0.40, 3: 0.45, 4: 0.50, 5: 0.55, 6: 0.60, 7: 0.65, 8: 0.70, 9: 0.75, 10: 0.80,
            11: 0.85, 12: 0.90, 13: 0.95, 14: 1.00, 15: 1.05, 16: 1.10, 17: 1.15, 18: 1.20, 19: 1.25, 20: 1.30
        },
        "Missile Barrage": {
            0: False, 1: True
        },
        "Missile Barrage Quantity": {
            0: 0, 1: 25, 2: 30, 3: 35, 4: 40, 5: 45, 6: 50
        },
        "Recharge Missile Barrage": {
            1: 1500, 2: 1250, 3: 1000, 4: 750, 5: 500, 6: 350, 7: 250
        },
    },
    "Modules": None,
    "Submodules": {
        "Damage Mult": "Smart Missiles - Damage",
        "Quantity": "Smart Missiles - Quantity",
        "Cooldown": "Smart Missiles - Cooldown",
    },
    "Relics": {
        "Damage Mult": "Ultimate Damage"
    }, 
}

# ============================================================================
# INNER LAND MINES LOOKUPS
# ============================================================================

INNER_LAND_MINES_LUT = {
    "Levels": {
        "Damage Mult": {
            0: 10, 1: 11, 2: 12, 3: 13, 4: 14, 5: 15, 6: 16, 7: 20, 8: 26, 9: 34, 10: 43,
            11: 55, 12: 69, 13: 87, 14: 108, 15: 134, 16: 164, 17: 200, 18: 243, 19: 293, 20: 352,
            21: 421, 22: 502, 23: 597, 24: 708, 25: 838, 26: 989, 27: 1165, 28: 1370, 29: 1608, 30: 1886,
            31: 2209, 32: 2585, 33: 3021
        },
        "Quantity": {
            0: 3, 1: 4, 2: 5, 3: 6
        },
        "Cooldown": {
            0: 200, 1: 190, 2: 180, 3: 170, 4: 160, 5: 150, 6: 140, 7: 130, 8: 120, 9: 110,
            10: 100, 11: 90, 12: 80, 13: 70, 14: 60, 15: 50
        },
    },
    "Labs": {
        "Inner Mine Blast Radius": {
            1: 0.10, 2: 0.20, 3: 0.30, 4: 0.40, 5: 0.50, 6: 0.60, 7: 0.70, 8: 0.80, 9: 0.90, 10: 1.00,
            11: 1.10, 12: 1.20, 13: 1.30, 14: 1.40, 15: 1.50, 16: 1.60, 17: 1.70, 18: 1.80, 19: 1.90, 20: 2.00
        },
        "Inner Mine Rotation Speed": {
            1: 0.80, 2: 1.60, 3: 2.40, 4: 3.20, 5: 4.00, 6: 4.80, 7: 5.60, 8: 6.40, 9: 7.20, 10: 8.00,
            11: 8.80, 12: 9.60, 13: 10.40, 14: 11.20, 15: 12.00, 16: 12.80, 17: 13.60, 18: 14.40, 19: 15.20, 20: 16.00
        },
        "Inner Mine Stun": {
            0: False, 1: True
        },
        "Inner Land Mine - Chrono Jump": {
            1: 5, 2: 10, 3: 15, 4: 20, 5: 25, 6: 30, 7: 35, 8: 40, 9: 45, 10: 50
        },
    },
    "Modules": None,
    "Submodules": {
        "Damage Mult": "Inner Land Mines - Damage Mult",
        "Quantity": "Inner Land Mines - Quantity",
        "Cooldown": "Inner Land Mines - Cooldown [s]",
    },
    "Relics": {
        "Damage Mult": "Ultimate Damage"    
    }
}

# ============================================================================
# POISON SWAMP LOOKUPS
# ============================================================================

POISON_SWAMP_LUT = {
    "Levels": {
        "Damage Mult": {
            0: 10, 1: 11, 2: 12, 3: 13, 4: 14, 5: 15, 6: 16, 7: 20, 8: 26, 9: 34, 10: 43,
            11: 55, 12: 69, 13: 87, 14: 108, 15: 134, 16: 164, 17: 200, 18: 243, 19: 293, 20: 352,
            21: 421, 22: 502, 23: 597, 24: 708, 25: 838, 26: 989, 27: 1165, 28: 1370, 29: 1608, 30: 1886,
            31: 2209, 32: 2585, 33: 3021
        },
        "Duration": {
            0: 30, 1: 35, 2: 40, 3: 45, 4: 50, 5: 55, 6: 60, 7: 65, 8: 70, 9: 75, 10: 80,
            11: 85, 12: 90, 13: 95, 14: 100
        },
        "Cooldown": {
            0: 125, 1: 120, 2: 115, 3: 110, 4: 105, 5: 100, 6: 95, 7: 90, 8: 85, 9: 80, 10: 75,
            11: 70, 12: 65, 13: 60, 14: 55, 15: 50
        },
    },
    "Labs": {
        "Size": {
            1: 0.04, 2: 0.08, 3: 0.12, 4: 0.16, 5: 0.20, 6: 0.24, 7: 0.28, 8: 0.32, 9: 0.36, 10: 0.40,
            11: 0.44, 12: 0.48, 13: 0.52, 14: 0.56, 15: 0.60, 16: 0.64, 17: 0.68, 18: 0.72, 19: 0.76, 20: 0.80,
            21: 0.84, 22: 0.88, 23: 0.92, 24: 0.96, 25: 1.00, 26: 1.04, 27: 1.08, 28: 1.12, 29: 1.16, 30: 1.20
        },
        "Stun": {
            0: False, 1: True
        },
        "Stun Chance": {
            1: 0.075, 2: 0.100, 3: 0.125, 4: 0.150, 5: 0.175, 6: 0.200, 7: 0.225, 8: 0.250, 9: 0.275, 10: 0.300,
            11: 0.325, 12: 0.350, 13: 0.375, 14: 0.400, 15: 0.425, 16: 0.450, 17: 0.475, 18: 0.500, 19: 0.525, 20: 0.550,
            21: 0.575, 22: 0.600, 23: 0.625, 24: 0.650, 25: 0.675, 26: 0.700, 27: 0.725, 28: 0.750, 29: 0.775, 30: 0.800
        },
        "Stun Time": {
            1: 1.3, 2: 1.6, 3: 1.9, 4: 2.2, 5: 2.5, 6: 2.8, 7: 3.1, 8: 3.4, 9: 3.7, 10: 4.0,
            11: 4.3, 12: 4.6, 13: 4.9, 14: 5.2, 15: 5.5, 16: 5.8, 17: 6.1, 18: 6.4, 19: 6.7, 20: 7.0,
            21: 7.3, 22: 7.6, 23: 7.9, 24: 8.2, 25: 8.5, 26: 8.8, 27: 9.1, 28: 9.4, 29: 9.7, 30: 10.0
        },
        "Swamp Rend - Basic Enemies": {
            1: 0.03, 2: 0.06, 3: 0.09, 4: 0.12, 5: 0.15, 6: 0.18, 7: 0.21, 8: 0.24, 9: 0.27, 10: 0.30,
            11: 0.33, 12: 0.36, 13: 0.39, 14: 0.42, 15: 0.45, 16: 0.48, 17: 0.51, 18: 0.54, 19: 0.57, 20: 0.60,
            21: 0.63, 22: 0.66, 23: 0.69, 24: 0.72, 25: 0.75, 26: 0.78, 27: 0.81, 28: 0.84, 29: 0.87, 30: 0.90
        },
        "Swamp Rend - Additional Enemies": {
            1: "Ranged Enemies", 2: "Fast Enemies", 3: "Tank Enemies", 4: "Protector Enemies", 5: "Boss Enemies", 6: "Vampire"
        },
    },
    "Modules": None,
    "Submodules": {
        "Damage Mult": "Poison Swamp - Damage [x]",
        "Duration": "Poison Swamp - Duration [s]",
        "Cooldown": "Poison Swamp - Cooldown [s]",
    },
    "Relics": {
        "Damage Mult": "Ultimate Damage"    
    }
}


# ============================================================================
# CHAIN LIGHTNING LOOKUPS
# ============================================================================

CHAIN_LIGHTNING_LUT = {
    "Levels": {
        "Damage Mult": {
            0: 2, 1: 3, 2: 5, 3: 9, 4: 14, 5: 22, 6: 32, 7: 46, 8: 63, 9: 85, 10: 113,
            11: 148, 12: 191, 13: 244, 14: 309, 15: 387, 16: 482, 17: 596, 18: 733, 19: 898, 20: 1094,
            21: 1328, 22: 1607, 23: 1937, 24: 2794, 25: 3342, 26: 3990, 27: 4755, 28: 5655, 29: 6715, 30: 7961
        },
        "Quantity": {
            0: 1, 1: 2, 2: 3, 3: 4, 4: 5
        },
        "Chance": {
            0: 0.05, 1: 0.065, 2: 0.08, 3: 0.095, 4: 0.11, 5: 0.125, 6: 0.14, 7: 0.155, 8: 0.17, 9: 0.185, 10: 0.20,
            11: 0.215, 12: 0.23, 13: 0.245, 14: 0.26, 15: 0.275
        },
    },
    "Labs": {
        "Chain Lightning Shock": {
            0: False, 1: True
        },
        "Shock Chance": {
            0: False, 1: True
        },
        "Shock Multiplier": {
            1: 1.14, 2: 1.18, 3: 1.22, 4: 1.26, 5: 1.30, 6: 1.34, 7: 1.38, 8: 1.42, 9: 1.46, 10: 1.50,
            11: 1.54, 12: 1.58, 13: 1.62, 14: 1.66
        },
        "Chain Thunder": {
            1: 0.03, 2: 0.06, 3: 0.09, 4: 0.12, 5: 0.15, 6: 0.18, 7: 0.21, 8: 0.24, 9: 0.27, 10: 0.30,
            11: 0.33, 12: 0.36, 13: 0.39, 14: 0.42, 15: 0.45, 16: 0.48, 17: 0.51, 18: 0.54, 19: 0.57, 20: 0.60,
            21: 0.63, 22: 0.66, 23: 0.69, 24: 0.72, 25: 0.75, 26: 0.78, 27: 0.81, 28: 0.84, 29: 0.87, 30: 0.90
        },
        "Lightning Amplifier-Scatter": {
                1: 1.25, 2: 2.50, 3: 3.75, 4: 5.00, 5: 6.25, 6: 7.50, 7: 8.75, 8: 10.00, 9: 11.25, 10: 12.50,
                11: 13.75, 12: 15.00, 13: 16.25, 14: 17.50, 15: 18.75, 16: 20.00, 17: 21.25, 18: 22.50, 19: 23.75, 20: 25.00,
                21: 26.25, 22: 27.50, 23: 28.75, 24: 30.00, 25: 31.25, 26: 32.50, 27: 33.75, 28: 35.00, 29: 36.25, 30: 37.50
        },
    },
    "Modules": None,
    "Submodules": {
        "Damage Mult": "Chain Lightning - Damage [x]",
        "Quantity": "Chain Lightning - Quantity",
        "Chance %": "Chain Lightning - Chance [%]",
    },
    "Relics": {
        "Damage Mult": "Ultimate Damage"    
    }
}

# ============================================================================
# LABS RESEARCH LOOKUPS
# ============================================================================
# Map weapon type + parameter to labs lookup table
# Labs levels map research level -> bonus value

LABS_LOOKUPS = {
    ("Golden Tower", "Duration"): GOLDEN_TOWER_DURATION_LABS_LOOKUP,
    ("Golden Tower", "Coin Bonus"): GOLDEN_TOWER_COIN_BONUS_LABS_LOOKUP,
    ("Black Hole",   "Coin Bonus"): BLACK_HOLE_COIN_BONUS_LABS_LOOKUP,
    ("Death Wave",   "Coin Bonus"): DEATH_WAVE_COIN_BONUS_LABS_LOOKUP,
    ("Spotlight",    "Coin Bonus"): SPOTLIGHT_COIN_BONUS_LABS_LOOKUP,
    ("Chrono Field", "Duration"): CHRONO_FIELD_DURATION_LABS_LOOKUP,
}

# ============================================================================
# ULTIMATE WEAPON EFFECT SOURCE CAPABILITIES
# ============================================================================

SOURCE_LABS = "UW_LABS"
SOURCE_MODULES = "UW_MODULES"
SOURCE_RELICS = "UW_RELICS"
SOURCE_ASSIST_MODS = "UW_ASSIST_MODS"
SOURCE_LEVELS = "UW_LEVELS"


def _normalize_lookup_name(text: str) -> str:
    return "".join(ch for ch in str(text).lower() if ch.isalnum())


_PARAMETER_ALIASES = {
    "Golden Tower": {
        "Bonus": "Coin Bonus",
    },
    "Golden Bot": {
        "Bonus": "Coin Bonus",
    },
    "Black Hole": {
        "Bonus": "Coin Bonus",
    },
    "Spotlight": {
        "Bonus": "Damage Mult",
        "Spotlight Missiles": "Missiles",
    },
    "Death Wave": {
        "Damage": "Damage Mult",
        "Bonus": "Damage Mult",
        "Coins Bonus": "Coin Bonus",
        "Death Wave Health": "Health",
    },
    "Chrono Field": {
        "Speed Reduction": "Slow %",
    },
}

_ENTITY_SOURCE_NAME_ALIASES = {
    "Ally": "Ally Chip",
    "Attack": "Attack Chip",
    "Fetch": "Fetch Chip",
    "Bounty": "Bounty Chip",
    "Summon": "Summon Chip",
    "Scout": "Scout Chip",
    "Summon Guardian": "Summon Chip",
}

# Unified source of truth: weapon + parameter -> set of available effect sources
UW_SOURCES_MAP = {
    # GOLDEN TOWER
    ("Golden Tower", "Coin Bonus"): frozenset([SOURCE_LEVELS, SOURCE_LABS, SOURCE_MODULES]),
    ("Golden Tower", "Duration"): frozenset([SOURCE_LEVELS, SOURCE_LABS, SOURCE_MODULES]),
    ("Golden Tower", "Cooldown"): frozenset([SOURCE_LEVELS, SOURCE_MODULES]),
    
    # BLACK HOLE
    ("Black Hole", "Size"): frozenset([SOURCE_LEVELS, SOURCE_MODULES]),
    ("Black Hole", "Duration"): frozenset([SOURCE_LEVELS, SOURCE_MODULES]),
    ("Black Hole", "Cooldown"): frozenset([SOURCE_LEVELS, SOURCE_MODULES]),
    ("Black Hole", "Damage Mult"): frozenset([SOURCE_LABS]),
    ("Black Hole", "Coin Bonus"): frozenset([SOURCE_LABS]),
    ("Black Hole", "Extra Black Hole"): frozenset([SOURCE_LABS]),
    ("Black Hole", "Black Hole Disable Ranged Enemies"): frozenset([SOURCE_LABS]),
    
    # DEATH WAVE
    ("Death Wave", "Damage Mult"): frozenset([SOURCE_LEVELS, SOURCE_MODULES]),    
    ("Death Wave", "Coin Bonus"): frozenset([SOURCE_LABS]),
    ("Death Wave", "Quantity"): frozenset([SOURCE_LEVELS, SOURCE_MODULES]),
    ("Death Wave", "Cooldown"): frozenset([SOURCE_LEVELS, SOURCE_MODULES]),
    ("Death Wave", "Health"): frozenset([SOURCE_LABS]),
    ("Death Wave", "Cells Bonus"): frozenset([SOURCE_LABS]),
    ("Death Wave", "Damage Amplifier"): frozenset([SOURCE_LABS]),
    ("Death Wave", "Armor Stripping"): frozenset([SOURCE_LABS]),
    
    # SPOTLIGHT
    ("Spotlight", "Damage Mult"): frozenset([SOURCE_LEVELS, SOURCE_MODULES]),
    ("Spotlight", "Coin Bonus"): frozenset([SOURCE_LABS]),
    ("Spotlight", "Angle"): frozenset([SOURCE_LEVELS, SOURCE_MODULES]),
    ("Spotlight", "Quantity"): frozenset([SOURCE_LEVELS]),
    ("Spotlight", "Missiles"): frozenset([SOURCE_LABS]),
    
    # CHRONO FIELD
    ("Chrono Field", "Duration"): frozenset([SOURCE_LEVELS, SOURCE_LABS, SOURCE_MODULES]),
    ("Chrono Field", "Cooldown"): frozenset([SOURCE_LEVELS, SOURCE_MODULES]),
    ("Chrono Field", "Slow %"): frozenset([SOURCE_LEVELS, SOURCE_MODULES]),
    ("Chrono Field", "Damage Reduction"): frozenset([SOURCE_LABS]),
    ("Chrono Field", "Damage Reduction %"): frozenset([SOURCE_LABS]),
    ("Chrono Field", "Range"): frozenset([SOURCE_LABS]),
    
    # SMART MISSILES
    ("Smart Missiles", "Damage Mult"): frozenset([SOURCE_LEVELS, SOURCE_MODULES]),
    ("Smart Missiles", "Quantity"): frozenset([SOURCE_LEVELS, SOURCE_MODULES]),
    ("Smart Missiles", "Cooldown"): frozenset([SOURCE_LEVELS, SOURCE_MODULES]),
    ("Smart Missiles", "Despawn Time"): frozenset([SOURCE_LABS]),
    ("Smart Missiles", "Missile Amplifier"): frozenset([SOURCE_LABS]),
    ("Smart Missiles", "Missiles Explosion"): frozenset([SOURCE_LABS]),
    ("Smart Missiles", "Missile Radius"): frozenset([SOURCE_LABS]),
    ("Smart Missiles", "Missile Barrage"): frozenset([SOURCE_LABS]),
    ("Smart Missiles", "Missile Barrage Quantity"): frozenset([SOURCE_LABS]),
    ("Smart Missiles", "Recharge Missile Barrage"): frozenset([SOURCE_LABS]),
    
    # INNER LAND MINES
    ("Inner Land Mines", "Damage %"): frozenset([SOURCE_LEVELS, SOURCE_MODULES]),
    ("Inner Land Mines", "Quantity"): frozenset([SOURCE_LEVELS, SOURCE_MODULES]),
    ("Inner Land Mines", "Cooldown"): frozenset([SOURCE_LEVELS, SOURCE_MODULES]),
    ("Inner Land Mines", "Inner Mine Blast Radius"): frozenset([SOURCE_LABS]),
    ("Inner Land Mines", "Inner Mine Rotation Speed"): frozenset([SOURCE_LABS]),
    ("Inner Land Mines", "Inner Mine Stun"): frozenset([SOURCE_LABS]),
    ("Inner Land Mines", "Inner Land Mine - Chrono Jump"): frozenset([SOURCE_LABS]),
    
    # POISON SWAMP
    ("Poison Swamp", "Damage "): frozenset([SOURCE_LEVELS, SOURCE_MODULES]),
    ("Poison Swamp", "Duration"): frozenset([SOURCE_LEVELS, SOURCE_MODULES]),
    ("Poison Swamp", "Cooldown"): frozenset([SOURCE_LEVELS, SOURCE_MODULES]),
    ("Poison Swamp", "Swamp Radius"): frozenset([SOURCE_LABS]),
    ("Poison Swamp", "Poison Swamp Stun"): frozenset([SOURCE_LABS]),
    ("Poison Swamp", "Swamp Stun Chance"): frozenset([SOURCE_LABS]),
    ("Poison Swamp", "Swamp Stun Time"): frozenset([SOURCE_LABS]),
    ("Poison Swamp", "Swamp Rend - Basic Enemies"): frozenset([SOURCE_LABS]),
    ("Poison Swamp", "Swamp Rend - Additional Enemies"): frozenset([SOURCE_LABS]),

    # CHAIN LIGHTNING
    ("Chain Lightning", "Damage Mult"): frozenset([SOURCE_LEVELS, SOURCE_MODULES]),
    ("Chain Lightning", "Quantity"): frozenset([SOURCE_LEVELS, SOURCE_MODULES]),
    ("Chain Lightning", "Chance %"): frozenset([SOURCE_LEVELS, SOURCE_MODULES]),
    ("Chain Lightning", "Chain Lightning Shock"): frozenset([SOURCE_LABS]),
    ("Chain Lightning", "Shock Chance"): frozenset([SOURCE_LABS]),
    ("Chain Lightning", "Shock Multiplier"): frozenset([SOURCE_LABS]),
    ("Chain Lightning", "Shock Chance"): frozenset([SOURCE_LABS]),
    ("Chain Lightning", "Chain Thunder"): frozenset([SOURCE_LABS]),
    ("Chain Lightning", "Lightning Amplifier-Scatter"): frozenset([SOURCE_LABS]),
}

GUARDIAN_SOURCES_MAP = {
    # ALLY CHIP
    ("Ally Chip", "Recovery Amount"): frozenset([SOURCE_LEVELS]),
    ("Ally Chip", "Cooldown"): frozenset([SOURCE_LEVELS]),
    ("Ally Chip", "Max Recovery"): frozenset([SOURCE_LEVELS]),
    
    # ATTACK CHIP
    ("Attack Chip", "Percentage"): frozenset([SOURCE_LEVELS]),
    ("Attack Chip", "Cooldown"): frozenset([SOURCE_LEVELS]),
    ("Attack Chip", "Targets"): frozenset([SOURCE_LEVELS]),
    
    # FETCH CHIP
    ("Fetch Chip", "Cooldown"): frozenset([SOURCE_LEVELS]),
    ("Fetch Chip", "Find Chance"): frozenset([SOURCE_LEVELS]),
    ("Fetch Chip", "Double Find Chance"): frozenset([SOURCE_LEVELS]),
    
    # BOUNTY CHIP
    ("Bounty Chip", "Multiplier"): frozenset([SOURCE_LEVELS]),
    ("Bounty Chip", "Cooldown"): frozenset([SOURCE_LEVELS]),
    ("Bounty Chip", "Targets"): frozenset([SOURCE_LEVELS]),
    
    # SUMMON CHIP
    ("Summon Chip", "Cooldown"): frozenset([SOURCE_LEVELS]),
    ("Summon Chip", "Duration"): frozenset([SOURCE_LEVELS]),
    ("Summon Chip", "Cash Bonus"): frozenset([SOURCE_LEVELS]),
    
    # SCOUT CHIP
    ("Scout Chip", "Cooldown"): frozenset([SOURCE_LEVELS]),
    ("Scout Chip", "Range"): frozenset([SOURCE_LEVELS]),
    ("Scout Chip", "Duration"): frozenset([SOURCE_LEVELS]),
}

BOT_SOURCES_MAP = {
    # GOLDEN BOT
    ("Golden Bot", "Duration"): frozenset([SOURCE_LEVELS, SOURCE_LABS]),
    ("Golden Bot", "Cooldown"): frozenset([SOURCE_LEVELS, SOURCE_LABS]),
    ("Golden Bot", "Bonus"): frozenset([SOURCE_LEVELS]),
    ("Golden Bot", "Range"): frozenset([SOURCE_LEVELS, SOURCE_RELICS]),
    
    # FLAME BOT (placeholder - no lookups defined yet)
    ("Flame Bot", "Damage Reduction"): frozenset([SOURCE_LEVELS]),
    ("Flame Bot", "Cooldown"): frozenset([SOURCE_LEVELS, SOURCE_LABS]),
    ("Flame Bot", "Damage"): frozenset([SOURCE_LEVELS]),
    ("Flame Bot", "Range"): frozenset([SOURCE_LEVELS, SOURCE_RELICS]),
    ("Flame Bot", "Burn Stack"): frozenset([SOURCE_LABS]),
    
    # THUNDER BOT (placeholder - no lookups defined yet)
    ("Thunder Bot", "Duration"): frozenset([SOURCE_LEVELS]),
    ("Thunder Bot", "Cooldown"): frozenset([SOURCE_LEVELS, SOURCE_LABS]),
    ("Thunder Bot", "Linger"): frozenset([SOURCE_LEVELS]),
    ("Thunder Bot", "Range"): frozenset([SOURCE_LEVELS, SOURCE_RELICS]),
    ("Thunder Bot", "Linger Time"): frozenset([SOURCE_LABS]),
    
    # AMPLIFY BOT (placeholder - no lookups defined yet)
    ("Amplify Bot", "Duration"): frozenset([SOURCE_LEVELS, SOURCE_LABS]),
    ("Amplify Bot", "Cooldown"): frozenset([SOURCE_LEVELS, SOURCE_LABS]),
    ("Amplify Bot", "Damage"): frozenset([SOURCE_LEVELS]),
    ("Amplify Bot", "Range"): frozenset([SOURCE_LEVELS, SOURCE_RELICS]),
}


def normalize_weapon_parameter(weapon_name: str, param_name: str) -> tuple[str, str]:
    """Normalize aliases so capability lookups match analyzer output."""
    weapon_aliases = _PARAMETER_ALIASES.get(weapon_name, {})
    return weapon_name, weapon_aliases.get(param_name, param_name)


def _normalize_entity_name_for_sources(entity_name: str) -> str:
    """Map display/entity names to source-map entity keys."""
    return _ENTITY_SOURCE_NAME_ALIASES.get(entity_name, entity_name)


def _get_sources_map_for_entity(entity_name: str) -> dict[tuple[str, str], frozenset[str]]:
    """Resolve entity source map from registry first, then by name fallback."""
    registry = globals().get("LOOKUP_TABLE_REGISTRY")
    if isinstance(registry, dict):
        for entities in registry.values():
            if isinstance(entities, dict) and entity_name in entities:
                entry = entities.get(entity_name)
                if isinstance(entry, dict):
                    sources_map = entry.get("sources_map")
                    if isinstance(sources_map, dict):
                        return sources_map

    normalized = _normalize_entity_name_for_sources(entity_name).lower()
    if "chip" in normalized:
        return GUARDIAN_SOURCES_MAP
    if "bot" in normalized:
        return BOT_SOURCES_MAP
    return UW_SOURCES_MAP


def get_available_effect_sources(weapon_name: str, param_name: str) -> tuple[str, ...]:
    """Return supported non-base effect sources for a weapon parameter.
    
    Filters UW_SOURCES_MAP to exclude SOURCE_LEVELS (base level), returning only
    non-base sources like labs, modules, relics, and assist mods.
    """
    weapon_name, param_name = normalize_weapon_parameter(weapon_name, param_name)
    source_entity = _normalize_entity_name_for_sources(weapon_name)
    sources_map = _get_sources_map_for_entity(weapon_name)
    sources = sources_map.get((source_entity, param_name), frozenset())
    
    # Filter out UW_LEVELS, return only non-base sources in order
    non_base = tuple(
        source for source in (SOURCE_LABS, SOURCE_MODULES, SOURCE_RELICS, SOURCE_ASSIST_MODS)
        if source in sources
    )
    return non_base


def get_effect_source_flags(weapon_name: str, param_name: str) -> dict[str, object]:
    """Return UI-friendly capability flags for non-base effect sources."""
    weapon_name, param_name = normalize_weapon_parameter(weapon_name, param_name)
    source_entity = _normalize_entity_name_for_sources(weapon_name)
    sources_map = _get_sources_map_for_entity(weapon_name)
    sources = sources_map.get((source_entity, param_name), frozenset())

    return {
        "available_effect_sources": get_available_effect_sources(weapon_name, param_name),
        "has_any_effect_source": bool(sources - {SOURCE_LEVELS}),
        "levels_supported": SOURCE_LEVELS in sources,
        "labs_supported": SOURCE_LABS in sources,
        "module_supported": SOURCE_MODULES in sources,
        "relic_supported": SOURCE_RELICS in sources,
        "assist_mods_supported": SOURCE_ASSIST_MODS in sources,
    }


def has_effect_source(weapon_name: str, param_name: str, source: str) -> bool:
    """Convenience predicate for single-source capability checks."""
    weapon_name, param_name = normalize_weapon_parameter(weapon_name, param_name)
    source_entity = _normalize_entity_name_for_sources(weapon_name)
    sources_map = _get_sources_map_for_entity(weapon_name)
    return source in sources_map.get((source_entity, param_name), frozenset())


def _get_registry_lut(entity_name: str) -> dict[str, object]:
    """Return the LUT block for an entity from LOOKUP_TABLE_REGISTRY."""
    registry = globals().get("LOOKUP_TABLE_REGISTRY")
    if not isinstance(registry, dict):
        return {}

    for entities in registry.values():
        if not isinstance(entities, dict):
            continue
        entry = entities.get(entity_name)
        if not isinstance(entry, dict):
            continue
        lut = entry.get("lut")
        if isinstance(lut, dict):
            return lut

    return {}


def get_labs_lookup_table(entity_name: str, param_name: str) -> dict | None:
    """Return labs lookup table for a canonical parameter, if available."""
    entity_name, canonical_param = normalize_weapon_parameter(entity_name, param_name)

    direct = LABS_LOOKUPS.get((entity_name, canonical_param))
    if isinstance(direct, dict):
        return direct

    lut = _get_registry_lut(entity_name)
    labs_bucket = lut.get("Labs") if isinstance(lut, dict) else None
    if not isinstance(labs_bucket, dict):
        return None

    for raw_param, lookup in labs_bucket.items():
        if not isinstance(lookup, dict):
            continue
        _, normalized_raw = normalize_weapon_parameter(entity_name, str(raw_param))
        if normalized_raw == canonical_param:
            return lookup

    return None


def get_labs_parameters(entity_name: str) -> list[str]:
    """Return canonical labs parameter names for the given entity."""
    names: list[str] = []
    seen: set[str] = set()

    lut = _get_registry_lut(entity_name)
    labs_bucket = lut.get("Labs") if isinstance(lut, dict) else None
    if isinstance(labs_bucket, dict):
        for raw_param in labs_bucket.keys():
            _, canonical = normalize_weapon_parameter(entity_name, str(raw_param))
            if canonical not in seen:
                seen.add(canonical)
                names.append(canonical)

    for weapon_name, param_name in LABS_LOOKUPS.keys():
        if weapon_name != entity_name:
            continue
        _, canonical = normalize_weapon_parameter(entity_name, str(param_name))
        if canonical not in seen:
            seen.add(canonical)
            names.append(canonical)

    return names


def get_data_view_entry_catalog() -> dict[str, dict[str, dict[str, object]]]:
    """Build clean per-entity entry catalog for data-driven pages.

    Uses source maps as the primary declaration of available entries, then unions
    LUT-defined parameters to avoid dropping valid static lookup entries.
    """
    out: dict[str, dict[str, dict[str, object]]] = {}
    registry = globals().get("LOOKUP_TABLE_REGISTRY")
    if not isinstance(registry, dict):
        return out

    for section_name, entities in registry.items():
        if not isinstance(entities, dict):
            continue

        section_entries: dict[str, dict[str, object]] = {}
        for entity_name, entry in entities.items():
            if not isinstance(entry, dict):
                continue

            lut = entry.get("lut")
            sources_map = entry.get("sources_map")
            normalized_entity = _normalize_entity_name_for_sources(entity_name)

            source_params = set()
            param_sources: dict[str, tuple[str, ...]] = {}
            if isinstance(sources_map, dict):
                for key, source_values in sources_map.items():
                    if not (isinstance(key, tuple) and len(key) == 2):
                        continue
                    map_entity, map_param = key
                    if map_entity != normalized_entity:
                        continue

                    source_params.add(map_param)
                    if isinstance(source_values, frozenset):
                        ordered = tuple(
                            src
                            for src in (SOURCE_LEVELS, SOURCE_LABS, SOURCE_MODULES, SOURCE_RELICS, SOURCE_ASSIST_MODS)
                            if src in source_values
                        )
                    else:
                        ordered = tuple()
                    param_sources[map_param] = ordered

            lut_params = set()
            if isinstance(lut, dict):
                for bucket in ("Levels", "Labs", "Modules", "Submodules", "Relics"):
                    bucket_data = lut.get(bucket)
                    if isinstance(bucket_data, dict):
                        for k in bucket_data.keys():
                            _, canonical_param = normalize_weapon_parameter(entity_name, str(k))
                            lut_params.add(canonical_param)

            all_params = sorted(source_params | lut_params)
            section_entries[entity_name] = {
                "entries": all_params,
                "entry_sources": param_sources,
            }

        out[section_name] = section_entries

    return out

# ============================================================================
# GUARDIAN CHIP LOOKUPS
# ============================================================================

ALLY_CHIP_LOOKUP = {
    "Levels": {
        "Recovery Amount": {0: 0.01, 1: 0.02, 2: 0.03, 3: 0.04, 4: 0.05, 5: 0.06, 6: 0.07, 7: 0.08, 8: 0.09, 9: 0.10,
                            10: 0.11, 11: 0.12, 12: 0.13, 13: 0.14, 14: 0.15, 15: 0.16, 16: 0.17, 17: 0.18, 18: 0.19,
                            19: 0.20, 20: 0.21, 21: 0.22, 22: 0.23, 23: 0.24, 24: 0.25, 25: 0.26, 26: 0.27, 27: 0.28,
                            28: 0.29, 29: 0.30, 30: 0.31, 31: 0.32, 32: 0.33, 33: 0.34, 34: 0.35, 35: 0.36, 36: 0.37,
                            37: 0.38, 38: 0.39, 39: 0.40, 40: 0.41, 41: 0.42, 42: 0.43, 43: 0.44, 44: 0.45, 45: 0.46,
                            46: 0.47, 47: 0.48, 48: 0.49, 49: 0.50},
        "Cooldown": {0: 120, 1: 119, 2: 118, 3: 117, 4: 116, 5: 115, 6: 114, 7: 113, 8: 112, 9: 111, 10: 110, 11: 109,
                        12: 108, 13: 107, 14: 106, 15: 105, 16: 104, 17: 103, 18: 102, 19: 101, 20: 100, 21: 99, 22: 98,
                        23: 97, 24: 96, 25: 95, 26: 94, 27: 93, 28: 92, 29: 91, 30: 90, 31: 89, 32: 88, 33: 87, 34: 86,
                        35: 85, 36: 84, 37: 83, 38: 82, 39: 81, 40: 80, 41: 79, 42: 78, 43: 77, 44: 76, 45: 75, 46: 74,
                        47: 73, 48: 72, 49: 71, 50: 70, 51: 69, 52: 68, 53: 67, 54: 66, 55: 65, 56: 64, 57: 63, 58: 62,
                        59: 61, 60: 60, 61: 59, 62: 58, 63: 57, 64: 56, 65: 55, 66: 54, 67: 53, 68: 52, 69: 51, 70: 50,
                        71: 49, 72: 48, 73: 47, 74: 46, 75: 45, 76: 44, 77: 43, 78: 42, 79: 41, 80: 40,81: 39, 82: 38,
                        83: 37, 84: 36, 85: 35, 86: 34, 87: 33, 88: 32, 89: 31, 90: 30},
        "Max Recovery": {0: 1.1, 1: 1.2, 2: 1.3, 3: 1.4, 4: 1.5, 5: 1.6, 6: 1.7, 7: 1.8, 8: 1.9, 9: 2.0, 10: 2.1, 11: 2.2, 12: 2.3, 13: 2.4, 14: 2.5,
                            15: 2.6, 16: 2.7, 17: 2.8, 18: 2.9, 19: 3.0, 20: 3.1, 21: 3.2, 22: 3.3, 23: 3.4, 24: 3.5, 25: 3.6, 26: 3.7, 27: 3.8,
                            28: 3.9, 29: 4.0, 30: 4.1, 31: 4.2, 32: 4.3, 33: 4.4, 34: 4.5, 35: 4.6, 36: 4.7, 37: 4.8, 38: 4.9, 39: 5.0, 40: 5.1, 41: 5.2,
                            42: 5.3, 43: 5.4, 44: 5.5, 45: 5.6, 46: 5.7, 47: 5.8, 48: 5.9, 49: 6.0, 50: 6.1, 51: 6.2, 52: 6.3, 53: 6.4, 54: 6.5, 55: 6.6,
                            56: 6.7, 57: 6.8, 58: 6.9, 59: 7.0, 60: 7.1, 61: 7.2, 62: 7.3, 63: 7.4, 64: 7.5, 65: 7.6, 66: 7.7, 67: 7.8, 68: 7.9, 69: 8.0,
                            70: 8.1, 71: 8.2, 72: 8.3, 73: 8.4, 74: 8.5, 75: 8.6, 76: 8.7, 77: 8.8, 78: 8.9, 79: 9.0, 80: 9.1, 81: 9.2, 82: 9.3, 83: 9.4, 84: 9.5,
                            85: 9.6, 86: 9.7, 87: 9.8, 88: 9.9, 89: 10.0}
    },
    "Labs":       None,
    "Modules":    None,
    "Submodules": None,
    "Relics":     None,
}

ATTACK_CHIP_LOOKUP = {
    "Levels": {
        "Percentage": {0: 0.01, 1: 0.02, 2: 0.03, 3: 0.04, 4: 0.05, 5: 0.06, 6: 0.07, 7: 0.08, 8: 0.09, 9: 0.10, 10: 0.11, 11: 0.12, 12: 0.13, 13: 0.14, 14: 0.15,
                            15: 0.16, 16: 0.17, 17: 0.18, 18: 0.19, 19: 0.20},
        "Cooldown": {0: 120, 1: 119, 2: 118, 3: 117, 4: 116, 5: 115, 6: 114, 7: 113, 8: 112, 9: 111, 10: 110, 11: 109,
                        12: 108, 13: 107, 14: 106, 15: 105, 16: 104, 17: 103, 18: 102, 19: 101, 20: 100, 21: 99, 22: 98,
                        23: 97, 24: 96, 25: 95, 26: 94, 27: 93, 28: 92, 29: 91, 30: 90, 31: 89, 32: 88, 33: 87, 34: 86,
                        35: 85, 36: 84, 37: 83, 38: 82, 39: 81, 40: 80, 41: 79, 42: 78, 43: 77, 44: 76, 45: 75, 46: 74,
                        47: 73, 48: 72, 49: 71, 50: 70, 51: 69, 52: 68, 53: 67, 54: 66, 55: 65, 56: 64, 57: 63, 58: 62,
                        59: 61, 60: 60, 61: 59, 62: 58, 63: 57, 64: 56, 65: 55, 66: 54, 67: 53, 68: 52, 69: 51, 70: 50,
                        71: 49, 72: 48, 73: 47, 74: 46, 75: 45, 76: 44, 77: 43, 78: 42, 79: 41, 80: 40,81: 39, 82: 38,
                        83: 37, 84: 36, 85: 35, 86: 34, 87: 33, 88: 32, 89: 31, 90: 30},
        "Targets": {0: 1, 1: 2, 2: 3, 3: 4, 4: 5, 5: 6, 6: 7, 7: 8, 8: 9, 9: 10}
    },
    "Labs":       None,
    "Modules":    None,
    "Submodules": None,
    "Relics":     None,
}

FETCH_CHIP_LOOKUP = {
    "Levels": {
        "Cooldown": {0: 120, 1: 119, 2: 118, 3: 117, 4: 116, 5: 115, 6: 114, 7: 113, 8: 112, 9: 111, 10: 110, 11: 109,
                        12: 108, 13: 107, 14: 106, 15: 105, 16: 104, 17: 103, 18: 102, 19: 101, 20: 100, 21: 99, 22: 98,
                        23: 97, 24: 96, 25: 95, 26: 94, 27: 93, 28: 92, 29: 91, 30: 90, 31: 89, 32: 88, 33: 87, 34: 86,
                        35: 85, 36: 84, 37: 83, 38: 82, 39: 81, 40: 80, 41: 79, 42: 78, 43: 77, 44: 76, 45: 75, 46: 74,
                        47: 73, 48: 72, 49: 71, 50: 70, 51: 69, 52: 68, 53: 67, 54: 66, 55: 65, 56: 64, 57: 63, 58: 62,
                        59: 61, 60: 60},
        "Find Chance": {0: 0.10, 1: 0.11, 2: 0.12, 3: 0.13, 4: 0.14, 5: 0.15, 6: 0.16, 7: 0.17, 8: 0.18, 9: 0.19,
                        10: 0.20, 11: 0.21, 12: 0.22, 13: 0.23, 14: 0.24, 15: 0.25, 16: 0.26, 17: 0.27, 18: 0.28,
                        19: 0.29, 20: 0.30, 21: 0.31, 22: 0.32, 23: 0.33, 24: 0.34, 25: 0.35, 26: 0.36, 27: 0.37,
                        28: 0.38, 29: 0.39, 30: 0.40, 31: 0.41, 32: 0.42, 33: 0.43, 34: 0.44, 35: 0.45, 36: 0.46,
                        37: 0.47, 38: 0.48, 39: 0.49, 40: 0.50},
        "Double Find Chance": {0: 0.02, 1: 0.03, 2: 0.04, 3: 0.05, 4: 0.06, 5: 0.07, 6: 0.08, 7: 0.09, 8: 0.10, 9: 0.11, 10: 0.12, 11: 0.13, 12: 0.14, 13: 0.15, 14: 0.16, 15: 0.17,
                                16: 0.18, 17: 0.19, 18: 0.20, 19: 0.21, 20: 0.22, 21: 0.23, 22: 0.24, 23: 0.25, 24: 0.26, 25: 0.27, 26: 0.28, 27: 0.29,
                                28: 0.30, 29: 0.31, 30: 0.32, 31: 0.33, 32: 0.34, 33: 0.35, 34: 0.36, 35: 0.37, 36: 0.38, 37: 0.39, 38: 0.40, 39: 0.41, 40: 0.42,
                                41: 0.43, 42: 0.44, 43: 0.45, 44: 0.46, 45: 0.47, 46: 0.48, 47: 0.49, 48: 0.50
                                }
    },
    "Labs":       None,
    "Modules":    None,
    "Submodules": None,
    "Relics":     None,
}

BOUNTY_CHIP_LOOKUP = {
    "Levels": {
        "Multiplier": {0: 0.01, 1: 0.02, 2: 0.03, 3: 0.04, 4: 0.05, 5: 0.06, 6: 0.07, 7: 0.08, 8: 0.09, 9: 0.10, 10: 0.11, 11: 0.12, 12: 0.13, 13: 0.14, 14: 0.15,
                    15: 0.16, 16: 0.17, 17: 0.18, 18: 0.19, 19: 0.20, 20: 0.21, 21: 0.22, 22: 0.23, 23: 0.24, 24: 0.25, 25: 0.26, 26: 0.27, 27: 0.28, 28: 0.29, 29: 0.30, 30: 0.31, 31: 0.32, 32: 0.33, 33: 0.34, 34: 0.35, 35: 0.36, 36: 0.37, 37: 0.38, 38: 0.39, 39: 0.40, 40: 0.41, 41: 0.42, 42: 0.43, 43: 0.44, 44: 0.45, 45: 0.46, 46: 0.47, 47: 0.48, 48: 0.49, 49: 0.50,50: 0.51, 51: 0.52, 52: 0.53, 53: 0.54, 54: 0.55, 55: 0.56, 56: 0.57, 57: 0.58, 58: 0.59, 59: 0.60,60: 0.61, 61: 0.62, 62: 0.63, 63: 0.64, 64: 0.65, 65: 0.66, 66: 0.67, 67: 0.68, 68: 0.69, 69: 0.70, 70: 0.71, 71: 0.72, 72: 0.73, 73: 0.74, 74: 0.75, 75: 0.76,76: 0.77, 77: 0.78, 78: 0.79, 79: 0.80, 80: 0.81,81: 0.82, 82: 0.83, 83: 0.84, 84: 0.85, 85: 0.86, 86: 0.87, 87: 0.88, 88: 0.89, 89: 0.90,90: 0.91, 91: 0.92, 92: 0.93, 93: 0.94,94: 0.95,95: 0.96,96: 0.97,97: 0.98,98: 0.99,99:1.00},
        "Cooldown": {0: 120, 1: 119, 2: 118, 3: 117, 4: 116, 5: 115, 6: 114, 7: 113, 8: 112, 9: 111, 10: 110, 11: 109,
                        12: 108, 13: 107, 14: 106, 15: 105, 16: 104, 17: 103, 18: 102, 19: 101, 20: 100, 21: 99, 22: 98,
                        23: 97, 24: 96, 25: 95, 26: 94, 27: 93, 28: 92, 29: 91, 30: 90, 31: 89, 32: 88, 33: 87, 34: 86,
                        35: 85, 36: 84, 37: 83, 38: 82, 39: 81, 40: 80, 41: 79, 42: 78, 43: 77, 44: 76, 45: 75, 46: 74,
                        47: 73, 48: 72, 49: 71, 50: 70, 51: 69, 52: 68, 53: 67, 54: 66, 55: 65, 56: 64, 57: 63, 58: 62,
                        59: 61, 60: 60},
        "Targets": {0: 1, 1: 2, 2: 3, 3: 4, 4: 5, 5: 6, 6: 7, 7: 8, 8: 9, 9: 10}
    },
    "Labs":       None,
    "Modules":    None,
    "Submodules": None,
    "Relics":     None,
}

SUMMON_CHIP_LOOKUP = {
    "Levels": {
        "Cooldown": {0: 120, 1: 119, 2: 118, 3: 117, 4: 116, 5: 115, 6: 114, 7: 113, 8: 112, 9: 111, 10: 110, 11: 109,
                        12: 108, 13: 107, 14: 106, 15: 105, 16: 104, 17: 103, 18: 102, 19: 101, 20: 100, 21: 99, 22: 98,
                        23: 97, 24: 96, 25: 95, 26: 94, 27: 93, 28: 92, 29: 91, 30: 90, 31: 89, 32: 88, 33: 87, 34: 86,
                        35: 85, 36: 84, 37: 83, 38: 82, 39: 81, 40: 80, 41: 79, 42: 78, 43: 77, 44: 76, 45: 75, 46: 74,
                        47: 73, 48: 72, 49: 71, 50: 70},
        "Duration": {0: 5, 1: 6, 2: 7, 3: 8, 4: 9, 5: 10, 6: 11, 7: 12, 8: 13, 9: 14, 10: 15, 11: 16, 12: 17, 13: 18, 14: 19, 15: 20, 16: 21, 17: 22, 18: 23, 19: 24, 20: 25, 21: 26, 22: 27, 23: 28, 24: 29, 25: 30, 26: 31, 27: 32, 28: 33, 29: 34, 30: 35},
        "Cash Bonus": {0: 1, 1: 2, 2: 3, 3: 4, 4: 5, 5: 6, 6: 7, 7: 8, 8: 9, 9: 10}
    },
    "Labs":       None,
    "Modules":    None,
    "Submodules": None,
    "Relics":     None,
}

SCOUT_CHIP_LOOKUP = {
    "Levels": {
        "Cooldown": {0: 105, 1: 104, 2: 103, 3: 102, 4: 101, 5: 100, 6: 99, 7: 98, 8: 97, 9: 96, 10: 95, 11: 94, 12: 93, 13: 92, 14: 91, 15: 90, 16: 89, 17: 88, 18: 87, 19: 86, 20: 85, 21: 84, 22: 83, 23: 82, 24: 81, 25: 80, 26: 79, 27: 78, 28: 77, 29: 76, 30: 75, 31: 74, 32: 73, 33: 72, 34: 71, 35: 70, 36: 69, 37: 68, 38: 67, 39: 66, 40: 65, 41: 64, 42: 63, 43: 62, 44: 61, 45: 60, 46: 59, 47: 58, 48: 57, 49: 56, 50: 55, 51: 54, 52: 53, 53: 52, 54: 51, 55: 50, 56: 49, 57: 48, 58: 47, 59: 46, 60: 45, 61: 44, 62: 43, 63: 42, 64: 41, 65: 40, 66: 39, 67: 38, 68: 37, 69: 36, 70: 35},
        "Range": {0: 2.0, 1: 2.1, 2: 2.2, 3: 2.3, 4: 2.4, 5: 2.5, 6: 2.6, 7: 2.7, 8: 2.8, 9: 2.9, 10: 3.0, 11: 3.1, 12: 3.2, 13: 3.3, 14: 3.4, 15: 3.5, 16: 3.6, 17: 3.7, 18: 3.8, 19: 3.9, 20: 4.0, 21: 4.1, 22: 4.2, 23: 4.3, 24: 4.4, 25: 4.5, 26: 4.6, 27: 4.7, 28: 4.8, 29: 4.9, 30: 5.0, 31: 5.1, 32: 5.2, 33: 5.3, 34: 5.4, 35: 5.5, 36: 5.6, 37: 5.7, 38: 5.8, 39: 5.9, 40: 6.0},
        "Duration": {0: 5, 1: 6, 2: 7, 3: 8, 4: 9, 5: 10, 6: 11, 7: 12, 8: 13, 9: 14, 10: 15, 11: 16, 12: 17, 13: 18, 14: 19, 15: 20, 16: 21, 17: 22, 18: 23, 19: 24, 20: 25, 21: 26, 22: 27, 23: 28, 24: 29, 25: 30, 26: 31, 27: 32, 28: 33,29:34,30:35}
    },
    "Labs":       None,
    "Modules":    None,
    "Submodules": None,
    "Relics":     None,
}

# Store full nested structures before extracting ["Levels"] for backward compatibility
_ALLY_CHIP_FULL   = ALLY_CHIP_LOOKUP
_ATTACK_CHIP_FULL = ATTACK_CHIP_LOOKUP
_FETCH_CHIP_FULL  = FETCH_CHIP_LOOKUP
_BOUNTY_CHIP_FULL = BOUNTY_CHIP_LOOKUP
_SUMMON_CHIP_FULL = SUMMON_CHIP_LOOKUP
_SCOUT_CHIP_FULL  = SCOUT_CHIP_LOOKUP

# Per-chip lookup constants — point to ["Levels"] so {param: {level: value}} access is preserved
ALLY_CHIP_LOOKUP   = _ALLY_CHIP_FULL["Levels"]
ATTACK_CHIP_LOOKUP = _ATTACK_CHIP_FULL["Levels"]
FETCH_CHIP_LOOKUP  = _FETCH_CHIP_FULL["Levels"]
BOUNTY_CHIP_LOOKUP = _BOUNTY_CHIP_FULL["Levels"]
SUMMON_CHIP_LOOKUP = _SUMMON_CHIP_FULL["Levels"]
SCOUT_CHIP_LOOKUP  = _SCOUT_CHIP_FULL["Levels"]

# Full nested lookup dict for DataManager iteration
GUARDIAN_CHIP_LOOKUPS = {
    "Ally": _ALLY_CHIP_FULL,
    "Attack": _ATTACK_CHIP_FULL,
    "Fetch": _FETCH_CHIP_FULL,
    "Bounty": _BOUNTY_CHIP_FULL,
    "Summon": _SUMMON_CHIP_FULL,
    "Scout": _SCOUT_CHIP_FULL,
}

# Backward compatibility alias.
GUARDIAN_LOOKUPS = GUARDIAN_CHIP_LOOKUPS

# Guardian static conversion rules used by DataManager.
GUARDIAN_PERCENT_PARAMS = frozenset(
    [
        "Recovery Amount",
        "Percentage",
        "Find Chance",
        "Double Find Chance",
    ]
)

GUARDIAN_PARAM_UNITS = {
    "Cooldown": "s",
    "Duration": "s",
    "Recovery Amount": "%",
    "Percentage": "%",
    "Find Chance": "%",
    "Double Find Chance": "%",
    "Range": "x",
    "Max Recovery": "x",
    "Multiplier": "x",
    "Cash Bonus": "x",
    "Targets": "#",
}

GUARDIAN_DEFAULT_VALUES = {
    "Scout": {
        "Cooldown": (100.0, "s"),
        "Range": (2.1, "x"),
        "Duration": (13.0, "s"),
    }
}


def lookup_with_clamp(table: dict[int, object], level: int) -> object:
    """Return lookup value for level; clamp to nearest lower key or minimum key."""
    if not table:
        return None
    if level in table:
        return table[level]
    keys = sorted(table.keys())
    lower = [k for k in keys if k <= level]
    if lower:
        return table[lower[-1]]
    return table[keys[0]]


def get_guardian_param_unit(param_name: str) -> str:
    """Return display unit for a guardian parameter."""
    return GUARDIAN_PARAM_UNITS.get(param_name, "")


def convert_guardian_lookup_value(param_name: str, raw_value: object) -> float:
    """Convert static lookup value into effective display value."""
    value = float(raw_value) if isinstance(raw_value, (int, float, str)) else float(0)
    if param_name in GUARDIAN_PERCENT_PARAMS:
        return value * 100.0
    return value


def get_guardian_fallback_param_values(chip_name: str) -> dict[str, tuple[float, str]]:
    """Return static fallback values for guardian chips missing in userData.json."""
    fallback = GUARDIAN_DEFAULT_VALUES.get(chip_name, {})
    return dict(fallback)


# ============================================================================
# UW SIMULATION STATIC CONFIG
# ============================================================================

WAVE_BASETIME = 26
WAVE_COOLDOWN_TOURNAMENT = 4.5
WAVE_COOLDOWN_FARMING = 9

TIER_CONFIG = {
    "Tier 1": {"wave_time": WAVE_BASETIME, "wave_cooldown": WAVE_COOLDOWN_FARMING, "boss_waves": 10, "type": "Farming", "coin_multiplier": 1.00},
    "Tier 2": {"wave_time": WAVE_BASETIME, "wave_cooldown": WAVE_COOLDOWN_FARMING, "boss_waves": 10, "type": "Farming", "coin_multiplier": 1.80},
    "Tier 3": {"wave_time": WAVE_BASETIME, "wave_cooldown": WAVE_COOLDOWN_FARMING, "boss_waves": 10, "type": "Farming", "coin_multiplier": 2.60},
    "Tier 4": {"wave_time": WAVE_BASETIME, "wave_cooldown": WAVE_COOLDOWN_FARMING, "boss_waves": 10, "type": "Farming", "coin_multiplier": 3.40},
    "Tier 5": {"wave_time": WAVE_BASETIME, "wave_cooldown": WAVE_COOLDOWN_FARMING, "boss_waves": 10, "type": "Farming", "coin_multiplier": 4.20},
    "Tier 6": {"wave_time": WAVE_BASETIME, "wave_cooldown": WAVE_COOLDOWN_FARMING, "boss_waves": 10, "type": "Farming", "coin_multiplier": 5.00},
    "Tier 7": {"wave_time": WAVE_BASETIME, "wave_cooldown": WAVE_COOLDOWN_FARMING, "boss_waves": 10, "type": "Farming", "coin_multiplier": 5.80},
    "Tier 8": {"wave_time": WAVE_BASETIME, "wave_cooldown": WAVE_COOLDOWN_FARMING, "boss_waves": 10, "type": "Farming", "coin_multiplier": 6.60},
    "Tier 9": {"wave_time": WAVE_BASETIME, "wave_cooldown": WAVE_COOLDOWN_FARMING, "boss_waves": 10, "type": "Farming", "coin_multiplier": 7.50},
    "Tier 10": {"wave_time": WAVE_BASETIME, "wave_cooldown": WAVE_COOLDOWN_FARMING, "boss_waves": 10, "type": "Farming", "coin_multiplier": 8.70},
    "Tier 11": {"wave_time": WAVE_BASETIME, "wave_cooldown": WAVE_COOLDOWN_FARMING, "boss_waves": 10, "type": "Farming", "coin_multiplier": 10.30},
    "Tier 12": {"wave_time": WAVE_BASETIME, "wave_cooldown": WAVE_COOLDOWN_FARMING, "boss_waves": 10, "type": "Farming", "coin_multiplier": 12.20},
    "Tier 13": {"wave_time": WAVE_BASETIME, "wave_cooldown": WAVE_COOLDOWN_FARMING, "boss_waves": 10, "type": "Farming", "coin_multiplier": 14.70},
    "Tier 14": {"wave_time": WAVE_BASETIME, "wave_cooldown": WAVE_COOLDOWN_FARMING, "boss_waves": 9, "type": "Farming", "coin_multiplier": 17.60},
    "Tier 15": {"wave_time": WAVE_BASETIME, "wave_cooldown": WAVE_COOLDOWN_FARMING, "boss_waves": 8, "type": "Farming", "coin_multiplier": 21.30},
    "Tier 16": {"wave_time": WAVE_BASETIME, "wave_cooldown": WAVE_COOLDOWN_FARMING, "boss_waves": 7, "type": "Farming", "coin_multiplier": 25.30},
    "Tier 17": {"wave_time": WAVE_BASETIME, "wave_cooldown": WAVE_COOLDOWN_FARMING, "boss_waves": 7, "type": "Farming", "coin_multiplier": 29.10},
    "Tier 18": {"wave_time": WAVE_BASETIME, "wave_cooldown": WAVE_COOLDOWN_FARMING, "boss_waves": 5, "type": "Farming", "coin_multiplier": 33.00},
    "Tier 19": {"wave_time": WAVE_BASETIME, "wave_cooldown": WAVE_COOLDOWN_FARMING, "boss_waves": 5, "type": "Farming", "coin_multiplier": 40.00},
    "Tier 20": {"wave_time": WAVE_BASETIME, "wave_cooldown": WAVE_COOLDOWN_FARMING, "boss_waves": 5, "type": "Farming", "coin_multiplier": 48.00},
    "Tier 21": {"wave_time": WAVE_BASETIME, "wave_cooldown": WAVE_COOLDOWN_FARMING, "boss_waves": 5, "type": "Farming", "coin_multiplier": 60.00},
    "Copper": {"wave_time": WAVE_BASETIME, "wave_cooldown": WAVE_COOLDOWN_TOURNAMENT, "boss_waves": 10, "type": "Tournament"},
    "Silver": {"wave_time": WAVE_BASETIME, "wave_cooldown": WAVE_COOLDOWN_TOURNAMENT, "boss_waves": 9, "type": "Tournament"},
    "Gold": {"wave_time": WAVE_BASETIME, "wave_cooldown": WAVE_COOLDOWN_TOURNAMENT, "boss_waves": 8, "type": "Tournament"},
    "Platinum": {"wave_time": WAVE_BASETIME, "wave_cooldown": WAVE_COOLDOWN_TOURNAMENT, "boss_waves": 7, "type": "Tournament"},
    "Champion": {"wave_time": WAVE_BASETIME, "wave_cooldown": WAVE_COOLDOWN_TOURNAMENT, "boss_waves": 6, "type": "Tournament"},
    "Legends": {"wave_time": WAVE_BASETIME, "wave_cooldown": WAVE_COOLDOWN_TOURNAMENT, "boss_waves": 5, "type": "Tournament"},
}

# Dissonance category labels used by disco import mapping.
DISCO_TYPES = ["attack disco", "defense disco", "utility disco", "uw disco"]


def build_disco_tier_map_template() -> dict[str, dict[str, object]]:
    """Build default tier mapping scaffold from TIER_CONFIG.

    Returns one entry per configured tier so downstream code can fill in
    max_wave/disco_type values without missing tier keys.
    """
    template: dict[str, dict[str, object]] = {}
    for tier_name in TIER_CONFIG.keys():
        template[tier_name] = {
            "max_wave": 0,
            "disco_type": "",
        }
    return template

UW_CONFIG = {
    "Chrono Field": {"base_cooldown": 53, "base_duration": 41, "color_hex": "#00FFFF", "can_queue": False},
    "Black Hole": {"base_cooldown": 46, "base_duration": 33, "color_hex": "#9933FF", "can_queue": True},
    "Golden Tower": {"base_cooldown": 170, "base_duration": 45, "color_hex": "#FF6600", "can_queue": True},
    "Death Wave": {"base_cooldown": 170, "base_duration": 20, "color_hex": "#FF0000", "can_queue": False},
    "Golden Bot": {"base_cooldown": 100, "base_duration": 26, "color_hex": "#FFD700", "can_queue": False},
    "Summon Guardian": {"base_cooldown": 100, "base_duration": 30, "color_hex": "#C532CD", "can_queue": False},
    "Smart Missiles": {"base_cooldown": 120, "base_duration": 15, "color_hex": "#00FF00", "can_queue": False},
    "Inner Land Mines": {"base_cooldown": 130, "base_duration": 25, "color_hex": "#DC143C", "can_queue": False},
    "Poison Swamp": {"base_cooldown": 140, "base_duration": 30, "color_hex": "#32CD32", "can_queue": False},
}


# ============================================================================
# ASSIST MODULE STATS FOR DROPDOWNS
# ============================================================================

ASS_UW_RARITY = {
    "None"
    "Epic",
    "Legendary",
    "Mythic",
    "Ancestral"
}

ASS_UW_STATS = {
    0:0.01, 1:0.02, 2:0.03, 3:0.04, 4:0.05, 5:0.06, 6:0.07, 7:0.08, 8:0.09, 9:0.10, 10:0.11, 11:0.12, 12:0.13, 13:0.14, 14:0.15,
    15:0.16, 16:0.17, 17:0.18, 18:0.19, 19:0.20, 20:0.21, 21:0.22, 22:0.23, 23:0.24, 24:0.25, 25:0.26, 26:0.27, 27:0.28, 28:0.29, 29:0.30, 30:0.31,
    31:0.32, 32:0.33, 33:0.34, 34:0.35, 35:0.36, 36:0.37, 37:0.38, 38:0.39, 39:0.40, 40:0.41, 41:0.42, 42:0.43, 43:0.44, 44:0.45, 45:0.46, 46:0.47, 47:0.48, 48:0.49, 49:0.50,
    50:0.51, 51:0.52, 52:0.53, 53:0.54, 54:0.55, 55:0.56, 56:0.57, 57:0.58, 58:0.59, 59:0.60, 60:0.61, 61:0.62, 62:0.63, 63:0.64, 64:0.65, 65:0.66, 66:0.67, 67:0.68, 68:0.69, 69:0.70
}

ASS_UW_SUBSTATS_LABS = {
    0:0.01, 1:0.02, 2:0.03, 3:0.04, 4:0.05, 5:0.06, 6:0.07, 7:0.08, 8:0.09, 9:0.10, 10:0.11, 11:0.12, 12:0.13, 13:0.14, 14:0.15,
    15:0.16, 16:0.17, 17:0.18, 18:0.19, 19:0.20, 20:0.21, 21:0.22, 22:0.23, 23:0.24, 24:0.25, 25:0.26, 26:0.27, 27:0.28, 28:0.29, 29:0.30
}

ASS_UW_MODULE_LABS = {
    0:0.01, 1:0.02, 2:0.03, 3:0.04, 4:0.05, 5:0.06, 6:0.07, 7:0.08, 8:0.09, 9:0.10, 10:0.11, 11:0.12, 12:0.13, 13:0.14, 14:0.15,
    15:0.16, 16:0.17, 17:0.18, 18:0.19, 19:0.20, 20:0.21, 21:0.22, 22:0.23, 23:0.24, 24:0.25, 25:0.26, 26:0.27, 27:0.28, 28:0.29, 29:0.30
}

# ============================================================================
# PERMA-CALC SHARED STATIC CONSTANTS
# ============================================================================

WA_CARD = {
    "None": 0.0,
    "1 Star": 0.30,
    "2 Star": 0.34,
    "3 Star": 0.38,
    "4 Star": 0.42,
    "5 Star": 0.46,
    "6 Star": 0.50,
    "7 Star": 0.54,
}

FARMING_PERKS = {
    "Black_Hole_Duration": 12,
    "Death_Wave_Duration": 4,
    "Chrono_Field_Duration": 5,
    "Swamp_Radius_Mult": 1.5,
    "Smart_Missiles_Amount": 4,
    "Golden_Tower_Bonus": 1.5,
    "Chain_Lightning_Damage": 2.0,
    "Spotlight_Damage_Mult": 1.5,
}

GC_EFFECTS = {
    "None": 0.0,
    "Epic": 10.0,
    "Legendary": 13.0,
    "Mythic": 17.0,
    "Ancestral": 20.0,
}

MVN_EFFECTS = {
    "None": None,
    "Epic": 20.0,
    "Legendary": 10.0,
    "Mythic": 1.0,
    "Ancestral": -10.0,
}

UW_PERMA_CONFIG = {
    "Black Hole": {
        "cooldown": 46,
        "duration": 32,
        "color_hex": "#9933FF",
        "color_rgba": "rgba(153, 51, 255, 0.8)",
        "color_rgba_light": "rgba(153, 51, 255, 0.6)",
        "can_queue": True,
    },
    "Golden Tower": {
        "cooldown": 170,
        "duration": 45,
        "color_hex": "#FF6600",
        "color_rgba": "rgba(255, 102, 0, 0.8)",
        "color_rgba_light": "rgba(255, 102, 0, 0.6)",
        "can_queue": True,
    },
    "Death Wave": {
        "cooldown": 170,
        "duration": 20,
        "color_hex": "#FF0000",
        "color_rgba": "rgba(255, 0, 0, 0.8)",
        "color_rgba_light": "rgba(255, 0, 0, 0.6)",
        "can_queue": False,
    },
    "Chrono Field": {
        "cooldown": 100,
        "duration": 29,
        "color_hex": "#00FFFF",
        "color_rgba": "rgba(0, 255, 255, 0.8)",
        "color_rgba_light": "rgba(0, 255, 255, 0.6)",
        "can_queue": False,
    },
    "Golden Bot": {
        "cooldown": 100,
        "duration": 26,
        "color_hex": "#FFD700",
        "color_rgba": "rgba(255, 215, 0, 0.8)",
        "color_rgba_light": "rgba(255, 215, 0, 0.6)",
        "can_queue": False,
    },
    "Flame Bot": {
        "cooldown": 75,
        "duration": 0,
        "color_hex": "#FF6600",
        "color_rgba": "rgba(255, 102, 0, 0.8)",
        "color_rgba_light": "rgba(255, 102, 0, 0.6)",
        "can_queue": False,
    },
    "Thunder Bot": {
        "cooldown": 120,
        "duration": 0,
        "color_hex": "#FF2244",
        "color_rgba": "rgba(255, 34, 68, 0.8)",
        "color_rgba_light": "rgba(255, 34, 68, 0.6)",
        "can_queue": False,
    },
    "Amplify Bot": {
        "cooldown": 100,
        "duration": 26,
        "color_hex": "#9B59B6",
        "color_rgba": "rgba(155, 89, 182, 0.8)",
        "color_rgba_light": "rgba(155, 89, 182, 0.6)",
        "can_queue": False,
    },
    "Smart Missiles": {
        "cooldown": 120,
        "duration": 15,
        "color_hex": "#00FF00",
        "color_rgba": "rgba(0, 255, 0, 0.8)",
        "color_rgba_light": "rgba(0, 255, 0, 0.6)",
        "can_queue": False,
    },
    "Inner Land Mines": {
        "cooldown": 130,
        "duration": 25,
        "color_hex": "#DC143C",
        "color_rgba": "rgba(220, 20, 60, 0.8)",
        "color_rgba_light": "rgba(220, 20, 60, 0.6)",
        "can_queue": False,
    },
    "Poison Swamp": {
        "cooldown": 140,
        "duration": 30,
        "color_hex": "#32CD32",
        "color_rgba": "rgba(50, 205, 50, 0.8)",
        "color_rgba_light": "rgba(50, 205, 50, 0.6)",
        "can_queue": False,
    },
    "Summon Guardian": {
        "cooldown": 100,
        "duration": 30,
        "color_hex": "#C532CD",
        "color_rgba": "rgba(50, 205, 50, 0.8)",
        "color_rgba_light": "rgba(50, 205, 50, 0.6)",
        "can_queue": False,
    },
}

# ============================================================================
# ULTIMATE WEAPON UNIQUE MODULE EFFECTS
# ============================================================================

CANNON_UNIQUE_MODULE_EFFECTS = {
    "Astral Deliverance": {"Description": "Bounce shot's range is increased by 3% of the tower's total range. Each bounce increases the projectile's damage by [x]%", "Epic": 20, "Legendary": 40, "Mythic": 60, "Ancestral": 80},
    "Being Annihilator": {"Description": "When you super crit, your next [x] attacks are guaranteed super crits.", "Epic": 3, "Legendary": 4, "Mythic": 5, "Ancestral": 6},
    "Death Penalty": {"Description": "Chance of [x]% to mark an enemy for death when it spawns, causing the first hit to destroy it.", "Epic": 5, "Legendary": 8, "Mythic": 11, "Ancestral": 15},
    "Havoc Bringer": {"Description": "[x]% chance for rend armor to instantly go to max.", "Epic": 10, "Legendary": 13, "Mythic": 15, "Ancestral": 20},
    "Shrink Ray": {"Description": "Attacks have a 1% chance to apply a non-stacking effect that decreases the enemy's mass by [x]%", "Epic": 10, "Legendary": 20, "Mythic": 30, "Ancestral": 40},
    "Amplifying Strike": {"Description": "Killing a boss or elite enemy increases Tower Damage by 5x for [x]s", "Epic": 5, "Legendary": 11, "Mythic": 18, "Ancestral": 26}
}

ARMOR_UNIQUE_MODULE_EFFECTS = {
    "Anti-Cube Portal": {"Description": "Enemies take [x]x damage for 7s after they are hit by a shockwave.", "Epic": 10, "Legendary": 15, "Mythic": 20, "Ancestral": 25},
    "Negative Mass Projector": {"Description": "If an orb doesn't kill the enemy it will apply a stacking debuff, reducing its damage and speed by [x]% per hit, to a max reduction of 50%", "Epic": 1.0, "Legendary": 1.5, "Mythic": 2.0, "Ancestral": 2.5},
    "Wormhole Redirector": {"Description": "Health Regen can heal up to [x]% of Package Max Recovery", "Epic": 25, "Legendary": 50, "Mythic": 75, "Ancestral": 100},
    "Space Displacer": {"Description": "Landmines have a [x]% chance to spawn as an Inner Land Mine (20 max) instead of a normal mine. These mines autonomously move and organize around the tower.", "Epic": 15, "Legendary": 20, "Mythic": 25, "Ancestral": 30},
    "Sharp Fortitude": {"Description": "Increase the Wall's health and regen by x[x]. Enemies take +1% increased damage from wall thorns per subsequent hit.", "Epic": 1.25, "Legendary": 1.5, "Mythic": 2, "Ancestral": 2.5},
    "Orbital Augment": {"Description": "Adds [x] orbiting Electrons around the tower. Each Electron deals damage equal to 15% of the enemy's remaining health (quarter effective against Bosses and Fleets)", "Epic": 2, "Legendary": 4, "Mythic": 6, "Ancestral": 8}
}

GENERATOR_UNIQUE_MODULE_EFFECTS = {
    "Singularity Harness": {"Description": "Increase the range of each bot by +[x]m. Enemies hit by the Flame Bot receive double damage.", "Epic": 5, "Legendary": 8, "Mythic": 11, "Ancestral": 15},
    "Galaxy Compressor": {"Description": "Collecting a recovery package reduced the cooldown of all Ultimate Weapons except Poison Swamp by [x]s.", "Epic": 10, "Legendary": 13, "Mythic": 17, "Ancestral": 20},
    "Pulsar Harvester": {"Description": "Each time a projectile hits an enemy, there is a [x]% chance that it will reduce the enemy's Health and Attack level by 1 (diminishing returns after 100 reductions)", "Epic": 1.0, "Legendary": 1.5, "Mythic": 2.0, "Ancestral": 2.5},
    "Black Hole Digestor": {"Description": "Temporarily get [x]% extra Coins/ Kill Bonus for each free upgrade you got on the current wave. Free Upgrades can not increase Tower Range.", "Epic": 3, "Legendary": 5, "Mythic": 7, "Ancestral": 10},
    "Project Funding": {"Description": "Tower damage is multiplied by [x]% of the number of digits in your current cash", "Epic": 12.5, "Legendary": 25, "Mythic": 50, "Ancestral": 100},
    "Restorative Bonus": {"Description": "Packages grant a 50% attack speed boost for [x]s, decaying for 60 seconds.", "Epic": 15, "Legendary": 20, "Mythic": 25, "Ancestral": 30}
}

CORE_UNIQUE_MODULE_EFFECTS = {
    "Om Chip": {"Description": "Spotlight will rotate to focus a boss. Bosses reflect the light around it to nearby enemies, increasing by x[x] the damage they receive.", "Epic": 2, "Legendary": 4, "Mythic": 7, "Ancestral": 15},
    "Harmony Conductor": {"Description": "[x]% chance of poisoned enemies to miss-attack (bosses chance is halved).", "Epic": 15, "Legendary": 20, "Mythic": 25, "Ancestral": 30},
    "Dimension Core": {"Description": "Chain lightning have 60% chance of hitting the initial target. Shock chance and multiplier is doubled. If shock is applied again to the same enemy the shock multiplier will add up to a max stack of [x].", "Epic": 5, "Legendary": 10, "Mythic": 15, "Ancestral": 20},
    "Multiverse Nexus": {"Description": "Death Wave, Golden Tower and Black Hole will always activate at the same time, but the cooldown will be the average of those +/-[x]s.", "Epic": 20, "Legendary": 10, "Mythic": 1, "Ancestral": -10},
    "Magnetic Hook": {"Description": "[x] Inner Land Mines are fired at Bosses as they enter Tower range. 25% of Elites have Inner Land Mines fired at them as they enter Tower range.", "Epic": 1, "Legendary": 2, "Mythic": 3, "Ancestral": 4},
    "Primordial Collapse": {"Description": "Spawns one additional Black Hole. Damage from enemies within a Black Hole is decreased by [x]%", "Epic": 50, "Legendary": 55, "Mythic": 65, "Ancestral": 80},
}

# ============================================================================
# SUBMODULE STATS PER ULTIMATE WEAPON
# ============================================================================

CANNON_SUBMODULE_STATS = {
    "Attack Speed": {"Common": 0.3, "Rare": 0.5, "Epic": 0.7, "Legendary": 1, "Mythic": 3, "Ancestral": 5},
    "Crit Chance [%]": {"Common": 2, "Rare": 3, "Epic": 4, "Legendary": 6, "Mythic": 8, "Ancestral": 10},
    "Crit Factor": {"Common": 2, "Rare": 4, "Epic": 6, "Legendary": 8, "Mythic": 12, "Ancestral": 15},
    "Attack Range [m]": {"Common": 2, "Rare": 4, "Epic": 8, "Legendary": 12, "Mythic": 20, "Ancestral": 30},
    "Damage / Meter [m]": {"Common": 0.005, "Rare": 0.01, "Epic": 0.025, "Legendary": 0.04, "Mythic": 0.075, "Ancestral": 0.15},
    "Multishot Chance [%]": {"Common": None, "Rare": 3, "Epic": 5, "Legendary": 7, "Mythic": 10, "Ancestral": 13},
    "Multishot Targets": {"Common": None, "Rare": None, "Epic": 1, "Legendary": 2, "Mythic": 3, "Ancestral": 4},
    "Rapid Fire Chance [%]": {"Common": None, "Rare": 2, "Epic": 4, "Legendary": 6, "Mythic": 9, "Ancestral": 12},
    "Rapid Fire Duration": {"Common": None, "Rare": 0.4, "Epic": 0.8, "Legendary": 1.4, "Mythic": 2.5, "Ancestral": 3.5},
    "Bounce Shot Chance": {"Common": None, "Rare": 2, "Epic": 3, "Legendary": 5, "Mythic": 9, "Ancestral": 12},
    "Bounce Shot Targets": {"Common": None, "Rare": None, "Epic": 1, "Legendary": 2, "Mythic": 3, "Ancestral": 4},
    "Bounce Shot Range": {"Common": None, "Rare": 0.5, "Epic": 0.8, "Legendary": 1.2, "Mythic": 1.8, "Ancestral": 2.0},
    "Super Crit Chance": {"Common": None, "Rare": None, "Epic": 3, "Legendary": 5, "Mythic": 7, "Ancestral": 10},
    "Super Crit Multi": {"Common": None, "Rare": None, "Epic": 2, "Legendary": 3, "Mythic": 5, "Ancestral": 7},
    "Rend Armor Chance": {"Common": None, "Rare": None, "Epic": None, "Legendary": 2, "Mythic": 5, "Ancestral": 8},
    "Rend Armor Multi": {"Common": None, "Rare": None, "Epic": None, "Legendary": 2, "Mythic": 5, "Ancestral": 8},
    "Max Rend Armor Multi": {"Common": None, "Rare": None, "Epic": None, "Legendary": 200, "Mythic": 300, "Ancestral": 500}
}

ARMOR_SUBMODULE_STATS = {
    "Health Regen [%]": {"Common": 20, "Rare": 40, "Epic": 60, "Legendary": 100, "Mythic": 200, "Ancestral": 400},
    "Defense [%]": {"Common": 1, "Rare": 2, "Epic": 3, "Legendary": 5, "Mythic": 6, "Ancestral": 8},
    "Defense Absolute [%]": {"Common": 15, "Rare": 25, "Epic": 40, "Legendary": 100, "Mythic": 500, "Ancestral": 1000},
    "Thorns Damage": {"Common": None, "Rare": None, "Epic": 2, "Legendary": 4, "Mythic": 7, "Ancestral": 10},
    "Lifesteal [%]": {"Common": None, "Rare": None, "Epic": 0.3, "Legendary": 0.5, "Mythic": 1.5, "Ancestral": 2.0},
    "Knockback Chance [%]": {"Common": None, "Rare": None, "Epic": 2, "Legendary": 4, "Mythic": 6, "Ancestral": 9},
    "Knockback Force": {"Common": None, "Rare": None, "Epic": 0.1, "Legendary": 0.4, "Mythic": 0.9, "Ancestral": 1.5},
    "Orb Speed": {"Common": None, "Rare": None, "Epic": 1, "Legendary": 1.5, "Mythic": 2, "Ancestral": 3},
    "Orbs": {"Common": None, "Rare": None, "Epic": None, "Legendary": None, "Mythic": 1, "Ancestral": 2},
    "Shockwave Size": {"Common": None, "Rare": None, "Epic": 0.1, "Legendary": 0.3, "Mythic": 0.7, "Ancestral": 1},
    "Shockwave Frequency [s]": {"Common": None, "Rare": None, "Epic": -1, "Legendary": -2, "Mythic": -3, "Ancestral": -4},
    "Land Mine Damage [%]": {"Common": None, "Rare": 30, "Epic": 50, "Legendary": 150, "Mythic": 500, "Ancestral": 800},
    "Land Mine Chance [%]": {"Common": None, "Rare": 1.5, "Epic": 3, "Legendary": 6, "Mythic": 9, "Ancestral": 12},
    "Land Mine Radius": {"Common": None, "Rare": 0.1, "Epic": 0.15, "Legendary": 0.3, "Mythic": 0.75, "Ancestral": 1},
    "Death Defy": {"Common": None, "Rare": None, "Epic": None, "Legendary": 1.5, "Mythic": 3.5, "Ancestral": 5},
    "Wall Health [%]": {"Common": None, "Rare": None, "Epic": 20, "Legendary": 40, "Mythic": 90, "Ancestral": 120},
    "Wall Rebuild [s]": {"Common": None, "Rare": None, "Epic": -20, "Legendary": -40, "Mythic": -80, "Ancestral": -100}
}

GENERATOR_SUBMODULE_STATS = {
    "Cash Bonus": {"Common": 0.1, "Rare": 0.2, "Epic": 0.3, "Legendary": 0.5, "Mythic": 1.2, "Ancestral": 2.5},
    "Cash / Wave": {"Common": 30, "Rare": 50, "Epic": 100, "Legendary": 200, "Mythic": 500, "Ancestral": 1000},
    "Coins / Kill Bonus": {"Common": 0.1, "Rare": 0.2, "Epic": 0.3, "Legendary": 0.4, "Mythic": 0.5, "Ancestral": 0.6},
    "Coins / Wave": {"Common": 20, "Rare": 35, "Epic": 60, "Legendary": 120, "Mythic": 200, "Ancestral": 350},
    "Free Attack Upgrade [%]": {"Common": 2, "Rare": 4, "Epic": 6, "Legendary": 8, "Mythic": 10, "Ancestral": 12},
    "Free Defense Upgrade [%]": {"Common": 2, "Rare": 4, "Epic": 6, "Legendary": 8, "Mythic": 10, "Ancestral": 12},
    "Free Utility Upgrade [%]": {"Common": 2, "Rare": 4, "Epic": 6, "Legendary": 8, "Mythic": 10, "Ancestral": 12},
    "Interest / Wave [%]": {"Common": None, "Rare": None, "Epic": 2, "Legendary": 4, "Mythic": 6, "Ancestral": 8},
    "Recovery Amount [%]": {"Common": None, "Rare": None, "Epic": 3, "Legendary": 5, "Mythic": 7, "Ancestral": 10},
    "Max Recovery": {"Common": None, "Rare": None, "Epic": 0.4, "Legendary": 0.7, "Mythic": 1.0, "Ancestral": 1.5},
    "Package Chance [%]": {"Common": None, "Rare": None, "Epic": 5, "Legendary": 8, "Mythic": 11, "Ancestral": 15},
    "Enemy Attack Level Skip [%]": {"Common": None, "Rare": None, "Epic": 2, "Legendary": 4, "Mythic": 6, "Ancestral": 8},
    "Enemy Health Level Skip [%]": {"Common": None, "Rare": None, "Epic": 2, "Legendary": 4, "Mythic": 6, "Ancestral": 8}
}

CORE_SUBMODULE_STATS = {
    "Golden Tower - Bonus": {"Common": None, "Rare": None, "Epic": 1, "Legendary": 2, "Mythic": 3, "Ancestral": 4},
    "Golden Tower - Duration [s]": {"Common": None, "Rare": None, "Epic": None, "Legendary": 2, "Mythic": 4, "Ancestral": 7},
    "Golden Tower - Cooldown [s]": {"Common": None, "Rare": None, "Epic": None, "Legendary": -5, "Mythic": -8, "Ancestral": -12},
    "Black Hole - Size [m]": {"Common": 2, "Rare": 4, "Epic": 6, "Legendary": 8, "Mythic": 10, "Ancestral": 12},
    "Black Hole - Duration [s]": {"Common": None, "Rare": None, "Epic": None, "Legendary": 2, "Mythic": 3, "Ancestral": 4},
    "Black Hole - Cooldown [s]": {"Common": None, "Rare": None, "Epic": None, "Legendary": -2, "Mythic": -3, "Ancestral": -4},
    "Spotlight - Bonus": {"Common": 1.2, "Rare": 2.5, "Epic": 3.5, "Legendary": 10, "Mythic": 15, "Ancestral": 20},
    "Spotlight - Angle": {"Common": None, "Rare": None, "Epic": 3, "Legendary": 6, "Mythic": 11, "Ancestral": 15},
    "Chrono Field - Duration [s]": {"Common": None, "Rare": None, "Epic": None, "Legendary": 4, "Mythic": 7, "Ancestral": 10},
    "Chrono Field - Speed Reduction [%]": {"Common": None, "Rare": None, "Epic": 3, "Legendary": 8, "Mythic": 11, "Ancestral": 15},
    "Chrono Field - Cooldown [s]": {"Common": None, "Rare": None, "Epic": None, "Legendary": -4, "Mythic": -7, "Ancestral": -10},
    "Death Wave - Damage [x]": {"Common": 8, "Rare": 15, "Epic": 25, "Legendary": 50, "Mythic": 100, "Ancestral": 250},
    "Death Wave - Quantity": {"Common": None, "Rare": None, "Epic": None, "Legendary": 1, "Mythic": 2, "Ancestral": 3},
    "Death Wave - Cooldown [s]": {"Common": None, "Rare": None, "Epic": None, "Legendary": -6, "Mythic": -10, "Ancestral": -13},
    "Smart Missiles - Damage": {"Common": 8, "Rare": 15, "Epic": 25, "Legendary": 50, "Mythic": 100, "Ancestral": 250},
    "Smart Missiles - Quantity": {"Common": None, "Rare": None, "Epic": 1, "Legendary": 2, "Mythic": 4, "Ancestral": 5},
    "Smart Missiles - Cooldown [s]": {"Common": None, "Rare": None, "Epic": None, "Legendary": -2, "Mythic": -4, "Ancestral": -6},
    "Inner Land Mines - Damage [x]": {"Common": 8, "Rare": 15, "Epic": 25, "Legendary": 50, "Mythic": 100, "Ancestral": 250},
    "Inner Land Mines - Quantity": {"Common": None, "Rare": None, "Epic": None, "Legendary": 1, "Mythic": 2, "Ancestral": 3},
    "Inner Land Mines - Cooldown [s]": {"Common": None, "Rare": None, "Epic": -5, "Legendary": -8, "Mythic": -10, "Ancestral": -13},
    "Poison Swamp - Damage [x]": {"Common": 8, "Rare": 15, "Epic": 25, "Legendary": 50, "Mythic": 100, "Ancestral": 250},
    "Poison Swamp - Duration [s]": {"Common": None, "Rare": None, "Epic": None, "Legendary": 2, "Mythic": 5, "Ancestral": 10},
    "Poison Swamp - Cooldown [s]": {"Common": None, "Rare": -2, "Epic": -4, "Legendary": -6, "Mythic": -8, "Ancestral": -10},
    "Chain Lightning - Damage [x]": {"Common": 8, "Rare": 15, "Epic": 25, "Legendary": 50, "Mythic": 100, "Ancestral": 250},
    "Chain Lightning - Quantity": {"Common": None, "Rare": None, "Epic": 1, "Legendary": 2, "Mythic": 3, "Ancestral": 4},
    "Chain Lightning - Chance [%]": {"Common": 2, "Rare": 4, "Epic": 6, "Legendary": 9, "Mythic": 12, "Ancestral": 15}
}

# ============================================================================
# BOT LEVEL STATS
# ============================================================================

# Shared bot parameter keys for consistent lookup structure.
DURATION = "Duration"
COOLDOWN = "Cooldown"
BONUS = "Bonus"
COIN_BONUS = "Coin Bonus"
RANGE = "Range"
DAMAGE = "Damage"
DAMAGE_REDUCTION = "Damage Reduction"

GOLDEN_BOT_LUT = {
    "Levels": {
        "Duration": {
            1: 20.5, 2: 21.0, 3: 21.5, 4: 22.0, 5: 22.5, 6: 23.0, 7: 23.5, 8: 24.0, 9: 24.5, 10: 25.0,
            11: 25.5, 12: 26.0, 13: 26.5, 14: 27.0, 15: 27.5, 16: 28.0, 17: 28.5, 18: 29.0, 19: 29.5, 20: 30.0,
            21: 30.5, 22: 31.0, 23: 31.5, 24: 32.0, 25: 32.5, 26: 33.0, 27: 33.5, 28: 34.0, 29: 34.5, 30: 35.0
        },
        "Cooldown": {
            1: 117, 2: 114, 3: 111, 4: 108, 5: 105, 6: 102, 7: 99, 8: 96, 9: 93, 10: 90,
            11: 87, 12: 84, 13: 81, 14: 78, 15: 75
        },
        "Bonus": {
            1: 2.2, 2: 2.4, 3: 2.6, 4: 2.8, 5: 3.0, 6: 3.2, 7: 3.4, 8: 3.6, 9: 3.8, 10: 4.0,
            11: 4.2, 12: 4.4, 13: 4.6, 14: 4.8, 15: 5.0, 16: 5.2, 17: 5.4, 18: 5.6, 19: 5.8, 20: 6.0,
            21: 6.2, 22: 6.4, 23: 6.6, 24: 6.8, 25: 7.0, 26: 7.2, 27: 7.4, 28: 7.6, 29: 7.8, 30: 8.0
        },
        "Range": {
            1: 22, 2: 24, 3: 26, 4: 28, 5: 30, 6: 32, 7: 34, 8: 36, 9: 38, 10: 40,
            11: 42, 12: 44, 13: 46, 14: 48, 15: 50
        },
    },
    "Labs": {
        "Cooldown": {
            0: 0, 1: -1, 2: -2, 3: -3, 4: -4, 5: -5, 6: -6, 7: -7, 8: -8, 9: -9, 10: -10,
            11: -11, 12: -12, 13: -13, 14: -14, 15: -15, 16: -16, 17: -17, 18: -18, 19: -19, 20: -20,
            21: -21, 22: -22, 23: -23, 24: -24, 25: -25
        },
        "Duration": {
            0: 0, 1: 0.50, 2: 1.00, 3: 1.50, 4: 2.00, 5: 2.50, 6: 3.00, 7: 3.50, 8: 4.00, 9: 4.50, 10: 5.00,
            11: 5.50, 12: 6.00, 13: 6.50, 14: 7.00, 15: 7.50, 16: 8.00, 17: 8.50, 18: 9.00, 19: 9.50, 20: 10.00
        },
    },
    "Modules":    None,
    "Submodules": None,
    "Relics":     {"Range": "Bot Range Bonus"},
}

GOLDEN_BOT_DURATION_LOOKUP      = GOLDEN_BOT_LUT["Levels"]["Duration"]
GOLDEN_BOT_COOLDOWN_LOOKUP      = GOLDEN_BOT_LUT["Levels"]["Cooldown"]
GOLDEN_BOT_BONUS_LOOKUP         = GOLDEN_BOT_LUT["Levels"]["Bonus"]
GOLDEN_BOT_RANGE_LOOKUP         = GOLDEN_BOT_LUT["Levels"]["Range"]
GOLDEN_BOT_COOLDOWN_LABS_LOOKUP = GOLDEN_BOT_LUT["Labs"]["Cooldown"]
GOLDEN_BOT_DURATION_LABS_LOOKUP = GOLDEN_BOT_LUT["Labs"]["Duration"]

GOLDEN_BOT_LOOKUPS = {
    DURATION:   GOLDEN_BOT_LUT["Levels"]["Duration"],
    COOLDOWN:   GOLDEN_BOT_LUT["Levels"]["Cooldown"],
    BONUS:      GOLDEN_BOT_LUT["Levels"]["Bonus"],
    COIN_BONUS: GOLDEN_BOT_LUT["Levels"]["Bonus"],
    RANGE:      GOLDEN_BOT_LUT["Levels"]["Range"],
}

GOLDEN_BOT_LOOKUP = GOLDEN_BOT_LOOKUPS

AMPLIFY_BOT_LUT = {
    "Levels": {
        "Duration": {
            1: 20.5, 2: 21.0, 3: 21.5, 4: 22.0, 5: 22.5, 6: 23.0, 7: 23.5, 8: 24.0, 9: 24.5, 10: 25.0,
            11: 25.5, 12: 26.0, 13: 26.5, 14: 27.0, 15: 27.5, 16: 28.0, 17: 28.5, 18: 29.0, 19: 29.5, 20: 30.0,
            21: 30.5, 22: 31.0, 23: 31.5, 24: 32.0, 25: 32.5, 26: 33.0, 27: 33.5, 28: 34.0, 29: 34.5, 30: 35.0
        },
        "Cooldown": {
            1: 117, 2: 114, 3: 111, 4: 108, 5: 105, 6: 102, 7: 99, 8: 96, 9: 93, 10: 90,
            11: 87, 12: 84, 13: 81, 14: 78, 15: 75
        },
        "Bonus": {
            1: 3.9, 2: 4.3, 3: 4.7, 4: 5.1, 5: 5.5, 6: 5.9, 7: 6.3, 8: 6.7, 9: 7.1, 10: 7.5,
            11: 7.9, 12: 8.3, 13: 8.7, 14: 9.1, 15: 9.5, 16: 9.9, 17: 10.3, 18: 10.7, 19: 11.1, 20: 11.5,
            21: 11.9, 22: 12.3, 23: 12.7, 24: 13.1, 25: 13.5, 26: 13.9, 27: 14.3, 28: 14.7, 29: 15.1, 30: 15.5
        },
    },
    "Labs": {
        "Cooldown": {
            0: 0, 1: -1, 2: -2, 3: -3, 4: -4, 5: -5, 6: -6, 7: -7, 8: -8, 9: -9, 10: -10,
            11: -11, 12: -12, 13: -13, 14: -14, 15: -15, 16: -16, 17: -17, 18: -18, 19: -19, 20: -20,
            21: -21, 22: -22, 23: -23, 24: -24, 25: -25
        },
        "Duration": {
            0: 0, 1: 0.50, 2: 1.00, 3: 1.50, 4: 2.00, 5: 2.50, 6: 3.00, 7: 3.50, 8: 4.00, 9: 4.50, 10: 5.00,
            11: 5.50, 12: 6.00, 13: 6.50, 14: 7.00, 15: 7.50, 16: 8.00, 17: 8.50, 18: 9.00, 19: 9.50, 20: 10.00
        },
    },
    "Modules":    None,
    "Submodules": None,
    "Relics":     {"Range": "Bot Range Bonus"},
}

AMPLIFY_BOT_DURATION_LOOKUP      = AMPLIFY_BOT_LUT["Levels"]["Duration"]
AMPLIFY_BOT_COOLDOWN_LOOKUP      = AMPLIFY_BOT_LUT["Levels"]["Cooldown"]
AMPLIFY_BOT_BONUS_LOOKUP         = AMPLIFY_BOT_LUT["Levels"]["Bonus"]
AMPLIFY_BOT_COOLDOWN_LABS_LOOKUP = AMPLIFY_BOT_LUT["Labs"]["Cooldown"]
AMPLIFY_BOT_DURATION_LABS_LOOKUP = AMPLIFY_BOT_LUT["Labs"]["Duration"]

AMPLIFY_BOT_LOOKUPS = {
    DURATION: AMPLIFY_BOT_LUT["Levels"]["Duration"],
    COOLDOWN: AMPLIFY_BOT_LUT["Levels"]["Cooldown"],
    DAMAGE:   AMPLIFY_BOT_LUT["Levels"]["Bonus"],
    BONUS:    AMPLIFY_BOT_LUT["Levels"]["Bonus"],
}

AMPLIFY_BOT_LOOKUP = AMPLIFY_BOT_LOOKUPS

FLAME_BOT_LUT = {
    "Levels": {
        "Damage Reduction": {
            1: 0.23, 2: 0.26, 3: 0.29, 4: 0.32, 5: 0.35, 6: 0.38, 7: 0.41, 8: 0.44, 9: 0.47, 10: 0.50,
            11: 0.53, 12: 0.56, 13: 0.59, 14: 0.62, 15: 0.65, 16: 0.68, 17: 0.71, 18: 0.74, 19: 0.77, 20: 0.80,
            21: 0.83, 22: 0.86, 23: 0.89, 24: 0.92, 25: 0.95
        },
        "Cooldown": {
            1: 72, 2: 69, 3: 66, 4: 63, 5: 60, 6: 57, 7: 54, 8: 51, 9: 48, 10: 45,
            11: 42, 12: 39, 13: 36, 14: 33, 15: 30
        },
        "Damage": {
            1: 0.58, 2: 0.66, 3: 0.74, 4: 0.82, 5: 0.90, 6: 0.98, 7: 1.06, 8: 1.14, 9: 1.22, 10: 1.30,
            11: 1.38, 12: 1.46, 13: 1.54, 14: 1.62, 15: 1.70, 16: 1.78, 17: 1.86, 18: 1.94, 19: 2.02, 20: 2.10,
            21: 2.18, 22: 2.26, 23: 2.34, 24: 2.42, 25: 2.50, 26: 2.58, 27: 2.66, 28: 2.74, 29: 2.82, 30: 2.90
        },
    },
    "Labs": {
        "Cooldown": {
            0: 0, 1: -1, 2: -2, 3: -3, 4: -4, 5: -5, 6: -6, 7: -7, 8: -8, 9: -9, 10: -10,
            11: -11, 12: -12, 13: -13, 14: -14, 15: -15, 16: -16, 17: -17, 18: -18, 19: -19, 20: -20,
            21: -21, 22: -22, 23: -23, 24: -24, 25: -25
        },
        "Burn Stack": {
            0: 0, 1: 1, 2: 2, 3: 3, 4: 4, 5: 5
        },
    },
    "Modules":    None,
    "Submodules": None,
    "Relics":     {"Range": "Bot Range Bonus"},
}

ATTACK_DISCO_LUT = {
    "Levels": None,
    "Labs": {
        "Attack Echo Boost": {
            1: 0.005, 2: 0.01, 3: 0.015, 4: 0.02, 5: 0.025, 6: 0.03, 7: 0.035, 8: 0.04, 9: 0.045, 10: 0.05,
            11: 0.055, 12: 0.06, 13: 0.065, 14: 0.07, 15: 0.075, 16: 0.08, 17: 0.085, 18: 0.09, 19: 0.095, 20: 0.1
        }
    },
    "Modules":    None,
    "Submodules": None,
    "Relics":     None,
}

FLAME_BOT_DAMAGE_REDUCTION_LOOKUP = FLAME_BOT_LUT["Levels"]["Damage Reduction"]
FLAME_BOT_COOLDOWN_LOOKUP         = FLAME_BOT_LUT["Levels"]["Cooldown"]
FLAME_BOT_DAMAGE_LOOKUP           = FLAME_BOT_LUT["Levels"]["Damage"]
FLAME_BOT_COOLDOWN_LABS_LOOKUP    = FLAME_BOT_LUT["Labs"]["Cooldown"]
FLAME_BOT_BURN_STACK_LABS_LOOKUP  = FLAME_BOT_LUT["Labs"]["Burn Stack"]

# Canonical bot summary lookup tables aligned with source-map parameter names.
FLAME_BOT_LOOKUPS = {
    DAMAGE_REDUCTION: FLAME_BOT_LUT["Levels"]["Damage Reduction"],
    COOLDOWN:         FLAME_BOT_LUT["Levels"]["Cooldown"],
    DAMAGE:           FLAME_BOT_LUT["Levels"]["Damage"],
}

FLAME_BOT_LOOKUP = FLAME_BOT_LOOKUPS

THUNDER_BOT_LUT = {
    "Levels": {},
    "Labs": {},
    "Modules": None,
    "Submodules": None,
    "Relics": {"Range": "Bot Range Bonus"},
}

# Canonical bot level lookup map.
BOT_LOOKUPS = {
    "Golden Bot": GOLDEN_BOT_LOOKUP,
    "Amplify Bot": AMPLIFY_BOT_LOOKUP,
    "Flame Bot": FLAME_BOT_LOOKUP,
}

# Shared canonical map for all entities that use level-based parameter tables.
LEVEL_LOOKUPS_BY_ENTITY = {
    **ULTIMATE_WEAPON_LOOKUPS,
    **BOT_LOOKUPS,
}

BOT_LABS_LOOKUPS = {
    ("Golden Bot", "Cooldown"): GOLDEN_BOT_COOLDOWN_LABS_LOOKUP,
    ("Golden Bot", "Duration"): GOLDEN_BOT_DURATION_LABS_LOOKUP,
    ("Flame Bot", "Cooldown"): FLAME_BOT_COOLDOWN_LABS_LOOKUP,
    ("Flame Bot", "Burn Stack"): FLAME_BOT_BURN_STACK_LABS_LOOKUP,
    ("Amplify Bot", "Cooldown"): AMPLIFY_BOT_COOLDOWN_LABS_LOOKUP,
    ("Amplify Bot", "Duration"): AMPLIFY_BOT_DURATION_LABS_LOOKUP,
}

# Add bot labs now that bot lab constants are defined.
LABS_LOOKUPS.update(
    {
        ("Golden Bot", "Cooldown"): GOLDEN_BOT_COOLDOWN_LABS_LOOKUP,
        ("Golden Bot", "Duration"): GOLDEN_BOT_DURATION_LABS_LOOKUP,
    }
)

# ============================================================================
# UNIFIED LOOKUP TABLE REGISTRY
# ============================================================================
# Central registry mapping all entities to their lookup tables and source info.
# Format: Category → Entity → {"lut": lookup_table, "sources_map": sources_map}

LOOKUP_TABLE_REGISTRY = {
    "Ultimate Weapons": {
        "Golden Tower": {
            "lut": GOLDEN_TOWER_LUT,
            "sources_map": UW_SOURCES_MAP,
        },
        "Black Hole": {
            "lut": BLACK_HOLE_LUT,
            "sources_map": UW_SOURCES_MAP,
        },
        "Death Wave": {
            "lut": DEATH_WAVE_LUT,
            "sources_map": UW_SOURCES_MAP,
        },
        "Spotlight": {
            "lut": SPOTLIGHT_LUT,
            "sources_map": UW_SOURCES_MAP,
        },
        "Chrono Field": {
            "lut": CHRONO_FIELD_LUT,
            "sources_map": UW_SOURCES_MAP,
        },
    },
    "Bots": {
        "Golden Bot": {
            "lut": GOLDEN_BOT_LUT,
            "sources_map": BOT_SOURCES_MAP,
        },
        "Amplify Bot": {
            "lut": AMPLIFY_BOT_LUT,
            "sources_map": BOT_SOURCES_MAP,
        },
        "Flame Bot": {
            "lut": FLAME_BOT_LUT,
            "sources_map": BOT_SOURCES_MAP,
        },
        "Thunder Bot": {
            "lut": THUNDER_BOT_LUT,
            "sources_map": BOT_SOURCES_MAP,
        },
    },
    "Guardians": {
        "Ally Chip": {
            "lut": GUARDIAN_CHIP_LOOKUPS["Ally"],
            "sources_map": GUARDIAN_SOURCES_MAP,
        },
        "Attack Chip": {
            "lut": GUARDIAN_CHIP_LOOKUPS["Attack"],
            "sources_map": GUARDIAN_SOURCES_MAP,
        },
        "Fetch Chip": {
            "lut": GUARDIAN_CHIP_LOOKUPS["Fetch"],
            "sources_map": GUARDIAN_SOURCES_MAP,
        },
        "Bounty Chip": {
            "lut": GUARDIAN_CHIP_LOOKUPS["Bounty"],
            "sources_map": GUARDIAN_SOURCES_MAP,
        },
        "Summon Chip": {
            "lut": GUARDIAN_CHIP_LOOKUPS["Summon"],
            "sources_map": GUARDIAN_SOURCES_MAP,
        },
        "Scout Chip": {
            "lut": GUARDIAN_CHIP_LOOKUPS["Scout"],
            "sources_map": GUARDIAN_SOURCES_MAP,
        },
    },
}


def _bucket_for_source(source: str) -> str | None:
    if source == SOURCE_LEVELS:
        return "Levels"
    if source == SOURCE_LABS:
        return "Labs"
    if source == SOURCE_MODULES:
        return "Modules"
    if source == SOURCE_RELICS:
        return "Relics"
    # Reuse Submodules bucket for assist-mod declarations.
    if source == SOURCE_ASSIST_MODS:
        return "Submodules"
    return None


def _find_existing_param_key(param_name: str, bucket_data: dict[str, object], entity_name: str) -> str | None:
    """Find equivalent key in a LUT bucket via aliases/synonyms/normalization."""
    target_norm = _normalize_lookup_name(param_name)
    if target_norm in {_normalize_lookup_name(k) for k in bucket_data.keys()}:
        for k in bucket_data.keys():
            if _normalize_lookup_name(k) == target_norm:
                return k

    # Forward alias (display -> canonical)
    canonical = _PARAMETER_ALIASES.get(entity_name, {}).get(param_name, param_name)
    canonical_norm = _normalize_lookup_name(canonical)
    for k in bucket_data.keys():
        if _normalize_lookup_name(k) == canonical_norm:
            return k

    # Reverse aliases (canonical -> display aliases)
    reverse_aliases = [a for a, c in _PARAMETER_ALIASES.get(entity_name, {}).items() if c == param_name]
    for alias_name in reverse_aliases:
        alias_norm = _normalize_lookup_name(alias_name)
        for k in bucket_data.keys():
            if _normalize_lookup_name(k) == alias_norm:
                return k

    # Common naming variants across sources/LUTs.
    synonym_candidates = {
        "bonus": ["multiplier", "coinbonus", "damagemult"],
        "coinbonus": ["bonus", "multiplier"],
        "damagemult": ["damage", "bonus"],
        "damage": ["damagemult", "damagepercent"],
        "damagepercent": ["damage"],
        "chancepercent": ["chance"],
        "slow": ["slowpercent"],
        "slowpercent": ["slow"],
    }
    for candidate_norm in synonym_candidates.get(target_norm, []):
        for k in bucket_data.keys():
            if _normalize_lookup_name(k) == candidate_norm:
                return k

    return None


def _sync_lut_entries_from_source_maps() -> None:
    """Ensure LUT buckets include all parameter entries declared by source maps."""
    for _, entities in LOOKUP_TABLE_REGISTRY.items():
        if not isinstance(entities, dict):
            continue

        for entity_name, entry in entities.items():
            if not isinstance(entry, dict):
                continue

            lut = entry.get("lut")
            sources_map = entry.get("sources_map")
            if not isinstance(lut, dict) or not isinstance(sources_map, dict):
                continue

            source_entity = _normalize_entity_name_for_sources(entity_name)

            for (map_entity, map_param), source_set in sources_map.items():
                if map_entity != source_entity or not isinstance(source_set, frozenset):
                    continue

                for source in source_set:
                    bucket_name = _bucket_for_source(source)
                    if bucket_name is None:
                        continue

                    bucket = lut.get(bucket_name)
                    if not isinstance(bucket, dict):
                        bucket = {}
                        lut[bucket_name] = bucket

                    if map_param in bucket:
                        continue

                    existing_key = _find_existing_param_key(map_param, bucket, entity_name)
                    if existing_key is not None:
                        bucket[map_param] = bucket[existing_key]
                    else:
                        # Placeholder table/value keeps LUT structurally complete for this source.
                        bucket[map_param] = {}


_sync_lut_entries_from_source_maps()