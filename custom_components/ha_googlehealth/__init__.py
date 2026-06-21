"""Die Google Health Custom Integration mit Config Flow Unterstützung."""
import logging
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)

PLATFORMS = ["sensor"]

async def async_setup(hass: HomeAssistant, config: dict):
    """Setzt die Komponente via YAML auf (wird für Abwärtskompatibilität benötigt)."""
    return True

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Setzt eine Instanz über die Benutzeroberfläche auf."""
    hass.data.setdefault(DOMAIN, {})
    
    # Weiterleitung an die sensor.py Plattform
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True

async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Entfernt eine Instanz sauber aus Home Assistant."""
    return await hass.config_entries.async_unload_platforms(entry, PLATFORMS)