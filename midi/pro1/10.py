class IntelligentOrchestrator:
    def __init__(self):
        self.instrument_pool = {
            'strings': ['violin', 'viola', 'cello', 'bass'],
            'woodwinds': ['flute', 'oboe', 'clarinet', 'bassoon'],
            'brass': ['trumpet', 'trombone', 'french_horn', 'tuba'],
            'percussion': ['piano', 'harp', 'timpani'],
            'electronic': ['synth', 'pad', 'bass_synth']
        }
        self.track_counter = 0
    
    def generate_orchestration(self, mood, complexity):
        """
        根据情绪和复杂度自动生成配器
        mood: 'happy', 'sad', 'epic', 'calm', 'tense'
        complexity: 1-5，复杂度等级
        """
        orchestration_plan = []
        
        # 基础声部（始终存在）
        base_instruments = ['piano', 'bass', 'drums']
        
        # 根据情绪选择声部
        mood_mapping = {
            'happy': ['violin', 'flute', 'trumpet'],
            'sad': ['cello', 'oboe', 'viola'],
            'epic': ['timpani', 'french_horn', 'synth_pad'],
            'calm': ['harp', 'flute', 'cello'],
            'tense': ['bassoon', 'viola', 'synth']
        }
        
        # 根据复杂度决定声部数量
        instrument_count = 3 + complexity * 2
        
        # 创建声部列表
        selected_instruments = base_instruments.copy()
        
        if mood in mood_mapping:
            selected_instruments.extend(mood_mapping[mood])
        
        # 确保不超出数量限制
        selected_instruments = selected_instruments[:instrument_count]
        
        # 为每个声部生成音频
        for i, instr in enumerate(selected_instruments):
            audio = self.generate_instrument_part(instr, i, complexity)
            orchestration_plan.append({
                'name': f"{instr}_{i}",
                'audio': audio,
                'volume': self.calculate_volume(instr, i),
                'pan': self.calculate_pan(i, len(selected_instruments))
            })
        
        return orchestration_plan
    
    def calculate_pan(self, index, total):
        """计算声相位置（立体声场分布）"""
        # 对称分布
        if total <= 1:
            return 0.5
        return index / (total - 1)  # 0到1之间