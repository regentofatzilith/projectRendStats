"""Debug wave index calculation."""

WAVE_DURATION = 30.14

for t in [0, 30, 60, 90, 120]:
    wave_idx = int(t // WAVE_DURATION)
    print(f"t={t:3d}: wave_idx = int({t} / {WAVE_DURATION}) = {wave_idx}")
    print(f"         Expected wave start at {wave_idx * WAVE_DURATION:.2f}")
    print(f"         Rounded to second: {int(round(wave_idx * WAVE_DURATION))}")
    print()
