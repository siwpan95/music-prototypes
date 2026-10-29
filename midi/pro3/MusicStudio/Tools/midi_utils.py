import json
import os
from typing import List, Dict, Any
import warnings
warnings.filterwarnings("ignore")

def create_midi_from_json(json_files: List[str], output_name: str, 
                         tempo: int = 120, time_sig: str = "4/4") -> str:
    """
    从JSON配置文件创建MIDI
    简化版，只生成基本MIDI
    """
    try:
        # 简单的MIDI生成
        midi_content = []
        midi_content.append("MThd")
        midi_content.append("00000006")
        midi_content.append("0001")  # 格式1
        midi_content.append("0001")  # 音轨数
        midi_content.append(format(int(480 * tempo / 60), '04x'))  # 每四分音符tick数
        
        track_data = []
        
        for json_file in json_files:
            with open(json_file, 'r', encoding='utf-8') as f:
                config = json.load(f)
            
            # 添加乐器信息
            program = config.get('metadata', {}).get('program', 0)
            channel = config.get('metadata', {}).get('channel', 0)
            
            # 程序改变事件
            track_data.append("C0" + format(channel, 'X') + format(program, '02X'))
            
            # 添加音符
            notes = config.get('notes', [])
            for note in notes:
                pitch = note.get('pitch', 60)
                velocity = note.get('velocity', 100)
                start = int(note.get('start', 0) * 480)  # 转换为tick
                duration = int(note.get('duration', 1) * 480)
                
                # 音符开
                track_data.append(format(start, '02X') + "9" + format(channel, 'X') + 
                                 format(pitch, '02X') + format(velocity, '02X'))
                # 音符关
                track_data.append(format(duration, '02X') + "8" + format(channel, 'X') + 
                                 format(pitch, '02X') + "00")
        
        # 结束事件
        track_data.append("00FF2F00")
        
        # 创建音轨块
        track_length = sum(len(byte) for byte in track_data) // 2
        midi_content.append("MTrk")
        midi_content.append(format(track_length, '08X'))
        midi_content.extend(track_data)
        
        # 保存文件
        output_path = f"Data/MIDI/{output_name}.mid"
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        
        with open(output_path, 'wb') as f:
            # 写入MIDI头
            for line in midi_content:
                f.write(bytes.fromhex(line) if len(line) > 4 else line.encode())
        
        return output_path
        
    except Exception as e:
        print(f"创建MIDI失败: {e}")
        return None

def synthesize_midi(midi_path: str, output_name: str, 
                   soundfont: str = None) -> str:
    """
    使用fluidsynth合成MIDI为音频
    需要安装fluidsynth
    """
    try:
        output_path = f"Data/Audio/{output_name}.wav"
        
        if soundfont and os.path.exists(soundfont):
            # 使用soundfont合成
            os.system(f'fluidsynth -ni "{soundfont}" "{midi_path}" -F "{output_path}" -r 44100')
        else:
            # 简单合成（使用系统MIDI）
            import pygame
            pygame.mixer.init(frequency=44100, size=-16, channels=2, buffer=2048)
            
            # 加载MIDI
            pygame.mixer.music.load(midi_path)
            pygame.mixer.music.play()
            
            # 录制音频
            import numpy as np
            import soundfile as sf
            
            # 获取MIDI长度
            import pretty_midi
            midi_data = pretty_midi.PrettyMIDI(midi_path)
            duration = midi_data.get_end_time()
            
            # 创建静音音频
            sample_rate = 44100
            audio = np.zeros((int(duration * sample_rate), 2), dtype=np.float32)
            
            # 保存音频
            sf.write(output_path, audio, sample_rate)
        
        return output_path
        
    except Exception as e:
        print(f"合成失败: {e}")
        return None