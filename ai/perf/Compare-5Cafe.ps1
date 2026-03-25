[CmdletBinding()]
param(
    [string]$BaselineUrl = "http://127.0.0.1:8000",
    [string]$AfterUrl = "http://127.0.0.1:8001",
    [int]$Iterations = 10,
    [string]$Payload = "5-cafe",
    [string]$ResultsDir = ""
)

$ErrorActionPreference = "Stop"

$scriptRoot = $PSScriptRoot
if ([string]::IsNullOrWhiteSpace($scriptRoot) -and -not [string]::IsNullOrWhiteSpace($PSCommandPath)) {
    $scriptRoot = Split-Path -Parent $PSCommandPath
}

if ([string]::IsNullOrWhiteSpace($scriptRoot)) {
    $scriptRoot = (Get-Location).Path
}

if ([string]::IsNullOrWhiteSpace($ResultsDir)) {
    $ResultsDir = Join-Path $scriptRoot ("results\{0}-{1}" -f $Payload, (Get-Date -Format "yyyyMMdd-HHmmss"))
}

$k6ScriptPath = Join-Path $scriptRoot "k6\cafe-crawling.js"
$fixturePath = Join-Path $scriptRoot ("k6\fixtures\{0}.json" -f $Payload)

function Get-JsonPropertyValue {
    param(
        [Parameter(Mandatory = $true)]
        [object]$Object,
        [Parameter(Mandatory = $true)]
        [string]$Name
    )

    if ($null -eq $Object) {
        return $null
    }

    $property = $Object.PSObject.Properties[$Name]
    if ($null -eq $property) {
        return $null
    }

    return $property.Value
}

function Get-K6MetricValue {
    param(
        [Parameter(Mandatory = $true)]
        [object]$Summary,
        [Parameter(Mandatory = $true)]
        [string]$MetricName,
        [Parameter(Mandatory = $true)]
        [string]$FieldName
    )

    $metrics = Get-JsonPropertyValue -Object $Summary -Name "metrics"
    $metric = Get-JsonPropertyValue -Object $metrics -Name $MetricName
    if ($null -eq $metric) {
        return $null
    }

    $values = Get-JsonPropertyValue -Object $metric -Name "values"
    $value = Get-JsonPropertyValue -Object $values -Name $FieldName
    if ($null -ne $value) {
        return [double]$value
    }

    $fallback = Get-JsonPropertyValue -Object $metric -Name $FieldName
    if ($null -ne $fallback) {
        return [double]$fallback
    }

    return $null
}

function Format-MetricValue {
    param(
        [object]$Value,
        [string]$Unit
    )

    if ($null -eq $Value) {
        return "n/a"
    }

    switch ($Unit) {
        "ms" { return "{0:N2} ms" -f $Value }
        "pct" { return "{0:P2}" -f $Value }
        default { return "{0:N0}" -f $Value }
    }
}

function Format-DeltaValue {
    param(
        [object]$Value,
        [string]$Unit
    )

    if ($null -eq $Value) {
        return "n/a"
    }

    switch ($Unit) {
        "ms" { return "{0:+0.00;-0.00;0.00} ms" -f $Value }
        "pct" { return "{0:+0.00%;-0.00%;0.00%}" -f $Value }
        default { return "{0:+0;-0;0}" -f $Value }
    }
}

function Format-DeltaPercent {
    param(
        [object]$Baseline,
        [object]$After
    )

    if ($null -eq $Baseline -or $null -eq $After) {
        return "n/a"
    }

    if ([math]::Abs($Baseline) -lt 0.000001) {
        if ([math]::Abs($After) -lt 0.000001) {
            return "0.00%"
        }

        return "n/a"
    }

    $deltaPercent = (($After - $Baseline) / $Baseline) * 100
    return "{0:+0.00%;-0.00%;0.00%}" -f ($deltaPercent / 100)
}

function Invoke-K6Run {
    param(
        [Parameter(Mandatory = $true)]
        [string]$Label,
        [Parameter(Mandatory = $true)]
        [string]$BaseUrl
    )

    $summaryPath = Join-Path $ResultsDir ("{0}.json" -f $Label)
    $metricsPath = Join-Path $ResultsDir ("{0}-metrics.txt" -f $Label)

    Write-Host ""
    Write-Host ("[{0}] Running {1} against {2}" -f $Label.ToUpperInvariant(), $Payload, $BaseUrl)

    $arguments = @(
        "run",
        $k6ScriptPath,
        "-e", "BASE_URL=$BaseUrl",
        "-e", "PAYLOAD=$Payload",
        "-e", "ITERATIONS=$Iterations",
        "--summary-export", $summaryPath
    )

    & k6 @arguments
    if ($LASTEXITCODE -ne 0) {
        throw ("k6 run failed for {0} (exit code {1})" -f $Label, $LASTEXITCODE)
    }

    try {
        $metricsBody = Invoke-WebRequest -Uri ("{0}/metrics" -f $BaseUrl) | Select-Object -ExpandProperty Content
        Set-Content -Path $metricsPath -Value $metricsBody
    }
    catch {
        Write-Warning ("Could not fetch /metrics from {0}: {1}" -f $BaseUrl, $_.Exception.Message)
    }

    return [pscustomobject]@{
        Label       = $Label
        BaseUrl     = $BaseUrl
        SummaryPath = $summaryPath
        MetricsPath = $metricsPath
        Summary     = Get-Content -Raw $summaryPath | ConvertFrom-Json
    }
}

if (-not (Test-Path $k6ScriptPath)) {
    throw ("k6 script not found: {0}" -f $k6ScriptPath)
}

if (-not (Test-Path $fixturePath)) {
    throw ("Fixture not found: {0}" -f $fixturePath)
}

$fixtureText = Get-Content -Raw $fixturePath
$fixtureData = $fixtureText | ConvertFrom-Json

if (-not $fixtureText.TrimStart().StartsWith("[")) {
    throw ("Fixture must be a JSON array: {0}" -f $fixturePath)
}

$fixtureItems = @($fixtureData)
if ($fixtureItems.Count -lt 1) {
    throw ("Fixture must contain at least one cafe: {0}" -f $fixturePath)
}

New-Item -ItemType Directory -Force -Path $ResultsDir | Out-Null

Write-Host ("Fixture check passed: {0} contains {1} cafes." -f $Payload, $fixtureItems.Count)
Write-Host ("Results directory: {0}" -f $ResultsDir)

$baseline = Invoke-K6Run -Label "baseline" -BaseUrl $BaselineUrl
$after = Invoke-K6Run -Label "after" -BaseUrl $AfterUrl

$metricSpecs = @(
    @{ Label = "HTTP Req Avg"; Metric = "http_req_duration"; Field = "avg"; Unit = "ms" },
    @{ Label = "HTTP Req P50"; Metric = "http_req_duration"; Field = "med"; Unit = "ms" },
    @{ Label = "HTTP Req P95"; Metric = "http_req_duration"; Field = "p(95)"; Unit = "ms" },
    @{ Label = "HTTP Req Max"; Metric = "http_req_duration"; Field = "max"; Unit = "ms" },
    @{ Label = "Iteration Avg"; Metric = "iteration_duration"; Field = "avg"; Unit = "ms" },
    @{ Label = "Iteration P50"; Metric = "iteration_duration"; Field = "med"; Unit = "ms" },
    @{ Label = "Iteration P95"; Metric = "iteration_duration"; Field = "p(95)"; Unit = "ms" },
    @{ Label = "HTTP Fail Rate"; Metric = "http_req_failed"; Field = "rate"; Unit = "pct" },
    @{ Label = "Iterations"; Metric = "iterations"; Field = "count"; Unit = "count" }
)

$comparisonRows = foreach ($spec in $metricSpecs) {
    $baselineValue = Get-K6MetricValue -Summary $baseline.Summary -MetricName $spec.Metric -FieldName $spec.Field
    $afterValue = Get-K6MetricValue -Summary $after.Summary -MetricName $spec.Metric -FieldName $spec.Field
    $deltaValue = if ($null -ne $baselineValue -and $null -ne $afterValue) { $afterValue - $baselineValue } else { $null }

    [pscustomobject]@{
        Metric   = $spec.Label
        Baseline = Format-MetricValue -Value $baselineValue -Unit $spec.Unit
        After    = Format-MetricValue -Value $afterValue -Unit $spec.Unit
        Delta    = Format-DeltaValue -Value $deltaValue -Unit $spec.Unit
        DeltaPct = Format-DeltaPercent -Baseline $baselineValue -After $afterValue
    }
}

$comparisonCsvPath = Join-Path $ResultsDir "comparison.csv"
$comparisonTxtPath = Join-Path $ResultsDir "comparison.txt"

$comparisonRows | Export-Csv -NoTypeInformation -Encoding utf8 -Path $comparisonCsvPath
$comparisonTable = $comparisonRows | Format-Table -AutoSize | Out-String
Set-Content -Path $comparisonTxtPath -Value $comparisonTable

Write-Host ""
Write-Host ("{0} comparison summary" -f $Payload)
Write-Host $comparisonTable
Write-Host ("Saved summary exports to {0} and {1}" -f $baseline.SummaryPath, $after.SummaryPath)
Write-Host ("Saved comparison report to {0}" -f $comparisonTxtPath)
