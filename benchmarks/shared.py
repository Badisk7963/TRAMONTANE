"""Shared constants and utilities for Tramontane benchmarks."""

from __future__ import annotations

CODE_TO_REVIEW = '''\
import sqlite3
import os

def get_user(user_id):
    conn = sqlite3.connect("users.db")
    query = f"SELECT * FROM users WHERE id = {user_id}"
    result = conn.execute(query).fetchone()
    conn.close()
    return result

def save_file(filename, content):
    path = "/tmp/" + filename
    with open(path, "w") as f:
        f.write(content)
    return path

API_KEY = "sk-1234567890abcdef"
'''

BUG_KEYWORDS: dict[str, list[str]] = {
    "sql_injection": ["sql injection", "sql-injection", "f-string", "parameterized", "sanitiz"],
    "path_traversal": ["path traversal", "directory traversal", "path injection", "../", "os.path"],
    "hardcoded_secret": ["hardcoded", "api key", "secret", "credential", "api_key", "sensitive"],
}


def count_bugs(output: str) -> int:
    """Count how many of the 3 intentional bugs the output identifies."""
    lower = output.lower()
    found = 0
    for _bug, keywords in BUG_KEYWORDS.items():
        if any(kw in lower for kw in keywords):
            found += 1
    return found


def bugs_detail(output: str) -> dict[str, bool]:
    """Return which specific bugs were found."""
    lower = output.lower()
    return {
        bug: any(kw in lower for kw in keywords)
        for bug, keywords in BUG_KEYWORDS.items()
    }
