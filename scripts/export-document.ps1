param()
$ErrorActionPreference = 'Stop'
$taskRoot = Split-Path -Parent $PSScriptRoot
$taskDocx = Join-Path $taskRoot 'docs/Manejo-de-Scripts.docx'
$taskPdf = Join-Path $taskRoot 'docs/Manejo-de-Scripts.pdf'
if (-not (Test-Path -LiteralPath $taskDocx)) { throw 'No existe el Word académico. Ejecuta primero create-academic-document.py.' }
$wordApplication = $null
$taskDocument = $null
try {
    $wordApplication = New-Object -ComObject Word.Application
    $wordApplication.Visible = $false
    $wordApplication.DisplayAlerts = 0
    $taskDocument = $wordApplication.Documents.Open($taskDocx, $false, $false)
    [void]$taskDocument.Fields.Update()
    foreach ($tableOfContents in $taskDocument.TablesOfContents) { $tableOfContents.Update() }
    $taskDocument.Repaginate()
    [void]$taskDocument.Fields.Update()
    $taskDocument.Save()
    $taskDocument.ExportAsFixedFormat($taskPdf, 17)
    $pages = $taskDocument.ComputeStatistics(2)
    @{ timestamp = (Get-Date).ToUniversalTime().ToString('o'); converter = 'Microsoft Word COM, documento propio oculto'; pages = $pages; docx = 'docs/Manejo-de-Scripts.docx'; pdf = 'docs/Manejo-de-Scripts.pdf'; tocUpdated = $true } | ConvertTo-Json | Set-Content -Encoding UTF8 -LiteralPath (Join-Path $taskRoot 'evidence/document-export.json')
    Write-Output "Word y PDF exportados. Páginas: $pages. Índice actualizado."
}
finally {
    if ($null -ne $taskDocument) { $taskDocument.Close(0); [void][System.Runtime.InteropServices.Marshal]::ReleaseComObject($taskDocument) }
    if ($null -ne $wordApplication) { $wordApplication.Quit(); [void][System.Runtime.InteropServices.Marshal]::ReleaseComObject($wordApplication) }
    [GC]::Collect()
    [GC]::WaitForPendingFinalizers()
}
