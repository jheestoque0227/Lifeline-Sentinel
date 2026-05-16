$ErrorActionPreference = "Stop"

$vendorDir = Join-Path $PSScriptRoot "..\app\static\vendor"
New-Item -ItemType Directory -Force -Path $vendorDir | Out-Null

$fontDir = Join-Path $PSScriptRoot "..\app\static\css\files"
New-Item -ItemType Directory -Force -Path $fontDir | Out-Null

Copy-Item -Force (Join-Path $PSScriptRoot "..\node_modules\alpinejs\dist\cdn.min.js") (Join-Path $vendorDir "alpine.min.js")
Copy-Item -Force (Join-Path $PSScriptRoot "..\node_modules\chart.js\dist\chart.umd.js") (Join-Path $vendorDir "chart.umd.js")
Copy-Item -Force (Join-Path $PSScriptRoot "..\node_modules\flowbite\dist\flowbite.min.js") (Join-Path $vendorDir "flowbite.min.js")
Copy-Item -Force (Join-Path $PSScriptRoot "..\node_modules\@fontsource\inter\files\*") $fontDir

$fontAwesomeDir = Join-Path $vendorDir "fontawesome"
$fontAwesomeWebfontsDir = Join-Path $vendorDir "webfonts"
New-Item -ItemType Directory -Force -Path $fontAwesomeDir | Out-Null
New-Item -ItemType Directory -Force -Path $fontAwesomeWebfontsDir | Out-Null
Copy-Item -Force (Join-Path $PSScriptRoot "..\node_modules\@fortawesome\fontawesome-free\css\all.min.css") (Join-Path $fontAwesomeDir "all.min.css")
Copy-Item -Force (Join-Path $PSScriptRoot "..\node_modules\@fortawesome\fontawesome-free\webfonts\*") $fontAwesomeWebfontsDir
