#!/usr/bin/env bash
set -euo pipefail

REPO="mnckapilan/odf-skills"
ALL_SKILLS=(ods odt)

# ── helpers ───────────────────────────────────────────────────────────────────

# Read from /dev/tty so interactive prompts work even when piped via curl | sh
ask() {
    printf "%s " "$1"
    read -r reply </dev/tty
    echo "$reply"
}

say() { echo "$@"; }

# ── parse flags / args ────────────────────────────────────────────────────────

SKILLS_ARG=()
LOCATION=""

while [[ $# -gt 0 ]]; do
    case "$1" in
        --local)  LOCATION="local";  shift ;;
        --global) LOCATION="global"; shift ;;
        --*)      say "Unknown flag: $1"; exit 1 ;;
        *)        SKILLS_ARG+=("$1"); shift ;;
    esac
done

# ── select skills ─────────────────────────────────────────────────────────────

if [ ${#SKILLS_ARG[@]} -gt 0 ]; then
    INSTALL=("${SKILLS_ARG[@]}")
else
    say ""
    say "Which skills would you like to install?"
    say "  1) ods  — OpenDocument Spreadsheet (.ods)"
    say "  2) odt  — OpenDocument Text (.odt)"
    say "  3) Both (default)"
    say ""
    choice=$(ask "Choice [3]:")
    case "${choice:-3}" in
        1)   INSTALL=(ods) ;;
        2)   INSTALL=(odt) ;;
        3)   INSTALL=("${ALL_SKILLS[@]}") ;;
        ods) INSTALL=(ods) ;;
        odt) INSTALL=(odt) ;;
        *)   say "Invalid choice."; exit 1 ;;
    esac
fi

# Validate skill names
for skill in "${INSTALL[@]}"; do
    valid=false
    for s in "${ALL_SKILLS[@]}"; do [ "$skill" = "$s" ] && valid=true && break; done
    if [ "$valid" = false ]; then
        say "Unknown skill: $skill. Available: ${ALL_SKILLS[*]}"
        exit 1
    fi
done

# ── select location ───────────────────────────────────────────────────────────

if [ -z "$LOCATION" ]; then
    say ""
    say "Install location:"
    say "  1) Global — ~/.claude/skills/  (available in all projects, default)"
    say "  2) Local  — ./.claude/skills/  (this project only)"
    say ""
    choice=$(ask "Choice [1]:")
    case "${choice:-1}" in
        1|global) LOCATION="global" ;;
        2|local)  LOCATION="local"  ;;
        *)        say "Invalid choice."; exit 1 ;;
    esac
fi

# ── resolve destination ───────────────────────────────────────────────────────

if [ -n "${CLAUDE_SKILLS_DIR:-}" ]; then
    SKILLS_DIR="$CLAUDE_SKILLS_DIR"
elif [ "$LOCATION" = "local" ]; then
    SKILLS_DIR="$(pwd)/.claude/skills"
else
    SKILLS_DIR="$HOME/.claude/skills"
fi

# ── download and install ──────────────────────────────────────────────────────

TMP=$(mktemp -d)
trap 'rm -rf "$TMP"' EXIT

say ""
say "Downloading odf-skills..."
curl -fsSL "https://github.com/$REPO/archive/refs/heads/main.tar.gz" \
    | tar -xz -C "$TMP" --strip-components=1

mkdir -p "$SKILLS_DIR"

for skill in "${INSTALL[@]}"; do
    dest="$SKILLS_DIR/$skill"
    if [ -d "$dest" ]; then
        say "Updating  $skill → $dest"
    else
        say "Installing $skill → $dest"
    fi
    rm -rf "$dest"
    mkdir -p "$dest/scripts"
    cp "$TMP/$skill/SKILL.md"          "$dest/SKILL.md"
    cp "$TMP/$skill/scripts/$skill.py" "$dest/scripts/$skill.py"
done

say ""
cmds=$(printf "/%s " "${INSTALL[@]}"); cmds="${cmds% }"
say "Done. Invoke with ${cmds// / or /} in your agent."
