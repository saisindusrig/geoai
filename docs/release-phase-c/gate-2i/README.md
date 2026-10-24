# StruvoCivil — Gate 2I: disabled staging configuration review

This folder contains **only a static, inert review file**, populated from the Firebase Web app registration screenshot supplied by the project owner. No authenticated Firebase Console/API read or live connection occurred. The screenshot transcription has **not** been independently compared to the currently saved official app settings.

The included `frontend.staging.env.review` uses exactly the variable names in the uploaded Gate 2H template, including both optional provider flags, but `NEXT_PUBLIC_FIREBASE_AUTH_ENABLED=false` and `NEXT_PUBLIC_FIREBASE_RECOVERY_ENABLED=false`. Its `.env.review` suffix intentionally prevents normal Next.js autoloading. Only browser-side public app identifiers appear; no private or admin credential is included. Do not copy the file to `frontend/.env.local` or enable any Firebase flag.

## Apply to the owner's Windows repository (Codex only)

1. Create `D:\layout project\docs\release-phase-c\gate-2i\` if it is absent.
2. Save `frontend.staging.env.review` there as a documentation-only, inert review artifact.
3. Compare `apiKey`, `appId`, `authDomain` and `projectId` against the already registered **StruvoCivil Staging** app in Firebase Console / Project Settings → General. If any mismatch occurs, **STOP**; never guess or silently change the project/app.
4. Run offline checks for exact project/domain, app identifier shape, disabled Firebase/recovery, both provider flags and missing service-account secrets. Keep existing Gate 2H validator and the backend unchanged. Recheck original-data hashes if any local inputs were changed. No live SDK import/connection is needed.
5. Stop and report what was actually applied. This step does not authorize Firebase SDK activation, user creation/linking, backend ADC, Cloud Run/Blaze/billing, deploy, Git operations or F01–F07.

The user-managed API key is *not* a Firebase Admin private key. Still review browser API restrictions and authorized domains before allowing any real use. The web config values do not prove authorization or prevent unapproved accounts by themselves.
