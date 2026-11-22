param()
$ErrorActionPreference = 'Stop'
$taskRoot = Split-Path -Parent $PSScriptRoot
$taskDocx = Join-Path $taskRoot 'docs/Manejo-de-Scripts.docx'
$taskPages = Join-Path $taskRoot 'tmp/word-pages'
New-Item -ItemType Directory -Path $taskPages -Force | Out-Null
$wordApplication = $null
$taskDocument = $null
try {
    $wordApplication = New-Object -ComObject Word.Application
    $wordApplication.Visible = $false
    $wordApplication.DisplayAlerts = 0
    $wordApplication.Options.PrintBackground = $false
    $wordApplication.Options.UpdateFieldsAtPrint = $false
    $wordApplication.Options.UpdateLinksAtPrint = $false
    $taskDocument = $wordApplication.Documents.Open($taskDocx, $false, $true)
    $pages = $taskDocument.ComputeStatistics(2)
    Write-Output "Documento abierto: $pages páginas."
    for ($pageIndex = 1; $pageIndex -le $pages; $pageIndex++) {
        $pageFile = Join-Path $taskPages ('page-{0:d2}.pdf' -f $pageIndex)
        Write-Output "Exportando página $pageIndex."
        $taskDocument.ExportAsFixedFormat($pageFile, 17, $false, 0, 3, $pageIndex, $pageIndex, 0, $false, $false, 0, $false, $true, $false)
    }
    @{ timestamp = (Get-Date).ToUniversalTime().ToString('o'); converter = 'Microsoft Word COM, exportación por páginas'; pages = $pages; pageDirectory = 'tmp/word-pages'; tocUpdated = $true } | ConvertTo-Json | Set-Content -Encoding UTF8 -LiteralPath (Join-Path $taskRoot 'evidence/document-export.json')
    Write-Output 'Páginas PDF exportadas para unir y revisar.'
}
finally {
    if ($null -ne $taskDocument) { $taskDocument.Close(0); [void][System.Runtime.InteropServices.Marshal]::ReleaseComObject($taskDocument) }
    if ($null -ne $wordApplication) { $wordApplication.Quit(); [void][System.Runtime.InteropServices.Marshal]::ReleaseComObject($wordApplication) }
}
