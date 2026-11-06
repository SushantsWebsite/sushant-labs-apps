"""Read-only Streamlit browser for the Sushant Labs Apps GitHub repository."""
from __future__ import annotations

import base64
from pathlib import PurePosixPath
from urllib.parse import quote

import requests
import streamlit as st

OWNER = "SushantsWebsite"
REPO = "sushant-labs-apps"
API_ROOT = f"https://api.github.com/repos/{OWNER}/{REPO}"
REPO_URL = f"https://github.com/{OWNER}/{REPO}"
MAX_DISPLAY_BYTES = 1_000_000
HEADERS = {
    "Accept": "application/vnd.github+json",
    "User-Agent": "sushant-labs-apps-streamlit-browser",
}
LANGUAGES = {
    ".py": "python",
    ".json": "json",
    ".yml": "yaml",
    ".yaml": "yaml",
    ".md": "markdown",
    ".toml": "toml",
    ".html": "html",
    ".css": "css",
    ".js": "javascript",
    ".ts": "typescript",
    ".sh": "bash",
    ".xml": "xml",
    ".csv": "text",
    ".txt": "text",
}


@st.cache_data(ttl=300, show_spinner=False)
def get_default_branch() -> str:
    response = requests.get(API_ROOT, headers=HEADERS, timeout=15)
    response.raise_for_status()
    return response.json()["default_branch"]


@st.cache_data(ttl=300, show_spinner=False)
def list_directory(path: str, ref: str) -> list[dict]:
    encoded_path = quote(path, safe="/")
    response = requests.get(
        f"{API_ROOT}/contents/{encoded_path}" if path else f"{API_ROOT}/contents",
        params={"ref": ref},
        headers=HEADERS,
        timeout=15,
    )
    response.raise_for_status()
    entries = response.json()
    if not isinstance(entries, list):
        raise ValueError("That path is not a directory.")
    return sorted(entries, key=lambda item: (item["type"] != "dir", item["name"].lower()))


@st.cache_data(ttl=300, show_spinner=False)
def read_text_file(path: str, ref: str) -> str:
    encoded_path = quote(path, safe="/")
    response = requests.get(
        f"{API_ROOT}/contents/{encoded_path}",
        params={"ref": ref},
        headers=HEADERS,
        timeout=15,
    )
    response.raise_for_status()
    data = response.json()
    if data.get("encoding") == "base64" and data.get("content"):
        raw = base64.b64decode(data["content"])
    elif data.get("download_url"):
        download = requests.get(data["download_url"], timeout=15)
        download.raise_for_status()
        raw = download.content
    else:
        raise ValueError("GitHub did not return file contents.")
    if len(raw) > MAX_DISPLAY_BYTES:
        raise ValueError("This file is larger than the in-browser display limit.")
    return raw.decode("utf-8-sig")


def github_blob_url(path: str, ref: str) -> str:
    return f"{REPO_URL}/blob/{quote(ref, safe='')}/{quote(path, safe='/')}"


def main() -> None:
    st.set_page_config(page_title="Sushant Labs Repository Browser", layout="wide")
    st.title("Sushant Labs Repository Browser")
    st.caption("Browse and read files from the public GitHub repository. Files are displayed as text and are not executed.")

    try:
        branch = get_default_branch()
    except requests.RequestException as error:
        st.error(f"Could not connect to GitHub: {error}")
        st.stop()

    if "browse_path" not in st.session_state:
        st.session_state.browse_path = ""

    current_path = st.session_state.browse_path
    try:
        entries = list_directory(current_path, branch)
    except (requests.RequestException, ValueError) as error:
        st.error(f"Could not list this folder: {error}")
        st.stop()

    st.sidebar.markdown(f"[Open repository on GitHub]({REPO_URL})")
    st.sidebar.caption(f"Default branch: `{branch}`")
    st.sidebar.markdown(f"**Folder:** `/{current_path}`" if current_path else "**Folder:** `/`")

    if current_path and st.sidebar.button("⬆️ Up one level", use_container_width=True):
        st.session_state.browse_path = str(PurePosixPath(current_path).parent)
        if st.session_state.browse_path == ".":
            st.session_state.browse_path = ""
        st.rerun()

    directories = [item for item in entries if item["type"] == "dir"]
    files = [item for item in entries if item["type"] == "file"]

    if directories:
        directory = st.sidebar.selectbox(
            "Folders",
            directories,
            format_func=lambda item: f"📁 {item['name']}",
            key=f"folders:{current_path}",
        )
        if st.sidebar.button("Open folder", use_container_width=True):
            st.session_state.browse_path = f"{current_path}/{directory['name']}".strip("/")
            st.rerun()
    else:
        st.sidebar.caption("No subfolders here.")

    selected = None
    if files:
        default_index = next((i for i, item in enumerate(files) if item["name"].lower() == "readme.md"), 0)
        selected = st.sidebar.selectbox(
            "Files",
            files,
            index=default_index,
            format_func=lambda item: f"📄 {item['name']}",
            key=f"files:{current_path}",
        )

    if selected is None:
        st.info("Choose a folder or file from the sidebar to browse the repository.")
        return

    full_path = selected["path"]
    st.subheader(full_path)
    st.link_button("View this file on GitHub", github_blob_url(full_path, branch))

    if selected.get("size", 0) > MAX_DISPLAY_BYTES:
        st.info("This file is too large to display here. Open it on GitHub to view or download it.")
        return

    try:
        contents = read_text_file(full_path, branch)
    except UnicodeDecodeError:
        st.warning("This appears to be a binary file, so its contents are not displayed.")
        return
    except (requests.RequestException, ValueError) as error:
        st.error(f"Could not read this file: {error}")
        return

    extension = PurePosixPath(full_path).suffix.lower()
    st.code(contents, language=LANGUAGES.get(extension, "text"), line_numbers=True)


if __name__ == "__main__":
    main()
