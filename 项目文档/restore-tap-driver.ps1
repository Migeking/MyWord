# =================================================================
#  restore-tap-driver.ps1 - 回滚 fix-tap-driver.ps1 的修改
#  恢复 FlClashHelperService 启动 + 启用 2 个 TAP 设备
# =================================================================

#Requires -RunAsAdministrator
$ErrorActionPreference = 'Stop'

function Write-Section($title) {
  Write-Host ""
  Write-Host "===== $title =====" -ForegroundColor Cyan
}
function Write-OK($msg)   { Write-Host "  [OK]   $msg" -ForegroundColor Green }
function Write-Warn($msg) { Write-Host "  [WARN] $msg" -ForegroundColor Yellow }
function Write-Info($msg) { Write-Host "  [INFO] $msg" -ForegroundColor Gray }

$isAdmin = ([Security.Principal.WindowsPrincipal][Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole(
  [Security.Principal.WindowsBuiltInRole]::Administrator
)
if (-not $isAdmin) {
  Write-Host "  [FAIL] 当前不是管理员, 请右键 PowerShell -> 以管理员身份运行" -ForegroundColor Red
  Read-Host "按 Enter 退出"
  exit 1
}

Write-Host "  将要执行:" -ForegroundColor Yellow
Write-Host "    1. FlClashHelperService 改回 StartType=Automatic 并启动" -ForegroundColor Yellow
Write-Host "    2. 启用 2 个 TAP 设备 (cfw-tap + 以太网 4)" -ForegroundColor Yellow
Write-Host "    3. 200.15 可能恢复到 以太网 4 上" -ForegroundColor Yellow
Write-Host ""
Write-Host "  ⚠️  注意: 回滚后 1Panel 10086 仍会被 TAP 驱动拦截, 你会回到修复前的状态" -ForegroundColor Yellow
Write-Host ""
$conf = Read-Host "  确认回滚? (yes/no)"
if ($conf -ne 'yes') { Write-Host "  取消"; exit 0 }

# 1. Service 改回自动
Write-Section "1. FlClashHelperService -> Automatic + Start"
try {
  Set-Service -Name 'FlClashHelperService' -StartupType Automatic -ErrorAction Stop
  Start-Service -Name 'FlClashHelperService' -ErrorAction Stop
  Write-OK "Service 已启动"
} catch {
  Write-Warn "Service 操作失败: $($_.Exception.Message)"
}

# 2. 启用 TAP 设备
Write-Section "2. 启用 TAP 设备"
$pnpTaps = Get-PnpDevice | Where-Object {$_.FriendlyName -match 'TAP-Windows'}
foreach ($pnp in $pnpTaps) {
  Write-Host "  $($pnp.FriendlyName) [$($pnp.InstanceId)]" -ForegroundColor Gray
  pnputil /enable-device $pnp.InstanceId 2>&1 | Out-Null
  if ($LASTEXITCODE -eq 0) {
    Write-OK "    已 enable"
  } else {
    Write-Warn "    enable 失败 (exit=$LASTEXITCODE)"
  }
}

# 3. 启用网络适配器
Write-Section "3. 启用网络适配器 (Enable-NetAdapter)"
$taps = Get-NetAdapter | Where-Object {$_.InterfaceDescription -match 'TAP'}
foreach ($tap in $taps) {
  if ($tap.Status -eq 'Disabled') {
    try {
      Enable-NetAdapter -Name $tap.Name -Confirm:$false -ErrorAction Stop
      Start-Sleep 2
      $after = Get-NetAdapter -Name $tap.Name
      Write-OK "  $($tap.Name) -> Status=$($after.Status)"
    } catch {
      Write-Warn "  $($tap.Name): $($_.Exception.Message)"
    }
  }
}

# 4. 看 200.15 是否恢复
Write-Section "4. 验证 200.15 归属"
$ips200 = Get-NetIPAddress -AddressFamily IPv4 | Where-Object {$_.IPAddress -like "192.168.200.*"}
if ($ips200) {
  $ips200 | Format-Table InterfaceAlias,IPAddress -AutoSize | Out-String | Write-Host
} else {
  Write-Host "  [INFO] 200.x 段仍未恢复 (可能需要重启网络栈: ipconfig /renew)" -ForegroundColor Yellow
}

Write-Section "✅ 回滚完成"
Write-Host "  已恢复到 FlClash 默认状态" -ForegroundColor Green
Write-Host "  ⚠️  1Panel 10086 仍会被拦截, 用 10087 隧道方案: http://127.0.0.1:10087/1panel" -ForegroundColor Yellow
Read-Host "按 Enter 退出"
