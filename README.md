[![CI status](https://github.com/mithem/home_automation/actions/workflows/main.yml/badge.svg)](https://github.com/mithem/home_automation/actions/workflows/main.yml)
[![CodeQL](https://github.com/mithem/home_automation/actions/workflows/codeql-analysis.yml/badge.svg)](https://github.com/mithem/home_automation/actions/workflows/codeql-analysis.yml)

# home_automation

A project for home automation. That's organizing and compressing homework on truenas and related scripts/programs or otherwise useful but maybe unrelated stuff.

## Configuration

Required configuration items are left blank (`<value>`), optional ones are populated with their default value.

```yaml
log_dir: <path to log dir>
homework_dir: <path to homework dir>
archive_dir: <path to archive dir>
compose_file: docker-compose.yml
moodle_dl_dir: <path to moodle dir> # dir where moodle-dl will download courses to
extra_compress_dirs: [] # extra dirs to watch and compress files in when applicable
storage:
  file: # either file or redis provider required
    path: <path to backend sqlite db>
  redis:
    host: <host>
    port: <port>
    username: (none)
    password: (none)
email:
  address: <email>
home_assistant:
  url: <url> # including scheme
  token: <token>
  insecure_https: false
  deployment: # need either this or the `portainer` key in order to support home assistant updates
    namespace: <k8s namespace>
    name: <deployment name>
  portainer:
    environment: <environment>
    stack: <stack>
portainer:
  url: <url> # including scheme
  username: <username>
  password: <password>
  insecure_https: false
kubernetes:
  url: <url> # to k8s control server, including scheme
  insecure_https: false
  api_key: <api key>
  ssl_ca_cert_path: <path to ca cert>
process:
  user: <user>
  group: <group>
things_server:
  url: <url> # including scheme
  insecure_https: false
api_server:
  interface: 127.0.0.1
  workers: 2
  ssl_cert_path: <path to cert>
  ssl_key_path: <path to private key>
runner:
  cron_user: <user>
git:
  discard_changes: false # discard changes on pull
  remotes: []
  branch: master # branch to pull
frontend:
  # image name to build & push, as well as use in the k8s deployment. If using a custom registry, make sure to prepend that (e.g. 'registry.com/frontend')
  image_name: home_automation_frontend
  namespace: default
  deployment_name: frontend
  service_name: frontend
  replicas: 1
  backend_ip_address: (autodetected) # ip address to reach backend server on (from the frontend pods)
docker:
  build:
    network: (some internal docker network) # may want to use 'host' if docker network environment is misconfigured/restricted
  registry:
    registry_url: <url> # including scheme
    auth:
      username: <username>
      password: <password>
heimdall:
  url: <url> # including scheme
```
