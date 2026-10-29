def create_song_example():
    """创建示例歌曲"""
    # 初始化混音器
    mixer = MusicMixer(sample_rate=44100)
    
    # 1. 创建钢琴声部
    piano = InstrumentTrack("piano", program=0)
    for i in range(8):
        piano.add_note(pitch=60 + i*2, start_time=i*0.5, duration=0.4)
    piano_audio = piano.synthesize(duration=4)
    mixer.add_track("piano", piano_audio, volume=0.7, pan=0.4)
    
    # 2. 创建贝斯声部
    bass = InstrumentTrack("bass", program=33)  # 电贝斯
    for i in range(4):
        bass.add_note(pitch=36, start_time=i*1.0, duration=0.8)
    bass_audio = bass.synthesize(duration=4)
    mixer.add_track("bass", bass_audio, volume=0.5, pan=0.5)
    
    # 3. 创建鼓声部（简单节奏）
    kick = AudioSynthesizer().generate_waveform(60, 0.1, 'sine')
    snare = AudioSynthesizer().generate_waveform(200, 0.05, 'noise')
    
    # 创建鼓节奏
    drum_pattern = []
    for beat in range(8):
        if beat % 2 == 0:
            drum_pattern.extend(kick * 0.5)
        if beat % 4 == 0:
            drum_pattern.extend(snare * 0.3)
        else:
            drum_pattern.extend(np.zeros(1000))  # 静音
    
    mixer.add_track("drums", np.array(drum_pattern), volume=0.6, pan=0.6)
    
    # 4. 混合并导出
    final_mix = mixer.mix_tracks()
    mixer.export_wav("my_song.wav")
    
    return final_mix