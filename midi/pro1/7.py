# 继续使用之前的混音器
def add_instrument_to_existing_mixer(mixer, new_audio, instrument_name, 
                                     volume=1.0, pan=0.5):
    """
    向已有混音器添加新声部
    """
    mixer.add_track(instrument_name, new_audio, volume, pan)
    
# 示例使用
mixer = MusicMixer()  # 假设已存在的混音器
piano_audio = generate_piano_part()  # 生成钢琴声部
add_instrument_to_existing_mixer(mixer, piano_audio, "piano", 0.8, 0.4)