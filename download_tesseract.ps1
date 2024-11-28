$tesseractUrl = "https://digi.bib.uni-mannheim.de/tesseract/tesseract-ocr-w64-setup-5.3.1.20230401.exe"
$installerPath = "$env:TEMP\tesseract-installer.exe"

Write-Host "Downloading Tesseract OCR installer..."
Invoke-WebRequest -Uri $tesseractUrl -OutFile $installerPath

Write-Host "Running installer..."
Start-Process -FilePath $installerPath -Wait

Write-Host "Installation complete!"
