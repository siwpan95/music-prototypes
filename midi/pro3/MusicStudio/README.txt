音乐制作系统 v2.0 (批处理版)
========================================

系统要求：
- Windows 7/8/10/11
- 4GB 内存
- 1GB 可用硬盘空间
- 支持音频播放

快速开始：
1. 运行 00_Setup\Install.bat 安装系统
2. 运行 MusicStudio.bat 启动主程序
3. 按照菜单提示操作

功能模块：

1. 参数生成器
   - 创建乐器配置文件
   - 支持模板和自定义
   - 导出JSON格式

2. MIDI生成器
   - 从配置文件生成MIDI
   - 支持批量生成
   - 可设置曲速和拍号

3. 音频混合器
   - MIDI转音频
   - 多轨混合
   - 效果器处理
   - 最终导出

4. 人声处理器
   - 音高校正
   - 和声生成
   - 效果处理
   - 降噪

5. 采样管理器
   - 音频切片
   - 格式转换
   - 批量处理

工具集：
- ConvertMIDI.bat    MIDI转换工具
- ProcessVocal.bat   人声处理工具
- SamplerTool.bat    采样工具
- BatchProcess.bat   批量处理器

文件结构：
Data\            数据文件
  Instruments\   乐器配置
  MIDI\          MIDI文件
  Audio\         音频文件
Output\          输出文件
  Projects\      项目文件
  Renders\       渲染文件
  Exports\       导出文件
Config\          配置文件
Libs\            库文件
  SoundFonts\    音色库
  Samples\       采样库

常用命令：
- 生成乐器配置：01_ParamGen\ParamGen.bat
- 创建MIDI：02_MIDIGen\MIDIGen.bat
- 混合音频：03_AudioMix\AudioMix.bat
- 批量处理：Tools\BatchProcess.bat

技术支持：
- 查看文档：Docs\Manual.pdf
- 在线帮助：无
- 报告问题：查看Logs\error.log

注意事项：
1. 首次运行前请先安装
2. 音色库需单独下载
3. 处理大文件需要足够内存
4. 建议关闭其他音频程序

版本：v2.0
更新日期：2024
作者：Music Studio Team