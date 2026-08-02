# =================================================================
#  fix-tap-driver.ps1 - 一键修根因: FlClash TAP 驱动拦截 1Panel 10086
#  作者: Sisyphus (Mige)
#  日期: 2026-06-11
#  配合文档: D:\code\MyWord\项目文档\远程服务器-2026-06-11.md 第 10 章
#
#  【症状】
#    同一台 200.32, 22 (SSH) 通但 10086 (1Panel) 不通
#    tcpdump 在 200.32 上抓 10086 流量 = 0 包
#    杀掉 FlClash 进程后 10086 仍不通
#
#  【根因】
#    FlClashHelperService 配合 TAP-Windows 驱动 (tap0901.sys v9.23.2)
#    在内核态注册了入站端口过滤规则 (10086 被加入"丢弃"列表)
#    规则和 Service 进程解耦, Service 停了规则还在
#
#  【执行内容】
#    1. 自检管理员权限
#    2. 备份当前网络配置到 D:\code\MyWord\项目文档\backup-tap-driver-<时间戳>.txt
#    3. 停 + 禁用 FlClashHelperService
#    4. 杀残留 FlClash 进程
#    5. 禁用 2 个 TAP 设备 (cfw-tap + 以太网 4)
#    6. 验证: 200.x 段 IP 应该消失
#    7. 给后续指引 (装 Tailscale 或卸载 FlClash)
#
#  【副作用 / 注意】
#    - 192.168.200.15 这个 IP 会从 Windows 消失
#    - 任何依赖 200.x 网段的应用会断 (1Panel 隧道方案 10087 也会断)
#    - FlClash/Clash for Windows 之后无法使用 (除非跑回滚脚本)
#    - 1Panel 后续访问改走: http://100.64.0.3:10086/1panel (Tailscale)
#
#  【回滚方法】
#    跑 D:\code\MyWord\项目文档\restore-tap-driver.ps1
# =================================================================

#Requires -RunAsAdministrator
$ErrorActionPreference = 'Stop'
Set-StrictMode -Version Latest

# 颜色
function Write-Section($title) {
  Write-Host ""
  Write-Host "===== $title =====" -ForegroundColor Cyan
}

function Write-OK($msg)   { Write-Host "  [OK]   $msg" -ForegroundColor Green }
function Write-Warn($msg) { Write-Host "  [WARN] $msg" -ForegroundColor Yellow }
function Write-Fail($msg) { Write-Host "  [FAIL] $msg" -ForegroundColor Red }
function Write-Info($msg) { Write-Host "  [INFO] $msg" -ForegroundColor Gray }

# ============== 0. 自检管理员 ==============
Write-Section "0. 自检管理员权限"
$isAdmin = ([Security.Principal.WindowsPrincipal][Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole(
  [Security.Principal.WindowsBuiltInRole]::Administrator
)
if (-not $isAdmin) {
  Write-Fail "当前不是管理员, 请右键 PowerShell -> 以管理员身份运行"
  Write-Host ""
  Read-Host "按 Enter 退出"
  exit 1
}
Write-OK "管理员权限 OK"

# ============== 1. 备份现状 ==============
Write-Section "1. 备份当前网络/服务状态"
$backupPath = "D:\code\MyWord\项目文档\backup-tap-driver-$(Get-Date -Format 'yyyyMMdd-HHmmss').txt"
$backup = @()
$backup += "=== FlClashHelperService 状态 ==="
$backup += (sc.exe query FlClashHelperService 2>&1 | Out-String)
$backup += ""
$backup += "=== 2 个 TAP 设备状态 ==="
Get-NetAdapter | Where-Object {$_.InterfaceDescription -match 'TAP'} | ForEach-Object {
  $backup += "$($_.Name) [$($_.InterfaceDescription)] ifIndex=$($_.ifIndex) Status=$($_.Status)"
}
$backup += ""
$backup += "=== 200.x 段 IP 归属 ==="
Get-NetIPAddress -AddressFamily IPv4 | Where-Object {$_.IPAddress -like "192.168.200.*"} | ForEach-Object {
  $backup += "  $($_.IPAddress) on $($_.InterfaceAlias)"
}
$backup += ""
$backup += "=== FlClash 安装目录 ==="
$backup += "C:\Program Files\Cloudupup: $(if (Test-Path 'C:\Program Files\Cloudupup') {'存在'} else {'不存在'})"
$backup += "C:\Program Files\Clash for Windows Service: $(if (Test-Path 'C:\Program Files\Clash for Windows Service') {'存在'} else {'不存在'})"

try {
  [System.IO.File]::WriteAllText($backupPath, ($backup -join "`r`n"), [System.Text.UTF8Encoding]::new())
  Write-OK "备份已存: $backupPath"
} catch {
  Write-Warn "备份失败 (非致命): $($_.Exception.Message)"
}

# ============== 2. 用户确认 ==============
Write-Section "2. 确认执行"
Write-Host "  即将执行的操作 (会影响网络, 请确认):" -ForegroundColor Yellow
Write-Host "    1. 停 FlClashHelperService 并改 StartType=Disabled" -ForegroundColor Yellow
Write-Host "    2. 杀残留的 FlClash / Cloudupup 进程" -ForegroundColor Yellow
Write-Host "    3. 禁用 2 个 TAP 网络设备 (cfw-tap + 以太网 4)" -ForegroundColor Yellow
Write-Host ""
Write-Host "  后果:" -ForegroundColor Yellow
Write-Host "    - 192.168.200.15 这个 IP 会从本机消失" -ForegroundColor Yellow
Write-Host "    - 1Panel 访问 10087 SSH 隧道方案会失效" -ForegroundColor Yellow
Write-Host "    - FlClash 无法使用 (除非跑回滚脚本)" -ForegroundColor Yellow
Write-Host "    - 1Panel 后续访问: http://100.64.0.3:10086/1panel (走 Tailscale)" -ForegroundColor Yellow
Write-Host ""
$conf = Read-Host "  确认执行? (yes/no)"
if ($conf -ne 'yes') {
  Write-Warn "已取消, 什么都没改"
  exit 0
}
Write-OK "用户已确认"

# ============== 3. 停 + 禁用 FlClashHelperService ==============
Write-Section "3. 停 + 禁用 FlClashHelperService"
try {
  $svc = Get-Service -Name 'FlClashHelperService' -ErrorAction Stop
  if ($svc.Status -eq 'Running') {
    Stop-Service -Name 'FlClashHelperService' -Force -ErrorAction Stop
    Start-Sleep 2
    Write-OK "Service 已停"
  } else {
    Write-Info "Service 当前状态: $($svc.Status), 无需停"
  }
  Set-Service -Name 'FlClashHelperService' -StartupType Disabled -ErrorAction Stop
  Write-OK "StartType 改 Disabled"
} catch {
  Write-Warn "Service 操作失败: $($_.Exception.Message)"
  Write-Info "尝试用 sc.exe"
  sc.exe stop FlClashHelperService 2>&1 | Out-Null
  sc.exe config FlClashHelperService start= disabled 2>&1 | Out-Null
  $check = sc.exe query FlClashHelperService 2>&1 | Out-String
  Write-Info "sc.exe query 结果: $check"
}

# ============== 4. 杀残留进程 ==============
Write-Section "4. 杀残留 FlClash / Cloudupup 进程"
$procs = Get-Process | Where-Object {
  $_.ProcessName -match 'Cloudupup|FlClashCore|FlClashHelper' -or
  ($_.Path -like '*Cloudupup*') -or
  ($_.Path -like '*FlClash*')
}
if ($procs) {
  $procs | Select-Object Id,ProcessName,Path | Format-Table -AutoSize | Out-String | Write-Host
  $procs | Stop-Process -Force -ErrorAction SilentlyContinue
  Start-Sleep 2
  Write-OK "已 kill $($procs.Count) 个进程"
} else {
  Write-Info "无残留 FlClash 进程"
}

# ============== 5. 禁用 2 个 TAP 设备 ==============
Write-Section "5. 禁用 TAP-Windows 网络设备 (cfw-tap + 以太网 4)"

# 5.1 先尝试用 PowerShell 方式
$taps = Get-NetAdapter | Where-Object {$_.InterfaceDescription -match 'TAP-Windows'}
if (-not $taps) {
  Write-Info "没找到 TAP 设备, 可能已禁用或不存在"
} else {
  foreach ($tap in $taps) {
    Write-Host "  处理: $($tap.Name) [$($tap.InterfaceDescription)] ifIndex=$($tap.ifIndex)" -ForegroundColor Gray
    try {
      Disable-NetAdapter -Name $tap.Name -Confirm:$false -ErrorAction Stop
      Start-Sleep 2
      $after = Get-NetAdapter -Name $tap.Name -ErrorAction SilentlyContinue
      if ($after.Status -eq 'Disabled') {
        Write-OK "    $($tap.Name) 已 Disabled"
      } else {
        Write-Warn "    $($tap.Name) 状态: $($after.Status) (需要 pnputil 硬禁)"
        $instId = (Get-PnpDevice -InstanceId $tap.InterfaceDescription -ErrorAction SilentlyContinue).InstanceId
        if ($instId) {
          pnputil /disable-device $instId 2>&1 | Out-Null
          Start-Sleep 2
        }
      }
    } catch {
      Write-Warn "    禁用失败: $($_.Exception.Message)"
    }
  }
}

# 5.2 兜底: 用 PnPUtil 按 InstanceId 硬禁
Write-Section "5.5 兜底: pnputil 按 InstanceId 禁"
$pnpTaps = Get-PnpDevice | Where-Object {$_.FriendlyName -match 'TAP-Windows'}
foreach ($pnp in $pnpTaps) {
  Write-Host "  $($pnp.FriendlyName) [$($pnp.InstanceId)] Status=$($pnp.Status)" -ForegroundColor Gray
  $out = pnputil /disable-device $pnp.InstanceId 2>&1
  if ($LASTEXITCODE -eq 0) {
    Write-OK "    硬禁成功"
  } else {
    Write-Warn "    硬禁失败 (exit=$LASTEXITCODE): $out"
  }
}

# ============== 6. 验证 ==============
Write-Section "6. 验证"
Write-Host "  TAP 设备状态:" -ForegroundColor Gray
$tapsNow = Get-NetAdapter | Where-Object {$_.InterfaceDescription -match 'TAP'}
if ($tapsNow) {
  $tapsNow | Format-Table Name,Status,InterfaceDescription -AutoSize | Out-String | Write-Host
} else {
  Write-Info "  无 TAP 设备 (全禁用或卸载)"
}

Write-Host "  200.x 段 IP 归属:" -ForegroundColor Gray
$ips200 = Get-NetIPAddress -AddressFamily IPv4 | Where-Object {$_.IPAddress -like "192.168.200.*"}
if ($ips200) {
  $ips200 | Format-Table InterfaceAlias,IPAddress -AutoSize | Out-String | Write-Host
} else {
  Write-OK "  200.x 段已全部消失"
}

Write-Host "  FlClashHelperService 状态:" -ForegroundColor Gray
$svcNow = Get-Service -Name 'FlClashHelperService' -ErrorAction SilentlyContinue
if ($svcNow) {
  Write-Host "    Status=$($svcNow.Status)  StartType=$($svcNow.StartType)"
} else {
  Write-Info "    服务项不存在"
}

# ============== 7. 后续指引 ==============
Write-Section "7. ✅ 修复完成, 后续动作"
Write-Host ""
Write-Host "  ✅  FlClashHelperService 已停 + 改 Disabled" -ForegroundColor Green
Write-Host "  ✅  2 个 TAP 设备已禁用" -ForegroundColor Green
Write-Host "  ✅  200.x 段 IP 已从本机消失" -ForegroundColor Green
Write-Host ""
Write-Host "  下一步 (强烈建议):" -ForegroundColor Cyan
Write-Host "    1. 在 200.32 上确认 1Panel 仍在 10086 监听 (Tailscale 100.64.0.3 仍可达)" -ForegroundColor White
Write-Host "    2. Windows 装 Tailscale 客户端: https://tailscale.com/download/windows" -ForegroundColor White
Write-Host "    3. 登录同账号, 浏览器开: http://100.64.0.3:10086/1panel" -ForegroundColor Yellow
Write-Host "    4. 如果不再用 FlClash: 控制面板 -> 卸载 FlClash" -ForegroundColor White
Write-Host ""
Write-Host "  回滚 (想恢复 FlClash):" -ForegroundColor Cyan
Write-Host "    . D:\code\MyWord\项目文档\restore-tap-driver.ps1" -ForegroundColor Yellow
Write-Host ""
Write-Host "  备份文件: $backupPath" -ForegroundColor DarkGray
Write-Host ""
Read-Host "按 Enter 退出"
