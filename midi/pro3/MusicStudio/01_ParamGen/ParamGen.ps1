param(
    [Parameter(Mandatory=$true)]
    [ValidateSet("Create", "Edit", "Batch", "Import", "Export")]
    [string]$Action,
    
    [string]$Name,
    [int]$Type = 1,
    [int]$Program = 0,
    [int]$Volume = 100,
    [int]$Pan = 64,
    [string]$File,
    [int]$Index = 1,
    [string]$Prefix = "Instrument",
    [int]$Pattern = 1,
    [string]$Midi,
    [string]$OutName
)

# 设置编码
$OutputEncoding = [System.Text.Encoding]::UTF8
$ErrorActionPreference = "Stop"

function Create-Instrument {
    param($name, $type, $program, $volume, $pan)
    
    $timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    
    # 创建配置对象
    $config = @{
        metadata = @{
            instrument_name = $name
            program = $program
            channel = if ($type -eq 2) { 9 } else { 0 }
            creation_time = $timestamp
            version = "1.0"
        }
        parameters = @{
            volume = $volume
            pan = $pan
            reverb = 0
            chorus = 0
        }
        notes = @()
    }
    
    # 根据类型生成音符
    switch ($type) {
        1 { # 旋律乐器
            $config.notes = Generate-Melody
        }
        2 { # 打击乐
            $config.notes = Generate-Drums
        }
        3 { # 和声乐器
            $config.notes = Generate-Chords
        }
    }
    
    # 保存为JSON
    $json = $config | ConvertTo-Json -Depth 10
    $outPath = "Data\Instruments\$name.json"
    
    [System.IO.File]::WriteAllText($outPath, $json, [System.Text.Encoding]::UTF8)
    Write-Host "配置已保存: $outPath" -ForegroundColor Green
}

function Generate-Melody {
    $notes = @()
    $patterns = @(
        @(60, 62, 64, 65, 67, 69, 71, 72),  # C大调音阶
        @(60, 64, 67, 60, 64, 67, 60, 64),  # C大三和弦琶音
        @(60, 65, 67, 72, 67, 65, 60, 55)   # 简单旋律
    )
    
    $pattern = Get-Random -InputObject $patterns
    for ($i = 0; $i -lt 8; $i++) {
        $note = @{
            pitch = $pattern[$i % $pattern.Length]
            velocity = Get-Random -Minimum 80 -Maximum 110
            start = $i * 0.5
            duration = 0.4
        }
        $notes += $note
    }
    
    return $notes
}

function Generate-Drums {
    $notes = @()
    $drumMap = @{
        "kick" = 36
        "snare" = 38
        "hihat" = 42
        "crash" = 49
    }
    
    $pattern = @(
        @("kick", 0.0),
        @("hihat", 0.5),
        @("snare", 1.0),
        @("hihat", 1.5),
        @("kick", 2.0),
        @("hihat", 2.5),
        @("snare", 3.0),
        @("hihat", 3.5)
    )
    
    foreach ($hit in $pattern) {
        $note = @{
            pitch = $drumMap[$hit[0]]
            velocity = if ($hit[0] -eq "kick" -or $hit[0] -eq "snare") { 100 } else { 80 }
            start = $hit[1]
            duration = 0.1
        }
        $notes += $note
    }
    
    return $notes
}

function Generate-Chords {
    $notes = @()
    $chords = @(
        @(60, 64, 67),  # C大三和弦
        @(62, 65, 69),  # D小三和弦
        @(64, 67, 71),  # E小三和弦
        @(65, 69, 72),  # F大三和弦
        @(67, 71, 74),  # G大三和弦
        @(69, 72, 76)   # A小三和弦
    )
    
    for ($i = 0; $i -lt 4; $i++) {
        $chord = $chords[$i % $chords.Length]
        foreach ($pitch in $chord) {
            $note = @{
                pitch = $pitch
                velocity = 90
                start = $i
                duration = 1.0
            }
            $notes += $note
        }
    }
    
    return $notes
}

function Import-FromMIDI {
    param($midiPath, $outName)
    
    if (-not (Test-Path $midiPath)) {
        Write-Host "MIDI文件不存在: $midiPath" -ForegroundColor Red
        return
    }
    
    # 简化：这里应该解析MIDI文件
    # 实际实现需要MIDI解析库
    
    Write-Host "正在导入MIDI: $midiPath" -ForegroundColor Yellow
    Write-Host "注意：完整MIDI导入需要Python脚本" -ForegroundColor Yellow
    
    # 调用Python脚本
    $pythonScript = "import_midi.py"
    if (Test-Path $pythonScript) {
        python $pythonScript $midiPath $outName
    } else {
        # 创建基本配置
        $config = @{
            metadata = @{
                instrument_name = $outName
                program = 0
                channel = 0
                creation_time = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
            }
            parameters = @{
                volume = 100
                pan = 64
            }
            notes = @()
        }
        
        $json = $config | ConvertTo-Json
        $outPath = "Data\Instruments\$outName.json"
        [System.IO.File]::WriteAllText($outPath, $json, [System.Text.Encoding]::UTF8)
        Write-Host "已创建基本配置: $outPath" -ForegroundColor Green
    }
}

# 主逻辑
switch ($Action) {
    "Create" {
        Create-Instrument -name $Name -type $Type -program $Program -volume $Volume -pan $Pan
    }
    "Edit" {
        if (Test-Path $File) {
            $content = Get-Content $File -Raw
            $config = $content | ConvertFrom-Json
            
            Write-Host "当前配置:" -ForegroundColor Cyan
            $config | ConvertTo-Json | Write-Host -ForegroundColor Yellow
            
            # 这里可以添加编辑逻辑
        } else {
            Write-Host "文件不存在: $File" -ForegroundColor Red
        }
    }
    "Batch" {
        for ($i = 1; $i -le $Index; $i++) {
            $name = "$Prefix-$i"
            $type = Get-Random -Minimum 1 -Maximum 4
            $program = Get-Random -Minimum 0 -Maximum 128
            $volume = Get-Random -Minimum 80 -Maximum 120
            
            Create-Instrument -name $name -type $type -program $program -volume $volume
        }
    }
    "Import" {
        Import-FromMIDI -midiPath $Midi -outName $OutName
    }
}