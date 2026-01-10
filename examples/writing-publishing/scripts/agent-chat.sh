        #!/usr/bin/env bash
        set -euo pipefail

        if [ "$#" -lt 2 ]; then
          echo "Usage: $0 <role> <message>"
          exit 1
        fi

        role="$1"
        message="$2"
        log_dir="${LOG_DIR:-logs}"
        mkdir -p "$log_dir"
        timestamp=$(date -u +"%Y-%m-%dT%H:%M:%SZ")
        printf "[%s] [%s] %s
" "$timestamp" "$role" "$message" >> "$log_dir/agent-chat.log"
