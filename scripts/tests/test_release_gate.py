"""Release gate regression with synthetic ZIPs; does not build/run Minecraft."""

from contextlib import redirect_stderr, redirect_stdout
import hashlib
import io
import json
import os
from pathlib import Path
from string import Template
import sys
import tempfile
import tomllib
import unittest
from unittest.mock import patch
import warnings
import zipfile

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "scripts"))
import verify_release as gate


def zip_bytes(entries):
    output = io.BytesIO()
    with zipfile.ZipFile(output, "w") as archive:
        for name, content in entries.items():
            archive.writestr(name, content)
    return output.getvalue()


class ReleaseGateTest(unittest.TestCase):
    def setUp(self):
        temp = tempfile.TemporaryDirectory(prefix="tacz-release-test-")
        self.addCleanup(temp.cleanup)
        self.root = Path(temp.name)
        self.tag = "26.1.2_R3"
        self.properties = {
            "minecraft_version": "26.1.2", "minecraft_version_range": "[26.1.2]",
            "neo_version": "26.1.2.97", "mod_id": "tacz", "mod_name": "TaCZ: Renovated",
            "mod_license": "GPL-3.0-only", "mod_version": "1.1.8+neoforge.26.1.2.R3",
        }
        self.write_properties()
        self.notes = self.root / "docs/publish/RELEASE_NOTES.md"
        self.notes.parent.mkdir(parents=True)
        self.notes.write_text(f"<!-- release-version: {self.properties['mod_version']} -->\n", encoding="utf-8")
        resources = self.root / "src/main/resources"
        self.entries = {}
        paths = list((REPO / "src/main/resources").glob("*mixins*.json"))
        paths.append(REPO / "src/main/resources" / gate.AT)
        for source in paths:
            name = source.relative_to(REPO / "src/main/resources")
            target = resources / name
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(source.read_bytes())
            self.entries[name.as_posix()] = source.read_bytes()
        template = (REPO / "src/main/templates/META-INF/neoforge.mods.toml").read_text(encoding="utf-8")
        self.entries["META-INF/neoforge.mods.toml"] = Template(template).substitute(self.properties)
        # Minimal classes are only names for the structural gate, not JVM bytecode.
        self.lua_path = "META-INF/jarjar/luaj-jse-3.0.1.jar"
        self.math_path = "META-INF/jarjar/commons-math3-3.6.1.jar"
        self.entries[self.lua_path] = zip_bytes({
            "org/luaj/vm2/LuaError.class": b"fixture",
            "org/luaj/vm2/lib/StringLib.class": b"fixture",
        })
        self.entries[self.math_path] = zip_bytes({"org/apache/commons/math3/util/FastMath.class": b"fixture"})
        self.set_embedded([self.lua_path, self.math_path])
        self.jar = self.root / "build/libs" / f"tacz-{self.properties['mod_version']}.jar"
        self.jar.parent.mkdir(parents=True)

    def write_properties(self, **changes):
        values = self.properties | changes
        (self.root / "gradle.properties").write_text("\n".join(f"{k}={v}" for k, v in values.items()), encoding="utf-8")

    def set_embedded(self, paths):
        self.entries["META-INF/jarjar/metadata.json"] = json.dumps({"jars": [{"path": p} for p in paths]})

    def check_jar(self):
        self.jar.write_bytes(zip_bytes(self.entries))
        return gate.check_artifact(self.root, self.properties)

    def test_valid_source_and_jar(self):
        self.assertEqual(gate.check_source(self.root, self.tag), self.properties)
        jar, digest = self.check_jar()
        self.assertEqual(jar, self.jar)
        self.assertEqual(digest, hashlib.sha256(self.jar.read_bytes()).hexdigest())

    def test_wrong_tags(self):
        for tag in ("26.1.2_R2", "1.21.11_R3", "26.1.2", "26.1.2_R3\n", "26.1.2_R3;exit 0"):
            with self.subTest(tag=tag), self.assertRaises(ValueError):
                gate.check_source(self.root, tag)

    def test_wrong_properties(self):
        cases = (("minecraft_version", "1.21.11"), ("minecraft_version_range", "[26.2]"),
                 ("neo_version", "21.11.45"), ("neo_version", "26.1.2.97-beta"),
                 ("mod_id", "tacz_renovated"), ("mod_version", "1.1.8-neoforge.26.1.2.R3"),
                 ("mod_version", "1.1.8+neoforge.1.21.11.R3"))
        for key, value in cases:
            with self.subTest(key=key, value=value), self.assertRaises(ValueError):
                self.write_properties(**{key: value})
                gate.check_source(self.root, self.tag)

    def test_duplicate_property(self):
        with (self.root / "gradle.properties").open("a") as file:
            file.write("\nmod_id=tacz\n")
        with self.assertRaisesRegex(ValueError, "Duplicate"):
            gate.check_source(self.root, self.tag)

    def test_unreviewed_or_wrong_notes(self):
        for markers in ([], ["UNRELEASED"], ["1.1.8+neoforge.1.21.11.R3"],
                        [self.properties["mod_version"]] * 2):
            with self.subTest(markers=markers), self.assertRaises(ValueError):
                self.notes.write_text("\n".join(f"<!-- release-version: {v} -->" for v in markers))
                gate.check_source(self.root, self.tag)

    def test_missing_notes(self):
        self.notes.unlink()
        with self.assertRaises(OSError):
            gate.check_source(self.root, self.tag)

    def test_only_wrong_or_sources_jar(self):
        for name in ("tacz-other.jar", f"tacz-{self.properties['mod_version']}-sources.jar"):
            (self.jar.parent / name).write_bytes(zip_bytes(self.entries))
        with self.assertRaisesRegex(ValueError, "Missing exact"):
            gate.check_artifact(self.root, self.properties)

    def test_wrong_packaged_metadata(self):
        original = self.entries["META-INF/neoforge.mods.toml"]
        replacements = (
            ('version="1.1.8+neoforge.26.1.2.R3"', 'version="1.1.8+neoforge.26.1.2.R2"'),
            ('modId="tacz"', 'modId="wrong"'),
            ('versionRange="[26.1.2]"', 'versionRange="[1.21.11]"'),
            ('versionRange="[26.1.2.97,)"', 'versionRange="[21.11.45,)"'),
            ('type="required"', 'type="optional"'),
            ('file="META-INF/accesstransformer.cfg"', 'file="missing.cfg"'),
        )
        for before, after in replacements:
            with self.subTest(before=before), self.assertRaises(ValueError):
                self.entries["META-INF/neoforge.mods.toml"] = original.replace(before, after)
                self.check_jar()

    def test_missing_required_entries(self):
        for name in ("META-INF/neoforge.mods.toml", gate.AT, "META-INF/jarjar/metadata.json", self.lua_path):
            with self.subTest(name=name):
                content = self.entries.pop(name)
                with self.assertRaises((KeyError, ValueError)):
                    self.check_jar()
                self.entries[name] = content

    def test_missing_or_extra_mixin(self):
        original = self.entries.pop("tacz.mixins.json")
        with self.assertRaisesRegex(ValueError, "Mixin configs"):
            self.check_jar()
        self.entries["tacz.mixins.json"] = original
        self.entries["extra.mixins.json"] = "{}"
        with self.assertRaisesRegex(ValueError, "Mixin configs"):
            self.check_jar()

    def test_changed_mixin_or_at(self):
        for name in ("tacz.mixins.json", gate.AT):
            with self.subTest(name=name):
                original = self.entries[name]
                self.entries[name] = b"different"
                with self.assertRaises(ValueError):
                    self.check_jar()
                self.entries[name] = original

    def test_invalid_jarjar_registration(self):
        traversal = "META-INF/jarjar/../luaj.jar"
        self.entries[traversal] = self.entries[self.lua_path]
        cases = ([self.math_path], [self.lua_path, self.math_path, self.lua_path],
                 [self.lua_path, "META-INF/jarjar/missing.jar"], ["../luaj.jar", self.math_path],
                 [traversal, self.math_path])
        for paths in cases:
            with self.subTest(paths=paths), self.assertRaises(ValueError):
                self.set_embedded(paths)
                self.check_jar()

    def test_luaj_without_stringlib(self):
        self.entries[self.lua_path] = zip_bytes({"org/luaj/vm2/LuaError.class": b"fixture"})
        with self.assertRaisesRegex(ValueError, "Incomplete embedded luaj"):
            self.check_jar()

    def test_corrupt_inner_and_outer_zip(self):
        self.entries[self.lua_path] = b"not a jar"
        with self.assertRaises(zipfile.BadZipFile):
            self.check_jar()
        self.jar.write_bytes(b"not a jar")
        with self.assertRaises(zipfile.BadZipFile):
            gate.check_artifact(self.root, self.properties)

    def test_malformed_toml(self):
        self.entries["META-INF/neoforge.mods.toml"] = "[["
        with self.assertRaises(tomllib.TOMLDecodeError):
            self.check_jar()

    def test_duplicate_zip_entry(self):
        self.jar.write_bytes(zip_bytes(self.entries))
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", UserWarning)
            with zipfile.ZipFile(self.jar, "a") as jar:
                jar.writestr("tacz.mixins.json", b"duplicate")
        with self.assertRaisesRegex(ValueError, "Duplicate ZIP"):
            gate.check_artifact(self.root, self.properties)

    def test_cli_outputs_only_after_success(self):
        self.check_jar()
        output = self.root / "github-output"
        argv = ["verify_release.py", "--tag", self.tag, "--artifact"]
        with patch.object(gate, "ROOT", self.root), patch.object(sys, "argv", argv), \
                patch.dict(os.environ, {"GITHUB_OUTPUT": str(output)}), \
                redirect_stdout(io.StringIO()), redirect_stderr(io.StringIO()):
            self.assertEqual(gate.main(), 0)
            self.assertIn(f"jar=build/libs/{self.jar.name}\n", output.read_text())
            self.assertIn("sha256=", output.read_text())
            output.unlink()
            self.notes.write_text("<!-- release-version: UNRELEASED -->")
            self.assertEqual(gate.main(), 1)
            self.assertFalse(output.exists())


if __name__ == "__main__":
    unittest.main()
