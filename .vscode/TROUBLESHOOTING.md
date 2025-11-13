# VS Code Terminal "Relaunch Terminal" Troubleshooting Guide

## Problem Description

The persistent "relaunch terminal" prompt in VS Code or GitHub Codespaces occurs when extensions (particularly Claude Code and Git extensions) update environment variables, and the terminal needs to be refreshed to incorporate these changes.

## Root Cause

Extensions like Claude Code set environment variables for IDE integration. When the terminal is opened before extensions fully initialize, or when extensions update their environment contributions, the shell doesn't receive the necessary environment variables, triggering the relaunch prompt.

## Immediate Solutions

### 1. Relaunch the Terminal (Quickest Fix)

Simply click the "Relaunch Terminal" button in the prompt, or manually:
- Close the current terminal (click the trash icon)
- Open a new terminal (`Ctrl+Shift+\`` or `Cmd+Shift+\``)

### 2. Reload the VS Code Window

Press `Ctrl+Shift+P` (or `Cmd+Shift+P` on Mac), then:
- Type "Developer: Reload Window"
- Press Enter

This reloads all extensions and ensures the terminal gets the correct environment.

## Preventive Measures (Now Configured)

### VS Code Settings (`.vscode/settings.json`)

The following configurations have been added to help prevent this issue:

1. **Persistent Terminal Sessions**: Maintains terminal state across reloads
2. **Shell Integration**: Enables proper extension-to-terminal communication
3. **Python Environment Management**: Prevents conflicts with Python extension

### Dev Container Configuration (`.devcontainer/devcontainer.json`)

For GitHub Codespaces users, this ensures:
- Proper extension installation order
- Environment variables are set correctly on container creation
- Consistent shell configuration

## Long-term Resolution Steps

### Step 1: Ensure Extensions Are Up-to-Date

1. Open the Extensions panel (`Ctrl+Shift+X` or `Cmd+Shift+X`)
2. Check for updates to:
   - Claude Code for VS Code
   - Python
   - GitLens (if installed)
3. Update all extensions to the latest versions

### Step 2: Verify Settings Are Applied

1. Close all open terminals
2. Reload the VS Code window (`Ctrl+Shift+P` → "Developer: Reload Window")
3. Wait for all extensions to fully load (check the status bar)
4. Open a new terminal

### Step 3: For Codespaces Users

If you're using GitHub Codespaces:

1. **Rebuild Container** (most thorough):
   - Press `Ctrl+Shift+P` (or `Cmd+Shift+P`)
   - Type "Codespaces: Rebuild Container"
   - Select "Rebuild Container"
   - Wait for the rebuild to complete (this may take a few minutes)

2. **Restart Codespace** (quicker):
   - Go to https://github.com/codespaces
   - Find your codespace
   - Click "..." → "Stop codespace"
   - Start it again

### Step 4: Clear Extension Cache (If Issue Persists)

If the problem continues after the above steps:

```bash
# Clear npm cache (for Claude Code CLI)
npm cache clean --force

# Clear VS Code extension cache (in Codespaces)
rm -rf ~/.vscode-remote/extensions/*
```

Then reload the VS Code window.

## Checking Your Environment

To verify your environment is correctly configured, run:

```bash
env | grep -E "(CLAUDE|VSCODE|SHELL|TERM)" | sort
```

You should see variables like:
- `CLAUDECODE=1`
- `CLAUDE_CODE_ENTRYPOINT=cli`
- `VSCODE_GIT_ASKPASS_*` variables
- `TERM_PROGRAM=vscode`

## When to Report an Issue

If the problem persists after trying all these steps, report it with:

1. **VS Code version**: Help → About
2. **Extension versions**: Extensions panel → Show Installed Extensions
3. **Environment**: Local VS Code or GitHub Codespaces
4. **Terminal output**: Any error messages in the terminal
5. **Steps to reproduce**: What you were doing when the issue occurred

### Where to Report

- **Claude Code issues**: https://github.com/anthropics/claude-code/issues
- **VS Code issues**: https://github.com/microsoft/vscode/issues
- **Codespaces issues**: https://github.com/github/feedback/discussions/categories/codespaces-feedback

## Additional Tips

1. **Wait for Extensions to Load**: After opening VS Code, wait a few seconds before opening a terminal to ensure all extensions have initialized.

2. **Use Persistent Sessions**: The settings now enable persistent terminal sessions, which maintains your terminal state across window reloads.

3. **Check Extension Conflicts**: If you have many extensions installed, try disabling non-essential ones to identify conflicts.

4. **Regular Updates**: Keep your extensions and VS Code updated to benefit from bug fixes.

## Quick Reference Commands

```bash
# Check current environment variables
env | grep -E "(CLAUDE|VSCODE)" | sort

# Reload VS Code window (from command palette)
# Ctrl+Shift+P → "Developer: Reload Window"

# Rebuild Codespace (from command palette)
# Ctrl+Shift+P → "Codespaces: Rebuild Container"

# Clear npm cache
npm cache clean --force

# Check Python version and location
which python3 && python3 --version
```

## Configuration Files

This repository now includes:

- `.vscode/settings.json` - VS Code workspace settings
- `.vscode/extensions.json` - Recommended extensions
- `.devcontainer/devcontainer.json` - Codespaces configuration

These configurations are version-controlled to ensure consistent development environments across the team.
