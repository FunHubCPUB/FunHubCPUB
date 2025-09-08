#!/bin/bash
# filepath: c:\Users\robot\FunHubCPUB\app\git_push_with_ssh.sh

# Start the SSH agent
eval "$(ssh-agent -s)"

# Add your SSH private key (not .pub!)
ssh-add ~/id_rsa.pub

# Stage all changes
git add .

# Commit with a message (use first argument or default)
COMMIT_MSG="${1:-Auto commit}"
git commit -m "$COMMIT_MSG"

# Push to remote
git push