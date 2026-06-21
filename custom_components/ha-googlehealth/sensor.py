import logging
import sqlite3
from datetime import timedelta
import voluptuous as vol

from homeassistant.components.sensor import SensorEntity, PLATFORM_SCHEMA
import homeassistant.helpers.config_validation as cv
from homeassistant.const import CONF_FILE_PATH
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)

SCAN_INTERVAL = timedelta(minutes=15)

PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend({
    vol.Required(CONF_FILE_PATH): cv.string,
})

async def async_setup_platform(hass, config, async_add_entities, discovery_info=None):
    """Setzt die GoogleHealth Sensoren via YAML auf."""
    db_path = config.get(CONF_FILE_PATH)

    # Der Coordinator steuert das zentrale Update-Intervall
    async def async_update_data():
        try:
            return await hass.async_add_executor_job(get_db_metrics, db_path)
        except Exception as err:
            raise UpdateFailed(f"Fehler beim Lesen der Datenbank: {err}")

    coordinator = DataUpdateCoordinator(
        hass,
        _LOGGER,
        name="googlehealth_metrics",
        update_method=async_update_data,
        update_interval=SCAN_INTERVAL,
    )

    # Erstes Update triggern
    await coordinator.async_config_entry_first_refresh()

    # Sensoren definieren (Spaltenname, Anzeigename, Einheit, Icon)
    sensor_types = [
        ("recovery", "AirMG Recovery", "%", "mdi:battery-heart"),
        ("strain", "AirMG Strain", "", "mdi:fire"),
        ("sleep", "AirMG Sleep Score", "%", "mdi:sleep"),
    ]

    entities = [
        AirMGSensor(coordinator, col, name, unit, icon)
        for col, name, unit, icon in sensor_types
    ]

    async_add_entities(entities, True)


def get_db_metrics(db_path):
    """Reine Python-Funktion zum Auslesen der SQLite-Datenbank (wird im Executor ausgeführt)."""
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT recovery, strain, sleep FROM metrics ORDER BY date DESC LIMIT 1")
        row = cursor.fetchone()
        return dict(row) if row else {}
    finally:
        conn.close()


class AirMGSensor(SensorEntity):
    """Repräsentation eines AirMG Sensors."""

    def __init__(self, coordinator, column, name, unit, icon):
        self.coordinator = coordinator
        self._column = column
        self._attr_name = name
        self._attr_native_unit_of_measurement = unit
        self._attr_icon = icon

    @property
    def should_poll(self):
        """Der Coordinator übernimmt das Polling."""
        return False

    @property
    def available(self):
        """Verfügbarkeit vom Status des Coordinators ableiten."""
        return self.coordinator.last_update_success

    @property
    def native_value(self):
        """Gibt den Wert aus den gecachten Coordinator-Daten zurück."""
        if self.coordinator.data:
            return self.coordinator.data.get(self._column)
        return None

    async def async_added_to_hull(self):
        """Sensor beim Coordinator registrieren."""
        self.async_on_remove(
            self.coordinator.async_add_listener(self.async_write_ha_state)
        )

    async def async_update(self):
        """Aktualisiert den Sensor über den Coordinator."""
        await self.coordinator.async_request_refresh()