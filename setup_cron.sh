#!/bin/bash
# AWT Launch Monitor - Cron Setup
# 하루 3회 (09:00, 15:00, 21:00) 텔레그램 알림 전송

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
LOG_DIR="$SCRIPT_DIR/logs"
PYTHON="$(which python3)"
MONITOR="$SCRIPT_DIR/monitor.py"

mkdir -p "$LOG_DIR"

CRON_CMD="$PYTHON $MONITOR --silent >> $LOG_DIR/\$(date +\%Y-\%m-\%d).log 2>&1"
CRON_SCHEDULE="0 9,15,21 * * * $CRON_CMD"

# Check if already installed
if crontab -l 2>/dev/null | grep -q "awt-launch-monitor"; then
    echo "Cron job already exists. Replacing..."
    crontab -l 2>/dev/null | grep -v "awt-launch-monitor" | crontab -
fi

# Install
(crontab -l 2>/dev/null; echo "# awt-launch-monitor"; echo "$CRON_SCHEDULE") | crontab -

echo "Cron job installed:"
echo "  Schedule: 09:00, 15:00, 21:00 daily"
echo "  Command:  python3 monitor.py --silent"
echo "  Logs:     $LOG_DIR/"
echo ""
echo "To verify: crontab -l"
echo "To remove: crontab -l | grep -v awt-launch-monitor | crontab -"
