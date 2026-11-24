# D盘安全清理：回收站 + Steam 孤儿目录（Steam 客户端已不管理的残留文件夹）
# 默认只预览，不删除。确认无误后加 -Execute 执行。
# 用法： powershell -ExecutionPolicy Bypass -File .\清理D盘_安全项.ps1
#        powershell -ExecutionPolicy Bypass -File .\清理D盘_安全项.ps1 -Execute
param([switch]$Execute)

$ErrorActionPreference = 'SilentlyContinue'

function Show-Drive {
    $d = Get-PSDrive D
    "D盘: 已用 {0:N1} GB / 共 {1:N1} GB，剩余 {2:N1} GB" -f (($d.Used)/1GB), ((($d.Used)+($d.Free))/1GB), ($d.Free/1GB)
}

"==== 清理前 ===="
Show-Drive
""

# --- 1. Steam 孤儿目录（有文件夹但没有对应的 appmanifest，Steam 里已看不到/已卸载残留）---
$common = 'D:\SteamLibrary\steamapps\common'
$manifests = @{}
Get-ChildItem 'D:\SteamLibrary\steamapps\appmanifest_*.acf' | ForEach-Object {
    $t = Get-Content $_.FullName -Raw
    if ($t -match '"installdir"\s*"([^"]*)"') { $manifests[$matches[1].ToLower()] = $_.Name }
}

$orphans = @()
Get-ChildItem $common -Directory | ForEach-Object {
    if (-not $manifests.ContainsKey($_.Name.ToLower())) {
        $sz = (Get-ChildItem $_.FullName -Recurse -File | Measure-Object Length -Sum).Sum
        $orphans += [pscustomobject]@{ Path = $_.FullName; GB = [math]::Round($sz/1GB, 2) }
    }
}

"==== Steam 孤儿目录（可安全删除，Steam 不会再更新它们）===="
$orphans | Sort-Object GB -Descending | ForEach-Object { "  {0,7:N2} GB  {1}" -f $_.GB, $_.Path }
"  小计: {0:N2} GB" -f (($orphans | Measure-Object GB -Sum).Sum)
""

# --- 2. 回收站 ---
$rb = 0
Get-ChildItem 'D:\$RECYCLE.BIN' -Recurse -File -Force | ForEach-Object { $rb += $_.Length }
"==== 回收站 ===="
"  {0:N2} GB" -f ($rb/1GB)
""

# --- 3. 重复的测试服客户端 ---
$dups = @('D:\WeGameApps\LOLTest')
"==== 疑似重复客户端（英雄联盟测试服，和正式服双份）===="
foreach ($p in $dups) {
    if (Test-Path $p) {
        $sz = (Get-ChildItem $p -Recurse -File | Measure-Object Length -Sum).Sum
        "  {0,7:N2} GB  {1}" -f ($sz/1GB), $p
    }
}
""

if (-not $Execute) {
    "以上为预览。确认后执行： powershell -ExecutionPolicy Bypass -File .\清理D盘_安全项.ps1 -Execute"
    "注意：LOLTest 需你自己决定——确认不玩测试服后再手动删除，脚本不自动删游戏。"
    exit 0
}

"==== 开始清理 ===="
foreach ($o in $orphans) {
    "删除: $($o.Path)"
    Remove-Item $o.Path -Recurse -Force
}
"清空回收站 D:"
Clear-RecycleBin -DriveLetter D -Force -Confirm:$false
""
"==== 清理后 ===="
Show-Drive
