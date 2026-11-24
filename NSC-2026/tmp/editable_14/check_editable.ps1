$ErrorActionPreference = 'Stop'
$taskOriginal = 'C:\Users\Raphael Angelo\Code\Competitions\NSC UB\deliverables\presentation\BERKAS_734_14_SLIDE_EDITABLE.pptx'
$taskCopy = 'C:\Users\Raphael Angelo\Code\Competitions\NSC UB\tmp\editable_14\editability-test.pptx'
Copy-Item -LiteralPath $taskOriginal -Destination $taskCopy
$taskPpt = New-Object -ComObject PowerPoint.Application
$taskDeck = $null
try {
    $taskDeck = $taskPpt.Presentations.Open($taskCopy, 0, 0, 0)
    $taskTextEdited = $false
    foreach ($taskShape in $taskDeck.Slides.Item(1).Shapes) {
        if ($taskShape.HasTextFrame -eq -1 -and $taskShape.TextFrame.HasText -eq -1) {
            if ($taskShape.TextFrame.TextRange.Text -eq 'BERKAS 734') {
                $taskShape.TextFrame.TextRange.Text = 'BERKAS 734 UJI'
                $taskTextEdited = $true
                break
            }
        }
    }
    $taskChartEdited = $false
    foreach ($taskShape in $taskDeck.Slides.Item(3).Shapes) {
        if ($taskShape.HasChart -eq -1) {
            $taskShape.Width = $taskShape.Width + 2
            $taskShape.Chart.ChartTitle.Text = 'Rasio residual (uji edit)'
            $taskChartEdited = $true
            break
        }
    }
    $taskDeck.Save()
    $taskDeck.Close()
    $taskDeck = $taskPpt.Presentations.Open($taskCopy, -1, 0, 0)
    $taskTextPersisted = $false
    foreach ($taskShape in $taskDeck.Slides.Item(1).Shapes) {
        if ($taskShape.HasTextFrame -eq -1 -and $taskShape.TextFrame.HasText -eq -1) {
            if ($taskShape.TextFrame.TextRange.Text -eq 'BERKAS 734 UJI') { $taskTextPersisted = $true }
        }
    }
    $taskChartPersisted = $false
    foreach ($taskShape in $taskDeck.Slides.Item(3).Shapes) {
        if ($taskShape.HasChart -eq -1 -and $taskShape.Chart.ChartTitle.Text -eq 'Rasio residual (uji edit)') { $taskChartPersisted = $true }
    }
    [PSCustomObject]@{text_edit=$taskTextEdited;chart_resize_and_title_edit=$taskChartEdited;text_saved_and_reopened=$taskTextPersisted;chart_saved_and_reopened=$taskChartPersisted;final_file_unchanged=$true} | ConvertTo-Json | Set-Content -LiteralPath 'C:\Users\Raphael Angelo\Code\Competitions\NSC UB\tmp\editable_14\editability-test.json' -Encoding utf8
    Get-Content -LiteralPath 'C:\Users\Raphael Angelo\Code\Competitions\NSC UB\tmp\editable_14\editability-test.json'
} finally {
    if ($null -ne $taskDeck) { $taskDeck.Close() }
    if ($taskPpt.Presentations.Count -eq 0) { $taskPpt.Quit() }
    [Runtime.InteropServices.Marshal]::ReleaseComObject($taskPpt) | Out-Null
}
