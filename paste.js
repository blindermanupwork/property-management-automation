const vscode = require('vscode');
const fs = require('fs');
const path = require('path');
const os = require('os');

/**
 * @param {vscode.ExtensionContext} context
 */
function activate(context) {
    let disposable = vscode.commands.registerCommand('claude-image-paste.pasteImage', async () => {
        try {
            // Check platform support
            const platform = getPlatform();
            if (!platform) {
                vscode.window.showErrorMessage(
                    'Claude Image Paste: Only supported on Windows and WSL environments'
                );
                return;
            }

            // Check for active terminal
            const activeTerminal = vscode.window.activeTerminal;
            if (!activeTerminal) {
                vscode.window.showErrorMessage(
                    'Claude Image Paste: No active terminal found. Please open a terminal first.'
                );
                return;
            }

            // Show progress notification
            vscode.window.withProgress({
                location: vscode.ProgressLocation.Notification,
                title: 'Retrieving image from clipboard...',
                cancellable: false
            }, async (progress) => {
                try {
                    const imagePath = await getImageFromClipboard(platform);
                    
                    if (imagePath) {
                        // Convert path if needed and insert
                        const pathToInsert = convertPathForTerminal(imagePath, platform, activeTerminal);
                        activeTerminal.sendText(pathToInsert, false);
                        
                        // Show success with file info
                        const stats = fs.statSync(imagePath);
                        const sizeKB = Math.round(stats.size / 1024);
                        vscode.window.showInformationMessage(
                            `Claude Image Paste: Inserted ${path.basename(imagePath)} (${sizeKB}KB)`
                        );
                    }
                } catch (error) {
                    throw error;
                }
            });
            
        } catch (error) {
            vscode.window.showErrorMessage(
                `Claude Image Paste: ${error.message}`
            );
        }
    });

    context.subscriptions.push(disposable);
}

/**
 * Determine the current platform
 * @returns {string|null} 'windows', 'wsl', or null if unsupported
 */
function getPlatform() {
    if (process.platform === 'win32') {
        return 'windows';
    }
    if (process.platform === 'linux' && fs.existsSync('/mnt/c/Windows')) {
        return 'wsl';
    }
    return null;
}

/**
 * Get image from clipboard using PowerShell
 * @param {string} platform - 'windows' or 'wsl'
 * @returns {Promise<string>} Path to the saved image
 */
async function getImageFromClipboard(platform) {
    const psScript = `
$ErrorActionPreference = 'Stop'
try {
    Add-Type -AssemblyName System.Windows.Forms
    Add-Type -AssemblyName System.Drawing
} catch {
    Write-Error "Failed to load required .NET assemblies. Ensure .NET Framework is installed."
    exit 1
}

# First check if there's a file list in clipboard
$files = [System.Windows.Forms.Clipboard]::GetFileDropList()
if ($files -and $files.Count -gt 0) {
    $sourceFile = $files[0]
    
    if (-not (Test-Path $sourceFile)) {
        Write-Error "Source file not found: $sourceFile"
        exit 1
    }
    
    # Check if it's an image file
    $imageExtensions = @('.png', '.jpg', '.jpeg', '.gif', '.bmp', '.webp', '.svg', '.ico', '.tiff', '.tif')
    $extension = [System.IO.Path]::GetExtension($sourceFile).ToLower()
    
    if ($imageExtensions -contains $extension) {
        # Copy the file to temp location, preserving extension
        $tempPath = [System.IO.Path]::Combine([System.IO.Path]::GetTempPath(), "claude_paste$extension")
        try {
            Copy-Item -Path $sourceFile -Destination $tempPath -Force -ErrorAction Stop
            Write-Output $tempPath
            exit 0
        } catch {
            Write-Error "Failed to copy file: $_"
            exit 1
        }
    } else {
        Write-Error "Clipboard contains a non-image file: $sourceFile"
        exit 1
    }
}

# If no files, check for clipboard image
try {
    $image = [System.Windows.Forms.Clipboard]::GetImage()
    if ($image -eq $null) {
        Write-Error "No image found in clipboard. Copy an image or image file and try again."
        exit 1
    }
    
    $tempPath = [System.IO.Path]::Combine([System.IO.Path]::GetTempPath(), "claude_paste.png")
    $image.Save($tempPath, [System.Drawing.Imaging.ImageFormat]::Png)
    $image.Dispose()
    Write-Output $tempPath
} catch {
    Write-Error "Failed to save clipboard image: $_"
    exit 1
}
    `.trim();

    const { exec } = require('child_process');
    const util = require('util');
    const execPromise = util.promisify(exec);

    // Build command based on platform
    let command;
    if (platform === 'wsl') {
        // From WSL, escape properly for bash
        const escapedScript = psScript
            .replace(/\$/g, '\\$')
            .replace(/"/g, '\\"')
            .replace(/`/g, '\\`');
        command = `pwsh.exe -NoProfile -Command "${escapedScript}"`;
    } else {
        // From Windows
        const escapedScript = psScript.replace(/"/g, '\\"');
        command = `pwsh -NoProfile -Command "${escapedScript}"`;
    }

    const { stdout, stderr } = await execPromise(command, {
        timeout: 10000 // 10 second timeout
    });
    
    if (stderr) {
        throw new Error(stderr.trim());
    }

    return stdout.trim();
}

/**
 * Convert Windows path to appropriate format for the terminal
 * @param {string} windowsPath - The Windows path
 * @param {string} platform - 'windows' or 'wsl'
 * @param {vscode.Terminal} terminal - The active terminal
 * @returns {string} The converted path
 */
function convertPathForTerminal(windowsPath, platform, terminal) {
    // If we're in WSL or the terminal is WSL, convert to WSL path
    if (platform === 'wsl' || 
        (terminal.name && terminal.name.toLowerCase().includes('wsl'))) {
        return windowsPath
            .replace(/\\/g, '/')
            .replace(/^([A-Z]):/, (match, drive) => `/mnt/${drive.toLowerCase()}`);
    }
    
    // Otherwise return Windows path as-is
    return windowsPath;
}

function deactivate() {}

module.exports = {
    activate,
    deactivate
}
