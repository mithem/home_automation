# a script meant to be invoked by pyscript (available via HACS)
# hence so many symbols not found to be defined by syntax highlighters

import aiohttp

url = "http://192.168.2.197:8001/api/v1/create-things-task-to-update-hass"

@service
def create_task_in_things_to_update_hass():
    log.debug("Trying to create task in things to update hass.")
    async with aiohttp.ClientSession() as session:
        async with session.post(url) as r:
            if r.ok:
                log.info("Successfully created task in Things.")
            else:
                log.error(f"Invalid response: {r.text}")
