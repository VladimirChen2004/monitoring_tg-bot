#!/bin/bash
SESSION_NAME="monitor-bot"
BOT_DIR="$(cd "$(dirname "$0")/.." && pwd)"

# Kill existing session if running
tmux kill-session -t "$SESSION_NAME" 2>/dev/null

# Create new session
tmux new-session -d -s "$SESSION_NAME" -c "$BOT_DIR"

# Activate venv and start bot
tmux send-keys -t "$SESSION_NAME" "source venv/bin/activate && python -m bot" Enter

echo "Bot started in tmux session '$SESSION_NAME'"
echo "Attach with: tmux attach -t $SESSION_NAME"
