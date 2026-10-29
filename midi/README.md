# midi

> 仓库：<https://gitee.com/siwpan/midi> ｜ 许可：MIT（见 [LICENSE](LICENSE)）

MusicStudio 音乐制作/DAW 项目，含四个阶段工程（pro1–pro4）与统一入口。

## 类型
代码项目（Python）

## 目录要点
- MusicStudio/：统一主入口（main.py），整合 Pro1 智能配器 + Pro2 DAW 界面 + Pro3 部署体系 + Pro4 完整引擎；Engine/ 下含音频合成、MIDI 转换、混音、编排、DAW 界面等模块
- pro1/：智能配器阶段脚本（1.py–14.py）
- pro2/：DAW 界面阶段（含 exa/、mayvbe/ 示例，setup.py、test_audio_engine.py）
- pro3/：部署体系阶段
- pro4/：完整引擎阶段，MusicStudioPro/（Engine + dist 打包产物 + Setup 安装程序）
- all.docx / all.txt / midi_projects_overview.html：项目说明文档

## 用途
音乐制作工作站与 MIDI 编排/合成工具，pro1–pro4 为演进版本。

## 测试状态
py_compile 语法检查：102 个自有脚本中 101 个通过；pro2/7.py 存在 IndentationError（缩进错误，疑似损坏）。
