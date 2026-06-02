# GUI versie van git_quickpush - kies een git-projectmap en push naar GitHub
Add-Type -AssemblyName System.Windows.Forms
Add-Type -AssemblyName System.Drawing

$script:SettingsPath = Join-Path $PSScriptRoot "git_quickpush_gui.settings.json"
$script:LastGitOutput = @()

function Load-GuiSettings {
    if (-not (Test-Path $script:SettingsPath)) {
        return @{}
    }

    try {
        $raw = Get-Content -Path $script:SettingsPath -Raw -ErrorAction Stop
        if ([string]::IsNullOrWhiteSpace($raw)) {
            return @{}
        }

        $data = ConvertFrom-Json -InputObject $raw -ErrorAction Stop
        if ($null -eq $data) {
            return @{}
        }

        return @{
            GitHubUsername = [string]$data.GitHubUsername
        }
    } catch {
        return @{}
    }
}

function Save-GuiSettings {
    param([string]$GitHubUsername)

    $payload = @{
        GitHubUsername = $GitHubUsername
    }

    $json = $payload | ConvertTo-Json
    Set-Content -Path $script:SettingsPath -Value $json -Encoding UTF8
}

# ─── Hulpfunctie: tekst toevoegen aan logvenster ───────────────────────────
function Write-Log {
    param([string]$Text, [System.Drawing.Color]$Color = [System.Drawing.Color]::White)
    $txtLog.SelectionStart = $txtLog.TextLength
    $txtLog.SelectionLength = 0
    $txtLog.SelectionColor = $Color
    $txtLog.AppendText("$Text`r`n")
    $txtLog.ScrollToCaret()
    $form.Refresh()
}

# ─── Hulpfunctie: git-commando uitvoeren en output loggen ──────────────────
function Invoke-Git {
    param([string[]]$GitArgs)
    $result = & git @GitArgs 2>&1
    $script:LastGitOutput = @($result)
    foreach ($line in $result) {
        $color = if ($line -match '^error:|^fatal:') { [System.Drawing.Color]::Salmon }
                 elseif ($line -match '^hint:') { [System.Drawing.Color]::SkyBlue }
                 else { [System.Drawing.Color]::LightGray }
        Write-Log "  $line" $color
    }
    return $LASTEXITCODE
}

function Handle-PushFailure {
    param([string]$OriginUrl)

    $outputText = ($script:LastGitOutput | ForEach-Object { [string]$_ }) -join "`n"
    if ($outputText -match "Repository not found|repository .* not found") {
        Write-Log "`nGitHub-repository niet gevonden. Waarschijnlijk bestaat de repo nog niet op GitHub." ([System.Drawing.Color]::Salmon)

        if (-not [string]::IsNullOrWhiteSpace($OriginUrl)) {
            Write-Log "Maak deze repository eerst aan op GitHub:" ([System.Drawing.Color]::Khaki)
            Write-Log "  $OriginUrl" ([System.Drawing.Color]::Khaki)

            $repoName = $null
            if ($OriginUrl -match "https://github\.com/[^/]+/([^/]+?)(?:\.git)?/?$") {
                $repoName = $Matches[1]
            }

            $newRepoUrl = "https://github.com/new"
            if (-not [string]::IsNullOrWhiteSpace($repoName)) {
                $encodedName = [System.Uri]::EscapeDataString($repoName)
                $newRepoUrl = "https://github.com/new?name=$encodedName"
            }

            $openNow = [System.Windows.Forms.MessageBox]::Show(
                "Repository niet gevonden op GitHub.`n`nWil je nu de GitHub pagina openen om de repo aan te maken?",
                "Repository Niet Gevonden",
                [System.Windows.Forms.MessageBoxButtons]::YesNo,
                [System.Windows.Forms.MessageBoxIcon]::Information
            )

            if ($openNow -eq [System.Windows.Forms.DialogResult]::Yes) {
                try {
                    Start-Process $newRepoUrl | Out-Null
                    Write-Log "GitHub aanmaakpagina geopend: $newRepoUrl" ([System.Drawing.Color]::Khaki)
                } catch {
                    Write-Log "Kon browser niet openen. Open handmatig: $newRepoUrl" ([System.Drawing.Color]::Khaki)
                }
            }
        }

        return
    }

    Write-Log "`nPush mislukt! Controleer remote URL, branch en rechten." ([System.Drawing.Color]::Salmon)
}

function Get-GitRepoRoot {
    param([string]$StartPath)

    if ([string]::IsNullOrWhiteSpace($StartPath) -or -not (Test-Path $StartPath)) {
        return $null
    }

    $resolvedPath = (Resolve-Path $StartPath).Path
    $result = & git -C $resolvedPath rev-parse --show-toplevel 2>$null
    if ($LASTEXITCODE -eq 0 -and $result) {
        return ($result | Select-Object -First 1).Trim()
    }

    return $null
}

function Get-GitOriginUrl {
    param([string]$RepoPath)

    $result = & git -C $RepoPath remote get-url origin 2>$null
    if ($LASTEXITCODE -eq 0 -and $result) {
        return ($result | Select-Object -First 1).Trim()
    }

    return $null
}

function Get-CurrentBranchName {
    param([string]$RepoPath)

    $result = & git -C $RepoPath branch --show-current 2>$null
    if ($LASTEXITCODE -eq 0 -and $result) {
        $branchName = ($result | Select-Object -First 1).Trim()
        if (-not [string]::IsNullOrWhiteSpace($branchName)) {
            return $branchName
        }
    }

    return $null
}

function Get-RemoteDefaultBranch {
    param([string]$RepoPath)

    $result = & git -C $RepoPath ls-remote --symref origin HEAD 2>$null
    if ($LASTEXITCODE -ne 0 -or -not $result) {
        return $null
    }

    foreach ($line in $result) {
        if ($line -match '^ref:\s+refs/heads/(?<branch>[^\s]+)\s+HEAD$') {
            return $Matches.branch.Trim()
        }
    }

    return $null
}

function Resolve-PushBranch {
    param([string]$RepoPath)

    $currentBranch = Get-CurrentBranchName -RepoPath $RepoPath
    if ([string]::IsNullOrWhiteSpace($currentBranch)) {
        $currentBranch = "master"
    }

    $remoteDefaultBranch = Get-RemoteDefaultBranch -RepoPath $RepoPath
    $pushBranch = $currentBranch
    if (-not [string]::IsNullOrWhiteSpace($remoteDefaultBranch)) {
        $pushBranch = $remoteDefaultBranch
    }

    return @{
        CurrentBranch = $currentBranch
        PushBranch = $pushBranch
    }
}

function Initialize-GitRepository {
    param([string]$RepoPath)

    Write-Log "`nNieuwe git-repository initialiseren in:" ([System.Drawing.Color]::Cyan)
    Write-Log "  $RepoPath" ([System.Drawing.Color]::Cyan)

    $exitCode = Invoke-Git -GitArgs @("init")
    if ($exitCode -ne 0) {
        Write-Log "`nGit init mislukt." ([System.Drawing.Color]::Salmon)
        return $false
    }

    return $true
}

function Ensure-DefaultGitIgnore {
    param([string]$RepoPath)

    $gitIgnorePath = Join-Path $RepoPath ".gitignore"

    $requiredRules = @(
        "__pycache__/"
        "*.py[cod]"
        "*.pyo"
        "*.pyd"
        ".venv/"
        "venv/"
        "env/"
        "build/"
        "dist/"
        "*.spec"
        ".pytest_cache/"
        ".mypy_cache/"
        ".ruff_cache/"
        ".DS_Store"
        "Thumbs.db"
    )

    if (-not (Test-Path $gitIgnorePath)) {
        $defaultGitIgnore = @(
            "# Python"
            "__pycache__/"
            "*.py[cod]"
            "*.pyo"
            "*.pyd"
            ""
            "# Virtual environments"
            ".venv/"
            "venv/"
            "env/"
            ""
            "# Build artifacts"
            "build/"
            "dist/"
            "*.spec"
            ""
            "# Tool caches"
            ".pytest_cache/"
            ".mypy_cache/"
            ".ruff_cache/"
            ""
            "# OS"
            ".DS_Store"
            "Thumbs.db"
        )

        Set-Content -Path $gitIgnorePath -Value $defaultGitIgnore -Encoding UTF8
        Write-Log "`.gitignore aangemaakt met standaard Python-regels." ([System.Drawing.Color]::Khaki)
        return
    }

    $existingLines = Get-Content -Path $gitIgnorePath -ErrorAction SilentlyContinue
    $existingRules = @{}
    foreach ($line in $existingLines) {
        $normalized = $line.Trim()
        if (-not [string]::IsNullOrWhiteSpace($normalized) -and -not $normalized.StartsWith("#")) {
            $existingRules[$normalized] = $true
        }
    }

    $missingRules = @()
    foreach ($rule in $requiredRules) {
        if (-not $existingRules.ContainsKey($rule)) {
            $missingRules += $rule
        }
    }

    if ($missingRules.Count -gt 0) {
        Add-Content -Path $gitIgnorePath -Value ""
        Add-Content -Path $gitIgnorePath -Value "# Added by Git Quick Push"
        Add-Content -Path $gitIgnorePath -Value $missingRules
        Write-Log "`.gitignore aangevuld met ontbrekende standaardregels." ([System.Drawing.Color]::Khaki)
    }
}

# ─── Formulier bouwen ──────────────────────────────────────────────────────
$form = New-Object System.Windows.Forms.Form
$form.Text = "Git Quick Push"
$form.Size = New-Object System.Drawing.Size(660, 560)
$form.StartPosition = "CenterScreen"
$form.BackColor = [System.Drawing.Color]::FromArgb(30, 30, 30)
$form.ForeColor = [System.Drawing.Color]::White
$form.Font = New-Object System.Drawing.Font("Segoe UI", 10)
$form.FormBorderStyle = "FixedDialog"
$form.MaximizeBox = $false

# Label: Projectmap
$lblFolder = New-Object System.Windows.Forms.Label
$lblFolder.Text = "Git-projectmap:"
$lblFolder.Location = New-Object System.Drawing.Point(15, 15)
$lblFolder.Size = New-Object System.Drawing.Size(120, 22)
$form.Controls.Add($lblFolder)

# Tekstveld: pad naar map
$txtFolder = New-Object System.Windows.Forms.TextBox
$txtFolder.Location = New-Object System.Drawing.Point(140, 13)
$txtFolder.Size = New-Object System.Drawing.Size(390, 24)
$txtFolder.BackColor = [System.Drawing.Color]::FromArgb(45, 45, 48)
$txtFolder.ForeColor = [System.Drawing.Color]::White
$txtFolder.BorderStyle = "FixedSingle"
$form.Controls.Add($txtFolder)

# Knop: map kiezen
$btnBrowse = New-Object System.Windows.Forms.Button
$btnBrowse.Text = "Bladeren..."
$btnBrowse.Location = New-Object System.Drawing.Point(545, 11)
$btnBrowse.Size = New-Object System.Drawing.Size(90, 28)
$btnBrowse.BackColor = [System.Drawing.Color]::FromArgb(60, 60, 60)
$btnBrowse.FlatStyle = "Flat"
$btnBrowse.Add_Click({
    $dlg = New-Object System.Windows.Forms.FolderBrowserDialog
    $dlg.Description = "Kies de hoofdmap van je git-project"
    $dlg.RootFolder = [System.Environment+SpecialFolder]::MyComputer
    $dlg.SelectedPath = "C:\"
    if ($dlg.ShowDialog() -eq "OK") {
        $txtFolder.Text = $dlg.SelectedPath
    }
})
$form.Controls.Add($btnBrowse)

# Label: Commit message
$lblMsg = New-Object System.Windows.Forms.Label
$lblMsg.Text = "Commit message:"
$lblMsg.Location = New-Object System.Drawing.Point(15, 55)
$lblMsg.Size = New-Object System.Drawing.Size(120, 22)
$form.Controls.Add($lblMsg)

# Tekstveld: commit message
$txtMsg = New-Object System.Windows.Forms.TextBox
$txtMsg.Location = New-Object System.Drawing.Point(140, 53)
$txtMsg.Size = New-Object System.Drawing.Size(495, 24)
$txtMsg.BackColor = [System.Drawing.Color]::FromArgb(45, 45, 48)
$txtMsg.ForeColor = [System.Drawing.Color]::White
$txtMsg.BorderStyle = "FixedSingle"
$form.Controls.Add($txtMsg)

# Label: GitHub gebruikersnaam
$lblUser = New-Object System.Windows.Forms.Label
$lblUser.Text = "GitHub gebruiker:"
$lblUser.Location = New-Object System.Drawing.Point(15, 95)
$lblUser.Size = New-Object System.Drawing.Size(120, 22)
$form.Controls.Add($lblUser)

# Tekstveld: GitHub gebruikersnaam (persistent)
$txtUser = New-Object System.Windows.Forms.TextBox
$txtUser.Location = New-Object System.Drawing.Point(140, 93)
$txtUser.Size = New-Object System.Drawing.Size(495, 24)
$txtUser.BackColor = [System.Drawing.Color]::FromArgb(45, 45, 48)
$txtUser.ForeColor = [System.Drawing.Color]::White
$txtUser.BorderStyle = "FixedSingle"
$form.Controls.Add($txtUser)

# Label: GitHub remote URL
$lblRemote = New-Object System.Windows.Forms.Label
$lblRemote.Text = "GitHub URL (optioneel):"
$lblRemote.Location = New-Object System.Drawing.Point(15, 135)
$lblRemote.Size = New-Object System.Drawing.Size(120, 22)
$form.Controls.Add($lblRemote)

# Tekstveld: GitHub remote URL
$txtRemote = New-Object System.Windows.Forms.TextBox
$txtRemote.Location = New-Object System.Drawing.Point(140, 133)
$txtRemote.Size = New-Object System.Drawing.Size(495, 24)
$txtRemote.BackColor = [System.Drawing.Color]::FromArgb(45, 45, 48)
$txtRemote.ForeColor = [System.Drawing.Color]::White
$txtRemote.BorderStyle = "FixedSingle"
$txtRemote.Text = "https://github.com/"
$form.Controls.Add($txtRemote)

# Checkbox: force push
$chkForce = New-Object System.Windows.Forms.CheckBox
$chkForce.Text = "Force push (--force) — gebruik alleen als jij de enige ontwikkelaar bent"
$chkForce.Location = New-Object System.Drawing.Point(15, 170)
$chkForce.Size = New-Object System.Drawing.Size(620, 22)
$chkForce.ForeColor = [System.Drawing.Color]::Orange
$form.Controls.Add($chkForce)

# Knop: Push uitvoeren
$btnPush = New-Object System.Windows.Forms.Button
$btnPush.Text = "Commit && Push naar GitHub"
$btnPush.Location = New-Object System.Drawing.Point(15, 202)
$btnPush.Size = New-Object System.Drawing.Size(620, 34)
$btnPush.BackColor = [System.Drawing.Color]::FromArgb(0, 122, 204)
$btnPush.ForeColor = [System.Drawing.Color]::White
$btnPush.FlatStyle = "Flat"
$btnPush.Font = New-Object System.Drawing.Font("Segoe UI", 10, [System.Drawing.FontStyle]::Bold)
$form.Controls.Add($btnPush)

# Logvenster
$txtLog = New-Object System.Windows.Forms.RichTextBox
$txtLog.Location = New-Object System.Drawing.Point(15, 248)
$txtLog.Size = New-Object System.Drawing.Size(620, 240)
$txtLog.BackColor = [System.Drawing.Color]::FromArgb(20, 20, 20)
$txtLog.ForeColor = [System.Drawing.Color]::LightGray
$txtLog.ReadOnly = $true
$txtLog.BorderStyle = "FixedSingle"
$txtLog.Font = New-Object System.Drawing.Font("Consolas", 9)
$txtLog.ScrollBars = "Vertical"
$form.Controls.Add($txtLog)

# Knop: log wissen
$btnClear = New-Object System.Windows.Forms.Button
$btnClear.Text = "Log wissen"
$btnClear.Location = New-Object System.Drawing.Point(15, 498)
$btnClear.Size = New-Object System.Drawing.Size(100, 26)
$btnClear.BackColor = [System.Drawing.Color]::FromArgb(60, 60, 60)
$btnClear.FlatStyle = "Flat"
$btnClear.Add_Click({ $txtLog.Clear() })
$form.Controls.Add($btnClear)

# Knop: sluiten
$btnClose = New-Object System.Windows.Forms.Button
$btnClose.Text = "Sluiten"
$btnClose.Location = New-Object System.Drawing.Point(535, 498)
$btnClose.Size = New-Object System.Drawing.Size(100, 26)
$btnClose.BackColor = [System.Drawing.Color]::FromArgb(60, 60, 60)
$btnClose.FlatStyle = "Flat"
$btnClose.Add_Click({ $form.Close() })
$form.Controls.Add($btnClose)

# Vul automatisch de huidige map in als die een git-repo is
$currentDir = Get-Location
if (Test-Path (Join-Path $currentDir ".git")) {
    $txtFolder.Text = $currentDir.Path
}

# Laad persistente GUI-instellingen
$guiSettings = Load-GuiSettings
if ($guiSettings.ContainsKey("GitHubUsername")) {
    $txtUser.Text = $guiSettings.GitHubUsername
}

# ─── Push-logica ───────────────────────────────────────────────────────────
$btnPush.Add_Click({
    $txtLog.Clear()
    $projectPath = $txtFolder.Text.Trim()
    $commitMsg   = $txtMsg.Text.Trim()
    $githubUserInput = $txtUser.Text.Trim()
    $remoteUrlInput = $txtRemote.Text.Trim()
    $forcePush   = $chkForce.Checked
    $repoRoot    = $null
    $isNewRepo   = $false
    $originUrl   = $null

    # Validaties
    if ([string]::IsNullOrWhiteSpace($projectPath)) {
        Write-Log "Fout: kies eerst een projectmap." ([System.Drawing.Color]::Salmon)
        return
    }
    $repoRoot = Get-GitRepoRoot -StartPath $projectPath
    if (-not $repoRoot) {
        if (-not (Test-Path $projectPath)) {
            Write-Log "Fout: '$projectPath' bestaat niet." ([System.Drawing.Color]::Salmon)
            return
        }

        $answer = [System.Windows.Forms.MessageBox]::Show(
            "Deze map is nog geen git-repository.`n`nWil je hier automatisch een nieuwe git-repository aanmaken?",
            "Nieuwe Git-repository",
            [System.Windows.Forms.MessageBoxButtons]::YesNo,
            [System.Windows.Forms.MessageBoxIcon]::Question
        )

        if ($answer -ne [System.Windows.Forms.DialogResult]::Yes) {
            Write-Log "Actie geannuleerd: geen bestaande git-repository gevonden." ([System.Drawing.Color]::Yellow)
            return
        }

        $repoRoot = $projectPath
        $isNewRepo = $true
    }
    if ($remoteUrlInput -eq "https://github.com/") {
        $remoteUrlInput = ""
    }

    # Gebruikersnaam persistent opslaan
    try {
        Save-GuiSettings -GitHubUsername $githubUserInput
    } catch {
        Write-Log "Kon gebruikersnaam niet opslaan in instellingen." ([System.Drawing.Color]::Khaki)
    }

    if ($repoRoot -ne $projectPath) {
        Write-Log "Gekozen map ligt binnen git-repository:" ([System.Drawing.Color]::Khaki)
        Write-Log "  $repoRoot" ([System.Drawing.Color]::Khaki)
        $txtFolder.Text = $repoRoot
    }

    # Navigeer naar projectmap
    Push-Location $repoRoot
    try {
        if ([string]::IsNullOrWhiteSpace($remoteUrlInput) -and -not [string]::IsNullOrWhiteSpace($githubUserInput)) {
            $repoName = Split-Path -Path $repoRoot -Leaf
            if (-not [string]::IsNullOrWhiteSpace($repoName)) {
                $remoteUrlInput = "https://github.com/$githubUserInput/$repoName.git"
                Write-Log "GitHub URL automatisch opgebouwd:" ([System.Drawing.Color]::Khaki)
                Write-Log "  $remoteUrlInput" ([System.Drawing.Color]::Khaki)
                $txtRemote.Text = $remoteUrlInput
            }
        }

        if ($isNewRepo) {
            if (-not (Initialize-GitRepository -RepoPath $repoRoot)) {
                return
            }

            if (-not [string]::IsNullOrWhiteSpace($remoteUrlInput)) {
                Write-Log "`nOrigin remote instellen..." ([System.Drawing.Color]::Cyan)
                $exitCode = Invoke-Git -GitArgs @("remote", "add", "origin", $remoteUrlInput)
                if ($exitCode -ne 0) {
                    Write-Log "`nOrigin remote kon niet ingesteld worden." ([System.Drawing.Color]::Salmon)
                    return
                }
                $originUrl = $remoteUrlInput
            }
        }

        Ensure-DefaultGitIgnore -RepoPath $repoRoot

        # VS Code Save All
        $codeCmd = Get-Command code -ErrorAction SilentlyContinue
        if ($codeCmd) {
            Write-Log "VS Code Save All triggeren..." ([System.Drawing.Color]::Cyan)
            & $codeCmd.Source --reuse-window --command workbench.action.files.saveAll 2>$null
            Start-Sleep -Milliseconds 800
        }

        # Git status
        Write-Log "`nHuidige git status:" ([System.Drawing.Color]::Cyan)
        Invoke-Git -GitArgs @("status", "--short") | Out-Null

        # Alles toevoegen
        Write-Log "`nBestanden toevoegen..." ([System.Drawing.Color]::Cyan)
        Invoke-Git -GitArgs @("add", "-A") | Out-Null

        # Controleer of er iets te committen is
        $staged = & git diff --cached --name-only 2>&1
        if (-not $staged) {
            # Geen nieuwe commit nodig; probeer wel eerste push te doen indien mogelijk.
            $originUrl = Get-GitOriginUrl -RepoPath $repoRoot
            if ([string]::IsNullOrWhiteSpace($originUrl) -and -not [string]::IsNullOrWhiteSpace($remoteUrlInput)) {
                Write-Log "`nOrigin remote instellen..." ([System.Drawing.Color]::Cyan)
                $exitCode = Invoke-Git -GitArgs @("remote", "add", "origin", $remoteUrlInput)
                if ($exitCode -ne 0) {
                    Write-Log "`nOrigin remote kon niet ingesteld worden." ([System.Drawing.Color]::Salmon)
                    return
                }
                $originUrl = Get-GitOriginUrl -RepoPath $repoRoot
            }

            if (-not [string]::IsNullOrWhiteSpace($originUrl)) {
                $hasHead = & git rev-parse --verify HEAD 2>$null
                if ($LASTEXITCODE -ne 0) {
                    Write-Log "`nGeen commit gevonden om te pushen. Maak eerst een eerste commit." ([System.Drawing.Color]::Khaki)
                    return
                }

                $pushBranchInfo = Resolve-PushBranch -RepoPath $repoRoot
                $currentBranch = $pushBranchInfo.CurrentBranch
                $pushBranch = $pushBranchInfo.PushBranch

                if ($currentBranch -ne $pushBranch) {
                    Write-Log "`nLokale branch wordt aangepast naar: $pushBranch" ([System.Drawing.Color]::Khaki)
                    $exitCode = Invoke-Git -GitArgs @("branch", "-M", $pushBranch)
                    if ($exitCode -ne 0) {
                        Write-Log "`nBranch kon niet worden aangepast naar $pushBranch." ([System.Drawing.Color]::Salmon)
                        return
                    }
                }

                Write-Log "`nGeen nieuwe wijzigingen, maar bestaande commits worden gepusht..." ([System.Drawing.Color]::Cyan)
                if ($forcePush) {
                    $exitCode = Invoke-Git -GitArgs @("push", "--force", "-u", "origin", $pushBranch)
                } else {
                    $exitCode = Invoke-Git -GitArgs @("push", "-u", "origin", $pushBranch)
                }

                if ($exitCode -ne 0) {
                    Handle-PushFailure -OriginUrl $originUrl
                } else {
                    Write-Log "`nKlaar! Bestaande commit(s) staan nu op GitHub." ([System.Drawing.Color]::LightGreen)
                    $txtMsg.Clear()
                }
                return
            }

            Write-Log "`nGeen wijzigingen om te committen. Vul een GitHub URL in om een eerste push te doen." ([System.Drawing.Color]::Yellow)
            return
        }

        if ([string]::IsNullOrWhiteSpace($commitMsg)) {
            Write-Log "Fout: vul een commit message in." ([System.Drawing.Color]::Salmon)
            return
        }

        Write-Log "`nTe committen bestanden:" ([System.Drawing.Color]::Cyan)
        Invoke-Git -GitArgs @("diff", "--cached", "--name-status") | Out-Null

        # Commit
        Write-Log "`nCommitten..." ([System.Drawing.Color]::Cyan)
        $exitCode = Invoke-Git -GitArgs @("commit", "-m", $commitMsg)
        if ($exitCode -ne 0) {
            Write-Log "`nCommit mislukt." ([System.Drawing.Color]::Salmon)
            return
        }

        # Push
        $originUrl = Get-GitOriginUrl -RepoPath $repoRoot
        if ([string]::IsNullOrWhiteSpace($originUrl) -and -not [string]::IsNullOrWhiteSpace($remoteUrlInput) -and -not $isNewRepo) {
            Write-Log "`nOrigin remote instellen..." ([System.Drawing.Color]::Cyan)
            $exitCode = Invoke-Git -GitArgs @("remote", "add", "origin", $remoteUrlInput)
            if ($exitCode -ne 0) {
                Write-Log "`nOrigin remote kon niet ingesteld worden." ([System.Drawing.Color]::Salmon)
                return
            }
            $originUrl = Get-GitOriginUrl -RepoPath $repoRoot
        }

        if (-not [string]::IsNullOrWhiteSpace($originUrl)) {
            $pushBranchInfo = Resolve-PushBranch -RepoPath $repoRoot
            $currentBranch = $pushBranchInfo.CurrentBranch
            $pushBranch = $pushBranchInfo.PushBranch

            Write-Log "`nPushen naar GitHub..." ([System.Drawing.Color]::Cyan)
            if ($currentBranch -ne $pushBranch) {
                Write-Log "Lokale branch wordt aangepast naar: $pushBranch" ([System.Drawing.Color]::Khaki)
                $exitCode = Invoke-Git -GitArgs @("branch", "-M", $pushBranch)
                if ($exitCode -ne 0) {
                    Write-Log "`nBranch kon niet worden aangepast naar $pushBranch." ([System.Drawing.Color]::Salmon)
                    return
                }
            }

            if ($forcePush) {
                $exitCode = Invoke-Git -GitArgs @("push", "--force", "-u", "origin", $pushBranch)
            } else {
                $exitCode = Invoke-Git -GitArgs @("push", "-u", "origin", $pushBranch)
            }

            if ($exitCode -ne 0) {
                Handle-PushFailure -OriginUrl $originUrl
            } else {
                Write-Log "`nKlaar! Je wijzigingen staan nu op GitHub." ([System.Drawing.Color]::LightGreen)
                $txtMsg.Clear()
            }
        } else {
            Write-Log "`nGeen origin remote gevonden. Commit is lokaal aangemaakt, maar nog niet gepusht." ([System.Drawing.Color]::Khaki)
            $txtMsg.Clear()
        }
    } finally {
        Pop-Location
    }
})

# ─── Formulier tonen ───────────────────────────────────────────────────────
[void]$form.ShowDialog()
