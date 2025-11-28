"""
JSON output formatting for headless mode.

Provides structured JSON output for all CLI commands to enable
automation and programmatic usage.
"""

import json
from typing import Any, Dict, List, Optional


class JSONOutput:
    """
    JSON output formatter for CLI commands.

    Provides consistent JSON structure across all commands:
    - Success: {"status": "success", "data": {...}}
    - Error: {"status": "error", "error_type": "...", "message": "..."}
    """

    @staticmethod
    def success(data: Dict[str, Any], **kwargs: Any) -> str:
        """
        Format success response.

        Args:
            data: Primary data payload
            **kwargs: Additional top-level fields

        Returns:
            JSON string
        """
        output = {"status": "success", "data": data}
        output.update(kwargs)
        return json.dumps(output, indent=2, ensure_ascii=False)

    @staticmethod
    def error(message: str, error_type: str = "error", **kwargs: Any) -> str:
        """
        Format error response.

        Args:
            message: Error message
            error_type: Error category (error, validation, crypto, stego, etc.)
            **kwargs: Additional error context

        Returns:
            JSON string
        """
        output = {
            "status": "error",
            "error_type": error_type,
            "message": message,
        }
        output.update(kwargs)
        return json.dumps(output, indent=2, ensure_ascii=False)


# Convenience functions for common command outputs
def backup_success(output_path: str, image_format: str, payload_size: int, capacity: int) -> str:
    """Format backup command success."""
    return JSONOutput.success(
        {
            "output_path": output_path,
            "image_format": image_format,
            "payload_size": payload_size,
            "capacity": capacity,
        }
    )


def restore_success(password: str, image_path: str) -> str:
    """Format restore command success."""
    return JSONOutput.success(
        {
            "password": password,
            "image_path": image_path,
        }
    )


def check_success(
    image_path: str,
    image_format: str,
    mode: str,
    size: tuple,
    capacity: int,
    max_password_size: int,
) -> str:
    """Format check command success."""
    return JSONOutput.success(
        {
            "image_path": image_path,
            "format": image_format,
            "mode": mode,
            "size": {"width": size[0], "height": size[1]},
            "capacity": capacity,
            "max_password_size": max_password_size,
        }
    )


def vault_create_success(output_path: str, entry_count: int, keys: List[str]) -> str:
    """Format vault create command success."""
    return JSONOutput.success(
        {
            "output_path": output_path,
            "entry_count": entry_count,
            "keys": keys,
        }
    )


def vault_add_success(output_path: str, entry_count: int, key_added: str) -> str:
    """Format vault add command success."""
    return JSONOutput.success(
        {
            "output_path": output_path,
            "entry_count": entry_count,
            "key_added": key_added,
        }
    )


def vault_get_success(
    key: str,
    password: str,
    username: Optional[str] = None,
    url: Optional[str] = None,
    notes: Optional[str] = None,
    has_totp: bool = False,
) -> str:
    """Format vault get command success."""
    data = {
        "key": key,
        "password": password,
    }
    if username:
        data["username"] = username
    if url:
        data["url"] = url
    if notes:
        data["notes"] = notes
    data["has_totp"] = has_totp
    return JSONOutput.success(data)


def vault_list_success(entries: List[Dict[str, Any]], entry_count: int) -> str:
    """Format vault list command success."""
    return JSONOutput.success(
        {
            "entries": entries,
            "entry_count": entry_count,
        }
    )


def vault_update_success(output_path: str, key_updated: str) -> str:
    """Format vault update command success."""
    return JSONOutput.success(
        {
            "output_path": output_path,
            "key_updated": key_updated,
        }
    )


def vault_delete_success(output_path: str, remaining_entries: int, key_deleted: str) -> str:
    """Format vault delete command success."""
    return JSONOutput.success(
        {
            "output_path": output_path,
            "remaining_entries": remaining_entries,
            "key_deleted": key_deleted,
        }
    )


def vault_export_success(output_path: str, entry_count: int, mode: str) -> str:
    """Format vault export command success."""
    return JSONOutput.success(
        {
            "output_path": output_path,
            "entry_count": entry_count,
            "mode": mode,  # "plaintext" or "redacted"
        }
    )


def vault_import_success(output_path: str, entry_count: int) -> str:
    """Format vault import command success."""
    return JSONOutput.success(
        {
            "output_path": output_path,
            "entry_count": entry_count,
        }
    )


def vault_totp_success(
    key: str,
    totp_code: str,
    time_remaining: int,
    totp_secret: Optional[str] = None,
) -> str:
    """Format vault totp command success."""
    data = {
        "key": key,
        "totp_code": totp_code,
        "time_remaining": time_remaining,
    }
    if totp_secret:
        data["totp_secret"] = totp_secret
    return JSONOutput.success(data)


def vault_search_success(results: List[Dict[str, Any]], query: str, count: int) -> str:
    """Format vault search command success."""
    return JSONOutput.success(
        {
            "results": results,
            "query": query,
            "count": count,
        }
    )


def batch_success(successful: int, failed: int, errors: List[str]) -> str:
    """Format batch operation success."""
    return JSONOutput.success(
        {
            "successful": successful,
            "failed": failed,
            "errors": errors,
        }
    )


def gallery_init_success(db_path: str) -> str:
    """Format gallery init command success."""
    return JSONOutput.success(
        {
            "db_path": db_path,
        }
    )


def gallery_add_success(
    name: str,
    path: str,
    entry_count: int,
    tags: Optional[List[str]] = None,
) -> str:
    """Format gallery add command success."""
    data = {
        "name": name,
        "path": path,
        "entry_count": entry_count,
    }
    if tags:
        data["tags"] = tags
    return JSONOutput.success(data)


def gallery_list_success(vaults: List[Dict[str, Any]], count: int) -> str:
    """Format gallery list command success."""
    return JSONOutput.success(
        {
            "vaults": vaults,
            "count": count,
        }
    )


def gallery_remove_success(name: str) -> str:
    """Format gallery remove command success."""
    return JSONOutput.success(
        {
            "name": name,
        }
    )


def gallery_refresh_success(name: str, entry_count: int) -> str:
    """Format gallery refresh command success."""
    return JSONOutput.success(
        {
            "name": name,
            "entry_count": entry_count,
        }
    )


def gallery_search_success(results: List[Dict[str, Any]], query: str, count: int) -> str:
    """Format gallery search command success."""
    return JSONOutput.success(
        {
            "results": results,
            "query": query,
            "count": count,
        }
    )
