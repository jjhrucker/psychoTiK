#!/bin/bash
# deploy.sh — commit everything and push to GitHub Pages
# Usage: ./deploy.sh "your commit message"
#        ./deploy.sh           (uses a timestamped default message)

set -e

MSG="${1:-Update $(date '+%Y-%m-%d %H:%M')}"

git add -A
git commit -m "$MSG"
git push origin main

echo ""
echo "✓ Pushed. Live at: https://jjhrucker.github.io/psychoTiK/psychopharmacology_tool.html"
