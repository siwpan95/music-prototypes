# 完整的使用流程
def complete_orchestration_example():
    # 1. 初始化
    orchestrator = DynamicOrchestrator(max_parallel_tracks=24)
    
    # 2. 添加基础声部
    bass = generate_bass()
    drums = generate_drums()
    piano = generate_piano()
    
    orchestrator.add_track_dynamic("bass", bass, volume=0.7, pan=0.5, layer=0)
    orchestrator.add_track_dynamic("drums", drums, volume=0.6, pan=0.5, layer=0)
    orchestrator.add_track_dynamic("piano", piano, volume=0.5, pan=0.4, layer=1)
    
    # 3. 在主歌后添加弦乐
    # 模拟等待主歌部分...
    
    strings = generate_strings("verse_melody")
    orchestrator.add_track_dynamic("strings_verse", strings, volume=0.4, pan=0.3, layer=2)
    
    # 4. 在副歌添加铜管
    brass = generate_brass("chorus_hit")
    orchestrator.add_track_dynamic("brass", brass, volume=0.8, pan=0.6, layer=2, mute_group="brass_group")
    
    # 5. 在桥段添加独奏乐器
    guitar_solo = generate_guitar_solo()
    orchestrator.add_track_dynamic("guitar_solo", guitar_solo, volume=0.9, pan=0.5, layer=3)
    
    # 6. 独奏吉他时静音铜管组
    orchestrator.mute_group("brass_group", mute=True)
    
    # 7. 最后重新混音
    final_audio = mix_all_tracks(orchestrator.tracks)
    
    return final_audio

def mix_all_tracks(tracks):
    """混合所有未静音的轨道"""
    active_tracks = [t for t in tracks if not t['mute']]
    
    if not active_tracks:
        return np.zeros(44100)  # 1秒静音
    
    # 找到最长轨道
    max_len = max(len(t['audio']) for t in active_tracks)
    
    # 创建混合缓冲区
    mix = np.zeros((max_len, 2))
    
    for track in active_tracks:
        audio = track['audio']
        if len(audio.shape) == 1:
            audio = np.vstack([audio, audio]).T
        
        # 对齐长度
        if len(audio) < max_len:
            padded = np.zeros((max_len, 2))
            padded[:len(audio)] = audio
            audio = padded
        else:
            audio = audio[:max_len]
        
        # 应用声相和音量
        left_gain = track['volume'] * (1 - track['pan'])
        right_gain = track['volume'] * track['pan']
        
        mix[:, 0] += audio[:, 0] * left_gain
        mix[:, 1] += audio[:, 1] * right_gain
    
    # 防止削波
    mix = mix / (np.max(np.abs(mix)) + 1e-6)
    
    return mix