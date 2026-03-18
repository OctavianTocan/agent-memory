"""
Integration tests for mem dump and mem import commands.

These tests use real SQLite databases in temp directories.
The only thing patched is the DB/DATA_DIR path (to avoid touching the real database).
"""

import json
import os
import sqlite3
import sys
import tempfile
import shutil
import subprocess

import pytest

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MEM_BIN = os.path.join(REPO_ROOT, "bin", "mem")


@pytest.fixture()
def tmp_env(tmp_path):
    """Create a temp AGENT_MEMORY_DIR with an initialised database.

    Returns a dict with the env vars and paths tests need.
    """
    data_dir = str(tmp_path / "agent-memory")
    os.makedirs(data_dir, exist_ok=True)

    env = os.environ.copy()
    env["AGENT_MEMORY_DIR"] = data_dir
    # No API key needed -- we never call the embedding API in these tests
    env.pop("GEMINI_API_KEY", None)

    # Initialise the schema by running `mem init`
    subprocess.run(
        [sys.executable, MEM_BIN, "init"],
        env=env,
        check=True,
        capture_output=True,
    )
    db_path = os.path.join(data_dir, "memory.db")
    assert os.path.exists(db_path)

    return {
        "env": env,
        "data_dir": data_dir,
        "db": db_path,
        "dump_file": os.path.join(data_dir, "test-dump.json"),
    }


def _run_mem(tmp_env, *args, expect_fail=False):
    """Helper: run `mem <args>` against the temp database."""
    result = subprocess.run(
        [sys.executable, MEM_BIN, *args],
        env=tmp_env["env"],
        capture_output=True,
        text=True,
    )
    if not expect_fail:
        assert result.returncode == 0, (
            f"mem {' '.join(args)} failed:\nstdout: {result.stdout}\nstderr: {result.stderr}"
        )
    return result


def _populate_db(db_path):
    """Insert sample data into all four tables using raw SQL.

    Returns the expected data so tests can assert against it.
    """
    conn = sqlite3.connect(db_path)
    conn.execute("PRAGMA foreign_keys = ON")

    # Facts
    conn.execute(
        "INSERT INTO facts (id, category, subject, content, created_at, updated_at) "
        "VALUES (1, 'user_info', 'name', 'Alice', '2026-01-01 10:00:00', '2026-01-01 10:00:00')"
    )
    conn.execute(
        "INSERT INTO facts (id, category, subject, content, created_at, updated_at) "
        "VALUES (2, 'work', 'employer', 'Acme Corp', '2026-01-02 12:00:00', '2026-01-02 12:00:00')"
    )
    conn.execute(
        "INSERT INTO facts (id, category, subject, content, created_at, updated_at) "
        "VALUES (3, 'preferences', 'editor', 'neovim', '2026-01-03 08:00:00', '2026-01-03 08:00:00')"
    )

    # Soul
    conn.execute(
        "INSERT INTO soul (id, aspect, content, created_at, updated_at) "
        "VALUES (1, 'tone', 'concise and direct', '2026-01-01 10:00:00', '2026-01-01 10:00:00')"
    )
    conn.execute(
        "INSERT INTO soul (id, aspect, content, created_at, updated_at) "
        "VALUES (2, 'style', 'no emojis', '2026-01-01 10:00:00', '2026-01-01 10:00:00')"
    )

    # Daily logs
    conn.execute(
        "INSERT INTO daily_logs (id, date, content, created_at) "
        "VALUES (1, '2026-01-01', 'started project setup', '2026-01-01 09:00:00')"
    )
    conn.execute(
        "INSERT INTO daily_logs (id, date, content, created_at) "
        "VALUES (2, '2026-01-01', 'configured CI pipeline', '2026-01-01 14:00:00')"
    )
    conn.execute(
        "INSERT INTO daily_logs (id, date, content, created_at) "
        "VALUES (3, '2026-01-02', 'deployed v1', '2026-01-02 16:00:00')"
    )

    # Embeddings (small fake vectors for facts 1 and 2; fact 3 has none)
    fake_vec_1 = json.dumps([0.1, 0.2, 0.3])
    fake_vec_2 = json.dumps([0.4, 0.5, 0.6])
    conn.execute(
        "INSERT INTO embeddings (id, fact_id, vector, model, created_at) "
        "VALUES (1, 1, ?, 'gemini-embedding-2-preview', '2026-01-01 10:01:00')",
        (fake_vec_1,),
    )
    conn.execute(
        "INSERT INTO embeddings (id, fact_id, vector, model, created_at) "
        "VALUES (2, 2, ?, 'gemini-embedding-2-preview', '2026-01-02 12:01:00')",
        (fake_vec_2,),
    )

    conn.commit()
    conn.close()


# ---------------------------------------------------------------------------
# Tests: mem dump
# ---------------------------------------------------------------------------


class TestDump:
    def test_dump_creates_file_with_all_tables(self, tmp_env):
        _populate_db(tmp_env["db"])
        result = _run_mem(tmp_env, "dump", tmp_env["dump_file"])

        assert os.path.exists(tmp_env["dump_file"])
        with open(tmp_env["dump_file"]) as f:
            data = json.load(f)

        # Top-level structure
        assert data["version"] == "1.0"
        assert "exported_at" in data
        assert "tables" in data

        # All four tables present
        assert set(data["tables"].keys()) == {
            "facts",
            "soul",
            "daily_logs",
            "embeddings",
        }

    def test_dump_contains_correct_fact_data(self, tmp_env):
        _populate_db(tmp_env["db"])
        _run_mem(tmp_env, "dump", tmp_env["dump_file"])

        with open(tmp_env["dump_file"]) as f:
            data = json.load(f)

        facts = data["tables"]["facts"]
        assert len(facts) == 3
        assert facts[0]["category"] == "user_info"
        assert facts[0]["subject"] == "name"
        assert facts[0]["content"] == "Alice"
        assert facts[0]["id"] == 1
        assert facts[0]["created_at"] == "2026-01-01 10:00:00"
        assert facts[0]["updated_at"] == "2026-01-01 10:00:00"

    def test_dump_contains_correct_soul_data(self, tmp_env):
        _populate_db(tmp_env["db"])
        _run_mem(tmp_env, "dump", tmp_env["dump_file"])

        with open(tmp_env["dump_file"]) as f:
            data = json.load(f)

        soul = data["tables"]["soul"]
        assert len(soul) == 2
        assert soul[0]["aspect"] == "tone"
        assert soul[1]["aspect"] == "style"

    def test_dump_contains_correct_log_data(self, tmp_env):
        _populate_db(tmp_env["db"])
        _run_mem(tmp_env, "dump", tmp_env["dump_file"])

        with open(tmp_env["dump_file"]) as f:
            data = json.load(f)

        logs = data["tables"]["daily_logs"]
        assert len(logs) == 3
        assert logs[0]["date"] == "2026-01-01"
        assert logs[0]["content"] == "started project setup"

    def test_dump_contains_embedding_vectors(self, tmp_env):
        _populate_db(tmp_env["db"])
        _run_mem(tmp_env, "dump", tmp_env["dump_file"])

        with open(tmp_env["dump_file"]) as f:
            data = json.load(f)

        embeddings = data["tables"]["embeddings"]
        assert len(embeddings) == 2
        assert embeddings[0]["fact_id"] == 1
        # Vector is stored as a JSON string in SQLite; dump preserves that
        vec = json.loads(embeddings[0]["vector"])
        assert vec == [0.1, 0.2, 0.3]
        assert embeddings[0]["model"] == "gemini-embedding-2-preview"

    def test_dump_empty_database(self, tmp_env):
        """Dumping an empty (but initialised) database should work."""
        _run_mem(tmp_env, "dump", tmp_env["dump_file"])

        with open(tmp_env["dump_file"]) as f:
            data = json.load(f)

        for table_rows in data["tables"].values():
            assert table_rows == []

    def test_dump_default_path(self, tmp_env):
        """When no path arg is given, dump should go to DATA_DIR/memory-dump.json."""
        _populate_db(tmp_env["db"])
        _run_mem(tmp_env, "dump")

        default = os.path.join(tmp_env["data_dir"], "memory-dump.json")
        assert os.path.exists(default)

        with open(default) as f:
            data = json.load(f)
        assert len(data["tables"]["facts"]) == 3

    def test_dump_no_database_fails(self, tmp_env):
        """If the database doesn't exist, dump should fail."""
        os.remove(tmp_env["db"])
        result = _run_mem(tmp_env, "dump", tmp_env["dump_file"], expect_fail=True)
        assert result.returncode != 0
        assert "No memory.db found" in result.stderr

    def test_dump_output_message(self, tmp_env):
        _populate_db(tmp_env["db"])
        result = _run_mem(tmp_env, "dump", tmp_env["dump_file"])
        # 3 facts + 2 soul + 3 logs + 2 embeddings = 10
        assert "10 rows" in result.stdout


# ---------------------------------------------------------------------------
# Tests: mem import
# ---------------------------------------------------------------------------


class TestImport:
    def _make_dump(self, tmp_env):
        """Helper: populate + dump, return the dump file path."""
        _populate_db(tmp_env["db"])
        _run_mem(tmp_env, "dump", tmp_env["dump_file"])
        return tmp_env["dump_file"]

    def test_import_into_fresh_database(self, tmp_env):
        """Dump, wipe the database, import, verify all data is back."""
        dump_file = self._make_dump(tmp_env)

        # Wipe the database
        os.remove(tmp_env["db"])

        # Import into a fresh DB (import should auto-init)
        result = _run_mem(tmp_env, "import", dump_file)
        assert "10 rows" in result.stdout

        # Verify all data round-tripped
        conn = sqlite3.connect(tmp_env["db"])
        assert conn.execute("SELECT COUNT(*) FROM facts").fetchone()[0] == 3
        assert conn.execute("SELECT COUNT(*) FROM soul").fetchone()[0] == 2
        assert conn.execute("SELECT COUNT(*) FROM daily_logs").fetchone()[0] == 3
        assert conn.execute("SELECT COUNT(*) FROM embeddings").fetchone()[0] == 2

        # Verify fact content
        row = conn.execute(
            "SELECT category, subject, content FROM facts WHERE id = 1"
        ).fetchone()
        assert row == ("user_info", "name", "Alice")

        # Verify embedding vector is intact
        vec_json = conn.execute(
            "SELECT vector FROM embeddings WHERE fact_id = 1"
        ).fetchone()[0]
        assert json.loads(vec_json) == [0.1, 0.2, 0.3]

        conn.close()

    def test_import_preserves_timestamps(self, tmp_env):
        """Timestamps from the dump should survive the round-trip."""
        dump_file = self._make_dump(tmp_env)
        os.remove(tmp_env["db"])

        _run_mem(tmp_env, "import", dump_file)

        conn = sqlite3.connect(tmp_env["db"])
        row = conn.execute(
            "SELECT created_at, updated_at FROM facts WHERE id = 1"
        ).fetchone()
        assert row[0] == "2026-01-01 10:00:00"
        assert row[1] == "2026-01-01 10:00:00"
        conn.close()

    def test_import_preserves_ids(self, tmp_env):
        """Row IDs from the dump should be preserved (important for fact_id FK)."""
        dump_file = self._make_dump(tmp_env)
        os.remove(tmp_env["db"])

        _run_mem(tmp_env, "import", dump_file)

        conn = sqlite3.connect(tmp_env["db"])
        ids = [
            r[0] for r in conn.execute("SELECT id FROM facts ORDER BY id").fetchall()
        ]
        assert ids == [1, 2, 3]

        emb_fact_ids = [
            r[0]
            for r in conn.execute(
                "SELECT fact_id FROM embeddings ORDER BY id"
            ).fetchall()
        ]
        assert emb_fact_ids == [1, 2]
        conn.close()

    def test_import_merge_mode(self, tmp_env):
        """Without --force, import should merge (INSERT OR REPLACE)."""
        _populate_db(tmp_env["db"])
        _run_mem(tmp_env, "dump", tmp_env["dump_file"])

        # Modify the dump: change Alice's name to Bob
        with open(tmp_env["dump_file"]) as f:
            data = json.load(f)
        data["tables"]["facts"][0]["content"] = "Bob"
        with open(tmp_env["dump_file"], "w") as f:
            json.dump(data, f)

        # Import without --force (merge)
        _run_mem(tmp_env, "import", tmp_env["dump_file"])

        conn = sqlite3.connect(tmp_env["db"])
        row = conn.execute("SELECT content FROM facts WHERE id = 1").fetchone()
        assert row[0] == "Bob"
        # Other rows still there
        assert conn.execute("SELECT COUNT(*) FROM facts").fetchone()[0] == 3
        conn.close()

    def test_import_force_replaces_all(self, tmp_env):
        """With --force, existing data should be wiped before importing."""
        _populate_db(tmp_env["db"])

        # Add an extra fact that is NOT in the dump
        conn = sqlite3.connect(tmp_env["db"])
        conn.execute(
            "INSERT INTO facts (id, category, subject, content) "
            "VALUES (99, 'extra', 'thing', 'should be wiped')"
        )
        conn.commit()
        conn.close()

        # Create dump from original 3-fact state
        # (we already have 4 rows in the DB now, but we'll import the 3-row dump)
        _run_mem(tmp_env, "dump", tmp_env["dump_file"])

        # The dump will have 4 facts (including id=99). Let's instead craft a dump
        # from the fixture data to test --force properly. Remove the extra row from dump.
        with open(tmp_env["dump_file"]) as f:
            data = json.load(f)
        data["tables"]["facts"] = [f for f in data["tables"]["facts"] if f["id"] != 99]
        with open(tmp_env["dump_file"], "w") as f:
            json.dump(data, f)

        _run_mem(tmp_env, "import", tmp_env["dump_file"], "--force")

        conn = sqlite3.connect(tmp_env["db"])
        assert conn.execute("SELECT COUNT(*) FROM facts").fetchone()[0] == 3
        assert (
            conn.execute("SELECT COUNT(*) FROM facts WHERE id = 99").fetchone()[0] == 0
        )
        conn.close()

    def test_import_file_not_found(self, tmp_env):
        result = _run_mem(tmp_env, "import", "/nonexistent/file.json", expect_fail=True)
        assert result.returncode != 0
        assert "File not found" in result.stderr

    def test_import_invalid_json_structure(self, tmp_env):
        """Import should reject a file missing the 'tables' key."""
        bad_file = os.path.join(tmp_env["data_dir"], "bad.json")
        with open(bad_file, "w") as f:
            json.dump({"version": "1.0", "data": []}, f)

        result = _run_mem(tmp_env, "import", bad_file, expect_fail=True)
        assert result.returncode != 0
        assert "missing 'tables'" in result.stderr

    def test_import_missing_table_in_dump(self, tmp_env):
        """Import should reject a dump missing one of the required tables."""
        bad_file = os.path.join(tmp_env["data_dir"], "incomplete.json")
        with open(bad_file, "w") as f:
            json.dump(
                {
                    "version": "1.0",
                    "tables": {"facts": [], "soul": [], "daily_logs": []},
                    # missing "embeddings"
                },
                f,
            )

        result = _run_mem(tmp_env, "import", bad_file, expect_fail=True)
        assert result.returncode != 0
        assert "missing tables" in result.stderr

    def test_import_output_message(self, tmp_env):
        dump_file = self._make_dump(tmp_env)
        os.remove(tmp_env["db"])

        result = _run_mem(tmp_env, "import", dump_file)
        assert "facts: 3" in result.stdout
        assert "soul: 2" in result.stdout
        assert "daily_logs: 3" in result.stdout
        assert "embeddings: 2" in result.stdout


# ---------------------------------------------------------------------------
# Tests: full round-trip
# ---------------------------------------------------------------------------


class TestRoundTrip:
    def test_dump_import_dump_is_identical(self, tmp_env):
        """Dump -> wipe -> import -> dump again should yield identical table data."""
        _populate_db(tmp_env["db"])

        dump1 = os.path.join(tmp_env["data_dir"], "dump1.json")
        dump2 = os.path.join(tmp_env["data_dir"], "dump2.json")

        _run_mem(tmp_env, "dump", dump1)

        # Wipe and reimport
        os.remove(tmp_env["db"])
        _run_mem(tmp_env, "import", dump1)

        # Dump again
        _run_mem(tmp_env, "dump", dump2)

        with open(dump1) as f:
            data1 = json.load(f)
        with open(dump2) as f:
            data2 = json.load(f)

        # Table contents should be identical (ignore exported_at timestamp)
        assert data1["tables"] == data2["tables"]
        assert data1["version"] == data2["version"]

    def test_round_trip_across_separate_directories(self, tmp_env, tmp_path):
        """Dump from one DB, import into a completely different directory."""
        _populate_db(tmp_env["db"])
        dump_file = os.path.join(tmp_env["data_dir"], "portable.json")
        _run_mem(tmp_env, "dump", dump_file)

        # Set up a second, totally fresh temp directory
        other_dir = str(tmp_path / "other-memory")
        os.makedirs(other_dir, exist_ok=True)
        env2 = tmp_env["env"].copy()
        env2["AGENT_MEMORY_DIR"] = other_dir

        # Import into the new directory (should auto-init)
        result = subprocess.run(
            [sys.executable, MEM_BIN, "import", dump_file],
            env=env2,
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0, result.stderr

        # Verify data in the new DB
        db2 = os.path.join(other_dir, "memory.db")
        conn = sqlite3.connect(db2)
        assert conn.execute("SELECT COUNT(*) FROM facts").fetchone()[0] == 3
        assert conn.execute("SELECT COUNT(*) FROM soul").fetchone()[0] == 2
        assert conn.execute("SELECT COUNT(*) FROM daily_logs").fetchone()[0] == 3
        assert conn.execute("SELECT COUNT(*) FROM embeddings").fetchone()[0] == 2

        # Spot-check content
        row = conn.execute(
            "SELECT content FROM facts WHERE subject = 'name'"
        ).fetchone()
        assert row[0] == "Alice"
        conn.close()

    def test_import_does_not_duplicate_on_rerun(self, tmp_env):
        """Running import twice (without --force) should not create duplicates."""
        _populate_db(tmp_env["db"])
        _run_mem(tmp_env, "dump", tmp_env["dump_file"])
        os.remove(tmp_env["db"])

        _run_mem(tmp_env, "import", tmp_env["dump_file"])
        _run_mem(tmp_env, "import", tmp_env["dump_file"])

        conn = sqlite3.connect(tmp_env["db"])
        assert conn.execute("SELECT COUNT(*) FROM facts").fetchone()[0] == 3
        assert conn.execute("SELECT COUNT(*) FROM soul").fetchone()[0] == 2
        assert conn.execute("SELECT COUNT(*) FROM daily_logs").fetchone()[0] == 3
        assert conn.execute("SELECT COUNT(*) FROM embeddings").fetchone()[0] == 2
        conn.close()
