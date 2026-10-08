"""Secrets, the local database and generated private files must never be committed."""
import subprocess
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def ignored(path):
    return subprocess.run(["git", "check-ignore", "-q", path], cwd=ROOT).returncode == 0


def tracked():
    out = subprocess.run(["git", "ls-files"], cwd=ROOT, capture_output=True, text=True).stdout
    return set(out.splitlines())


class TestRepoHygiene(unittest.TestCase):
    def test_private_files_are_ignored(self):
        for p in [".env", "crude_monitor.duckdb", "staging/x.json", "reports/monday_x.md", "Crude_Market_Monitor_3D.html"]:
            self.assertTrue(ignored(p), f"{p} must be in .gitignore")

    def test_private_files_are_not_tracked(self):
        files = tracked()
        self.assertNotIn(".env", files)
        self.assertFalse([f for f in files if f.endswith(".duckdb")])
        self.assertFalse([f for f in files if f.startswith(("staging/", "reports/"))])

    def test_agents_cannot_edit_files(self):
        for agent in (ROOT / ".claude" / "agents").glob("*.md"):
            header = agent.read_text().split("---")[1]
            tools_line = next(l for l in header.splitlines() if l.startswith("tools:"))
            self.assertNotIn("Edit", tools_line, agent.name)
            self.assertNotIn("Write", tools_line, agent.name)


if __name__ == "__main__":
    unittest.main()
