"""Switch platform for Gecko."""
from .geckolib import GeckoBlower, GeckoPump
from homeassistant.components.switch import SwitchEntity

from .const import DOMAIN, ICON
from .entity import GeckoEntity


async def async_setup_entry(hass, entry, async_add_entities):
    """Setup sensor platform."""
    facade = hass.data[DOMAIN][entry.entry_id].facade
    entities = [GeckoBinarySwitch(entry, blower) for blower in facade.blowers] + [GeckoBinarySwitch(entry, pump) for pump in facade.pumps]
    async_add_entities(entities, True)

        
class GeckoBinarySwitch(GeckoEntity, SwitchEntity):
    """gecko switch class."""

    def __init__(self, config_entry, automation_entity):
        super().__init__(config_entry, automation_entity)

    async def async_turn_on(self, **kwargs):  
        """Turn on the switch."""
        if("waterfall" in self._automation_entity.unique_id.lower()):
            self._automation_entity.set_mode("ON")
        else:        
            self._automation_entity.set_mode("HI")

    async def async_turn_off(self, **kwargs): 
        """Turn off the switch."""
        self._automation_entity.set_mode("OFF")

    @property
    def icon(self):
        """Return the icon of this switch."""
        return "mdi:pump"

    @property
    def is_on(self):
        """Return true if the switch is on."""
        return self._automation_entity._state_sensor.state!="OFF"

