$ErrorActionPreference = "Stop"

$vendorDir = Join-Path $PSScriptRoot "..\app\static\vendor"
New-Item -ItemType Directory -Force -Path $vendorDir | Out-Null

$fontDir = Join-Path $PSScriptRoot "..\app\static\css\files"
New-Item -ItemType Directory -Force -Path $fontDir | Out-Null

Copy-Item -Force (Join-Path $PSScriptRoot "..\node_modules\alpinejs\dist\cdn.min.js") (Join-Path $vendorDir "alpine.min.js")
Copy-Item -Force (Join-Path $PSScriptRoot "..\node_modules\chart.js\dist\chart.umd.js") (Join-Path $vendorDir "chart.umd.js")
Copy-Item -Force (Join-Path $PSScriptRoot "..\node_modules\flowbite\dist\flowbite.min.js") (Join-Path $vendorDir "flowbite.min.js")
Copy-Item -Force (Join-Path $PSScriptRoot "..\node_modules\jquery\dist\jquery.min.js") (Join-Path $vendorDir "jquery.min.js")
Copy-Item -Force (Join-Path $PSScriptRoot "..\node_modules\@fontsource\inter\files\*") $fontDir

$select2Dir = Join-Path $vendorDir "select2"
New-Item -ItemType Directory -Force -Path $select2Dir | Out-Null
Copy-Item -Force (Join-Path $PSScriptRoot "..\node_modules\select2\dist\css\select2.min.css") (Join-Path $select2Dir "select2.min.css")
Copy-Item -Force (Join-Path $PSScriptRoot "..\node_modules\select2\dist\js\select2.min.js") (Join-Path $select2Dir "select2.min.js")

$dataTablesDir = Join-Path $vendorDir "datatables"
New-Item -ItemType Directory -Force -Path $dataTablesDir | Out-Null
Copy-Item -Force (Join-Path $PSScriptRoot "..\node_modules\datatables.net-dt\css\dataTables.dataTables.min.css") (Join-Path $dataTablesDir "dataTables.dataTables.min.css")
Copy-Item -Force (Join-Path $PSScriptRoot "..\node_modules\datatables.net\js\dataTables.min.js") (Join-Path $dataTablesDir "dataTables.min.js")

$fontAwesomeDir = Join-Path $vendorDir "fontawesome"
$fontAwesomeWebfontsDir = Join-Path $vendorDir "webfonts"
New-Item -ItemType Directory -Force -Path $fontAwesomeDir | Out-Null
New-Item -ItemType Directory -Force -Path $fontAwesomeWebfontsDir | Out-Null
Copy-Item -Force (Join-Path $PSScriptRoot "..\node_modules\@fortawesome\fontawesome-free\css\all.min.css") (Join-Path $fontAwesomeDir "all.min.css")
Copy-Item -Force (Join-Path $PSScriptRoot "..\node_modules\@fortawesome\fontawesome-free\webfonts\*") $fontAwesomeWebfontsDir
