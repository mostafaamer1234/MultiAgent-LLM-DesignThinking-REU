#!/usr/bin/env python3
"""Build the text-only reproducibility artifacts from archived source captures."""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path


CHATGPT_URL = "https://chatgpt.com/share/688ce907-9a60-800f-9d8a-6e1af453ff65"
GROK_URL = "https://grok.com/share/c2hhcmQtMw%3D%3D_561bcaae-3230-49b8-96f8-2fe84b974a4d"
CLAUDE_URL = "https://claude.ai/share/252d9d57-20a8-4daf-84b5-f96e35c72b8f"


def extract_chatgpt(html_path: Path) -> list[tuple[str, str]]:
    source = html_path.read_text(encoding="utf-8")
    flat = None
    for match in re.finditer(r'"((?:[^"\\]|\\.){100,})"', source):
        try:
            value = json.loads('"' + match.group(1) + '"')
        except json.JSONDecodeError:
            continue
        if value.startswith('[{"_1"'):
            flat = json.loads(value)
            break
    if flat is None:
        raise RuntimeError("ChatGPT shared-conversation payload was not found")

    memo: dict[int, object] = {}

    def deref(value):
        if isinstance(value, int):
            if value < 0:
                return None
            if value in memo:
                return memo[value]
            raw = flat[value]
            if isinstance(raw, dict):
                result: dict[str, object] = {}
                memo[value] = result
                for key, item in raw.items():
                    result[str(deref(int(key[1:])))] = deref(item)
                return result
            if isinstance(raw, list):
                result_list: list[object] = []
                memo[value] = result_list
                result_list.extend(deref(item) for item in raw)
                return result_list
            return raw
        return value

    root = deref(0)
    route = root["loaderData"]["routes/share.$shareId.($action)"]
    data = route["serverResponse"]["data"]
    mapping = data["mapping"]

    node_id = "client-created-root"
    messages: list[tuple[str, str]] = []
    while True:
        node = mapping[node_id]
        message = node.get("message")
        if message:
            role = message.get("author", {}).get("role")
            parts = message.get("content", {}).get("parts", [])
            text = "\n".join(part for part in parts if isinstance(part, str)).strip()
            if role in {"user", "assistant"} and text:
                messages.append((role, text))
        children = node.get("children", [])
        if not children:
            break
        node_id = children[0]
    return messages


def write_chatgpt(output: Path, messages: list[tuple[str, str]]) -> None:
    chunks = [
        "# GPT-4o evaluation transcript\n",
        f"Source snapshot: {CHATGPT_URL}\n",
        "Model: GPT-4o (confirmed by the researcher; the share payload also identifies `gpt-4o` as the default model).\n",
        "The transcript below preserves every non-system message in the shared conversation, in chronological order.\n",
    ]
    for index, (role, text) in enumerate(messages, 1):
        label = "Researcher" if role == "user" else "GPT-4o"
        chunks.append(f"\n## Message {index} — {label}\n\n{text}\n")
    output.write_text("\n".join(chunks), encoding="utf-8")


def wrap_rendered(output: Path, title: str, model: str, url: str, body_path: Path, note: str) -> None:
    body = body_path.read_text(encoding="utf-8").strip()
    header = (
        f"# {title}\n\n"
        f"Source snapshot: {url}\n\n"
        f"Model: {model}\n\n"
        f"{note}\n\n"
        "## Rendered public transcript\n\n"
    )
    output.write_text(header + body + "\n", encoding="utf-8")


def main() -> None:
    if len(sys.argv) != 5:
        raise SystemExit("usage: build_reproducibility_package.py CHATGPT_HTML GROK_TEXT CLAUDE_TEXT OUTPUT_DIR")
    chatgpt_html, grok_text, claude_text, output_dir = map(Path, sys.argv[1:])
    output_dir.mkdir(parents=True, exist_ok=True)
    write_chatgpt(output_dir / "gpt-4o.md", extract_chatgpt(chatgpt_html))
    wrap_rendered(
        output_dir / "grok-4.md",
        "Grok 4 evaluation transcript",
        "Grok 4 (confirmed by the researcher and displayed by the public share)",
        GROK_URL,
        grok_text,
        "This is a verbatim text capture of the rendered public share, including the researcher prompts, pasted outputs, and Grok responses.",
    )
    wrap_rendered(
        output_dir / "claude-3.7-sonnet.md",
        "Claude 3.7 Sonnet evaluation transcript",
        "Claude 3.7 Sonnet (confirmed by the researcher)",
        CLAUDE_URL,
        claude_text,
        "This is a verbatim text capture of the rendered public share. Claude labels the uploaded input payloads as hidden in shared chats; its evaluator responses are present in full. The corresponding generated inputs are preserved under `../generated-outputs/`.",
    )


if __name__ == "__main__":
    main()
