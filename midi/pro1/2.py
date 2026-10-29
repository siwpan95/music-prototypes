import pretty_midi
import numpy as np
from scipy.io import wavfile
import soundfile as sf

class InstrumentTrack:
    def __init__(self, name, program=0, channel=0):
        """
        program: MIDI音色编号 (0=钢琴, 40=小提琴, 73=长笛等)
        """
        self.name = name
        self.midi = pretty_midi.PrettyMIDI()
        self.instrument = pretty_midi.Instrument(program=program)
        self.audio = None
    
    def add_note(self, pitch, start_time, duration, velocity=100):
        """添加音符"""
        note = pretty_midi.Note(
            velocity=velocity,
            pitch=pitch,
            start=start_time,
            end=start_time + duration
        )
        self.instrument.notes.append(note)
    
    def synthesize(self, duration=10):
        """合成音频"""
        self.midi.instruments.append(self.instrument)
        self.audio = self.midi.fluidsynth(fs=44100)
        return self.audio