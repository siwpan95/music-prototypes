class MusicMixer:
    def __init__(self, sample_rate=44100):
        self.tracks = {}
        self.sample_rate = sample_rate
        self.master = None
    
    def add_track(self, name, audio_data, volume=1.0, pan=0.5):
        """添加音轨"""
        self.tracks[name] = {
            'audio': audio_data,
            'volume': volume,
            'pan': pan,  # 0=左, 1=右, 0.5=居中
            'effects': []
        }
    
    def apply_panning(self, audio, pan):
        """应用声相定位"""
        if len(audio.shape) == 1:  # 单声道
            left = audio * (1 - pan)
            right = audio * pan
            return np.vstack([left, right]).T
        return audio
    
    def mix_tracks(self):
        """混合所有音轨"""
        # 确定最大长度
        max_length = max(len(track['audio']) for track in self.tracks.values())
        
        # 创建立体声混合缓冲区
        mix = np.zeros((max_length, 2))
        
        for track_info in self.tracks.values():
            audio = track_info['audio']
            
            # 应用声相
            if len(audio.shape) == 1:
                audio_panned = self.apply_panning(audio, track_info['pan'])
            else:
                audio_panned = audio
            
            # 调整音量
            audio_panned *= track_info['volume']
            
            # 对齐长度并混合
            if len(audio_panned) < max_length:
                padded = np.zeros((max_length, 2))
                padded[:len(audio_panned)] = audio_panned
                mix += padded
            else:
                mix += audio_panned[:max_length]
        
        # 限制幅度防止削波
        mix = np.clip(mix, -1, 1)
        self.master = mix
        return mix
    
    def export_wav(self, filename, normalized=True):
        """导出WAV文件"""
        if self.master is not None:
            if normalized:
                audio = self.master / np.max(np.abs(self.master))
            else:
                audio = self.master
            
            sf.write(filename, audio, self.sample_rate)
            print(f"已导出: {filename}")