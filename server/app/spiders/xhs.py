"""Wrapper to call the Spider_XHS low-level APIs in a safe, sandboxed way.

This module encapsulates loading the spider_xhs package and invoking its
`apis.xhs_pc_apis.XHS_Apis` and `xhs_utils.data_util.handle_note_info` helpers.
It avoids importing `main.py` and handles sys.path/CWD adjustments safely.
"""

import importlib
import importlib.util
import os
import sys
from typing import Any, Dict, Optional, Tuple

from loguru import logger


def fetch_xhs_note(note_url: str) -> Tuple[bool, str, Optional[Dict[str, Any]]]:
    """Try to fetch a Xiaohongshu note using the shipped spider_xhs package.

    Returns (success, message, note_info) where note_info is the processed
    dict from `xhs_utils.data_util.handle_note_info` on success.
    """
    spider_root = os.path.abspath(
        os.path.join(os.path.dirname(__file__), "..", "..", "spider_xhs")
    )
    spider_parent = os.path.abspath(os.path.join(spider_root, ".."))
    inserted_parent = False
    inserted_root = False

    try:
        # Ensure spider_parent is on sys.path for package imports
        if spider_parent not in sys.path:
            sys.path.insert(0, spider_parent)
            inserted_parent = True

        # Also add spider_root so relative imports and static file resolution work
        if spider_root not in sys.path:
            sys.path.insert(0, spider_root)
            inserted_root = True

        # Import low-level API class and helpers with spider_root as CWD so static requires resolve
        old_cwd = os.getcwd()
        try:
            os.chdir(spider_root)
            try:
                apis_mod = importlib.import_module("apis.xhs_pc_apis")
                XHS_Apis = getattr(apis_mod, "XHS_Apis")
                common_util = importlib.import_module("xhs_utils.common_util")
                data_util = importlib.import_module("xhs_utils.data_util")
                init = getattr(common_util, "init")
                handle_note_info = getattr(data_util, "handle_note_info")
            except Exception as e:
                logger.error(f"Failed to import low-level XHS apis or helpers: {e}")
                return False, f"Import error: {e}", None
        finally:
            try:
                os.chdir(old_cwd)
            except Exception:
                pass

        # Initialize environment (cookies & paths)
        try:
            cookies_str, _ = init()
        except Exception as e:
            logger.error(f"Failed to init spider_xhs environment: {e}")
            return False, f"Init error: {e}", None

        # Instantiate API and call
        apis = XHS_Apis()

        # The spider might expect to run with spider_root as cwd for static assets
        old_cwd = os.getcwd()
        try:
            os.chdir(spider_root)
            success, msg, raw = apis.get_note_info(note_url, cookies_str, proxies=None)
        finally:
            try:
                os.chdir(old_cwd)
            except Exception:
                pass

        if not success:
            logger.info(f"Spider fetch failed for {note_url}: {msg}")
            return False, str(msg), None

        # Normalize and return note_info
        try:
            note_info = raw.get("data", {}).get("items", [None])[0]
            if note_info is None:
                return False, "No items in spider response", None
            note_info["url"] = note_url
            note_info = handle_note_info(note_info)
            return True, "成功", note_info
        except Exception as e:
            logger.exception("Failed to process spider note_info")
            return False, f"Processing error: {e}", None

    finally:
        # Cleanup sys.path insertions
        try:
            if inserted_root and spider_root in sys.path:
                sys.path.remove(spider_root)
        except Exception:
            pass
        try:
            if inserted_parent and spider_parent in sys.path:
                sys.path.remove(spider_parent)
        except Exception:
            pass
