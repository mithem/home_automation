"""A script meant to be invoked by pyscript (available via HACS)
hence so many symbols not found to be defined by syntax highlighters etc."""
# pylint: disable=undefined-variable
# mypy: ignore_errors

import aiohttp

URL = "http://192.168.0.197:8001/api/v1/create-things-task-to-update-hass"

@service
def create_task_in_things_to_update_hass():
    """Try to contact things_server in order to create a task to update hass."""
    log.debug("Trying to create task in things to update hass.")
    async with aiohttp.ClientSession() as session:
        async with session.post(URL) as response:
            if response.ok:
                log.info("Successfully created task in Things.")
            else:
                log.error(f"Invalid response: {response.text}")
