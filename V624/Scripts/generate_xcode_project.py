#!/usr/bin/env python3

import argparse
import hashlib
import pathlib
import xml.etree.ElementTree as ET


ROOT = pathlib.Path(__file__).resolve().parent.parent
PROJECT_PATH = ROOT / "EudoraXcode.xcodeproj" / "project.pbxproj"
XML_PATH = ROOT / "Eudora.proj.xml"


APP_EXCLUDES = {
    "console.stubs.c",
    "MoreNetworkSetup.c",
    "mtest.c",
    "nag.c",
    "networksetuplibrary.c",
    "paywin.c",
    "regcode.c",
    "regcode_charsets.c",
    "regcode_v2.c",
    "register.c",
    "SpotlightAPI.c",
    "TAE.c",
    "TAECommon.c",
    "TAEDictionary.c",
    "TAEText.c",
}

APP_EXTRA_SOURCES = [
    "OpenSSL.cp",
    "ssl.c",
    "sslCerts.cp",
    "XcodeSupport/EudoraKerberosCompat.c",
    "XcodeSupport/EudoraFeatureStubs.c",
]

EDITOR_EXCLUDES = {
    "MachOWrapper.cp",
}

EDITOR_EXTRA_SOURCES = []

APP_RESOURCES = [
    "EudoraDotApp/Contents/Resources/Eudora.icns",
    "EudoraDotApp/Contents/Resources/Settings.icns",
]

FRAMEWORKS = [
    "Carbon.framework",
    "ApplicationServices.framework",
    "CoreServices.framework",
    "Security.framework",
    "SystemConfiguration.framework",
]

SOURCE_SUFFIXES = {".c", ".cp", ".cpp", ".cc"}


def pbx_id(label: str) -> str:
    return hashlib.md5(label.encode("utf-8")).hexdigest().upper()[:24]


def normalize_source(path: str) -> str | None:
    candidates = [
        ROOT / path,
        ROOT / "CrispinIMAP" / path,
        ROOT / "Editor/Source/Editor Source" / path,
    ]
    for candidate in candidates:
        if candidate.exists():
            return str(candidate.relative_to(ROOT))
    return None


def load_target_sources(target_name: str) -> list[str]:
    tree = ET.parse(XML_PATH)
    root = tree.getroot()
    target = next(t for t in root.findall("./TARGETLIST/TARGET") if t.findtext("NAME") == target_name)
    paths = []
    for file_node in target.find("FILELIST").findall("FILE"):
        raw = file_node.findtext("PATH")
        if not raw:
            continue
        normalized = normalize_source(raw)
        if normalized:
            paths.append(normalized)
    return paths


def source_type(path: str) -> str:
    suffix = pathlib.Path(path).suffix.lower()
    if suffix == ".c":
        return "sourcecode.c.c"
    if suffix in {".cp", ".cpp", ".cc"}:
        return "sourcecode.cpp.cpp"
    if suffix == ".pch":
        return "sourcecode.c.h"
    if suffix == ".h":
        return "sourcecode.c.h"
    if suffix == ".icns":
        return "image.icns"
    return "text"


def quote(value: str) -> str:
    if all(ch.isalnum() or ch in "._/$()" for ch in value):
        return value
    return '"' + value.replace('"', '\\"') + '"'


def plist_quote(value: str) -> str:
    return '"' + value.replace("\\", "\\\\").replace('"', '\\"') + '"'


def build_project() -> str:
    app_sources = [
        p
        for p in load_target_sources("Carbon")
        if pathlib.Path(p).name not in APP_EXCLUDES and pathlib.Path(p).suffix.lower() in SOURCE_SUFFIXES
    ]
    for extra in APP_EXTRA_SOURCES:
        if extra not in app_sources:
            app_sources.append(extra)
    editor_sources = [
        p
        for p in load_target_sources("editorCarbon")
        if pathlib.Path(p).suffix.lower() in SOURCE_SUFFIXES and pathlib.Path(p).name not in EDITOR_EXCLUDES
    ]
    for extra in EDITOR_EXTRA_SOURCES:
        if extra not in editor_sources:
            editor_sources.append(extra)

    file_refs = {}
    build_files = {}

    def add_file(path: str) -> str:
        if path in file_refs:
            return file_refs[path]
        ident = pbx_id("fileref:" + path)
        file_refs[path] = ident
        return ident

    def add_build_file(path: str, role: str) -> str:
        key = role + ":" + path
        if key in build_files:
            return build_files[key]
        ident = pbx_id("build:" + key)
        build_files[key] = ident
        return ident

    for path in app_sources + editor_sources + APP_RESOURCES:
        add_file(path)
    for framework in FRAMEWORKS:
        add_file(framework)

    product_app_ref = pbx_id("product:Eos.app")
    product_editor_ref = pbx_id("product:libeditorCarbon.a")

    sections = []

    # PBXBuildFile
    build_entries = []
    for path in app_sources:
        build_entries.append(
            f"\t\t{add_build_file(path, 'appsrc')} = {{isa = PBXBuildFile; fileRef = {add_file(path)} /* {path} */; }};"
        )
    for path in editor_sources:
        build_entries.append(
            f"\t\t{add_build_file(path, 'editsrc')} = {{isa = PBXBuildFile; fileRef = {add_file(path)} /* {path} */; }};"
        )
    for path in APP_RESOURCES:
        build_entries.append(
            f"\t\t{add_build_file(path, 'appres')} = {{isa = PBXBuildFile; fileRef = {add_file(path)} /* {path} */; }};"
        )
    for framework in FRAMEWORKS:
        role = "editorfw" if framework == "Carbon.framework" else "appfw"
        build_entries.append(
            f"\t\t{add_build_file(framework, role)} = {{isa = PBXBuildFile; fileRef = {add_file(framework)} /* {framework} */; }};"
        )
        if framework == "Carbon.framework":
            build_entries.append(
                f"\t\t{add_build_file(framework, 'appfw')} = {{isa = PBXBuildFile; fileRef = {add_file(framework)} /* {framework} */; }};"
            )
    build_entries.append(
        f"\t\t{pbx_id('build:editor-product')} = {{isa = PBXBuildFile; fileRef = {product_editor_ref} /* libeditorCarbon.a */; }};"
    )
    sections.append("/* Begin PBXBuildFile section */\n" + "\n".join(build_entries) + "\n/* End PBXBuildFile section */")

    # PBXContainerItemProxy
    container_proxy = pbx_id("container:editor")
    sections.append(
        "/* Begin PBXContainerItemProxy section */\n"
        f"\t\t{container_proxy} = {{isa = PBXContainerItemProxy; containerPortal = {pbx_id('project')} /* Project object */; proxyType = 1; remoteGlobalIDString = {pbx_id('target:editor')}; remoteInfo = editorCarbon; }};\n"
        "/* End PBXContainerItemProxy section */"
    )

    # PBXFileReference
    file_entries = []
    for path, ident in sorted(file_refs.items()):
        if path.endswith(".framework"):
            file_entries.append(
                f"\t\t{ident} = {{isa = PBXFileReference; lastKnownFileType = wrapper.framework; name = {quote(path)}; path = {quote(path)}; sourceTree = SDKROOT; }};"
            )
        else:
            file_entries.append(
                f"\t\t{ident} = {{isa = PBXFileReference; lastKnownFileType = {source_type(path)}; path = {quote(path)}; sourceTree = SOURCE_ROOT; }};"
            )
    file_entries.append(
        f"\t\t{product_app_ref} = {{isa = PBXFileReference; explicitFileType = wrapper.application; path = Eos.app; sourceTree = BUILT_PRODUCTS_DIR; }};"
    )
    file_entries.append(
        f"\t\t{product_editor_ref} = {{isa = PBXFileReference; explicitFileType = archive.ar; path = libeditorCarbon.a; sourceTree = BUILT_PRODUCTS_DIR; }};"
    )
    file_entries.append(
        f"\t\t{pbx_id('fileref:App.xcconfig')} = {{isa = PBXFileReference; lastKnownFileType = text.xcconfig; path = XcodeSupport/Configs/App.xcconfig; sourceTree = SOURCE_ROOT; }};"
    )
    file_entries.append(
        f"\t\t{pbx_id('fileref:Editor.xcconfig')} = {{isa = PBXFileReference; lastKnownFileType = text.xcconfig; path = XcodeSupport/Configs/Editor.xcconfig; sourceTree = SOURCE_ROOT; }};"
    )
    sections.append("/* Begin PBXFileReference section */\n" + "\n".join(file_entries) + "\n/* End PBXFileReference section */")

    # PBXFrameworksBuildPhase
    app_fw_files = [add_build_file("Carbon.framework", "appfw")] + [add_build_file(fw, "appfw") for fw in FRAMEWORKS if fw != "Carbon.framework"] + [pbx_id("build:editor-product")]
    editor_fw_files = [add_build_file("Carbon.framework", "editorfw")]
    sections.append(
        "/* Begin PBXFrameworksBuildPhase section */\n"
        f"\t\t{pbx_id('phase:appfw')} = {{isa = PBXFrameworksBuildPhase; buildActionMask = 2147483647; files = (\n"
        + "\n".join(f"\t\t\t{item} /* {next(k for k,v in build_files.items() if v == item).split(':',1)[1]} */," if item in build_files.values() else f"\t\t\t{item} /* libeditorCarbon.a */," for item in app_fw_files)
        + "\n\t\t); runOnlyForDeploymentPostprocessing = 0; };\n"
        f"\t\t{pbx_id('phase:editorfw')} = {{isa = PBXFrameworksBuildPhase; buildActionMask = 2147483647; files = (\n"
        + "\n".join(f"\t\t\t{item} /* Carbon.framework */," for item in editor_fw_files)
        + "\n\t\t); runOnlyForDeploymentPostprocessing = 0; };\n"
        "/* End PBXFrameworksBuildPhase section */"
    )

    # PBXGroup
    source_children = [file_refs[p] for p in app_sources]
    editor_children = [file_refs[p] for p in editor_sources]
    support_children = [file_refs[p] for p in APP_RESOURCES] + [pbx_id("fileref:App.xcconfig"), pbx_id("fileref:Editor.xcconfig")]
    sections.append(
        "/* Begin PBXGroup section */\n"
        f"\t\t{pbx_id('group:products')} = {{isa = PBXGroup; children = ({product_app_ref}, {product_editor_ref}); name = Products; sourceTree = \"<group>\"; }};\n"
        f"\t\t{pbx_id('group:appsources')} = {{isa = PBXGroup; children = ({', '.join(source_children)}); name = AppSources; sourceTree = \"<group>\"; }};\n"
        f"\t\t{pbx_id('group:editorsources')} = {{isa = PBXGroup; children = ({', '.join(editor_children)}); name = EditorSources; sourceTree = \"<group>\"; }};\n"
        f"\t\t{pbx_id('group:support')} = {{isa = PBXGroup; children = ({', '.join(support_children)}); name = BuildSupport; sourceTree = \"<group>\"; }};\n"
        f"\t\t{pbx_id('group:root')} = {{isa = PBXGroup; children = ({pbx_id('group:appsources')}, {pbx_id('group:editorsources')}, {pbx_id('group:support')}, {pbx_id('group:products')}); sourceTree = \"<group>\"; }};\n"
        "/* End PBXGroup section */"
    )

    # PBXNativeTarget
    sections.append(
        "/* Begin PBXNativeTarget section */\n"
        f"\t\t{pbx_id('target:app')} = {{isa = PBXNativeTarget; buildConfigurationList = {pbx_id('configlist:app')} /* Build configuration list for PBXNativeTarget \"Eudora\" */; buildPhases = ({pbx_id('phase:kerberosscript')}, {pbx_id('phase:opensslscript')}, {pbx_id('phase:appsources')}, {pbx_id('phase:appfw')}, {pbx_id('phase:appres')}, {pbx_id('phase:appscript')}); buildRules = (); dependencies = ({pbx_id('dependency:editor')}); name = Eudora; productName = Eos; productReference = {product_app_ref} /* Eos.app */; productType = \"com.apple.product-type.application\"; }};\n"
        f"\t\t{pbx_id('target:editor')} = {{isa = PBXNativeTarget; buildConfigurationList = {pbx_id('configlist:editor')} /* Build configuration list for PBXNativeTarget \"editorCarbon\" */; buildPhases = ({pbx_id('phase:editorsources')}, {pbx_id('phase:editorfw')}); buildRules = (); dependencies = (); name = editorCarbon; productName = editorCarbon; productReference = {product_editor_ref} /* libeditorCarbon.a */; productType = \"com.apple.product-type.library.static\"; }};\n"
        "/* End PBXNativeTarget section */"
    )

    # PBXProject
    sections.append(
        "/* Begin PBXProject section */\n"
        f"\t\t{pbx_id('project')} = {{isa = PBXProject; attributes = {{LastUpgradeCheck = 0940; ORGANIZATIONNAME = \"Eos Community Project\"; TargetAttributes = {{ }}; }}; buildConfigurationList = {pbx_id('configlist:project')} /* Build configuration list for PBXProject \"EudoraXcode\" */; compatibilityVersion = \"Xcode 9.3\"; developmentRegion = English; hasScannedForEncodings = 0; knownRegions = (en); mainGroup = {pbx_id('group:root')}; productRefGroup = {pbx_id('group:products')}; projectDirPath = \"\"; projectRoot = \"\"; targets = ({pbx_id('target:app')}, {pbx_id('target:editor')}); }};\n"
        "/* End PBXProject section */"
    )

    # PBXResourcesBuildPhase
    app_resource_files = [add_build_file(path, "appres") for path in APP_RESOURCES]
    sections.append(
        "/* Begin PBXResourcesBuildPhase section */\n"
        f"\t\t{pbx_id('phase:appres')} = {{isa = PBXResourcesBuildPhase; buildActionMask = 2147483647; files = ({', '.join(app_resource_files)}); runOnlyForDeploymentPostprocessing = 0; }};\n"
        "/* End PBXResourcesBuildPhase section */"
    )

    # PBXShellScriptBuildPhase
    kerberos_script = 'cd "$SRCROOT"\\npython3 Scripts/build_kerberos.py'
    openssl_script = 'cd "$SRCROOT"\\npython3 Scripts/build_openssl.py'
    script = 'cd "$SRCROOT"\\npython3 Scripts/build_resources.py --bundle-resources-dir "$TARGET_BUILD_DIR/$UNLOCALIZED_RESOURCES_FOLDER_PATH"'
    sections.append(
        "/* Begin PBXShellScriptBuildPhase section */\n"
        f"\t\t{pbx_id('phase:kerberosscript')} = {{isa = PBXShellScriptBuildPhase; buildActionMask = 2147483647; files = (); inputPaths = (); name = \"Build Vendored Kerberos\"; outputPaths = (); runOnlyForDeploymentPostprocessing = 0; shellPath = /bin/sh; shellScript = {plist_quote(kerberos_script)}; showEnvVarsInLog = 0; }};\n"
        f"\t\t{pbx_id('phase:opensslscript')} = {{isa = PBXShellScriptBuildPhase; buildActionMask = 2147483647; files = (); inputPaths = (); name = \"Build Vendored OpenSSL\"; outputPaths = (); runOnlyForDeploymentPostprocessing = 0; shellPath = /bin/sh; shellScript = {plist_quote(openssl_script)}; showEnvVarsInLog = 0; }};\n"
        f"\t\t{pbx_id('phase:appscript')} = {{isa = PBXShellScriptBuildPhase; buildActionMask = 2147483647; files = (); inputPaths = (); name = \"Build Legacy Resources\"; outputPaths = (); runOnlyForDeploymentPostprocessing = 0; shellPath = /bin/sh; shellScript = {plist_quote(script)}; showEnvVarsInLog = 0; }};\n"
        "/* End PBXShellScriptBuildPhase section */"
    )

    # PBXSourcesBuildPhase
    app_source_files = [add_build_file(path, "appsrc") for path in app_sources]
    editor_source_files = [add_build_file(path, "editsrc") for path in editor_sources]
    sections.append(
        "/* Begin PBXSourcesBuildPhase section */\n"
        f"\t\t{pbx_id('phase:appsources')} = {{isa = PBXSourcesBuildPhase; buildActionMask = 2147483647; files = ({', '.join(app_source_files)}); runOnlyForDeploymentPostprocessing = 0; }};\n"
        f"\t\t{pbx_id('phase:editorsources')} = {{isa = PBXSourcesBuildPhase; buildActionMask = 2147483647; files = ({', '.join(editor_source_files)}); runOnlyForDeploymentPostprocessing = 0; }};\n"
        "/* End PBXSourcesBuildPhase section */"
    )

    # PBXTargetDependency
    sections.append(
        "/* Begin PBXTargetDependency section */\n"
        f"\t\t{pbx_id('dependency:editor')} = {{isa = PBXTargetDependency; name = editorCarbon; target = {pbx_id('target:editor')} /* editorCarbon */; targetProxy = {container_proxy} /* PBXContainerItemProxy */; }};\n"
        "/* End PBXTargetDependency section */"
    )

    # XCBuildConfiguration
    def cfg_block(ident: str, name: str, base_ref: str | None, settings: dict[str, object]) -> str:
        parts = []
        for key, value in settings.items():
            if isinstance(value, list):
                rendered = "(" + ", ".join(quote(str(item)) for item in value) + ")"
            elif isinstance(value, str):
                rendered = quote(value)
            else:
                rendered = str(value)
            parts.append(f"\t\t\t\t{key} = {rendered};")
        if base_ref == pbx_id("fileref:App.xcconfig"):
            base_comment = "App.xcconfig"
        elif base_ref == pbx_id("fileref:Editor.xcconfig"):
            base_comment = "Editor.xcconfig"
        else:
            base_comment = "Configuration.xcconfig"
        base = f"\t\t\tbaseConfigurationReference = {base_ref} /* {base_comment} */;\n" if base_ref else ""
        return (
            f"\t\t{ident} = {{\n"
            f"\t\t\tisa = XCBuildConfiguration;\n"
            + base
            + "\t\t\tbuildSettings = {\n"
            + "\n".join(parts)
            + "\n\t\t\t};\n"
            + f"\t\t\tname = {name};\n"
            + "\t\t};"
        )

    xcbuild_entries = [
        cfg_block(
            pbx_id("cfg:project:Debug"),
            "Debug",
            None,
            {
                "SDKROOT": "macosx10.13",
            },
        ),
        cfg_block(
            pbx_id("cfg:project:Release"),
            "Release",
            None,
            {
                "SDKROOT": "macosx10.13",
            },
        ),
        cfg_block(
            pbx_id("cfg:app:Debug"),
            "Debug",
            pbx_id("fileref:App.xcconfig"),
            {
                "DEBUG_INFORMATION_FORMAT": "dwarf",
                "GCC_OPTIMIZATION_LEVEL": 0,
                "ONLY_ACTIVE_ARCH": "YES",
            },
        ),
        cfg_block(
            pbx_id("cfg:app:Release"),
            "Release",
            pbx_id("fileref:App.xcconfig"),
            {
                "DEBUG_INFORMATION_FORMAT": "dwarf-with-dsym",
                "GCC_OPTIMIZATION_LEVEL": "s",
                "ONLY_ACTIVE_ARCH": "NO",
            },
        ),
        cfg_block(
            pbx_id("cfg:editor:Debug"),
            "Debug",
            pbx_id("fileref:Editor.xcconfig"),
            {
                "DEBUG_INFORMATION_FORMAT": "dwarf",
                "GCC_OPTIMIZATION_LEVEL": 0,
                "ONLY_ACTIVE_ARCH": "YES",
            },
        ),
        cfg_block(
            pbx_id("cfg:editor:Release"),
            "Release",
            pbx_id("fileref:Editor.xcconfig"),
            {
                "DEBUG_INFORMATION_FORMAT": "dwarf-with-dsym",
                "GCC_OPTIMIZATION_LEVEL": "s",
                "ONLY_ACTIVE_ARCH": "NO",
            },
        ),
    ]
    sections.append("/* Begin XCBuildConfiguration section */\n" + "\n".join(xcbuild_entries) + "\n/* End XCBuildConfiguration section */")

    # XCConfigurationList
    sections.append(
        "/* Begin XCConfigurationList section */\n"
        f"\t\t{pbx_id('configlist:project')} = {{isa = XCConfigurationList; buildConfigurations = ({pbx_id('cfg:project:Debug')}, {pbx_id('cfg:project:Release')}); defaultConfigurationIsVisible = 0; defaultConfigurationName = Release; }};\n"
        f"\t\t{pbx_id('configlist:app')} = {{isa = XCConfigurationList; buildConfigurations = ({pbx_id('cfg:app:Debug')}, {pbx_id('cfg:app:Release')}); defaultConfigurationIsVisible = 0; defaultConfigurationName = Release; }};\n"
        f"\t\t{pbx_id('configlist:editor')} = {{isa = XCConfigurationList; buildConfigurations = ({pbx_id('cfg:editor:Debug')}, {pbx_id('cfg:editor:Release')}); defaultConfigurationIsVisible = 0; defaultConfigurationName = Release; }};\n"
        "/* End XCConfigurationList section */"
    )

    return (
        "// !$*UTF8*$!\n"
        "{\n"
        "\tarchiveVersion = 1;\n"
        "\tclasses = {\n\t};\n"
        "\tobjectVersion = 46;\n"
        "\tobjects = {\n\n"
        + "\n\n".join(sections)
        + "\n\n\t};\n"
        f"\trootObject = {pbx_id('project')} /* Project object */;\n"
        "}\n"
    )


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate the Xcode 9 Carbon project")
    parser.add_argument("--output", default=str(PROJECT_PATH))
    args = parser.parse_args()

    output = pathlib.Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(build_project(), encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
