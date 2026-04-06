$root = "c:\Users\jp_lopez\projects\abapobjectscreation"
$baseDir = Join-Path $root "extracted_code\UNESCO_CUSTOM_LOGIC"

$mapping = @{
    "FM_BUDGETING" = @("ZXFMDT*", "ZXFMYU*", "ZXFMCU*")
    "FM_MASTER_DATA" = @("ZXFMFUND*")
    "MM_PROCUREMENT" = @("ZXM06*")
    "PS_PROJECTS" = @("YJWB*", "ZXCN1*")
    "BI_REPORTING" = @("ZXRSA*")
    "TV_TRAVEL" = @("ZXTRV*")
    "FM_COCKPIT" = @("YFM_COCKPIT*")
}

foreach ($domain in $mapping.Keys) {
    $targetDir = Join-Path $baseDir $domain
    if (!(Test-Path $targetDir)) {
        New-Item -ItemType Directory -Path $targetDir -Force
    }
    
    foreach ($pattern in $mapping[$domain]) {
        $files = Get-ChildItem -Path $root -Filter $pattern -Include "*.abap"
        foreach ($file in $files) {
            $dest = Join-Path $targetDir $file.Name
            Move-Item -Path $file.FullName -Destination $dest -Force
            Write-Host "Moved $($file.Name) to $domain"
        }
    }
}
