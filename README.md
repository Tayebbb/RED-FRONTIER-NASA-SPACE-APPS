# RED FRONTIER NASA SPACE APPS

Mars rover modeling project with a preserved modular hybrid baseline and a separate, reference-guided Perseverance build.

## Current Build

- Blender source: [`art/source/rover/perseverance_detailed.blend`](art/source/rover/perseverance_detailed.blend)
- Assembled GLB: [`art/export/rover/perseverance/perseverance_rover.glb`](art/export/rover/perseverance/perseverance_rover.glb)
- Reference and fidelity report: [`art/qa/PERSEVERANCE_BUILD_REPORT.md`](art/qa/PERSEVERANCE_BUILD_REPORT.md)
- Session handoff: [`art/HANDOFF.md`](art/HANDOFF.md)

The Perseverance model is a visual approximation, not an engineering-certified or exact flight-hardware replica. See the build report for source credits, measured details, and limitations.

## Preserved Hybrid Baseline

The original modular rover and its QA artifacts remain under `art/`. The named pre-QA Blender source is retained as a backup.

## Verification

Run from the repository root with Node.js:

```powershell
node art/qa/verify_perseverance_export.cjs
node art/qa/verify_exports.cjs
```

The first command validates the textured Perseverance GLB; the second validates the legacy hybrid exports.
