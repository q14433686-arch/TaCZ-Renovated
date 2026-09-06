#!/usr/bin/env python3
"""Run the production Lua globals factory against the vendored LuaJ on Java 25.

Usage: python3 scripts/test_script_globals.py
Requires JDK 25 (JAVA_HOME or java/javac on PATH); no Gradle or network needed.

Only the Lua imports and secureStandardGlobals() are extracted from ScriptManager.
This avoids Minecraft bootstrap without duplicating the library list or changing
production visibility. This is NOT a test of NeoForge reload events or gameplay.
"""

from __future__ import annotations

import argparse
import os
from pathlib import Path
import re
import subprocess
import sys
import tempfile

REPO = Path(__file__).resolve().parent.parent
MANAGER = REPO / "src/main/java/com/tacz/guns/resource/manager/ScriptManager.java"
LUAJ = REPO / "libs/luaj-jse-3.0.1.jar"

HARNESS = """
public class ScriptGlobalsRegression {
    public static void main(String[] args) throws Exception {
        String tests = java.nio.file.Files.readString(java.nio.file.Path.of(args[0]));
        Globals globals = null;
        // Independent environments, as created for each manager/reload. LuaJ's
        // shared string metatable is deliberately NOT reset between instances.
        for (int i = 0; i < 3; i++) {
            globals = secureStandardGlobals();
            globals.load(tests, "script_globals_" + i).call();
        }

        int count = 0;
        try (var paths = java.nio.file.Files.walk(java.nio.file.Path.of(args[1]))) {
            for (var path : paths.filter(p -> p.toString().endsWith(".lua")).sorted().toList()) {
                try (var reader = java.nio.file.Files.newBufferedReader(path)) {
                    // Syntax/bytecode compilation only: no game API is installed.
                    globals.load(reader, path.toString());
                    count++;
                }
            }
        }
        if (count == 0) {
            throw new AssertionError("No bundled Lua scripts found");
        }
        System.out.println("PASS: string API, require/preload, excluded libraries, 3 fresh Globals");
        System.out.println("PASS: " + count + " bundled Lua scripts compile (not executed)");
    }
}
"""


def java_tool(name: str) -> str:
    home = os.environ.get("JAVA_HOME")
    if home:
        suffix = ".exe" if os.name == "nt" else ""
        return str(Path(home) / "bin" / (name + suffix))
    return name


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--java", default=java_tool("java"), help="Java 25 executable")
    parser.add_argument("--javac", default=java_tool("javac"), help="Java 25 compiler executable")
    args = parser.parse_args()

    source = MANAGER.read_text(encoding="utf-8")
    imports = re.findall(r"^import org\.luaj\.[^\n]+;", source, re.MULTILINE)
    factories = re.findall(
        r"^    private static Globals secureStandardGlobals\(\) \{\n.*?^    \}",
        source, re.MULTILINE | re.DOTALL,
    )
    if not imports or len(factories) != 1:
        parser.error("ScriptManager factory layout changed; update the test extractor")
    # Insert the exact production method, not a separately maintained factory.
    harness = "\n".join(imports) + HARNESS.rsplit("}", 1)[0] + factories[0] + "\n}\n"
    try:
        with tempfile.TemporaryDirectory(prefix="tacz-script-globals-") as temp:
            java_source = Path(temp) / "ScriptGlobalsRegression.java"
            java_source.write_text(harness, encoding="utf-8")
            subprocess.run([
                args.javac, "--release", "25", "-encoding", "UTF-8", "-proc:none",
                "-classpath", str(LUAJ), "-d", temp, str(java_source),
            ], check=True)
            subprocess.run([
                args.java, "-classpath", os.pathsep.join((temp, str(LUAJ))),
                "ScriptGlobalsRegression", str(REPO / "scripts/tests/script_globals.lua"),
                str(REPO / "src/main/resources"),
            ], check=True)
    except (OSError, subprocess.CalledProcessError) as error:
        print(f"FAIL: {error}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
