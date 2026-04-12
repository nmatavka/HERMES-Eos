#!/usr/bin/env python3

import argparse
import json
import os
import pathlib
import re
import shutil
import subprocess
import sys
import tempfile

from eudora_snapshot import (
    build_data_block,
    iter_resource_blocks,
    load_snapshot,
    rewrite_blocks,
    select_blocks,
    write_rez_source,
)


ROOT = pathlib.Path(__file__).resolve().parent.parent
GENERATED_DIR = ROOT / "XcodeSupport" / "GeneratedResources"
DLGX_INPUTS = [
    "credits.rsrc",
    "Help.rsrc",
    "ldaputils.rsrc",
    "RegTwo.rsrc",
    "SettingsIcons.rsrc",
    "ShLibDirAlias.rsrc",
    "Icons.rsrc",
    "nagWacky.rsrc",
    "SettingsTwo.rsrc",
    "common.rsrc",
]
REZ_INCLUDE_CANDIDATES = [
    ROOT,
    ROOT / "Include",
]
OPTIONAL_DLGX_INPUTS = {
    "nagWacky.rsrc",
}
CLASSIC_REZ_HEADERS = (
    "Types.r",
    "Pict.r",
    "CodeFragmentTypes.r",
    "AEObjects.r",
    "AERegistry.r",
)
_TOOLCHAIN_CONTEXT: dict[str, object] | None = None
VISIBLE_APP_NAME = "Eos"
VISIBLE_COMMUNITY_NAME = "Eos Community Project"
VISIBLE_COMMUNITY_COPYRIGHT = "Community build of classic Eudora sources"
COMMON_VISIBLE_REBRAND_REPLACEMENTS = (
    (
        "Both UIUC and HERMES have copyrights to parts of Eudoramail.  The rights to the program belong to UIUC, and HERMES is a licensee.",
        "This community build is based on the classic Eudora source release. See the source release license files for rights information.",
    ),
    (
        "HERMES will send you a program to take your order for the commercial version of Eudoramail.",
        "Commercial ordering is not part of the Eos community project.",
    ),
    (
        "HERMES will send you information about purchasing Eudoramail.",
        "Commercial purchasing is not part of the Eos community project.",
    ),
    (
        "Subscribe to the QUEST_News mailing list, and get occasional announcements regarding Eudoramail.",
        "QUEST_News is not part of the Eos community project.",
    ),
    (
        "You will then also be eligible for free upgrades to all new versions of Eudoramail that HERMES releases for the next twelve months, access to live technical support, and additional features not available in Sponsored or Light modes.",
        "Future Eos updates are community-maintained and provided on a best-effort basis.",
    ),
    ("people at HERMES", "people at ExampleCo"),
    ("HERMES Mail", "Community Mail"),
    ("qualcomm.com", "example.org"),
    ("http://www.qualcomm.com/eudora", "http://example.org/eos"),
    ("HERMES's main Eos web page", "the Eos project web page"),
    ("Copyright © 1992-2003 HERMES", VISIBLE_COMMUNITY_COPYRIGHT),
    ("Copyright © 1992-2003 Qualcomm, Inc.", VISIBLE_COMMUNITY_COPYRIGHT),
    ("Copyright (c) 1992-2003 Qualcomm, Inc.", VISIBLE_COMMUNITY_COPYRIGHT),
    ("Eudoramail", VISIBLE_APP_NAME),
)
VISIBLE_REBRAND_REPLACEMENTS = COMMON_VISIBLE_REBRAND_REPLACEMENTS + (
    ("QUALCOMM", VISIBLE_COMMUNITY_NAME.upper()),
    ("Qualcomm", VISIBLE_COMMUNITY_NAME),
    ("HERMES", VISIBLE_COMMUNITY_NAME),
    ("Eudora", VISIBLE_APP_NAME),
)


def run(cmd: list[str], *, cwd: pathlib.Path = ROOT, check: bool = True) -> None:
    print("+", " ".join(cmd))
    subprocess.run(cmd, cwd=str(cwd), check=check)


def tool_path(name: str) -> str | None:
    return shutil.which(name)


def command_output(cmd: list[str]) -> str | None:
    try:
        return subprocess.check_output(cmd, text=True, stderr=subprocess.DEVNULL).strip()
    except (FileNotFoundError, subprocess.CalledProcessError):
        return None


def rewrite_visible_text(text: str) -> str:
    updated = text
    for old, new in COMMON_VISIBLE_REBRAND_REPLACEMENTS:
        updated = updated.replace(old, new)
    return updated


def rewrite_visible_file(path: pathlib.Path) -> None:
    if not path.exists():
        return
    original = path.read_text(encoding="latin1", errors="replace")
    updated = rewrite_visible_text(original)
    if updated != original:
        path.write_text(updated, encoding="latin1")


def normalize_temp_copy(path: pathlib.Path) -> pathlib.Path:
    data = path.read_bytes().replace(b"\r", b"\n")
    temp = pathlib.Path(tempfile.mkstemp(prefix=path.stem + ".", suffix=path.suffix)[1])
    temp.write_bytes(data)
    return temp


def sync_legacy_include_outputs() -> None:
    for legacy_path in ROOT.glob(":include:*"):
        target = ROOT / "Include" / legacy_path.name.split(":include:", 1)[1]
        target.write_bytes(legacy_path.read_bytes())
        legacy_path.unlink()


def has_resource_fork(path: pathlib.Path) -> bool:
    try:
        listxattr = getattr(os, "listxattr", None)
        if listxattr is not None:
            return "com.apple.ResourceFork" in listxattr(path)
        xattr = tool_path("xattr")
        if xattr is None:
            return False
        result = subprocess.run(
            [xattr, "-p", "com.apple.ResourceFork", str(path)],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            check=False,
        )
        return result.returncode == 0
    except OSError:
        return False


def resource_file_has_contents(path: pathlib.Path) -> bool:
    if not path.exists():
        return False
    try:
        return path.stat().st_size > 0 or has_resource_fork(path)
    except OSError:
        return has_resource_fork(path)


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


def rez_include_paths() -> list[pathlib.Path]:
    includes = list(REZ_INCLUDE_CANDIDATES)
    sdk_path = current_sdk_path()
    if sdk_path is not None:
        includes.extend(
            [
                sdk_path / "usr" / "include",
                sdk_path
                / "System"
                / "Library"
                / "Frameworks"
                / "Carbon.framework"
                / "Headers",
                sdk_path
                / "System"
                / "Library"
                / "Frameworks"
                / "Carbon.framework"
                / "Frameworks"
                / "HIToolbox.framework"
                / "Headers",
                sdk_path
                / "System"
                / "Library"
                / "Frameworks"
                / "Carbon.framework"
                / "Frameworks"
                / "AE.framework"
                / "Headers",
                sdk_path
                / "System"
                / "Library"
                / "Frameworks"
                / "Carbon.framework"
                / "Frameworks"
                / "Help.framework"
                / "Headers",
            ]
        )
    result: list[pathlib.Path] = []
    seen: set[str] = set()
    for include in includes:
        include_str = str(include)
        if include_str in seen or not include.exists():
            continue
        seen.add(include_str)
        result.append(include)
    return result


def rez_include_args() -> list[str]:
    result = []
    for include in rez_include_paths():
        result.extend(["-i", str(include)])
    return result


def resolve_include_file(filename: str) -> pathlib.Path | None:
    for include in rez_include_paths():
        candidate = include / filename
        if candidate.exists():
            return candidate
    return None


def toolchain_context() -> dict[str, object]:
    global _TOOLCHAIN_CONTEXT
    if _TOOLCHAIN_CONTEXT is None:
        host_version = command_output(["sw_vers", "-productVersion"]) or "unknown"
        xcode_version = command_output(["xcodebuild", "-version"]) or "unknown"
        xcode_line = xcode_version.splitlines()[0] if xcode_version else "unknown"
        sdk_path = current_sdk_path()
        sdk_name = sdk_path.name if sdk_path is not None else "unknown"
        _TOOLCHAIN_CONTEXT = {
            "host_version": host_version,
            "xcode_line": xcode_line,
            "sdk_path": sdk_path,
            "sdk_name": sdk_name,
            "authoritative": host_version.startswith("10.13")
            and xcode_line == "Xcode 9.4.1"
            and sdk_name.lower().startswith("macosx10.13"),
        }
    return _TOOLCHAIN_CONTEXT


def warn_toolchain_context() -> None:
    context = toolchain_context()
    if context["authoritative"]:
        return
    print(
        "warning: host toolchain is "
        f"macOS {context['host_version']}, {context['xcode_line']}, SDK {context['sdk_name']}; "
        "authoritative Carbon resource builds are expected on macOS 10.13 with Xcode 9.4.1 "
        "and the macOS 10.13 SDK",
        file=sys.stderr,
    )
    missing_headers = [header for header in CLASSIC_REZ_HEADERS if resolve_include_file(header) is None]
    if missing_headers:
        print(
            "warning: classic Rez includes missing on this host: "
            + ", ".join(missing_headers)
            + "; continuing in non-authoritative preflight mode",
            file=sys.stderr,
        )


def run_rez_build(cmd: list[str], *, output: pathlib.Path, description: str) -> bool:
    try:
        run(cmd)
        return resource_file_has_contents(output)
    except subprocess.CalledProcessError:
        if toolchain_context()["authoritative"]:
            raise
        state = "retaining existing output" if resource_file_has_contents(output) else "output unavailable"
        print(
            f"warning: could not build {description} on this non-authoritative host; continuing preflight only ({state})",
            file=sys.stderr,
        )
        return resource_file_has_contents(output)


def append_derez_dialogs(derez: str, resource_file: pathlib.Path, output_handle) -> bool:
    cmd = [derez, *rez_include_args(), str(resource_file), "-only", "DLOG", "-only", "ALRT", "Types.r"]
    print("+", " ".join(cmd))
    try:
        subprocess.run(cmd, cwd=str(ROOT), check=True, stdout=output_handle)
        return True
    except subprocess.CalledProcessError:
        if toolchain_context()["authoritative"]:
            raise
        print(
            f"warning: could not DeRez dialogs from {resource_file.name} on this non-authoritative host; skipping it",
            file=sys.stderr,
        )
        return False


def run_perl_script(
    script: str,
    *args: str,
    stdout=None,
    force_extract: bool | None = None,
    cwd: pathlib.Path = ROOT,
) -> None:
    script_path = ROOT / script
    temp_script = normalize_temp_copy(script_path)
    try:
        first_line = temp_script.read_text(encoding="latin1", errors="replace").splitlines()[0].strip().lower()
        extract = force_extract if force_extract is not None else first_line.startswith("perl -x")
        cmd = ["perl"]
        if extract:
            cmd.append("-x")
        cmd.append(str(temp_script))
        cmd.extend(args)
        print("+", " ".join(cmd))
        subprocess.run(cmd, cwd=str(cwd), check=True, stdout=stdout)
        sync_legacy_include_outputs()
    finally:
        temp_script.unlink(missing_ok=True)


def manifest_outputs(manifest: dict) -> list[dict]:
    return manifest.get("resource_outputs", manifest.get("snapshot_outputs", []))


def encode_stub_data(stub_type: str, text: str) -> bytes:
    encoded = text.encode("latin1", errors="replace")
    if stub_type in {"STR ", "CSOm"}:
        return bytes([min(len(encoded), 255)]) + encoded[:255]
    if stub_type == "STR#":
        return b"\x00\x01" + bytes([min(len(encoded), 255)]) + encoded[:255]
    return encoded


def build_stub_source(spec: dict) -> str:
    stub = spec["stub"]
    stub_type = stub.get("type", "STR ")
    stub_id = int(stub.get("id", 128))
    stub_name = stub.get("name", spec["name"])
    stub_text = stub["text"]
    header = f"data '{stub_type}' ({stub_id}, \"{stub_name}\") {{"
    return build_data_block(header, encode_stub_data(stub_type, stub_text))


def buildversion_macros() -> dict[str, str]:
    path = ROOT / "Include" / "buildversion.h"
    if not path.exists():
        return {}
    text = path.read_bytes().replace(b"\r", b"\n").decode("latin1", errors="replace")
    macros: dict[str, str] = {}
    for line in text.splitlines():
        match = re.match(r"^\s*#define\s+([A-Z_]+)\s+([^\s/]+)", line)
        if match:
            macros[match.group(1)] = match.group(2)
    return macros


def default_version_string() -> str:
    macros = buildversion_macros()
    major = macros.get("MAJOR_VERSION")
    minor = macros.get("MINOR_VERSION")
    inc = macros.get("INC_VERSION")
    if major is None or minor is None:
        return "6.3"
    version = f"{major}.{minor}"
    if inc not in (None, "0"):
        version += f".{inc}"
    return version


def ensure_snapshot_outputs(manifest: dict) -> None:
    snapshot_path = ROOT / manifest["snapshot"]
    snapshot_text = load_snapshot(snapshot_path)
    blocks = list(iter_resource_blocks(snapshot_text))

    rez = tool_path("Rez")
    if rez is None:
        print("warning: Rez not found; snapshot extraction will stop at generated .r files", file=sys.stderr)

    GENERATED_DIR.mkdir(parents=True, exist_ok=True)

    for spec in manifest_outputs(manifest):
        mode = spec.get("mode", "snapshot_extract")
        if mode == "generated":
            continue
        output_r = ROOT / spec["output_r"]
        output_rsrc = ROOT / spec["output_rsrc"]
        output_r.parent.mkdir(parents=True, exist_ok=True)
        output_rsrc.parent.mkdir(parents=True, exist_ok=True)

        if mode == "snapshot_extract":
            selectors = spec.get("selectors", [])
            if not selectors:
                legacy_selector = {
                    key: spec[key]
                    for key in ("ids", "id_min", "id_max", "types", "name_regex", "names")
                    if key in spec
                }
                if legacy_selector:
                    selectors = [legacy_selector]
            selected = select_blocks(blocks, selectors)
            if spec.get("rewrite_policy") == "visible_strings":
                selected = rewrite_blocks(selected, VISIBLE_REBRAND_REPLACEMENTS)
            if selected:
                count = write_rez_source(output_r, selected)
                print(f"wrote {count} resources to {output_r}")
            elif "fallback_stub" in spec:
                output_r.write_text(build_data_block(
                    f"data '{spec['fallback_stub'].get('type', 'STR ')}' ({int(spec['fallback_stub'].get('id', 128))}, \"{spec['fallback_stub'].get('name', spec['name'])}\") {{",
                    encode_stub_data(
                        spec["fallback_stub"].get("type", "STR "),
                        spec["fallback_stub"]["text"],
                    ),
                ), encoding="latin1")
                count = 1
                print(f"wrote fallback stub to {output_r}")
            else:
                output_r.write_text("", encoding="latin1")
                count = 0
                print(f"warning: no snapshot resources matched {spec['name']}", file=sys.stderr)
        elif mode == "synthetic_stub":
            output_r.write_text(build_stub_source(spec), encoding="latin1")
            count = 1
            print(f"wrote synthetic stub to {output_r}")
        else:
            print(f"warning: unsupported manifest mode {mode} for {spec['name']}", file=sys.stderr)
            continue
        if rez is None or count == 0:
            continue
        run_rez_build(
            [rez, *rez_include_args(), "-o", str(output_rsrc), str(output_r)],
            output=output_rsrc,
            description=output_rsrc.name,
        )


def ensure_derived_text() -> None:
    run_perl_script("Bits/ProcessStrings", "StringDefs")
    run_perl_script("Bits/ProcessStrRes", "StrnDefs")
    rewrite_visible_file(ROOT / "StrnDefs.strn")
    run_perl_script("Bits/buildprefs", "PrefDefs")
    run_perl_script("Bits/processFilt", "FiltDefs")
    run_perl_script("Bits/buildaudit", "auditdefs")
    with open(ROOT / "Text.r", "w", encoding="latin1") as handle:
        run_perl_script("Bits/buildtext", *sorted(str(p.relative_to(ROOT)) for p in (ROOT / "TEXT").glob("*")), stdout=handle)
    rewrite_visible_file(ROOT / "Text.r")
    with open(ROOT / "HelpText.r", "w", encoding="latin1") as handle:
        run_perl_script("Bits/buildtext", *sorted(str(p.relative_to(ROOT)) for p in (ROOT / "HelpTEXT").glob("*")), stdout=handle)
    rewrite_visible_file(ROOT / "HelpText.r")


def ensure_rsrc_from_rez(source: str, output: str) -> bool:
    rez = tool_path("Rez")
    if rez is None:
        print(f"warning: Rez not found; skipping {output}", file=sys.stderr)
        return False
    return run_rez_build(
        [rez, *rez_include_args(), "-o", str(ROOT / output), str(ROOT / source)],
        output=ROOT / output,
        description=output,
    )


def ensure_two_dlgx_fallback() -> None:
    output = ROOT / "Two.dlgx.rsrc"
    if resource_file_has_contents(output):
        return
    snapshot_path = ROOT / "eudora.r"
    if not snapshot_path.exists():
        return
    rez = tool_path("Rez")
    if rez is None:
        print("warning: Rez not found; cannot build Two.dlgx fallback", file=sys.stderr)
        return
    dlgx_blocks = select_blocks(
        list(iter_resource_blocks(load_snapshot(snapshot_path))),
        [{"types": ["dlgx"]}],
    )
    if not dlgx_blocks:
        print("warning: no dlgx resources found in eudora.r for Two.dlgx fallback", file=sys.stderr)
        return
    GENERATED_DIR.mkdir(parents=True, exist_ok=True)
    output_r = GENERATED_DIR / "Two.dlgx.snapshot.r"
    count = write_rez_source(output_r, dlgx_blocks)
    if count == 0:
        return
    print("warning: using snapshot dlgx fallback for Two.dlgx.rsrc on this non-authoritative host", file=sys.stderr)
    run_rez_build(
        [rez, *rez_include_args(), "-o", str(output), str(output_r)],
        output=output,
        description="Two.dlgx.rsrc fallback",
    )


def ensure_versioned_plist() -> None:
    source = ROOT / "Eudora.plist"
    target = ROOT / "Eudora.rsrc.plist"
    if not source.exists():
        return

    version = os.environ.get("EUDORA_VERSION", default_version_string())
    text = source.read_text(encoding="latin1", errors="replace").replace("EUDORA_VERSION", version)
    target.write_text(text, encoding="latin1")


def ensure_legacy_graph(bundle_resources_dir: pathlib.Path | None) -> None:
    ensure_derived_text()
    if not resource_file_has_contents(ROOT / "credits.rsrc"):
        ensure_rsrc_from_rez("Credits.r", "credits.rsrc")
    ensure_rsrc_from_rez("common.rsrc.shell", "common.rsrc")
    ensure_rsrc_from_rez("two.rsrc.r", "two.rsrc")
    ensure_rsrc_from_rez("SettingsTwo.rsrc.r", "SettingsTwo.rsrc")

    rez = tool_path("Rez")
    derez = tool_path("DeRez") or tool_path("derez")
    if rez is not None:
        run_rez_build(
            [
                rez,
                *rez_include_args(),
                "-t",
                "rsrc",
                "-c",
                "RSED",
                str(ROOT / "TwoShell.r"),
                "-o",
                str(ROOT / "30.rsrc"),
            ],
            output=ROOT / "30.rsrc",
            description="30.rsrc",
        )

    if rez is not None and derez is not None and resource_file_has_contents(ROOT / "30.rsrc"):
        GENERATED_DIR.mkdir(parents=True, exist_ok=True)
        temp_dlog = GENERATED_DIR / "temp.DLOG.r"
        with temp_dlog.open("w", encoding="latin1") as handle:
            base_dialogs_available = append_derez_dialogs(derez, ROOT / "30.rsrc", handle)
        if base_dialogs_available:
            for extra in DLGX_INPUTS:
                extra_path = ROOT / extra
                if not resource_file_has_contents(extra_path):
                    qualifier = "optional " if extra in OPTIONAL_DLGX_INPUTS else ""
                    print(
                        f"warning: skipping {qualifier}dlgx input {extra} because it has no resource data",
                        file=sys.stderr,
                    )
                    continue
                with temp_dlog.open("a", encoding="latin1") as handle:
                    append_derez_dialogs(derez, extra_path, handle)
            temp_dlgx = GENERATED_DIR / "temp.dlgx.r"
            with temp_dlgx.open("w", encoding="latin1") as handle:
                run_perl_script("Bits/AddDlgx", str(temp_dlog), stdout=handle)
            run_rez_build(
                [rez, *rez_include_args(), "-o", str(ROOT / "Two.dlgx.rsrc"), str(temp_dlgx)],
                output=ROOT / "Two.dlgx.rsrc",
                description="Two.dlgx.rsrc",
            )
    ensure_two_dlgx_fallback()

    ensure_versioned_plist()

    if bundle_resources_dir is not None:
        bundle_resources_dir.mkdir(parents=True, exist_ok=True)
        if rez is not None:
            run_rez_build(
                [rez, *rez_include_args(), "-o", str(bundle_resources_dir / "EudoraLegacyResources.rsrc"), str(ROOT / "TwoAppShell.r")],
                output=bundle_resources_dir / "EudoraLegacyResources.rsrc",
                description="EudoraLegacyResources.rsrc",
            )
            run_rez_build(
                [rez, *rez_include_args(), "-o", str(bundle_resources_dir / "EudoraCarbonOverlay.rsrc"), str(ROOT / "carbon.r")],
                output=bundle_resources_dir / "EudoraCarbonOverlay.rsrc",
                description="EudoraCarbonOverlay.rsrc",
            )


def main() -> int:
    parser = argparse.ArgumentParser(description="Rebuild Eudora Carbon resources")
    parser.add_argument("--manifest", default="Scripts/resource_manifest.json")
    parser.add_argument("--bundle-resources-dir")
    args = parser.parse_args()

    warn_toolchain_context()
    manifest = json.loads((ROOT / args.manifest).read_text(encoding="utf-8"))
    ensure_snapshot_outputs(manifest)
    ensure_legacy_graph(pathlib.Path(args.bundle_resources_dir) if args.bundle_resources_dir else None)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
