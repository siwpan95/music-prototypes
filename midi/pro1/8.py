class AdvancedMusicGenerator(MusicMixer):
    def add_instruments_from_config(self, config_file):
        """
        从配置文件批量添加声部
        config_file可以是JSON/YAML等格式
        示例配置：
        {
            "instruments": [
                {
                    "name": "violin",
                    "type": "midi",
                    "program": 40,
                    "melody": [60, 62, 64, 65],
                    "volume": 0.7,
                    "pan": 0.3
                },
                {
                    "name": "cello",
                    "type": "audio",
                    "file": "cello_sequence.wav",
                    "volume": 0.6,
                    "pan": 0.7
                }
            ]
        }
        """
        import json
        with open(config_file, 'r') as f:
            config = json.load(f)
        
        for instr_config in config['instruments']:
            audio = self.generate_instrument_audio(instr_config)
            self.add_track(
                instr_config['name'],
                audio,
                instr_config.get('volume', 1.0),
                instr_config.get('pan', 0.5)
            )