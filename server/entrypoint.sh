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
  chmod 600 "$file" 2>/dev/null || true
}

# Anciennes clés par défaut, publiées dans le dépôt : traitées comme absentes
is_unset_or_default() {
  [ -z "$1" ] || [ "$1" = "$DEFAULT_API_KEYS_RAW" ]
}

persisted_api_keys="$(read_env_value "$PERSISTED_ENV_FILE" "API_KEYS_RAW" || true)"
app_env_api_keys="$(read_env_value "$APP_ENV_FILE" "API_KEYS_RAW" || true)"
current_api_keys="${API_KEYS_RAW:-}"

if ! is_unset_or_default "$current_api_keys"; then
  write_env_value "$PERSISTED_ENV_FILE" "API_KEYS_RAW" "$current_api_keys"
elif ! is_unset_or_default "$persisted_api_keys"; then
  export API_KEYS_RAW="$persisted_api_keys"
elif ! is_unset_or_default "$app_env_api_keys"; then
  export API_KEYS_RAW="$app_env_api_keys"
  write_env_value "$PERSISTED_ENV_FILE" "API_KEYS_RAW" "$app_env_api_keys"
else
  # Premier démarrage sans clé : deux clés aléatoires (widget, agent IA),
  # conservées dans le volume de données et affichées une seule fois.
  widget_key="widget-$(python -c 'import secrets; print(secrets.token_urlsafe(24))')"
  agent_key="agent-$(python -c 'import secrets; print(secrets.token_urlsafe(24))')"
  export API_KEYS_RAW="${widget_key},${agent_key}"
  write_env_value "$PERSISTED_ENV_FILE" "API_KEYS_RAW" "$API_KEYS_RAW"
  echo "==================================================================="
  echo "Clés API générées (affichées une seule fois, conservées dans $PERSISTED_ENV_FILE) :"
  echo "  Widget   : $widget_key"
  echo "  Agent IA : $agent_key"
  echo "Pour choisir vos propres clés : variable API_KEYS_RAW."
  echo "==================================================================="
fi

exec "$@"
