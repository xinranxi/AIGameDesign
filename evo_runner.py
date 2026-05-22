#!/usr/bin/env python3
"""
AI Game Evolution Runner
Autonomous game design evolution loop - no user input required.
Uses GitHub API for remote sync when available.
"""

import subprocess, json, os, sys, time
from pathlib import Path

REPO_DIR = Path("/opt/data/game-evolution")
TOKEN_FILE = Path("/opt/data/.github_token")
GH_TOKEN_ENV = "GITHUB_EVO_TOKEN"

def get_token():
    if os.environ.get(GH_TOKEN_ENV):
        return os.environ[GH_TOKEN_ENV]
    if TOKEN_FILE.exists():
        return TOKEN_FILE.read_text().strip()
    return None

def git(cmd, cwd=REPO_DIR):
    result = subprocess.run(cmd, shell=True, cwd=cwd, capture_output=True, text=True)
    return result.stdout.strip(), result.stderr.strip(), result.returncode

def load_json(name):
    with open(REPO_DIR / name) as f:
        return json.load(f)

def save_json(name, data):
    with open(REPO_DIR / name, "w") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def get_git_log(n=20):
    out, _, _ = git(f"git log --all --oneline -n {n}")
    return out.split("\n")

def get_current_gen():
    out, _, _ = git("git describe --tags --abbrev=0 2>/dev/null || echo 'v-g0'")
    if not out:
        return 0
    try:
        return int(out.split("-f")[0].replace("v-g", ""))
    except:
        return 0

def evolution_step(gen_n):
    """Execute one evolution step. Returns (new_fitness, new_novelty)."""
    # This is a skeleton - actual LLM-driven evolution happens via subagent
    # Here we update counters and prepare for next generation
    print(f"[Gen{gen_n}] Evolution step placeholder")
    return 70, 92

def main():
    token = get_token()
    repo = "xinranxi/AIGameDesign"
    
    print("=== AI Game Evolution Runner ===")
    print(f"Repo: {repo}")
    print(f"Token available: {bool(token)}")
    
    current_gen = get_current_gen()
    print(f"Current generation: {current_gen}")
    
    # Check git status
    out, _, rc = git("git status --short")
    if rc == 0 and out:
        print(f"Uncommitted changes:\n{out}")
        print("Committing...")
        _, err, rc = git("git add -A")
        commit_msg = f"Gen{current_gen}: auto-sync"
        _, err, rc = git(f'git commit -m "{commit_msg}"')
        if rc == 0:
            print(f"Committed: {commit_msg}")
        else:
            print(f"Commit failed: {err}")
    
    print("\n=== Evolution Loop Ready ===")
    print("To start evolution: python3 /opt/data/game-evolution/evo_runner.py --evolve")
    print("To push to GitHub: set GITHUB_EVO_TOKEN env var")

if __name__ == "__main__":
    main()
