param([switch]$UpdateOnly)
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
    $wordApplication.Options.PrintBackground = $false
    $wordApplication.Options.UpdateFieldsAtPrint = $false
    $wordApplication.Options.UpdateLinksAtPrint = $false
    Write-Output 'Abriendo el Word académico generado.'
    $taskDocument = $wordApplication.Documents.Open($taskDocx, $false, $false)
    Write-Output 'Actualizando campos e índice.'
    [void]$taskDocument.Fields.Update()
    foreach ($tableOfContents in $taskDocument.TablesOfContents) { $tableOfContents.Update() }
    $taskDocument.Repaginate()
    Write-Output 'Paginación terminada.'
    [void]$taskDocument.Fields.Update()
    $taskDocument.Save()
    if ($UpdateOnly) {
        $pages = $taskDocument.ComputeStatistics(2)
        @{ timestamp = (Get-Date).ToUniversalTime().ToString('o'); application = 'Microsoft Word'; opened = $true; fieldsUpdated = $true; tocUpdated = $true; repaginated = $true; pages = $pages; limitation = 'La exportación PDF de Word no finalizó; se usa composición independiente de ReportLab.' } | ConvertTo-Json | Set-Content -Encoding UTF8 -LiteralPath (Join-Path $taskRoot 'evidence/word-validation.json')
        Write-Output "Editable validado por Word. Páginas: $pages."
        return
    }
    Write-Output 'Exportando PDF con opciones explícitas.'
    $taskDocument.ExportAsFixedFormat($taskPdf, 17, $false, 0, 0, 1, 1, 0, $true, $false, 1, $false, $true, $false)
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
