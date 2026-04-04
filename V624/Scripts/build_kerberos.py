#!/usr/bin/env python3

import argparse
import hashlib
import json
import os
import pathlib
import shlex
import shutil
import subprocess
import sys


ROOT = pathlib.Path(__file__).resolve().parent.parent
SOURCE_ROOT = ROOT / "krb5-1.22.2"
KERBEROS_SOURCE_ROOT = SOURCE_ROOT / "src"
GENERATED_ROOT = ROOT / "XcodeSupport" / "Generated" / "Kerberos" / "darwin-i386"
WORK_ROOT = GENERATED_ROOT / "work"
INSTALL_ROOT = GENERATED_ROOT / "install"
STAMP_PATH = GENERATED_ROOT / "build-stamp.json"
LINK_FLAGS_PATH = GENERATED_ROOT / "KerberosLinkFlags.xcconfig"
DEPLOYMENT_TARGET = "10.13"
DEFAULT_CCACHE = "FILE:/tmp/krb5cc_%{uid}"
CONFIGURE_FLAGS = [
    "--disable-shared",
    "--enable-static",
    "--with-crypto-impl=builtin",
]
STATIC_LIBRARIES = (
    "libgssapi_krb5.a",
    "libkrb5.a",
    "libk5crypto.a",
    "libcom_err.a",
    "libkrb5support.a",
)
REQUIRED_HEADERS = (
    "krb5.h",
    "gssapi.h",
    "gssapi/gssapi.h",
    "gssapi/gssapi_krb5.h",
)
VENDORED_LIBS = {
    "gssapi_krb5",
    "krb5",
    "k5crypto",
    "com_err",
    "krb5support",
}


def tool_path(name: str) -> str | None:
    return shutil.which(name)


def command_output(cmd: list[str], *, cwd: pathlib.Path | None = None, env: dict[str, str] | None = None) -> str | None:
    try:
        return subprocess.check_output(
            cmd,
            cwd=str(cwd or ROOT),
            env=env,
            text=True,
            stderr=subprocess.DEVNULL,
        ).strip()
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
        "authoritative Kerberos builds are expected on macOS 10.13 with Xcode 9.4.1 "
        "and the macOS 10.13 SDK",
        file=sys.stderr,
    )


def run(cmd: list[str], *, cwd: pathlib.Path | None = None, env: dict[str, str] | None = None) -> None:
    print("+", " ".join(cmd))
    subprocess.run(cmd, cwd=str(cwd or ROOT), env=env, check=True)


def load_version() -> str:
    for line in (SOURCE_ROOT / "README").read_text(encoding="utf-8", errors="ignore").splitlines():
        if line.startswith("Release ") or line.startswith("Release:"):
            return line.split(None, 1)[1].strip()
    return SOURCE_ROOT.name


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
        "kerberos_version": load_version(),
        "source_dir": str(SOURCE_ROOT),
        "source_signature": source_signature(SOURCE_ROOT),
        "arch": "i386",
        "deployment_target": DEPLOYMENT_TARGET,
        "sdk_path": str(sdk_path) if sdk_path is not None else "",
        "default_ccache": DEFAULT_CCACHE,
        "configure_flags": CONFIGURE_FLAGS,
    }


def outputs_exist() -> bool:
    required = [
        INSTALL_ROOT / "bin" / "krb5-config",
        STAMP_PATH,
        LINK_FLAGS_PATH,
    ]
    required.extend(INSTALL_ROOT / "include" / pathlib.Path(name) for name in REQUIRED_HEADERS)
    required.extend(INSTALL_ROOT / "lib" / name for name in STATIC_LIBRARIES)
    return all(path.exists() for path in required)


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
    env["DEFCCNAME"] = DEFAULT_CCACHE
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


def find_archive(build_root: pathlib.Path, name: str) -> pathlib.Path:
    matches = sorted(build_root.rglob(name))
    if not matches:
        raise SystemExit(f"error: failed to find built archive {name}")
    return matches[0]


def copy_archives(source_root: pathlib.Path) -> None:
    lib_dir = INSTALL_ROOT / "lib"
    lib_dir.mkdir(parents=True, exist_ok=True)
    for archive_name in STATIC_LIBRARIES:
        source_archive = find_archive(source_root, archive_name)
        shutil.copy2(source_archive, lib_dir / archive_name)


def select_header_candidate(source_root: pathlib.Path, destination_name: str) -> pathlib.Path:
    basename = pathlib.Path(destination_name).name
    candidates = sorted(source_root.rglob(basename))
    if not candidates:
        raise SystemExit(f"error: failed to find generated header {destination_name}")
    for candidate in candidates:
        rel = str(candidate.relative_to(source_root)).replace(os.sep, "/")
        if destination_name == "gssapi.h" and rel.endswith("include/gssapi.h"):
            return candidate
        if destination_name == "gssapi/gssapi.h" and rel.endswith("include/gssapi/gssapi.h"):
            return candidate
        if destination_name == "gssapi/gssapi_krb5.h" and rel.endswith("gssapi_krb5.h"):
            return candidate
        if destination_name == "krb5.h" and rel.endswith("include/krb5.h"):
            return candidate
    return candidates[0]


def copy_required_headers(source_root: pathlib.Path) -> None:
    include_dir = INSTALL_ROOT / "include"
    include_dir.mkdir(parents=True, exist_ok=True)
    for destination_name in REQUIRED_HEADERS:
        destination = include_dir / pathlib.Path(destination_name)
        destination.parent.mkdir(parents=True, exist_ok=True)
        if destination.exists():
            continue
        source_header = select_header_candidate(source_root, destination_name)
        shutil.copy2(source_header, destination)


def copy_krb5_config(source_root: pathlib.Path) -> pathlib.Path:
    build_tools_dir = source_root / "build-tools"
    config_path = build_tools_dir / "krb5-config"
    if not config_path.exists():
        raise SystemExit("error: failed to build krb5-config")
    install_bin = INSTALL_ROOT / "bin"
    install_bin.mkdir(parents=True, exist_ok=True)
    target = install_bin / "krb5-config"
    shutil.copy2(config_path, target)
    target.chmod(0o755)
    return target


def filter_system_link_flags(raw_flags: str) -> list[str]:
    keep: list[str] = []
    tokens = shlex.split(raw_flags)
    i = 0
    while i < len(tokens):
        token = tokens[i]
        if token == "-framework" and i + 1 < len(tokens):
            keep.extend([token, tokens[i + 1]])
            i += 2
            continue
        if token in {"-L", "-I", "-F"} and i + 1 < len(tokens):
            flag_value = tokens[i + 1]
            if token == "-F":
                keep.extend([token, flag_value])
            i += 2
            continue
        if token.startswith("-l") and token[2:] in VENDORED_LIBS:
            i += 1
            continue
        if token.startswith("-L"):
            i += 1
            continue
        if token.startswith("-I"):
            i += 1
            continue
        keep.append(token)
        i += 1
    return keep


def write_link_flags_fragment(krb5_config_path: pathlib.Path) -> None:
    libs_output = command_output([str(krb5_config_path), "--libs", "gssapi"], cwd=krb5_config_path.parent)
    system_flags = filter_system_link_flags(libs_output or "")
    value = " ".join(system_flags)
    LINK_FLAGS_PATH.write_text(
        "EUDORA_KERBEROS_SYSTEM_LDFLAGS = "
        + (value if value else "")
        + "\n",
        encoding="utf-8",
    )


def build() -> None:
    sh_tool = tool_path("sh") or "/bin/sh"
    make = tool_path("make")
    if make is None:
        raise SystemExit("error: make is required to build Kerberos")

    warn_toolchain_context()

    GENERATED_ROOT.mkdir(parents=True, exist_ok=True)
    source_copy_root = WORK_ROOT / "source"
    copy_source_tree(source_copy_root)
    source_copy = source_copy_root / "src"

    shutil.rmtree(INSTALL_ROOT, ignore_errors=True)
    env = build_environment()

    configure_cmd = [
        sh_tool,
        str(source_copy / "configure"),
        *CONFIGURE_FLAGS,
        f"--prefix={INSTALL_ROOT}",
    ]
    run(configure_cmd, cwd=source_copy, env=env)
    run([make, "-j", str(os.cpu_count() or 4)], cwd=source_copy, env=env)
    run([make, "install-headers"], cwd=source_copy, env=env)
    copy_required_headers(source_copy)
    copy_archives(source_copy)
    krb5_config_path = copy_krb5_config(source_copy)
    write_link_flags_fragment(krb5_config_path)

    STAMP_PATH.write_text(json.dumps(stamp_payload(), indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(f"built vendored Kerberos into {INSTALL_ROOT}")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build vendored MIT Kerberos 1.22.2 for the Carbon Xcode target")
    parser.add_argument("--clean", action="store_true")
    parser.add_argument("--force", action="store_true")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    try:
        if args.clean:
            clean()
            print(f"removed {GENERATED_ROOT}")
            return 0
        if not args.force and is_up_to_date():
            print(f"vendored Kerberos is up to date at {INSTALL_ROOT}")
            return 0
        build()
        return 0
    except subprocess.CalledProcessError as exc:
        config_log = WORK_ROOT / "source" / "src" / "config.log"
        if config_log.exists():
            print(f"error: vendored Kerberos bootstrap failed; see {config_log}", file=sys.stderr)
        else:
            print(f"error: vendored Kerberos bootstrap failed while running {' '.join(exc.cmd)}", file=sys.stderr)
        return exc.returncode or 1


if __name__ == "__main__":
    raise SystemExit(main())
