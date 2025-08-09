#!/usr/bin/env bash
set -e
echo "🔧 Setting up Git hooks..."
git config core.hooksPath .githooks
echo "✅ Git hooks path set to .githooks"

