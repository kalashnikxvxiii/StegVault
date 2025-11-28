"""
Passphrase handling utilities for headless mode.

Supports multiple passphrase sources:
- Interactive prompt (default)
- File (--passphrase-file)
- Environment variable (STEGVAULT_PASSPHRASE)
"""

import os
import sys
from pathlib import Path
from typing import Optional

import click


def get_passphrase(
    passphrase: Optional[str] = None,
    passphrase_file: Optional[str] = None,
    env_var: str = "STEGVAULT_PASSPHRASE",
    prompt_text: str = "Passphrase",
    hide_input: bool = True,
    confirmation_prompt: bool = False,
) -> str:
    """
    Get passphrase from multiple sources with priority:
    1. Explicit passphrase parameter (if provided)
    2. File specified by --passphrase-file
    3. Environment variable (STEGVAULT_PASSPHRASE by default)
    4. Interactive prompt (fallback)

    Args:
        passphrase: Explicit passphrase (highest priority)
        passphrase_file: Path to file containing passphrase
        env_var: Environment variable name
        prompt_text: Text to display for interactive prompt
        hide_input: Hide input when prompting
        confirmation_prompt: Require confirmation when prompting

    Returns:
        Passphrase string

    Raises:
        click.ClickException: If file not found or not readable
        SystemExit: If file is empty or invalid
    """
    # Priority 1: Explicit passphrase
    if passphrase:
        return passphrase

    # Priority 2: Passphrase file
    if passphrase_file:
        try:
            file_path = Path(passphrase_file).expanduser().resolve()

            if not file_path.exists():
                raise click.ClickException(f"Passphrase file not found: {passphrase_file}")

            if not file_path.is_file():
                raise click.ClickException(f"Not a file: {passphrase_file}")

            # Read passphrase from file (strip whitespace/newlines)
            with open(file_path, "r", encoding="utf-8") as f:
                file_passphrase = f.read().strip()

            if not file_passphrase:
                click.echo("Error: Passphrase file is empty", err=True)
                sys.exit(2)

            return file_passphrase

        except (OSError, IOError) as e:
            raise click.ClickException(f"Failed to read passphrase file: {e}")

    # Priority 3: Environment variable
    env_passphrase = os.environ.get(env_var)
    if env_passphrase:
        if not env_passphrase.strip():
            click.echo(f"Error: Environment variable {env_var} is empty", err=True)
            sys.exit(2)
        return env_passphrase.strip()

    # Priority 4: Interactive prompt
    return click.prompt(prompt_text, hide_input=hide_input, confirmation_prompt=confirmation_prompt)


def validate_passphrase_sources(
    passphrase: Optional[str], passphrase_file: Optional[str], allow_prompt: bool = True
) -> None:
    """
    Validate that only one passphrase source is specified.

    Args:
        passphrase: Explicit passphrase
        passphrase_file: Passphrase file path
        allow_prompt: Whether interactive prompt is allowed

    Raises:
        click.ClickException: If multiple sources specified or no source in headless mode
    """
    sources_count = sum(
        [bool(passphrase), bool(passphrase_file), bool(os.environ.get("STEGVAULT_PASSPHRASE"))]
    )

    if sources_count > 1:
        raise click.ClickException(
            "Cannot specify multiple passphrase sources. "
            "Use only one of: --passphrase, --passphrase-file, or STEGVAULT_PASSPHRASE"
        )

    if not allow_prompt and sources_count == 0:
        raise click.ClickException(
            "No passphrase source specified for headless mode. "
            "Use --passphrase-file or set STEGVAULT_PASSPHRASE environment variable"
        )
