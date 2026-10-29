def live_add_instruments_example():
    """实时添加声部的示例"""
    import time
    
    # 创建混音器和初始声部
    mixer = MusicMixer()
    
    # 1. 初始声部
    bass = generate_bassline()
    mixer.add_track("bass", bass, volume=0.6, pan=0.5)
    
    drums = generate_drums()
    mixer.add_track("drums", drums, volume=0.7, pan=0.5)
    
    # 混合初始声部
    initial_mix = mixer.mix_tracks()
    
    # 2. 随时间添加新声部
    # 第8小节添加钢琴
    time.sleep(8 * 60 / 120)  # 假设120BPM，等待8小节
    
    piano = generate_piano_part()
    mixer.add_track("piano", piano, volume=0.5, pan=0.4)
    
    # 第16小节添加弦乐
    time.sleep(8 * 60 / 120)
    
    strings = generate_strings()
    mixer.add_track("strings", strings, volume=0.4, pan=0.3)
    
    # 重新混合
    updated_mix = mixer.mix_tracks()
    
    return updated_mix