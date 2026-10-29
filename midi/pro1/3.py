import numpy as np
from scipy import signal

class AudioSynthesizer:
    def __init__(self, sample_rate=44100):
        self.sample_rate = sample_rate
    
    def generate_waveform(self, frequency, duration, wave_type='sine'):
        """生成波形"""
        t = np.linspace(0, duration, int(self.sample_rate * duration))
        
        if wave_type == 'sine':
            return np.sin(2 * np.pi * frequency * t)
        elif wave_type == 'square':
            return signal.square(2 * np.pi * frequency * t)
        elif wave_type == 'sawtooth':
            return signal.sawtooth(2 * np.pi * frequency * t)
        # ... 更多波形