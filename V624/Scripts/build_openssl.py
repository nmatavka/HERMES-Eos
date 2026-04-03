#!/usr/bin/env python3

import argparse
import hashlib
import json
import os
import pathlib
import shutil
import subprocess
import sys


ROOT = pathlib.Path(__file__).resolve().parent.parent
SOURCE_ROOT = ROOT / "openssl-3.5.5"
GENERATED_ROOT = ROOT / "XcodeSupport" / "Generated" / "OpenSSL" / "darwin-i386"
WORK_ROOT = GENERATED_ROOT / "work"
INSTALL_ROOT = GENERATED_ROOT / "install"
STAMP_PATH = GENERATED_ROOT / "build-stamp.json"
BUILD_TARGET = "darwin-i386-cc"
DEPLOYMENT_TARGET = "10.13"
CONFIGURE_FLAGS = [
    "no-shared",
    "no-apps",
    "no-docs",
    "no-tests",
    "no-asm",
    "no-module",
    "no-pinshared",
]


def tool_path(name: str) -> str | None:
    return shutil.which(name)


def command_output(cmd: list[str]) -> str | None:
    try:
        return subprocess.check_output(cmd, text=True, stderr=subprocess.DEVNULL).strip()
    except (FileNotFoundError, subprocess.CalledProcessError):
        return None


def current_sdk_path() -> pathlib.Path | None:
    sdk = os.environ.get("SDKROOT")
    xcrun = tool_path("xcrun")
    if sdk:
        sdk_path = pathlib.Path(sdk)
        if sdk_path.exists():
            return sdk_path
        if xcrun is not None:
            resolved = command_output([xcrun, "--sdk", sdk, "--show-sdk-path"])
            if resolved:
                return pathlib.Path(resolved)
    if xcrun is not None:
        resolved = command_output([xcrun, "--show-sdk-path"])
        if resolved:
            return pathlib.Path(resolved)
    return None


def toolchain_context() -> dict[str, object]:
    host_version = command_output(["sw_vers", "-productVersion"]) or "unknown"
    xcode_version = command_output(["xcodebuild", "-version"]) or "unknown"
    xcode_line = xcode_version.splitlines()[0] if xcode_version else "unknown"
    sdk_path = current_sdk_path()
    sdk_name = sdk_path.name if sdk_path is not None else "unknown"
    authoritative = (
        host_version.startswith("10.13")
        and xcode_line == "Xcode 9.4.1"
        and sdk_name.lower().startswith("macosx10.13")
    )
    return {
        "host_version": host_version,
        "xcode_line": xcode_line,
        "sdk_path": sdk_path,
        "sdk_name": sdk_name,
        "authoritative": authoritative,
    }


def warn_toolchain_context() -> None:
    context = toolchain_context()
    if context["authoritative"]:
        return
    print(
        "warning: host toolchain is "
        f"macOS {context['host_version']}, {context['xcode_line']}, SDK {context['sdk_name']}; "
        "authoritative OpenSSL builds are expected on macOS 10.13 with Xcode 9.4.1 "
        "and the macOS 10.13 SDK",
        file=sys.stderr,
    )


def run(cmd: list[str], *, cwd: pathlib.Path | None = None, env: dict[str, str] | None = None) -> None:
    print("+", " ".join(cmd))
    subprocess.run(cmd, cwd=str(cwd or ROOT), env=env, check=True)


def load_version() -> str:
    version_data = SOURCE_ROOT / "VERSION.dat"
    major = minor = patch = None
    for line in version_data.read_text(encoding="utf-8").splitlines():
        if line.startswith("MAJOR="):
            major = line.split("=", 1)[1]
        elif line.startswith("MINOR="):
            minor = line.split("=", 1)[1]
        elif line.startswith("PATCH="):
            patch = line.split("=", 1)[1]
    if not (major and minor and patch):
        return SOURCE_ROOT.name
    return f"{major}.{minor}.{patch}"


def source_signature(root: pathlib.Path) -> str:
    digest = hashlib.sha256()
    for path in sorted(p for p in root.rglob("*") if p.is_file()):
        rel = str(path.relative_to(root)).replace(os.sep, "/")
        stat = path.stat()
        digest.update(rel.encode("utf-8"))
        digest.update(b"\0")
        digest.update(str(stat.st_size).encode("ascii"))
        digest.update(b"\0")
        digest.update(str(stat.st_mtime_ns).encode("ascii"))
        digest.update(b"\0")
    return digest.hexdigest()


def stamp_payload() -> dict[str, object]:
    context = toolchain_context()
    sdk_path = context["sdk_path"]
    return {
        "openssl_version": load_version(),
        "source_dir": str(SOURCE_ROOT),
        "source_signature": source_signature(SOURCE_ROOT),
        "target": BUILD_TARGET,
        "arch": "i386",
        "deployment_target": DEPLOYMENT_TARGET,
        "sdk_path": str(sdk_path) if sdk_path is not None else "",
        "configure_flags": CONFIGURE_FLAGS,
    }


def outputs_exist() -> bool:
    return all(
        path.exists()
        for path in (
            INSTALL_ROOT / "include" / "openssl" / "ssl.h",
            INSTALL_ROOT / "lib" / "libssl.a",
            INSTALL_ROOT / "lib" / "libcrypto.a",
            STAMP_PATH,
        )
    )


def is_up_to_date() -> bool:
    if not outputs_exist():
        return False
    try:
        existing = json.loads(STAMP_PATH.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return False
    return existing == stamp_payload()


def build_environment() -> dict[str, str]:
    env = os.environ.copy()
    sdk_path = current_sdk_path()
    cflags = [f"-mmacosx-version-min={DEPLOYMENT_TARGET}", "-arch", "i386"]
    ldflags = [f"-mmacosx-version-min={DEPLOYMENT_TARGET}", "-arch", "i386"]
    if sdk_path is not None:
        cflags.extend(["-isysroot", str(sdk_path)])
        ldflags.extend(["-isysroot", str(sdk_path)])
    env["CC"] = command_output(["xcrun", "-find", "clang"]) or env.get("CC", "clang")
    env["CXX"] = command_output(["xcrun", "-find", "clang++"]) or env.get("CXX", "clang++")
    env["AR"] = command_output(["xcrun", "-find", "ar"]) or env.get("AR", "ar")
    env["RANLIB"] = command_output(["xcrun", "-find", "ranlib"]) or env.get("RANLIB", "ranlib")
    env["CFLAGS"] = " ".join(cflags + ([env["CFLAGS"]] if env.get("CFLAGS") else []))
    env["CXXFLAGS"] = " ".join(cflags + ([env["CXXFLAGS"]] if env.get("CXXFLAGS") else []))
    env["LDFLAGS"] = " ".join(ldflags + ([env["LDFLAGS"]] if env.get("LDFLAGS") else []))
    return env


def clean() -> None:
    shutil.rmtree(GENERATED_ROOT, ignore_errors=True)


def copy_source_tree(destination: pathlib.Path) -> None:
    if destination.exists():
        shutil.rmtree(destination)
    shutil.copytree(
        SOURCE_ROOT,
        destination,
        ignore=shutil.ignore_patterns(".DS_Store", "__pycache__"),
    )


def build() -> None:
    perl = tool_path("perl")
    make = tool_path("make")
    if perl is None:
        raise SystemExit("error: perl is required to configure OpenSSL")
    if make is None:
        raise SystemExit("error: make is required to build OpenSSL")

    warn_toolchain_context()

    GENERATED_ROOT.mkdir(parents=True, exist_ok=True)
    source_copy = WORK_ROOT / "src"
    copy_source_tree(source_copy)

    prefix = str(INSTALL_ROOT)
    openssldir = str(INSTALL_ROOT / "ssl")
    env = build_environment()

    configure_cmd = [
        perl,
        str(source_copy / "Configure"),
        *CONFIGURE_FLAGS,
        f"--prefix={prefix}",
        f"--openssldir={openssldir}",
        BUILD_TARGET,
    ]
    run(configure_cmd, cwd=source_copy, env=env)
    run([make, "-j", str(os.cpu_count() or 4)], cwd=source_copy, env=env)
    shutil.rmtree(INSTALL_ROOT, ignore_errors=True)
    run([make, "install_sw"], cwd=source_copy, env=env)

    STAMP_PATH.write_text(json.dumps(stamp_payload(), indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(f"built vendored OpenSSL into {INSTALL_ROOT}")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build vendored OpenSSL 3.5.5 for the Carbon Xcode target")
    parser.add_argument("--clean", action="store_true")
    parser.add_argument("--force", action="store_true")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    if args.clean:
        clean()
        print(f"removed {GENERATED_ROOT}")
        return 0
    if not args.force and is_up_to_date():
        print(f"vendored OpenSSL is up to date at {INSTALL_ROOT}")
        return 0
    build()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
