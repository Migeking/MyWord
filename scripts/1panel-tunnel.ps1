# D:\code\MyWord\scripts\1panel-tunnel.ps1
# 1Panel SSH 隧道快捷脚本
# 用法: PowerShell 里 . .\1panel-tunnel.ps1
# 然后浏览器: http://127.0.0.1:10087/1panel
# 用户: admin / 密码: vExnz56sGGkLRFvA8LjS  (登录后立即改)
#
# 走通原理: 22 (SSH) 通, 10086 (1Panel) 不通
#           用 SSH 隧道 (走通的 22) 把不通的 10086 通过 200.32 内部 loopback 转发
#           cfw-tap TAP 驱动只拦入站 10086, 不拦 22 也不拦 loopback

$RemoteHost   = '192.168.200.32'
$RemotePass   = 'xyt@2023'   # 200.32 root 密码
$LocalPort    = 10087        # 本地监听端口
$RemotePort   = 10086        # 远程 1Panel 端口
$SshExe       = 'C:\Windows\System32\OpenSSH\ssh.exe'

Write-Host "=== 启动 1Panel SSH 隧道 ===" -ForegroundColor Cyan

# 1. 关掉旧隧道
Get-Process | Where-Object {$_.ProcessName -eq 'ssh' -and $_.CommandLine -like "*$LocalPort*"} | ForEach-Object {
  Write-Host "  Kill 旧隧道 PID $($_.Id)" -ForegroundColor DarkGray
  Stop-Process -Id $_.Id -Force
}
Start-Sleep 1

# 2. 写临时 askpass
$tmp = Join-Path $env:TEMP "askpass_$PID.cmd"
[System.IO.File]::WriteAllText($tmp, "@echo off`r`necho $RemotePass", [System.Text.ASCIIEncoding]::new())

# 3. 启 SSH 后台
$psi = New-Object System.Diagnostics.ProcessStartInfo
$psi.FileName = $SshExe
$psi.Arguments = "-f -N -o StrictHostKeyChecking=no -o UserKnownHostsFile=NUL -o ExitOnForwardFailure=yes -L ${LocalPort}:127.0.0.1:${RemotePort} root@$RemoteHost"
$psi.UseShellExecute = $false
$psi.RedirectStandardInput = $true
$psi.RedirectStandardError = $true
$psi.EnvironmentVariables["SSH_ASKPASS"] = $tmp
$psi.EnvironmentVariables["SSH_ASKPASS_REQUIRE"] = "force"
$psi.EnvironmentVariables["DISPLAY"] = ":0"
try {
  $proc = [System.Diagnostics.Process]::Start($psi)
  $proc.StandardInput.Close()
  Start-Sleep 3
} catch {
  Write-Host "  [FAIL] SSH 启动异常: $($_.Exception.Message)" -ForegroundColor Red
  Remove-Item $tmp -Force -ErrorAction SilentlyContinue
  exit 1
}

Remove-Item $tmp -Force -ErrorAction SilentlyContinue

# 4. 验证
$listen = Get-NetTCPConnection -LocalPort $LocalPort -State Listen -ErrorAction SilentlyContinue
if ($listen) {
  $ssh = Get-Process | Where-Object {$_.ProcessName -eq 'ssh' -and $_.CommandLine -like "*$LocalPort*"}
  Write-Host ""
  Write-Host "✅ 隧道已起" -ForegroundColor Green
  Write-Host "   SSH 进程 PID: $($ssh.Id)" -ForegroundColor Green
  Write-Host "   监听: 127.0.0.1:$LocalPort  ->  $RemoteHost`:127.0.0.1`:$RemotePort" -ForegroundColor Green
  Write-Host ""
  Write-Host "🌐 浏览器打开: http://127.0.0.1:$LocalPort/1panel" -ForegroundColor Yellow
  Write-Host "   用户: admin" -ForegroundColor Yellow
  Write-Host "   密码: vExnz56sGGkLRFvA8LjS  (登录后请立即修改)" -ForegroundColor Yellow
  Write-Host ""
  Write-Host "💡 关闭隧道: Get-Process ssh | Where-Object CommandLine -like '*$LocalPort*' | Stop-Process" -ForegroundColor DarkGray
} else {
  Write-Host "  [FAIL] $LocalPort 未监听, 隧道可能没起成功" -ForegroundColor Red
  Write-Host "  常见原因: 密码错、known_hosts 冲突、22 被另一会话占用" -ForegroundColor DarkGray
}