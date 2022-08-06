"""Run just the backend server (gunicorn), not the frontend."""
import os

import home_automation.config as haconfig


def run_backend_server(config: haconfig.Config):
    """Run the WSGI gunicorn server (not the frontend)."""
    # sometimes running gunicorn from shell is just equivalent to but way easier than
    # reverse-engineering gunicorn to get an appropriate entrypoint

    # only bind to localhost so the API isn't exposed outside (if
    # I need that at any point, an https proxy is a way better idea)

    # proxy for certificate management (don't want to re-configure 20 services
    # once the certificate changes)
    interface = (
        config.api_server.interface if config.api_server.interface else "127.0.0.1"
    )
    workers = config.api_server.workers if config.api_server.workers else 2
    extra_flags = ""
    if config.api_server.valid_ssl():
        extra_flags += f"--certfile '{config.api_server.ssl_cert_path}'"
        extra_flags += f" --keyfile '{config.api_server.ssl_key_path}'"
    command = f"python3 -m gunicorn --pid /var/run/home_automation/gunicorn.pid -w '{workers}' \
--bind {interface}:10001 {extra_flags} 'home_automation.server.backend:create_app()'"
    os.system(command)


def main():
    """Main entrypoint, only for when running just gunicorn (not via runner)"""
    config = haconfig.load_config()
    run_backend_server(config)


if __name__ == "__main__":
    main()
