# Eudoramail 6.3 Release Notes

## Summary

Eudoramail 6.3 is the current source release of the restored classic Mac mail client as a 32-bit i386 Carbon application. This port uses a minimal two-target Xcode project, rebuilt legacy resources recovered from `eudora.r`, and visible rebranding to `Eudoramail` / `HERMES` while preserving compatibility-sensitive internal identifiers where the build or on-disk formats still depend on them.

## How to Build on the Target Machine

The authoritative build target for this release is macOS 10.13 High Sierra with Xcode 9.4.1 and the macOS 10.13 SDK.

### Prerequisites

- macOS 10.13 High Sierra
- Xcode 9.4.1 with the macOS 10.13 SDK selected
- Command Line Tools installed
- `python3` and `perl` available in `PATH`
- No external OpenSSL installation is required; the build bootstraps vendored OpenSSL 3.5.5 from `openssl-3.5.5`

### Command Line Build

```sh
cd /path/to/eudora-carbon
python3 Scripts/generate_xcode_project.py
python3 Scripts/build_openssl.py
python3 Scripts/build_resources.py
xcodebuild -list -project EudoraXcode.xcodeproj
xcodebuild -project EudoraXcode.xcodeproj -scheme Eudora -configuration Debug build
xcodebuild -project EudoraXcode.xcodeproj -scheme Eudora -configuration Release build
```

### Xcode Build

1. Open `EudoraXcode.xcodeproj` in Xcode 9.4.1.
2. Select the `Eudora` scheme.
3. Build either the `Debug` or `Release` configuration.
4. The app target automatically bootstraps vendored OpenSSL and then runs the legacy resource build script during the build.

Newer macOS hosts can still run preflight resource extraction and project generation, but final Carbon build validation belongs on the High Sierra/Xcode 9.4.1 machine.

## What Changed

- The project now builds from a generated Xcode layout with exactly two targets: `Eudora` and `editorCarbon`.
- The supported build configurations are `Debug` and `Release`.
- The Xcode build is pinned to deployment target `10.13` and architecture `i386`.
- Legacy resources are rebuilt from `eudora.r`, including recovery of previously empty `.rsrc` files and resource-fork-aware handling for classic resource inputs.
- Visible product branding has been updated from `Qualcomm` to `HERMES` and from `Eudora` to `Eudoramail`.
- Visible version metadata has been updated to `6.3`.
- The current milestone is a free/non-registration-first build.
- The following legacy or proprietary features are disabled by default in this port: registration, Network Setup, GSSAPI, Wintertree spelling, TAE, Spotlight, Certicom SSL, and IMAP.
- OpenSSL is the only supported SSL path in this Xcode build.

## Compatibility Notes

- The application display name is `Eudoramail`, but the Xcode scheme remains `Eudora`.
- The bundle identifier remains `com.qualcomm.eudora` for compatibility.
- Compatibility-sensitive internal identifiers and legacy file or resource codes are intentionally not part of the visible rebrand.
- This release note describes the High Sierra/Xcode 9.4.1 build target, not a Mojave/Xcode 11 workflow.

## Build Notes

- `Scripts/generate_xcode_project.py` is the entrypoint for regenerating `EudoraXcode.xcodeproj`.
- `Scripts/build_openssl.py` is the vendored OpenSSL bootstrap entrypoint and produces the generated headers plus static libraries under `XcodeSupport/Generated/OpenSSL/darwin-i386/install`.
- `Scripts/build_resources.py` is the legacy resource build entrypoint used both manually and from the app target's shell build phase.
- The generated project currently exposes the `Eudora` and `editorCarbon` targets, `Debug` and `Release` configurations, deployment target `10.13`, and `i386` as the intended build architecture.

## Current Scope

This release is focused on making the Carbon source tree buildable again on the target machine with restored resources and stable visible branding. It documents the intended build flow and current feature defaults, but it does not claim broader runtime validation than has already been proven during the porting work.
