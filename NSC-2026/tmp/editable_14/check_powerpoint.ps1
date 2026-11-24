$ErrorActionPreference = 'Stop'
$taskDeckPath = 'C:\Users\Raphael Angelo\Code\Competitions\NSC UB\deliverables\presentation\BERKAS_734_14_SLIDE_EDITABLE.pptx'
$taskRenderPath = 'C:\Users\Raphael Angelo\Code\Competitions\NSC UB\tmp\editable_14\powerpoint-renders'
New-Item -ItemType Directory -Path $taskRenderPath -Force | Out-Null
$taskPpt = New-Object -ComObject PowerPoint.Application
$taskPresentation = $null
try {
    $taskPresentation = $taskPpt.Presentations.Open($taskDeckPath, -1, 0, 0)
    $taskPresentation.Export($taskRenderPath, 'PNG', 1600, 900)
    $taskNativeCharts = 0
    foreach ($taskSlide in $taskPresentation.Slides) {
        foreach ($taskShape in $taskSlide.Shapes) {
            if ($taskShape.HasChart -eq -1) { $taskNativeCharts++ }
        }
    }
    [PSCustomObject]@{ slides=$taskPresentation.Slides.Count; native_charts=$taskNativeCharts; exported_pngs=(Get-ChildItem -LiteralPath $taskRenderPath -Filter '*.PNG' | Measure-Object).Count; powerpoint_open='passed' } | ConvertTo-Json | Set-Content -LiteralPath (Join-Path $taskRenderPath 'native-check.json') -Encoding utf8
    Get-Content -LiteralPath (Join-Path $taskRenderPath 'native-check.json')
} finally {
    if ($null -ne $taskPresentation) { $taskPresentation.Close() }
    if ($taskPpt.Presentations.Count -eq 0) { $taskPpt.Quit() }
    [Runtime.InteropServices.Marshal]::ReleaseComObject($taskPpt) | Out-Null
}
