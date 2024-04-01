"""Water Heater module for the Heatmiser NetMonitor integration."""
from datetime import timedelta
import logging

import voluptuous as vol

from homeassistant.components.water_heater import (
    WaterHeaterEntityFeature,
    WaterHeaterEntity,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import STATE_OFF, STATE_ON, STATE_UNAVAILABLE, UnitOfTemperature
from homeassistant.core import HomeAssistant
from homeassistant.helpers import config_validation as cv, entity_platform
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.typing import ConfigType
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .heatmiser_hub import HeatmiserHub, HeatmiserStat
from .const import  DOMAIN
_LOGGER = logging.getLogger(__name__)

def setup_platform(hass: HomeAssistant, config: ConfigType) -> None:
    """Set up the Heatmiser platform."""
    # Assign configuration variables.
    # The configuration check takes care they are present.
    host = config["host"]
    username = config["username"]
    password = config["password"]

    hub = HeatmiserHub(host, username, password, hass)
    hub.get_devices_async()


async def async_setup_entry(hass: HomeAssistant, entry, async_add_entities):
    """Set up Heatmiser climate based on config_entry."""
    host = entry.data.get("host")
    username = entry.data.get("username")
    password = entry.data.get("password")
    hub = HeatmiserHub(host, username, password, hass)
    devices = await hub.get_devices_async()
    entities = []
    if devices:
        for stat in devices:
            if(stat.hw_timer_output!=STATE_UNAVAILABLE):
                entities.append(HeatmiserWaterHeater(stat, hub))

    async_add_entities(entities, True)

    platform = entity_platform.async_get_current_platform()

    platform.async_register_entity_service(
        "boost_hot_water",
        {
            vol.Optional("time_period", default="01:00:00"): vol.All(
                cv.time_period,
                cv.positive_timedelta,
                lambda td: td.total_seconds() // 3600,
            ),
        },
        "async_hot_water_boost",
    )


class HeatmiserWaterHeater(WaterHeaterEntity):
    """Heatmiser Water Heater Device."""

    def __init__(self, water_heater: HeatmiserStat, hub: HeatmiserHub) -> None:
        """Set up Heatmiser climate entity based on a stat."""
        self._attr_supported_features = WaterHeaterEntityFeature.ON_OFF
        self.water_heater = water_heater
        self.hub = hub
        self._attr_operation_list = [
            "gas",
            "off",
        ]

    @property
    def name(self):
        """Return the name of the water heater."""
        return self.water_heater.name +" Hot Water"

    @property
    def unique_id(self):
        """Return unique ID of entity."""
        return self.water_heater.id

    @property
    def temperature_unit(self):
        """Return the unit of measurement."""
        return UnitOfTemperature.CELSIUS

    @property
    def current_operation(self):
        """Return current operation."""
        return self.water_heater.hw_timer_output

    @property
    def icon(self):
        """Icon to use in the frontend, if any."""
        if(self.water_heater.hw_timer_output == STATE_ON):
            return "mdi:water-boiler"
        else:
            return "mdi:water-boiler-off"

    @property
    def supported_features(self):
        """Return the list of supported features."""
        return self._attr_supported_features

    @property
    def operation_list(self):
        """List of available operation modes."""
        return self._attr_operation_list

    async def async_turn_on(self, **kwargs):
        """Turn on hotwater."""
        await self.hub.set_boost_async(self.water_heater.name, 24)

    async def async_turn_off(self, **kwargs):
        """Turn off hotwater."""
        await self.hub.set_boost_async(self.water_heater.name, 0)

    async def async_set_operation_mode(self, operation_mode):
        """Set operation mode."""
        if (operation_mode==STATE_ON):
            await self.hub.set_boost_async(self.water_heater.name, 24)
        if (operation_mode==STATE_OFF):
            await self.hub.set_boost_async(self.water_heater.name, 0)

    async def async_hot_water_boost(self, time_period):
        """Handle the service call."""
        await self.hub.set_boost_async(self.water_heater.name, time_period)

    async def async_update(self):
        """Update all Node data."""
        new_heater_state = await self.hub.get_device_status_async(self.water_heater.name)
        if new_heater_state.hw_timer_output != None:
            new_heater_state.id = self.water_heater.id
            self.water_heater = new_heater_state

    @property
    def device_info(self) -> DeviceInfo:
        """Return the device info."""
        return DeviceInfo(
            identifiers={
                # Serial numbers are unique identifiers within a specific domain
                (DOMAIN, "heatmiser_nermonitor")
            },
            name="Netmonitor",
            manufacturer="Heatmiser",
        )



