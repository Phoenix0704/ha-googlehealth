import os
import voluptuous as vol
from homeassistant import config_entries
from homeassistant.const import CONF_FILE_PATH
from .const import DOMAIN

class GoogleHealthConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Steuert den Einrichtungsassistenten."""

    VERSION = 1

    async def async_step_user(self, user_input=None):
        errors = {}

        if user_input is not None:
            file_path = user_input[CONF_FILE_PATH]
            
            if not os.path.exists(file_path):
                errors["base"] = "file_not_found"
            else:
                await self.async_set_unique_id(file_path)
                self._abort_if_unique_id_configured()
                return self.async_create_entry(
                    title=f"Google Health ({os.path.basename(file_path)})", 
                    data=user_input
                )

        data_schema = vol.Schema({
            vol.Required(CONF_FILE_PATH): str,
        })

        return self.async_show_form(
            step_id="user", data_schema=data_schema, errors=errors
        )