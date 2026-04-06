$root = "c:\Users\jp_lopez\projects\abapobjectscreation"
$baseDir = Join-Path $root "extracted_code\UNESCO_CUSTOM_LOGIC"

$mapping = @{
    "FM_BUDGETING"     = @("ZXFMDT*_RPY.abap", "ZXFMYU*_RPY.abap", "ZXFMCU*_RPY.abap")
    "FM_MASTER_DATA"   = @("ZXFMFUND*_RPY.abap")
    "MM_PROCUREMENT"   = @("ZXM06*_RPY.abap")
    "PS_PROJECTS"      = @("YJWB001_RPY.abap", "ZXCN1U01_RPY.abap", "ZXCN1U21_RPY.abap", "ZXCN1U22_RPY.abap", "YCL_YPS8_BCS_BL*")
    "BI_REPORTING"     = @("ZXRSAU01_RPY.abap", "ZXRSAU02_RPY.abap")
    "TV_TRAVEL"        = @("ZXTRVU03_RPY.abap", "ZXTRVU05_RPY.abap")
    "FM_COCKPIT"       = @("YFM_COCKPIT*_RPY.abap", "YFM_COCKPITF01.abap", "YFM_COCKPITTOP.abap")
    "TECH_INTEGRATION" = @("YCL_SAP_TO_WORD*")
}

foreach ($domain in $mapping.Keys) {
    $targetDir = Join-Path $baseDir $domain
    if (!(Test-Path $targetDir)) {
        New-Item -ItemType Directory -Path $targetDir -Force
    }
    
    foreach ($pattern in $mapping[$domain]) {
        $files = Get-ChildItem -Path $root -Filter $pattern
        foreach ($file in $files) {
            $dest = Join-Path $targetDir $file.Name
            Move-Item -Path $file.FullName -Destination $dest -Force
            Write-Host "Moved $($file.Name) to $domain"
        }
    }
}
