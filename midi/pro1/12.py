def import_external_tracks(mixer):
    """导入外部音频文件作为声部"""
    import os
    
    # 从文件夹导入所有音频文件
    audio_folder = "audio_tracks/"
    
    for filename in os.listdir(audio_folder):
        if filename.endswith(('.wav', '.mp3', '.flac')):
            filepath = os.path.join(audio_folder, filename)
            
            # 使用librosa或soundfile加载
            import librosa
            audio, sr = librosa.load(filepath, sr=None, mono=False)
            
            # 如果需要，重采样到目标采样率
            if sr != mixer.sample_rate:
                audio = librosa.resample(audio, sr, mixer.sample_rate)
            
            # 提取声部名称
            track_name = os.path.splitext(filename)[0]
            
            # 添加到混音器
            mixer.add_track(track_name, audio, volume=1.0, pan=0.5)
    
    return mixer