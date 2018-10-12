#!/usr/bin/env bash
if [ ! -z "$TOKEN" ]; then
  echo "[+] Using provided Telegram token."
  cat config/telegram.json.template|sed "s/ADD_BOT_TOKEN_HERE/$TOKEN/g" > config/telegram.json
else
  echo "[-] No Telegram token provided."
  exit 1
fi
exec python ./start.py "$@"
