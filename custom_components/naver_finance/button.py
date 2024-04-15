"""Platform for sensor integration."""
# This file shows the setup for the sensors associated with the cover.
# They are setup in the same way with the call to the async_setup_entry function
# via HA from the module __init__. Each sensor has a device_class, this tells HA how
# to display it in the UI (for know types). The unit_of_measurement property tells HA
# what the unit is, so it can display the correct range. For predefined types (such as
# battery), the unit_of_measurement should match what's expected.
import logging
from xmlrpc.client import boolean
from .const import *
from homeassistant.helpers.entity import async_generate_entity_id
from homeassistant.components.button import ButtonEntity


_LOGGER = logging.getLogger(__name__)

# See cover.py for more details.
# Note how both entities for each roller sensor (battry and illuminance) are added at
# the same time to the same list. This way only a single async_add_devices call is
# required.

ENTITY_ID_FORMAT = DOMAIN + ".{}"


async def async_setup_entry(hass, config_entry, async_add_devices):
    """Add sensors for passed config_entry in HA."""

    device = hass.data[DOMAIN]["device"]

    new_devices = []

    button = NaverFinanceButton(hass, config_entry, device)
    new_devices.append(button)

    async_add_devices(new_devices)


# This base class shows the common properties and methods for a sensor as used in this
# example. See each sensor for further details about properties and methods that
# have been overridden.


class ButtonBase(ButtonEntity):
    """Base representation of a Hello World Sensor."""

    should_poll = False

    def __init__(self, device):
        """Initialize the sensor."""
        self._device = device
    # To link this entity to the cover device, this property must return an
    # identifiers value matching that used in the cover, but no other information such
    # as name. If name is returned, this entity will then also become a device in the
    # HA UI.

    @property
    def device_info(self):
        """Information about this entity/device."""
        return {
            "identifiers": {(DOMAIN, self._device.device_id)},
            # If desired, the name for the device could be different to the entity
            "name": self._device.name,
            "sw_version": self._device.firmware_version,
            "model": self._device.model,
            "manufacturer": self._device.manufacturer
        }

    # This property is important to let HA know if this entity is online or not.
    # If an entity is offline (return False), the UI will refelect this.
    # @property
    # def available(self) -> bool:
    #     """Return True if roller and hub is available."""
    #     return self._device.available

    async def async_added_to_hass(self):
        """Run when this Entity has been added to HA."""
        # Sensors should also register callbacks to HA when their state changes
        self._device.register_callback(self.async_write_ha_state)

    async def async_will_remove_from_hass(self):
        """Entity being removed from hass."""
        # The opposite of async_added_to_hass. Remove any registered call backs here.
        self._device.remove_callback(self.async_write_ha_state)


class NaverFinanceButton(ButtonBase):
    """Representation of a Thermal Comfort Sensor."""
    _attr_has_entity_name = True

    def __init__(self, hass, config, device):
        """Initialize the sensor."""
        super().__init__(device)

        self.hass = hass

        self.entity_id = async_generate_entity_id(
            ENTITY_ID_FORMAT, "{}_{}_{}".format(DOMAIN, config.entry_id, "refresh"), hass=hass)
        self._attr_name = "{}".format("refresh")

        # self._device_class = SENSOR_TYPES[sensor_type][0]
        self._attr_unique_id = self.entity_id
        self._device = device

    def press(self):
        self._device._loop.create_task(self._device.refresh())

    def update(self):
        """Update the state."""
