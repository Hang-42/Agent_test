#!/usr/bin/env bash
set -eo pipefail
export DSH_HOME=/out/dsh
export FAMILY_AGENT_LOCAL_DEMO=1
export DEEPSEEK_API_KEY="$(cat /run/secrets/deepseek)"
mkdir -p "$DSH_HOME" /out/state
if [ ! -f "$DSH_HOME/profiles/superagent/cordis.patch.yml" ]; then
  dsh superagent --from-default-profile web --dump-config >/dev/null
  dsh plugin --profile superagent add 'link:/opt/dsh-superagent'
  cat > "$DSH_HOME/profiles/superagent/cordis.patch.yml" <<'EOF'
- id: webserver
  config:
    host: 127.0.0.1
    port: 3082
- id: dsh-superagent
  config:
    stateDir: /out/state
- id: dsh-superagent-github
  disabled: true
EOF
fi
exec dsh superagent --no-open
