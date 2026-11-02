#!/usr/bin/env bash
# SessionStart: a marker check only, a few milliseconds. Prints one line of context for Claude.
D="${REEL_STUDIO_DATA:-$CLAUDE_PLUGIN_DATA}"
# commands from the Bash tool do not get CLAUDE_PLUGIN_DATA, so reel-tool reads it from this pointer
if [ -n "$CLAUDE_PLUGIN_DATA" ]; then
  mkdir -p "$CLAUDE_PLUGIN_DATA" 2>/dev/null
  printf '%s' "$CLAUDE_PLUGIN_DATA" > "$(dirname "$CLAUDE_PLUGIN_DATA")/.reel-studio-data" 2>/dev/null
fi
if grep -q '"whisper"' "$D/env/setup_state.json" 2>/dev/null; then
  echo "Reel Studio is ready. For ANY request to edit, cut, subtitle or animate a video, in any language, however short, use the reel-edit skill (reel-tool does the machine work; run it with the Bash tool)."
else
  echo "Reel Studio is installed but not set up yet. If the user wants to edit a video, tell them to run /reel-setup first (it installs 5-8 GB into the plugin's data folder)."
fi
exit 0
