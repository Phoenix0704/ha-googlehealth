import logging
import sqlite3
from datetime import timedelta

from homeassistant.components.sensor import SensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.const import CONF_FILE_PATH
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)

SCAN_INTERVAL = timedelta(minutes=15)

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry, async_add_entities):
    """Setzt die Google Health Sensoren basierend auf dem UI Config Entry auf."""
    db_path = entry.data[CONF_FILE_PATH]

    async def async_update_data():
        try:
            return await hass.async_add_executor_job(get_db_metrics, db_path)
        except Exception as err:
            raise UpdateFailed(f"Fehler beim Lesen der Datenbank: {err}")

    coordinator = DataUpdateCoordinator(
        hass,
        _LOGGER,
        name=f"googlehealth_metrics_{entry.entry_id}",
        update_method=async_update_data,
        update_interval=SCAN_INTERVAL,
    )

    # Ersten Abruf direkt beim Start erzwingen
    await coordinator.async_config_entry_first_refresh()

    sensor_types = [
        ("recovery", "Recovery", "%", "mdi:battery-heart"),
        ("strain", "Strain", "", "mdi:fire"),
        ("sleep", "Sleep Score", "%", "mdi:sleep"),
    ]

    entities = [
        GoogleHealthSensor(coordinator, col, name, unit, icon, entry.entry_id)
        for col, name, unit, icon in sensor_types
    ]

    async_add_entities(entities, True)


def get_db_metrics(db_path):
    """Liest die aktuellsten Metriken aus der SQLite-Datenbank."""
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT recovery, strain, sleep FROM metrics ORDER BY date DESC LIMIT 1")
        row = cursor.fetchone()
        return dict(row) if row else {}
    finally:
        conn.close()


class GoogleHealthSensor(SensorEntity):
    """Repräsentation eines Google Health Sensors."""

    def __init__(self, coordinator, column, name, unit, icon, entry_id):
        self.coordinator = coordinator
        self._column = column
        self._attr_name = name
        self._attr_native_unit_of_measurement = unit
        self._attr_icon = icon
        # Vergabe einer unique_id erlaubt die Verwaltung via UI
        self._attr_unique_id = f"{entry_id}_{column}"

    @property
    def should_poll(self):
        return False

    @property
    def available(self):
        return self.coordinator.last_update_success

    @property
    def native_value(self):
        if self.coordinator.data:
            return self.coordinator.data.get(self._column)
        return None

    async def async_added_to_hass(self):
        """Sensor beim DataUpdateCoordinator registrieren."""
        self.async_on_remove(
            self.coordinator.async_add_listener(self.async_write_ha_state)
        )

    async def async_update(self):
        """Aktualisiert den Sensor über den Coordinator."""
        await self.coordinator.async_request_refresh()