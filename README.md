# Latin Learner

Offline-first Android learner for Biblical Latin (POC).

**Package:** `com.latinpoc.learner` · **versionName:** `0.1.8-poc` · **scope:** Genesis only

## What ships

| Layer | Source | Status |
|-------|--------|--------|
| Latin tokens | Clementine Vulgate USFX | **Real** (Genesis 1–50) |
| Phonetics | ecclesiastical-italianate-v1 | **Generated** — Scriba gate |
| English verse row | Douay–Rheims Challoner (PD) | **Real** (verse-level) |
| Glosses | Whitaker WORDS DICTLINE | **Partial** — stubs for misses |
| Nav | Genesis chapters | Text-only UI |

See `docs/SOURCES.md`.

## Build & run

```bash
export ANDROID_HOME=/workspace/android-sdk
export JAVA_HOME=/workspace/.jdk/jdk-17.0.20.1+1
./gradlew :app:assembleDebug :app:testDebugUnitTest
# APK: app/build/outputs/apk/debug/app-debug.apk
```

Rebuild Genesis pack:

```bash
python3 tools/pipeline/build_genesis_pack.py
```

## Security (Argus)

- No `INTERNET` permission
- `allowBackup=false`
- Keep `androidx.emoji2` on classpath; `tools:node="remove"` **only** `EmojiCompatInitializer`
- ProfileInstaller excluded
- Release signing uses local debug keystore (POC sideload)

## Disclaimer

Independent POC — **not** an official Church product.
