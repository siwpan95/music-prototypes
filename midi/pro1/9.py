class DynamicOrchestrator:
    def __init__(self, max_parallel_tracks=16):
        """
        动态声部管理器
        max_parallel_tracks: 最大同时发声轨道数
        """
        self.tracks = []
        self.track_limit = max_parallel_tracks
        self.active_tracks = 0
        self.mute_groups = {}  # 静音组，用于控制相关声部
        self.track_layers = {}  # 轨道层级，用于分层控制
    
    def add_track_dynamic(self, name, audio, volume=1.0, pan=0.5, 
                          layer=0, mute_group=None):
        """
        动态添加声部，带资源管理
        """
        if self.active_tracks >= self.track_limit:
            print(f"警告：已达到最大轨道数({self.track_limit})")
            return False
        
        track_info = {
            'name': name,
            'audio': audio,
            'volume': volume,
            'pan': pan,
            'mute': False,
            'solo': False,
            'layer': layer
        }
        
        self.tracks.append(track_info)
        self.active_tracks += 1
        
        # 添加到静音组
        if mute_group:
            if mute_group not in self.mute_groups:
                self.mute_groups[mute_group] = []
            self.mute_groups[mute_group].append(len(self.tracks) - 1)
        
        # 添加到层级
        if layer not in self.track_layers:
            self.track_layers[layer] = []
        self.track_layers[layer].append(len(self.tracks) - 1)
        
        return True
    
    def remove_track(self, index):
        """移除声部"""
        if 0 <= index < len(self.tracks):
            removed = self.tracks.pop(index)
            self.active_tracks -= 1
            
            # 从静音组和层级中移除
            for mute_group, indices in self.mute_groups.items():
                if index in indices:
                    indices.remove(index)
                # 调整索引
                for i, idx in enumerate(indices):
                    if idx > index:
                        indices[i] -= 1
            
            for layer, indices in self.track_layers.items():
                if index in indices:
                    indices.remove(index)
                for i, idx in enumerate(indices):
                    if idx > index:
                        indices[i] -= 1
                        
            return removed
        return None
    
    def solo_layer(self, layer):
        """独奏指定层级"""
        for idx, track in enumerate(self.tracks):
            if track['layer'] == layer:
                track['solo'] = True
            else:
                track['mute'] = True
    
    def mute_group(self, group_name, mute=True):
        """静音/取消静音整个组"""
        if group_name in self.mute_groups:
            for idx in self.mute_groups[group_name]:
                self.tracks[idx]['mute'] = mute