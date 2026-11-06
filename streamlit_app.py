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


def api_get(url: str, **kwargs) -> requests.Response:
    response = requests.get(url, headers=HEADERS, timeout=20, **kwargs)
    response.raise_for_status()
    return response


@st.cache_data(ttl=300, show_spinner=False)
def get_default_branch() -> str:
    return api_get(API_ROOT).json()["default_branch"]


@st.cache_data(ttl=300, show_spinner=False)
def get_repository_tree(ref: str) -> list[dict]:
    """Fetch one recursive tree so the sidebar can show the full repository hierarchy."""
    data = api_get(f"{API_ROOT}/git/trees/{quote(ref, safe='')}", params={"recursive": "1"}).json()
    if data.get("truncated"):
        raise ValueError("GitHub returned a truncated file tree; try browsing the repository on GitHub.")
    return data.get("tree", [])


@st.cache_data(ttl=300, show_spinner=False)
def read_text_file(path: str, ref: str) -> str:
    encoded_path = quote(path, safe="/")
    data = api_get(
        f"{API_ROOT}/contents/{encoded_path}", params={"ref": ref}
    ).json()
    if data.get("encoding") == "base64" and data.get("content"):
        raw = base64.b64decode(data["content"])
    elif data.get("download_url"):
        raw = api_get(data["download_url"]).content
    else:
        raise ValueError("GitHub did not return file contents.")
    if len(raw) > MAX_DISPLAY_BYTES:
        raise ValueError("This file is larger than the in-browser display limit.")
    return raw.decode("utf-8-sig")


def make_tree(entries: list[dict], query: str = "", apps_only: bool = False) -> dict:
    """Build a nested, filtered tree containing files and their parent directories."""
    root = {"dirs": {}, "files": []}
    needle = query.strip().casefold()

    for entry in entries:
        if entry.get("type") != "blob":
            continue
        path = entry["path"]
        if apps_only and not path.startswith("apps/"):
            continue
        if needle and needle not in path.casefold():
            continue

        parts = path.split("/")
        node = root
        for folder in parts[:-1]:
            node = node["dirs"].setdefault(folder, {"dirs": {}, "files": []})
        node["files"].append({"name": parts[-1], "path": path, "size": entry.get("size", 0)})

    def sort_nodes(node: dict) -> None:
        node["files"].sort(key=lambda file: file["name"].casefold())
        node["dirs"] = dict(sorted(node["dirs"].items(), key=lambda item: item[0].casefold()))
        for child in node["dirs"].values():
            sort_nodes(child)

    sort_nodes(root)
    return root


def tree_file_paths(node: dict) -> set[str]:
    paths = {file["path"] for file in node["files"]}
    for child in node["dirs"].values():
        paths.update(tree_file_paths(child))
    return paths


def choose_file(path: str) -> None:
    st.session_state.selected_file = path


def render_tree(node: dict, query: str = "", parent: str = "") -> None:
    for name, child in node["dirs"].items():
        label = f"📁 {name}"
        with st.sidebar.expander(label, expanded=bool(query)):
            render_tree(child, query, f"{parent}{name}/")

    for file in node["files"]:
        st.sidebar.button(
            f"📄 {file['name']}",
            key=f"file:{file['path']}",
            type="primary" if st.session_state.get("selected_file") == file["path"] else "secondary",
            use_container_width=True,
            on_click=choose_file,
            args=(file["path"],),
            help=file["path"],
        )


def github_blob_url(path: str, ref: str) -> str:
    return f"{REPO_URL}/blob/{quote(ref, safe='')}/{quote(path, safe='/')}"


def main() -> None:
    st.set_page_config(page_title="Sushant Labs Repository Browser", layout="wide")
    st.title("Sushant Labs Repository Browser")
    st.caption("Browse the public repository, search filenames, and preview text files. Files are not executed.")

    try:
        branch = get_default_branch()
        entries = get_repository_tree(branch)
    except (requests.RequestException, ValueError) as error:
        st.error(f"Could not load the repository from GitHub: {error}")
        st.stop()

    if "selected_file" not in st.session_state:
        st.session_state.selected_file = "README.md"

    st.sidebar.markdown(f"[Open repository on GitHub]({REPO_URL})")
    st.sidebar.caption(f"Default branch: `{branch}`")
    query = st.sidebar.text_input("Search filenames", placeholder="e.g. pomodoro or README")
    apps_only = st.sidebar.checkbox("Only show apps/ files")
    filtered_tree = make_tree(entries, query=query, apps_only=apps_only)
    available_paths = tree_file_paths(filtered_tree)

    st.sidebar.markdown("### Repository files")
    if available_paths:
        render_tree(filtered_tree, query=query)
    else:
        st.sidebar.info("No files match these filters.")

    selected_path = st.session_state.get("selected_file")
    if selected_path not in available_paths:
        selected_path = None

    if selected_path is None:
        st.info("Select a file from the repository tree on the left.")
        return

    st.subheader(selected_path)
    st.link_button("View this file on GitHub", github_blob_url(selected_path, branch))

    metadata = next((entry for entry in entries if entry.get("path") == selected_path), {})
    if metadata.get("size", 0) > MAX_DISPLAY_BYTES:
        st.info("This file is too large to display here. Open it on GitHub to view or download it.")
        return

    try:
        contents = read_text_file(selected_path, branch)
    except UnicodeDecodeError:
        st.warning("This appears to be a binary file, so its contents are not displayed.")
        return
    except (requests.RequestException, ValueError) as error:
        st.error(f"Could not read this file: {error}")
        return

    if PurePosixPath(selected_path).name.casefold() == "readme.md":
        st.markdown(contents)
    else:
        extension = PurePosixPath(selected_path).suffix.lower()
        st.code(contents, language=LANGUAGES.get(extension, "text"), line_numbers=True)


if __name__ == "__main__":
    main()
