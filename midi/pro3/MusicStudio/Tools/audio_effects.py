import numpy as np
import os
from scipy import signal

def apply_effect(audio_path: str, output_name: str, 
                effect_type: int, amount: float) -> str:
    """应用音频效果器"""
    try:
        import soundfile as sf
        
        # 加载音频
        audio, sample_rate = sf.read(audio_path)
        
        if len(audio.shape) == 1:
            audio = np.vstack([audio, audio]).T
        
        # 应用效果
        if effect_type == 1:  # 混响
            processed = apply_reverb_simple(audio, amount, sample_rate)
        elif effect_type == 2:  # 均衡器
            processed = apply_eq_simple(audio, amount)
        elif effect_type == 3:  # 压缩器
            processed = apply_compression_simple(audio, amount)
        elif effect_type == 4:  # 延迟
            processed = apply_delay_simple(audio, amount, sample_rate)
        elif effect_type == 5:  # 合唱
            processed = apply_chorus_simple(audio, amount, sample_rate)
        else:
            processed = audio
        
        # 保存结果
        output_path = f"Data/Audio/{output_name}.wav"
        sf.write(output_path, processed, sample_rate)
        
        return output_path
        
    except Exception as e:
        print(f"应用效果器失败: {e}")
        return None

def apply_reverb_simple(audio: np.ndarray, amount: float, 
                       sample_rate: int) -> np.ndarray:
    """简单混响效果"""
    delay_samples = int(0.03 * sample_rate)  # 30ms延迟
    decay = 0.5 * amount
    
    wet = np.zeros_like(audio)
    
    for i in range(len(audio)):
        if i >= delay_samples:
            wet[i] = audio[i] + decay * wet[i - delay_samples]
    
    mixed = (1 - amount) * audio + amount * wet
    return mixed

def apply_eq_simple(audio: np.ndarray, amount: float) -> np.ndarray:
    """简单均衡器"""
    # 三频段均衡
    if len(audio.shape) > 1:
        result = np.zeros_like(audio)
        for ch in range(audio.shape[1]):
            result[:, ch] = audio[:, ch] * (1 + amount * 0.5)
    else:
        result = audio * (1 + amount * 0.5)
    
    return np.clip(result, -1, 1)

def apply_compression_simple(audio: np.ndarray, 
                           amount: float) -> np.ndarray:
    """简单压缩器"""
    threshold = 0.5
    ratio = 1.0 + amount * 3.0
    
    if len(audio.shape) > 1:
        compressed = np.zeros_like(audio)
        for ch in range(audio.shape[1]):
            for i in range(len(audio)):
                sample = audio[i, ch]
                abs_sample = abs(sample)
                
                if abs_sample > threshold:
                    over = abs_sample - threshold
                    compressed_sample = threshold + over / ratio
                    compressed[i, ch] = compressed_sample if sample >= 0 else -compressed_sample
                else:
                    compressed[i, ch] = sample
    else:
        compressed = np.zeros_like(audio)
        for i, sample in enumerate(audio):
            abs_sample = abs(sample)
            
            if abs_sample > threshold:
                over = abs_sample - threshold
                compressed_sample = threshold + over / ratio
                compressed[i] = compressed_sample if sample >= 0 else -compressed_sample
            else:
                compressed[i] = sample
    
    return compressed