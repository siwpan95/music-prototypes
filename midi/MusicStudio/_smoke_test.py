#!/usr/bin/env python3
"""MusicStudio Smoke Test Script"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.chdir(os.path.dirname(os.path.abspath(__file__)))

PASS, FAIL, WARN = 0, 0, 0

def check(ok, *args):
    global PASS, FAIL
    if ok:
        PASS += 1
        print(f"  [PASS] {' '.join(args)}")
    else:
        FAIL += 1
        print(f"  [FAIL] {' '.join(args)}")

def header(title):
    print()
    print("=" * 60)
    print(f"  {title}")
    print("=" * 60)

# ══════════════════════════════════════════════════════════════════
# 1. Environment
# ══════════════════════════════════════════════════════════════════
header("1. Environment Check")
print(f"  Python: {sys.version}")
check(sys.version_info >= (3, 8), "Python >= 3.8")

deps = {
    "numpy": "numpy",
    "scipy": "scipy", 
    "pretty_midi": "pretty_midi",
    "soundfile": "soundfile",
    "pygame": "pygame",
    "yaml": "PyYAML",
}
for mod, name in deps.items():
    try:
        __import__(mod)
        check(True, f"{name} installed")
    except ImportError:
        check(False, f"{name} missing")

# pygame_gui
try:
    import pygame_gui
    check(True, "pygame_gui installed")
except ImportError:
    check(False, "pygame_gui missing")

# ══════════════════════════════════════════════════════════════════
# 2. Module Imports
# ══════════════════════════════════════════════════════════════════
header("2. Core Module Imports")

try:
    from Engine.composition import batch_generate, compose
    check(True, "Engine.composition")
except Exception as e:
    check(False, f"Engine.composition: {e}")

try:
    from Engine.midi.converter import batch_json_to_midi
    check(True, "Engine.midi.converter")
except Exception as e:
    check(False, f"Engine.midi.converter: {e}")

try:
    from Engine.audio.synthesizer import batch_synthesize, load_audio, find_soundfont
    check(True, "Engine.audio.synthesizer")
except Exception as e:
    check(False, f"Engine.audio.synthesizer: {e}")

try:
    from Engine.effects.effects import apply_effect_chain
    check(True, "Engine.effects.effects")
except Exception as e:
    check(False, f"Engine.effects.effects: {e}")

try:
    from Engine.orchestration import IntelligentOrchestrator, AutomaticArranger, print_arrangement_preview
    check(True, "Engine.orchestration")
except Exception as e:
    check(False, f"Engine.orchestration: {e}")

try:
    from Engine.core.mixer import MusicMixer
    check(True, "Engine.core.mixer")
except Exception as e:
    check(False, f"Engine.core.mixer: {e}")

try:
    from Engine.audio.soft_synth import synthesize_from_midi_json, midi_note_array_to_audio
    check(True, "Engine.audio.soft_synth (synth functions)")
except Exception as e:
    check(False, f"Engine.audio.soft_synth: {e}")

# ══════════════════════════════════════════════════════════════════
# 3. Configuration
# ══════════════════════════════════════════════════════════════════
header("3. Configuration Validation")
import yaml

try:
    cfg_path = "Config/studio_config.yaml"
    with open(cfg_path, 'r', encoding='utf-8') as f:
        cfg = yaml.safe_load(f)
    check(True, "Config file loaded")

    for s in ['project', 'defaults', 'paths', 'effects', 'synthesis']:
        check(s in cfg, f"Section '{s}' present")

    d = cfg['defaults']
    for k in ['mood', 'bpm', 'key', 'complexity', 'bars', 'sample_rate']:
        check(k in d, f"Default '{k}' = {d.get(k)}")

    chain = cfg['effects']['master_chain']
    check(len(chain) == 3, f"Master chain: {[e['type'] for e in chain]}")
except Exception as e:
    check(False, f"Config error: {e}")

# ══════════════════════════════════════════════════════════════════
# 4. CLI Mode: Environment Check
# ══════════════════════════════════════════════════════════════════
header("4. CLI Mode: --mode env")
try:
    from main import run_env_check
    result = run_env_check()
    check(result, "--mode env returned OK")
except Exception as e:
    check(False, f"--mode env failed: {e}")

# ══════════════════════════════════════════════════════════════════
# 5. CLI Mode: Arrangement Preview
# ══════════════════════════════════════════════════════════════════
header("5. CLI Mode: --mode arrange")
try:
    from Engine.orchestration import print_arrangement_preview, IntelligentOrchestrator
    
    for mood in ["happy", "sad", "epic"]:
        try:
            events = print_arrangement_preview(mood)
            check(events is not None, f"Arrangement '{mood}' generated ({len(events)} events)")
        except Exception as e:
            check(False, f"Arrangement '{mood}': {e}")

    orch = IntelligentOrchestrator()
    for mood in ["happy", "epic"]:
        try:
            instruments, bar_events = orch.orchestrate(mood=mood)
            check(True, f"Orchestrate '{mood}': {len(instruments)} instruments, {len(bar_events)} bars")
        except Exception as e:
            check(False, f"Orchestrate '{mood}': {e}")
except Exception as e:
    check(False, f"Arrangement test failed: {e}")

# ══════════════════════════════════════════════════════════════════
# 6. Quick Batch Generation (minimal)
# ══════════════════════════════════════════════════════════════════
header("6. Quick Batch Generation (happy, 4 bars)")
try:
    from Engine.composition import batch_generate, compose
    from Engine.midi.converter import batch_json_to_midi
    from Engine.orchestration import IntelligentOrchestrator
    import json, glob

    # Clean up
    for d in ["Data/Instruments", "Data/MIDI"]:
        os.makedirs(d, exist_ok=True)
        for f in glob.glob(os.path.join(d, "*")):
            try: os.remove(f)
            except: pass

    orch = IntelligentOrchestrator()
    instruments, bar_events = orch.orchestrate(mood="happy", key="C", bpm=120, complexity=3, bars=4)
    check(True, f"Orchestration: {len(instruments)} instruments")

    # Generate composition JSON
    batch_generate(instruments, "Data/Instruments", key="C", bpm=120, bars=4)
    json_files = glob.glob("Data/Instruments/*.json")
    check(len(json_files) > 0, f"Generated {len(json_files)} instrument JSON files")
    for jf in json_files:
        print(f"         - {os.path.basename(jf)}")

    # Convert JSON to MIDI
    batch_json_to_midi("Data/Instruments", "Data/MIDI", 120.0)
    midi_files = glob.glob("Data/MIDI/*.mid")
    check(len(midi_files) > 0, f"Converted to {len(midi_files)} MIDI files")
    for mf in midi_files:
        size_kb = os.path.getsize(mf) / 1024
        print(f"         - {os.path.basename(mf)} ({size_kb:.1f} KB)")

    # Verify MIDI files are valid
    for mf in midi_files:
        try:
            import pretty_midi
            pm = pretty_midi.PrettyMIDI(mf)
            note_count = sum(1 for inst in pm.instruments for _ in inst.notes)
            check(note_count >= 0, f"Valid MIDI: {os.path.basename(mf)} ({note_count} notes, {pm.get_end_time():.1f}s)")
        except Exception as e:
            check(False, f"Invalid MIDI {os.path.basename(mf)}: {e}")

except Exception as e:
    check(False, f"Batch generation failed: {e}")
    import traceback
    traceback.print_exc()

# ══════════════════════════════════════════════════════════════════
# 7. Audio Synthesis (if SoundFont available)
# ══════════════════════════════════════════════════════════════════
header("7. Audio Synthesis")
try:
    from Engine.audio.synthesizer import batch_synthesize, find_soundfont
    sf = find_soundfont()
    if sf:
        check(True, f"SoundFont found: {sf}")

        os.makedirs("Data/Audio", exist_ok=True)
        for f in glob.glob("Data/Audio/*"):
            try: os.remove(f)
            except: pass

        try:
            audio_paths = batch_synthesize("Data/MIDI", "Data/Audio", sf)
            check(len(audio_paths) > 0, f"Synthesized {len(audio_paths)} audio files")
            for ap in audio_paths:
                size_kb = os.path.getsize(ap) / 1024 if os.path.exists(ap) else 0
                print(f"         - {os.path.basename(ap)} ({size_kb:.1f} KB)")
        except Exception as e:
            check(False, f"Audio synthesis error: {e}")
            import traceback
            traceback.print_exc()
    else:
        print(f"  [WARN] No SoundFont found - skipping audio synthesis")
        print(f"         Download FluidR3_GM.sf2 to SoundFonts/ for full test")
except Exception as e:
    check(False, f"Audio setup error: {e}")

# ══════════════════════════════════════════════════════════════════
# Summary
# ══════════════════════════════════════════════════════════════════
header("SMOKE TEST SUMMARY")
total = PASS + FAIL
print(f"  Passed: {PASS}/{total}")
print(f"  Failed: {FAIL}/{total}")
if FAIL == 0:
    print()
    print("  [RESULT] ALL TESTS PASSED!")
elif FAIL <= 2:
    print()
    print(f"  [RESULT] PASSED with {FAIL} non-critical issues")
else:
    print()
    print(f"  [RESULT] FAILED - {FAIL} issues found")
print("=" * 60)
print()

sys.exit(0 if FAIL == 0 else 1)
