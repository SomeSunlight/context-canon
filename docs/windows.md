# Windows filesystem locks

ContextCanon performs many small verified filesystem operations and deliberately publishes important files and immutable package directories atomically. On Linux this is normally uneventful. On Windows, real project use has repeatedly hit `PermissionError: [WinError 5] Access is denied` because antivirus or other background scanners temporarily hold project files or directories open while ContextCanon tries to replace or rename them.

This is not treated as a theoretical edge case. It has occurred repeatedly during ContextCanon development and owner onboarding, including a real `placement-publish` run that failed unchanged before the project directory was excluded from Microsoft Defender real-time scanning and succeeded immediately afterwards.

## Recommended setup

If your organization and security policy permit it, exclude the **project directory** from real-time antivirus scanning before doing sustained ContextCanon work on Windows. Keep the exclusion as narrow as practical; do not disable antivirus globally.

For JetBrains IDE users, the IDE may show a Microsoft Defender performance/security notification. Use its **Exclude Folders** action and approve the elevated Windows prompt. This is usually preferable on managed developer machines where JetBrains is an approved tool and direct Defender exclusion settings may be restricted.

You can also inspect Microsoft Defender exclusions from PowerShell where policy allows it:

```powershell
(Get-MpPreference).ExclusionPath
```

ContextCanon cannot determine which background process owns a transient Windows lock and cannot safely override a scanner or organization policy.

## Errno 13 is not automatically WinError 5

Windows/Python can also surface a generic `PermissionError: [Errno 13] Permission denied`. ContextCanon does **not** automatically treat that as the known transient scanner-lock case unless Windows actually reports WinError 5 / access denied.

A generic Errno 13 can instead indicate a normal ACL problem or that software attempted a file operation on the wrong filesystem type. For example, Git may expose a submodule/gitlink as one directory entry; inventory must recognize that directory rather than try to open it as a file.

The CLI therefore preserves the exact operation/path context for generic permission failures and reserves the scanner guidance below for the actual WinError-5/access-denied shape.

## When `WinError 5` still appears

ContextCanon retries the bounded atomic operations that are known to suffer short-lived locks. If Windows still denies the operation, the CLI reports the original operation/error together with this scanner guidance instead of exposing a Python traceback.

After correcting the scanner/exclusion problem, rerun the **same ContextCanon command**. Commands that use ContextCanon's journaled onboarding publication path roll back their own incomplete managed mutations before returning the failure.

If the same error persists even with the project directory excluded from real-time scanning, investigate the path with a process/handle viewer: another editor, indexer, backup client, sync tool, shell, or security product may still be holding the file or directory open.
