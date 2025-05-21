import logging
import requests
from homeassistant.components.light import LightEntity
from homeassistant.const import STATE_OFF, STATE_ON, STATE_UNKNOWN
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed
from datetime import timedelta

# Logger
_LOGGER = logging.getLogger(__name__)

def setup_platform(hass, config, add_entities, discovery_info=None):
    """Set up the Crestron light platform."""
    crestron_data = hass.data["crestron_controller"]
    coordinator = CrestronLightDataUpdateCoordinator(hass, crestron_data)
    devices = coordinator.data.get("lights", [])
    if not devices:
        _LOGGER.debug("No lights found")
    else:
        _LOGGER.debug("Lights found: %s", devices)
        add_entities(CrestronLight(coordinator, light) for light in devices)

class CrestronLightDataUpdateCoordinator(DataUpdateCoordinator):
    """Class to manage fetching Crestron light data."""
    def __init__(self, hass, crestron_data):
        """Initialize."""
        self.base_url = crestron_data["base_url"]
        self.auth_key = crestron_data["auth_key"]
        super().__init__(
            hass,
            _LOGGER,
            name="Crestron Light",
            update_interval=timedelta(seconds=30),
        )
        self.data = {}
    async def _async_update_data(self):
        """Fetch data from Crestron API."""
        try:
            response = requests.get(f"{self.base_url}/cws/api/lights", headers={"Crestron-RestAPI-AuthKey": self.auth_key})
            if response.status_code != 200:
                raise UpdateFailed(f"Error fetching data: {response.status_code}")
            return response.json()
        except Exception as err:
            raise UpdateFailed(f"Error fetching data: {err}")
        
class CrestronLight(LightEntity):
    """Representation of a Crestron light."""

    def __init__(self, coordinator, light):
        """Initialize the light."""
        self.coordinator = coordinator
        self._light = light
        self._state = STATE_UNKNOWN

    @property
    def name(self):
        """Return the name of the light."""
        return self._light["name"]
    
    @property
    def is_on(self):
        """Return True if the light is on."""
        return self._state == STATE_ON
    
    @property
    def unique_id(self):
        """Return a unique ID for this light."""
        return self._light["id"]
    
    @property
    def should_poll(self):
        """Return False if the entity should not be polled."""
        return True
    async def async_turn_on(self, **kwargs):
        """Turn the light on."""
        try:
            response = requests.post(f"{self.coordinator.base_url}/cws/api/lights/{self._light['id']}/on", headers={"Crestron-RestAPI-AuthKey": self.coordinator.auth_key})
            if response.status_code == 200:
                self._state = STATE_ON
                self.async_write_ha_state()
            else:
                _LOGGER.error("Failed to turn on light: %s", response.status_code)
        except Exception as err:
            _LOGGER.error("Error turning on light: %s", err)
    async def async_turn_off(self, **kwargs):
        """Turn the light off."""
        try:
            response = requests.post(f"{self.coordinator.base_url}/cws/api/lights/{self._light['id']}/off", headers={"Crestron-RestAPI-AuthKey": self.coordinator.auth_key})
            if response.status_code == 200:
                self._state = STATE_OFF
                self.async_write_ha_state()
            else:
                _LOGGER.error("Failed to turn off light: %s", response.status_code)
        except Exception as err:
            _LOGGER.error("Error turning off light: %s", err)
    async def async_update(self):
        """Update the light state."""
        try:
            response = requests.get(f"{self.coordinator.base_url}/cws/api/lights/{self._light['id']}", headers={"Crestron-RestAPI-AuthKey": self.coordinator.auth_key})
            if response.status_code == 200:
                data = response.json()
                self._state = STATE_ON if data["state"] == "on" else STATE_OFF
                self.async_write_ha_state()
            else:
                _LOGGER.error("Failed to update light: %s", response.status_code)
        except Exception as err:
            _LOGGER.error("Error updating light: %s", err)


