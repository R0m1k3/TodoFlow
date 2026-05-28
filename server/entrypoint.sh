#!/bin/sh
set -eu

DEFAULT_API_KEYS_RAW="widget-token-secure-789,ai-agent-token-secure-101"
PERSISTED_ENV_FILE="${PERSISTED_ENV_FILE:-/app/data/.env}"
APP_ENV_FILE="${APP_ENV_FILE:-/app/.env}"

read_env_value() {
  file="$1"
  name="$2"

  if [ ! -f "$file" ]; then
    return 0
  fi

  sed -n "s/^[[:space:]]*${name}[[:space:]]*=[[:space:]]*//p" "$file" \
    | tail -n 1 \
    | sed 's/^"//; s/"$//; s/^'\''//; s/'\''$//'
}

write_env_value() {
  file="$1"
  name="$2"
  value="$3"

  mkdir -p "$(dirname "$file")"

  if [ -f "$file" ] && grep -q "^[[:space:]]*${name}[[:space:]]*=" "$file"; then
    escaped_value=$(printf '%s' "$value" | sed 's/[\/&]/\\&/g')
    sed -i "s/^[[:space:]]*${name}[[:space:]]*=.*/${name}=${escaped_value}/" "$file"
  else
    printf '%s=%s\n' "$name" "$value" >> "$file"
  fi
}

persisted_api_keys="$(read_env_value "$PERSISTED_ENV_FILE" "API_KEYS_RAW" || true)"
app_env_api_keys="$(read_env_value "$APP_ENV_FILE" "API_KEYS_RAW" || true)"
current_api_keys="${API_KEYS_RAW:-}"

if [ -n "$persisted_api_keys" ] && { [ -z "$current_api_keys" ] || [ "$current_api_keys" = "$DEFAULT_API_KEYS_RAW" ]; }; then
  export API_KEYS_RAW="$persisted_api_keys"
elif [ -n "$app_env_api_keys" ] && { [ -z "$current_api_keys" ] || [ "$current_api_keys" = "$DEFAULT_API_KEYS_RAW" ]; }; then
  export API_KEYS_RAW="$app_env_api_keys"
  if [ "$app_env_api_keys" != "$DEFAULT_API_KEYS_RAW" ]; then
    write_env_value "$PERSISTED_ENV_FILE" "API_KEYS_RAW" "$app_env_api_keys"
  fi
elif [ -n "$current_api_keys" ] && [ "$current_api_keys" != "$DEFAULT_API_KEYS_RAW" ]; then
  write_env_value "$PERSISTED_ENV_FILE" "API_KEYS_RAW" "$current_api_keys"
fi

exec "$@"
