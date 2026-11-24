# 查找 SCUM 专用服务端（Steam 版 AppID 3792580）安装位置
# 用法：在目标 Windows 机器上用 PowerShell（管理员）运行： powershell -ExecutionPolicy Bypass -File .\Find-SCUM-Server.ps1
$ErrorActionPreference = 'SilentlyContinue'

Write-Host "=== 1. Steam 库清单中查找 Dedicated Server (3792580) ===" -ForegroundColor Cyan
$libs = @()
$vdf = @(
  "$env:ProgramFiles(x86)\Steam\steamapps\libraryfolders.vdf",
  "$env:ProgramFiles\Steam\steamapps\libraryfolders.vdf"
)
foreach ($v in $vdf) { if (Test-Path $v) { $libs += (Get-Content $v | Select-String '"path"' | ForEach-Object { ($_ -split '"')[3] }) } }
$libs = $libs | ForEach-Object { $_ -replace '\\\\','\' } | Sort-Object -Unique
foreach ($l in $libs) {
  $acf = Join-Path $l "steamapps\appmanifest_3792580.acf"
  if (Test-Path $acf) {
    Write-Host "[命中] $acf"
    Get-Content $acf | Select-String '"(name|installdir|SizeOnDisk|LastUpdated)"'
  }
}

Write-Host "=== 2. 服务端可执行文件 ===" -ForegroundColor Cyan
foreach ($l in $libs) {
  $p = Join-Path $l "steamapps\common"
  Get-ChildItem $p -Directory | Where-Object { $_.Name -match 'SCUM' } | ForEach-Object {
    Write-Host "[目录] $($_.FullName)"
    Get-ChildItem $_.FullName -Recurse -Filter 'SCUMServer*.exe' -Depth 5 | ForEach-Object { Write-Host "  [启动器] $($_.FullName)  $($_.LastWriteTime)" }
  }
}

Write-Host "=== 3. 服务端配置与存档 ===" -ForegroundColor Cyan
foreach ($l in $libs) {
  $p = Join-Path $l "steamapps\common"
  Get-ChildItem $p -Directory | Where-Object { $_.Name -match 'SCUM' } | ForEach-Object {
    Get-ChildItem $_.FullName -Recurse -Filter 'ServerSettings.ini' -Depth 8 | ForEach-Object { Write-Host "  [配置] $($_.FullName)" }
    Get-ChildItem $_.FullName -Recurse -Directory -Filter 'WindowsServer' -Depth 8 | ForEach-Object { Write-Host "  [存档] $($_.FullName)" }
  }
}

Write-Host "=== 4. 正在运行的服务端进程 / 监听端口 ===" -ForegroundColor Cyan
Get-Process | Where-Object { $_.ProcessName -match 'SCUM|steamcmd' } | Select-Object Id,ProcessName,Path | Format-Table -AutoSize
Get-NetUDPEndpoint | Where-Object { $_.LocalPort -in 7042,7043,27015 } | Select-Object LocalAddress,LocalPort,OwningProcess | Format-Table -AutoSize

Write-Host "=== 5. 全盘兜底搜索 steamcmd.exe 与 SCUMServer ===" -ForegroundColor Cyan
Get-PSDrive -PSProvider FileSystem | ForEach-Object {
  Get-ChildItem "$($_.Root)" -Recurse -Depth 5 -Include 'steamcmd.exe','SCUMServer-Win64-Shipping.exe' | ForEach-Object { Write-Host "  [兜底] $($_.FullName)" }
}
Write-Host "扫描完成。" -ForegroundColor Green
