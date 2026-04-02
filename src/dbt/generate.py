"""Auto-generate manifest.json using a dummy profiles.yml.

Reads the profile name from dbt_project.yml, creates a fake profiles.yml
with dummy Postgres credentials, runs `dbt deps && dbt parse`, then
cleans up. dbt parse never connects to the database — it only needs a
syntactically valid profile to produce manifest.json.
"""

from __future__ import annotations

import os
import shutil
import subprocess
from pathlib import Path

import yaml


def read_profile_name(project_dir: str) -> str:
    """Extract the profile name from dbt_project.yml."""
    project_file = Path(project_dir) / "dbt_project.yml"
    if not project_file.exists():
        raise FileNotFoundError(f"dbt_project.yml not found at {project_file}")

    with open(project_file) as f:
        project_config = yaml.safe_load(f)

    profile = project_config.get("profile")
    if not profile:
        raise ValueError("No 'profile' key found in dbt_project.yml")

    return profile


def create_dummy_profiles(profile_name: str, profiles_dir: str) -> None:
    """Write a dummy profiles.yml with fake Postgres credentials."""
    dummy = {
        profile_name: {
            "target": "ci",
            "outputs": {
                "ci": {
                    "type": "postgres",
                    "host": "localhost",
                    "port": 5432,
                    "user": "ci",
                    "password": "ci",
                    "dbname": "ci",
                    "schema": "public",
                }
            },
        }
    }
    profiles_path = Path(profiles_dir) / "profiles.yml"
    profiles_path.parent.mkdir(parents=True, exist_ok=True)

    with open(profiles_path, "w") as f:
        yaml.dump(dummy, f, default_flow_style=False)


def generate_manifest(project_dir: str, dbt_version: str) -> str:
    """Generate manifest.json by running dbt parse with a dummy profile.

    Returns the path to the generated manifest.json.
    """
    project_dir = os.path.abspath(project_dir)
    profiles_dir = os.path.join(project_dir, ".dataci_profiles")
    profiles_yml = os.path.join(profiles_dir, "profiles.yml")

    # Back up existing profiles.yml in the project dir if it exists
    existing_profiles = os.path.join(project_dir, "profiles.yml")
    backup_path = existing_profiles + ".dataci_backup"
    has_backup = False

    if os.path.exists(existing_profiles):
        shutil.copy2(existing_profiles, backup_path)
        has_backup = True

    try:
        # Read profile name from dbt_project.yml
        profile_name = read_profile_name(project_dir)
        print(f"  Profile: {profile_name}")

        # Create dummy profiles.yml
        create_dummy_profiles(profile_name, profiles_dir)
        print(f"  Created dummy profiles.yml at {profiles_yml}")

        # Install dbt-core + dbt-postgres (needed for dummy profile type)
        print(f"  Installing dbt-core=={dbt_version} and dbt-postgres...")
        subprocess.run(
            ["pip", "install", "--quiet", f"dbt-core=={dbt_version}", "dbt-postgres"],
            check=True,
            capture_output=True,
            text=True,
        )

        # Run dbt deps (install packages if packages.yml exists)
        packages_file = Path(project_dir) / "packages.yml"
        dependencies_file = Path(project_dir) / "dependencies.yml"
        if packages_file.exists() or dependencies_file.exists():
            print("  Running dbt deps...")
            deps_result = subprocess.run(
                ["dbt", "deps", "--profiles-dir", profiles_dir],
                cwd=project_dir,
                capture_output=True,
                text=True,
            )
            if deps_result.returncode != 0:
                print(f"  dbt deps stdout: {deps_result.stdout}")
                print(f"  dbt deps stderr: {deps_result.stderr}")
                # Continue anyway — deps failure might not block parse
                # (e.g., private packages that aren't needed for DAG structure)
                print("  Warning: dbt deps failed, continuing with dbt parse...")

        # Run dbt parse to generate manifest.json
        print("  Running dbt parse...")
        result = subprocess.run(
            ["dbt", "parse", "--profiles-dir", profiles_dir],
            cwd=project_dir,
            capture_output=True,
            text=True,
        )

        if result.returncode != 0:
            print(f"  dbt parse stdout: {result.stdout}")
            print(f"  dbt parse stderr: {result.stderr}")
            raise RuntimeError(f"dbt parse failed with exit code {result.returncode}")

        manifest_path = os.path.join(project_dir, "target", "manifest.json")
        if not os.path.exists(manifest_path):
            raise FileNotFoundError(
                f"manifest.json not generated at {manifest_path}. "
                f"dbt output: {result.stdout}"
            )

        print(f"  Manifest generated at {manifest_path}")
        return manifest_path

    finally:
        # Clean up dummy profiles
        if os.path.exists(profiles_dir):
            shutil.rmtree(profiles_dir)

        # Restore backed up profiles.yml
        if has_backup and os.path.exists(backup_path):
            shutil.move(backup_path, existing_profiles)
