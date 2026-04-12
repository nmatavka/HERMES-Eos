# Eos 6.3 Release Notes

## Summary

This note is for people building the source release, not for end users looking for a finished binary.

Eos 6.3 is the current Carbon/Xcode port of the classic Mac mail client as a 32-bit `i386` application. The tree now builds from a minimal generated Xcode project, uses recovered classic resources from `eudora.r`, uses vendored OpenSSL and vendored MIT Kerberos, and applies the visible `Eos` community branding while leaving compatibility-sensitive internal identifiers in place where the code or file formats still depend on them.

## Authoritative Build Target

The build host of record is:

- macOS 10.13 High Sierra
- Xcode 9.4.1
- macOS 10.13 SDK

This is not a Mojave/Xcode 11 build and it is not a modern macOS/Xcode build.

Newer hosts can still regenerate the Xcode project and run some preflight scripts, but they are not authoritative. If a newer host fails while trying to link `i386` test binaries, that is expected host-toolchain mismatch, not proof that the source tree is broken.

## Project Shape

- Generated project: `EudoraXcode.xcodeproj`
- Targets: `Eudora`, `editorCarbon`
- Configurations: `Debug`, `Release`
- Deployment target: `10.13`
- Architecture: `i386`
- Carbon entrypoint: `SimpleStart`

`Scripts/generate_xcode_project.py` is the source of truth for the Xcode project layout. If the checked-in project looks stale, regenerate it instead of hand-editing the target matrix.

## Vendored Build Dependencies

No external OpenSSL or Kerberos installation is required or expected.

The tree bootstraps these in-repo dependencies:

- `openssl-3.5.5`
- `krb5-1.22.2`

Generated outputs land under:

- `XcodeSupport/Generated/OpenSSL/darwin-i386`
- `XcodeSupport/Generated/Kerberos/darwin-i386`

Both bootstrap scripts are incremental. Re-running them is safe. If you need to force a rebuild, use `--force`. If you need to discard generated state, use `--clean`.

## Prerequisites

- macOS 10.13 High Sierra
- Xcode 9.4.1 with the macOS 10.13 SDK selected
- Command Line Tools installed
- `python3` in `PATH`
- `perl` in `PATH`
- `make` in `PATH`

No Homebrew OpenSSL, no separate MIT Kerberos package, and no old Kerberos SDK should be required for the supported build flow.

## Recommended Command-Line Build

For a clean first build on the target machine:

```sh
cd /path/to/eudora-carbon
python3 Scripts/generate_xcode_project.py
python3 Scripts/build_kerberos.py
python3 Scripts/build_openssl.py
python3 Scripts/build_resources.py
xcodebuild -list -project EudoraXcode.xcodeproj
xcodebuild -project EudoraXcode.xcodeproj -scheme Eudora -configuration Debug build
xcodebuild -project EudoraXcode.xcodeproj -scheme Eudora -configuration Release build
```

The manual bootstrap steps are recommended for the first pass because they make failures easier to isolate. After that, the app target also runs the vendored Kerberos bootstrap, vendored OpenSSL bootstrap, and legacy resource build automatically during Xcode builds.

## Xcode Build

1. Open `EudoraXcode.xcodeproj` in Xcode 9.4.1.
2. Select the `Eudora` scheme.
3. Build `Debug` or `Release`.
4. The app target automatically runs:
   - `Scripts/build_kerberos.py`
   - `Scripts/build_openssl.py`
   - `Scripts/build_resources.py`

## Current Feature Status

These are the intended build-time defaults in the Xcode port:

- Enabled:
  - Carbon app target plus `editorCarbon` static library
  - recovered classic resources
  - OpenSSL 3.5.5 as the only SSL/TLS stack
  - MIT Kerberos 1.22.2 as the Kerberos/GSS backend
  - IMAP in the Xcode build
  - GSSAPI-backed Kerberos auth paths
- Disabled:
  - registration / nag-commercial flows
  - Network Setup
  - Wintertree spelling
  - TAE
  - Spotlight
  - Certicom SSL
  - literal Kerberos IV / KPOP shipping behavior

Important Kerberos note:

- In the Xcode port, legacy Kerberos behavior is treated as a KRB5 replacement.
- IMAP Kerberos auth is GSSAPI-based.
- POP Kerberos is interpreted as POP `AUTH GSSAPI` on the normal POP path, not as old KPOP ticket-send behavior.
- Literal `KERBEROS_V4` does not ship.

## Branding and Compatibility Notes

- Visible product name: `Eos`
- Visible organization branding: community project only
- Xcode scheme name: `Eudora`
- Bundle identifier: `com.qualcomm.eudora`

The built app, plist metadata, and resource-generation path now brand the project as `Eos`. Compatibility-sensitive internal identifiers, legacy resource codes, and on-disk format hooks were not blindly renamed.

## Troubleshooting

- If `Scripts/build_kerberos.py` or `Scripts/build_openssl.py` warns that the host is not macOS 10.13 / Xcode 9.4.1 / macOS 10.13 SDK, take that warning seriously.
- If a newer host fails with errors about missing `i386` support or `libSystem.tbd`, move the build to the High Sierra machine. That is an unsupported-host problem.
- If the Xcode project does not reflect the current script logic, rerun `python3 Scripts/generate_xcode_project.py`.
- If generated dependency state looks stale, clean and rebuild:

```sh
python3 Scripts/build_kerberos.py --clean
python3 Scripts/build_openssl.py --clean
python3 Scripts/build_resources.py
```

- If vendored Kerberos bootstrap fails on the target machine, inspect:
  - `XcodeSupport/Generated/Kerberos/darwin-i386/work/source/src/config.log`

## What Has Been Proven So Far

Repo-side validation has confirmed the generated project shape and the bootstrap wiring, including the two-target Xcode layout and the vendored dependency entrypoints.

The final proof steps still belong on the authoritative High Sierra/Xcode 9.4.1 machine:

- full `Debug` build
- full `Release` build
- launch smoke test
- IMAP smoke test
- TLS smoke test

This release note describes the supported source-build path and current port status. It does not claim broader runtime validation than has actually been completed on the target machine.
