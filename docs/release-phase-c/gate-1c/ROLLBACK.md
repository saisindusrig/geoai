# Gate1C rollback — prepared byte copies, no data rollback

Exact launcher bytes were copied before edits to `rollback/run-website.bat` and `rollback/start-copilot-review.ps1`; `before.json` records their hashes and effective Node22/PATH behavior. Never roll back databases, package versions, geometry, history or accounting.

If verification regresses, stop only newly launched validation processes. Restore the two files with PowerShell from the workspace root:

```powershell
Copy-Item -LiteralPath 'D:\layout project\docs\release-phase-c\gate-1c\rollback\run-website.bat' -Destination 'D:\layout project\run-website.bat'
Copy-Item -LiteralPath 'D:\layout project\docs\release-phase-c\gate-1c\rollback\start-copilot-review.ps1' -Destination 'D:\layout project\start-copilot-review.ps1'
Get-FileHash -Algorithm SHA256 -LiteralPath 'D:\layout project\run-website.bat','D:\layout project\start-copilot-review.ps1'
```

Expected original hashes: BAT `d9c5cbbb0d74b805b2ce4a1af91f62fe61829826ca250bfed54856c865b2fd65`; PowerShell `36acca56dba7eba129c166935c1f6afe438a4fbece56e68d2b83dcdfae66ee8b`. The new helper can remain inert; restored launchers do not reference it. No deletion is needed.

The restored files inherit existing system Node22.18.0 again. The new batch uses SETLOCAL and PowerShell restores PATH in finally, so no machine/user PATH repair is needed. Existing running processes are not switched by editing launcher files. Rollback is a local availability path, not Firebase qualification: Node22 does not satisfy Firebase13.1 engines, so Firebase must remain disabled.

The same byte restore and Node22 selection are demonstrated in an isolated rollback fixture, without restoring the working launchers merely for the test. Evidence is retained; no original data is rewritten.
