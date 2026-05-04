#Requires -Version 5.1
<#
.SYNOPSIS
    Auto-detects ESP32 Arduino core paths and generates c_cpp_properties.json
    using ONLY PowerShell 5.1 compatible syntax (no ||, &&, or 2>nul).

.DESCRIPTION
    This script replaces the broken wildcard-based configuration that causes
    PowerShell parser errors in Windows PowerShell 5.1.

    It searches for the ESP32 core in standard Arduino15 paths, extracts exact
    version numbers, and writes a clean c_cpp_properties.json with absolute paths.

.USAGE
    Right-click -> "Run with PowerShell"  OR
    In VS Code terminal:  .\scripts\setup_vscode_esp32.ps1
#>

$ErrorActionPreference = "Stop"

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------
$UserName    = $env:USERNAME
$Workspace   = $PSScriptRoot | Split-Path -Parent  # Project root
$VscodeDir   = Join-Path $Workspace ".vscode"
$JsonPath    = Join-Path $VscodeDir "c_cpp_properties.json"

# Standard Arduino ESP32 installation path
$Esp32Base   = "C:\Users\$UserName\AppData\Local\Arduino15\packages\esp32"
$HardwareDir = Join-Path $Esp32Base "hardware\esp32"
$ToolsDir    = Join-Path $Esp32Base "tools\xtensa-esp32-elf-gcc"

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "ESP32 VS Code Setup (PowerShell 5.1 Safe)" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# ---------------------------------------------------------------------------
# Helper: Find first subdirectory name (replaces wildcard resolution)
# ---------------------------------------------------------------------------
function Get-FirstSubdirName {
    param([string]$Path)
    if (Test-Path $Path) {
        $items = Get-ChildItem -Path $Path -Directory -ErrorAction SilentlyContinue
        if ($items) {
            return $items[0].Name
        }
    }
    return $null
}

# ---------------------------------------------------------------------------
# Detect ESP32 core version
# ---------------------------------------------------------------------------
$CoreVersion = Get-FirstSubdirName -Path $HardwareDir
if (-not $CoreVersion) {
    Write-Host "ERROR: ESP32 core not found." -ForegroundColor Red
    Write-Host "Expected path: $HardwareDir" -ForegroundColor Red
    Write-Host ""
    Write-Host "Please install the ESP32 board support first:" -ForegroundColor Yellow
    Write-Host "  1. Open Arduino IDE" -ForegroundColor Yellow
    Write-Host "  2. File -> Preferences -> Additional Board Manager URLs" -ForegroundColor Yellow
    Write-Host "     Add: https://raw.githubusercontent.com/espressif/arduino-esp32/gh-pages/package_esp32_index.json" -ForegroundColor Yellow
    Write-Host "  3. Tools -> Board -> Board Manager -> Search 'ESP32' -> Install" -ForegroundColor Yellow
    Write-Host ""
    Write-Host "Or use PlatformIO instead (see platformio.ini in this project)." -ForegroundColor Green
    exit 1
}

Write-Host "Found ESP32 core version: $CoreVersion" -ForegroundColor Green

# ---------------------------------------------------------------------------
# Detect GCC toolchain version
# ---------------------------------------------------------------------------
$GccVersion = Get-FirstSubdirName -Path $ToolsDir
if (-not $GccVersion) {
    Write-Host "WARNING: GCC toolchain not found at $ToolsDir" -ForegroundColor Yellow
    Write-Host "IntelliSense will be limited until the toolchain is installed." -ForegroundColor Yellow
    $CompilerPath = ""
} else {
    Write-Host "Found GCC toolchain version: $GccVersion" -ForegroundColor Green
    $CompilerPath = "C:/Users/$UserName/AppData/Local/Arduino15/packages/esp32/tools/xtensa-esp32-elf-gcc/$GccVersion/bin/xtensa-esp32-elf-gcc.exe"
}

# ---------------------------------------------------------------------------
# Build include paths
# ---------------------------------------------------------------------------
$IncludePaths = @(
    "`${workspaceFolder}/**",
    "C:/Users/$UserName/AppData/Local/Arduino15/packages/esp32/hardware/esp32/$CoreVersion/cores/esp32/**",
    "C:/Users/$UserName/AppData/Local/Arduino15/packages/esp32/hardware/esp32/$CoreVersion/libraries/**",
    "C:/Users/$UserName/AppData/Local/Arduino15/packages/esp32/hardware/esp32/$CoreVersion/tools/sdk/include/**",
    "C:/Users/$UserName/Documents/Arduino/libraries/**"
)

# ---------------------------------------------------------------------------
# Build JSON payload
# ---------------------------------------------------------------------------
$config = @{
    configurations = @(
        @{
            name            = "ESP32 Arduino"
            includePath     = $IncludePaths
            defines         = @("ARDUINO=10800", "ESP32", "CORE_DEBUG_LEVEL=0")
            compilerPath    = $CompilerPath
            cStandard       = "c11"
            cppStandard     = "c++11"
            intelliSenseMode= "gcc-x64"
            forcedInclude   = @()
        }
    )
    version = 4
}

# ---------------------------------------------------------------------------
# Write JSON file
# ---------------------------------------------------------------------------
if (-not (Test-Path $VscodeDir)) {
    New-Item -ItemType Directory -Path $VscodeDir | Out-Null
}

$jsonString = $config | ConvertTo-Json -Depth 10
# Convert backslashes in the JSON string to forward slashes for consistency
$jsonString = $jsonString -replace '\\', '/'

$jsonString | Out-File -FilePath $JsonPath -Encoding utf8

Write-Host ""
Write-Host "SUCCESS: Written $JsonPath" -ForegroundColor Green
Write-Host ""
Write-Host "Next steps:" -ForegroundColor Cyan
Write-Host "  1. Reload VS Code window (Ctrl+Shift+P -> Developer: Reload Window)" -ForegroundColor White
Write-Host "  2. Or run: C/C++: Rescan Workspace" -ForegroundColor White
Write-Host ""

