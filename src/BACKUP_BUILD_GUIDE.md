# MKVApp Backup & Build Handleiding

## 🔄 Backup maken

### Optie 1: Via BAT bestand (Eenvoudig)
Dubbelklik op: `create_backup.bat`

### Optie 2: Via PowerShell (Meer opties)
```powershell
# Standaard backup (zonder virtual environment)
.\create_backup.ps1

# Inclusief virtual environment (grotere backup)
.\create_backup.ps1 -IncludeVenv

# Aangepaste backup locatie
.\create_backup.ps1 -BackupDir "D:\Mijn_Backups"
```

### Backup locatie
Backups worden standaard opgeslagen in:
- `C:\Python_W_new\Backups\`
- Bestandsnaam: `MKVApp_Source_YYYY-MM-DD_HHMMSS.zip`

### Wat wordt er gebackupt?
✅ Alle Python source code (.py bestanden)
✅ PyInstaller spec file (MKVApp.spec)
✅ Build scripts (.bat, .sh)
✅ Settings folder met alle configuraties
✅ Requirements.txt met dependencies
✅ Documentatie bestanden
✅ Alle modules: actions, binding, config, menus, mkvapp, utils, widgets
❌ Virtual environment (tenzij -IncludeVenv gebruikt wordt)
❌ Build artifacts (dist, build folders)
❌ __pycache__ folders

---

## 🔨 Portable EXE maken

### Stap 1: Zorg dat dependencies geïnstalleerd zijn
```powershell
# Activeer virtual environment
.\.venv\Scripts\Activate.ps1

# Installeer/update dependencies
pip install -r requirements.txt

# Installeer PyInstaller (als nog niet geïnstalleerd)
pip install pyinstaller
```

### Stap 2: Build de portable EXE
Dubbelklik op: `create_portable.bat`

Of via command line:
```cmd
create_portable.bat
```

### Output
De portable distributie wordt aangemaakt in:
- `C:\Python_W_new\MKVApp_Portable\`

Inclusief:
- `MKVApp.exe` - De executable
- `Settings\` - Alle configuratie bestanden
- `Start_MKVApp.bat` - Launcher script
- `README.txt` - Gebruikersinstructies

---

## ♻️ Backup terugzetten

### Stap 1: Extract de backup
Pak de `.zip` backup uit naar gewenste locatie, bijvoorbeeld:
- `C:\Python_W_new\project_restored\`

### Stap 2: Maak nieuwe virtual environment
```powershell
cd C:\Python_W_new\project_restored\src
python -m venv .venv
```

### Stap 3: Activeer en installeer dependencies
```powershell
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

### Stap 4: Test de applicatie
```powershell
python app_launcher.py
```

---

## 📋 Handige commando's

### Backup maken en direct testen
```powershell
.\create_backup.ps1
# Check laatste backup
Get-ChildItem C:\Python_W_new\Backups\ | Sort-Object LastWriteTime -Descending | Select-Object -First 1
```

### Oude backups opruimen (ouder dan 30 dagen)
```powershell
$BackupPath = "C:\Python_W_new\Backups"
$DaysToKeep = 30
Get-ChildItem $BackupPath -Filter "MKVApp_Source_*.zip" | 
    Where-Object { $_.LastWriteTime -lt (Get-Date).AddDays(-$DaysToKeep) } | 
    Remove-Item -Verbose
```

### Backup grootte checken
```powershell
$total = (Get-ChildItem C:\Python_W_new\Backups\MKVApp_Source_*.zip | Measure-Object -Property Length -Sum).Sum / 1GB
Write-Host "Totale backup grootte: $([math]::Round($total, 2)) GB"
```

---

## 🚨 Troubleshooting

### "PyInstaller not found"
```powershell
.\.venv\Scripts\Activate.ps1
pip install pyinstaller
```

### "Build failed" bij create_portable.bat
1. Check of alle dependencies geïnstalleerd zijn
2. Controleer `MKVApp.spec` op fouten
3. Run handmatig: `pyinstaller --clean MKVApp.spec`
4. Check output voor specifieke errors

### Backup script werkt niet
1. Zorg dat PowerShell execution policy toegestaan is:
   ```powershell
   Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
   ```
2. Of gebruik: `powershell -ExecutionPolicy Bypass -File create_backup.ps1`

---

## ✅ Best Practices

1. **Maak regelmatig backups:**
   - Voor grote wijzigingen
   - Na succesvolle tests
   - Voor het distribueren van exe

2. **Test de portable exe:**
   - Op schone machine zonder Python
   - Met verschillende video/subtitle bestanden
   - Check of alle features werken

3. **Bewaar backup info:**
   - Elke backup bevat `BACKUP_INFO.txt`
   - Documenteert datum, computer, gebruiker
   - Instructies voor restore

4. **Virtual environment:**
   - Standaard NIET in backup (scheelt ruimte)
   - Kan altijd opnieuw aangemaakt worden
   - Gebruik `-IncludeVenv` alleen voor volledige snapshot

---

## 📞 Snelle referentie

| Actie | Commando |
|-------|----------|
| Backup maken | `.\create_backup.bat` |
| EXE maken | `.\create_portable.bat` |
| App starten | `python app_launcher.py` |
| Dependencies installeren | `pip install -r requirements.txt` |
| Virtual env activeren | `.\.venv\Scripts\Activate.ps1` |
| Testen | `python -m pytest tests/` |

---

*Laatst bijgewerkt: 2026-02-07*
