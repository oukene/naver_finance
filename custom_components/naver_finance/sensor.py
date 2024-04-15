"""Platform for sensor integration."""
# This file shows the setup for the sensors associated with the cover.
# They are setup in the same way with the call to the async_setup_entry function
# via HA from the module __init__. Each sensor has a device_class, this tells HA how
# to display it in the UI (for know types). The unit_of_measurement property tells HA
# what the unit is, so it can display the correct range. For predefined types (such as
# battery), the unit_of_measurement should match what's expected.
import ssl
import logging
from threading import Timer
import aiohttp

import json
import asyncio

from .const import *
from homeassistant.helpers.entity import async_generate_entity_id
from homeassistant.components.sensor import SensorEntity
from bs4 import BeautifulSoup as bs
from datetime import datetime
import traceback


_LOGGER = logging.getLogger(__name__)

# See cover.py for more details.
# Note how both entities for each roller sensor (battry and illuminance) are added at
# the same time to the same list. This way only a single async_add_devices call is
# required.

ENTITY_ID_FORMAT = DOMAIN + ".{}"

async def async_setup_entry(hass, config_entry, async_add_devices):
    """Add sensors for passed config_entry in HA."""

    hass.data[DOMAIN]["listener"] = []
    
    device = hass.data[DOMAIN]["device"]

    new_devices = []

    for entity in config_entry.options.get(CONF_KEYWORDS, {}):
        new_devices.append(
            NaverFinanceSensor(
                hass,
                config_entry,
                device,
                entity.get(CONF_WORD),
                entity.get(CONF_UNIT),
                entity.get(CONF_IMAGE),
                entity.get(CONF_REFRESH_PERIOD),
            )
        )

    if new_devices:
        async_add_devices(new_devices)


class Device:
    def __init__(self, name, entry_id):
        """Init dummy roller."""
        self._id = entry_id
        self.name = name
        self._callbacks = set()
        self._loop = asyncio.get_event_loop()
        # Reports if the roller is moving up or down.
        # >0 is up, <0 is down. This very much just for demonstration.

        # Some static information about this device
        self.firmware_version = VERSION
        self.model = NAME
        self.manufacturer = NAME
        self._entities = {}

    @property
    def device_id(self):
        """Return ID for roller."""
        return self._id

    def register_callback(self, callback):
        """Register callback, called when Roller changes state."""
        self._callbacks.add(callback)

    def remove_callback(self, callback):
        """Remove previously registered callback."""
        self._callbacks.discard(callback)

    # In a real implementation, this library would call it's call backs when it was
    # notified of any state changeds for the relevant device.
    async def publish_updates(self):
        """Schedule call all registered callbacks."""
        for callback in self._callbacks:
            callback()

    def publish_updates(self):
        """Schedule call all registered callbacks."""
        for callback in self._callbacks:
            callback()

    def add_entity(self, word, entity):
        self._entities[word] = entity

    async def refresh(self):
        for k, v in self._entities.items():
            await v.get_price()


# This base class shows the common properties and methods for a sensor as used in this
# example. See each sensor for further details about properties and methods that
# have been overridden.


class SensorBase(SensorEntity):
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
    @property
    def available(self) -> bool:
        """Return True if roller and hub is available."""
        return True

    async def async_added_to_hass(self):
        """Run when this Entity has been added to HA."""
        # Sensors should also register callbacks to HA when their state changes
        self._device.register_callback(self.async_write_ha_state)

    async def async_will_remove_from_hass(self):
        """Entity being removed from hass."""
        # The opposite of async_added_to_hass. Remove any registered call backs here.
        self._device.remove_callback(self.async_write_ha_state)


class NaverFinanceSensor(SensorBase):
    """Representation of a Thermal Comfort Sensor."""
    _attr_has_entity_name = True
    
    def __init__(self, hass, config, device, word, unit, image, refresh_period):
        """Initialize the sensor."""
        super().__init__(device)

        self.hass = hass
        self._word = word

        self.entity_id = async_generate_entity_id(
            ENTITY_ID_FORMAT, "{}_{}_{}".format(NAME, config.entry_id, word), hass=hass)
        self._attr_unique_id = async_generate_entity_id(
            ENTITY_ID_FORMAT, "{}_{}_{}".format(NAME, config.entry_id, word), hass=hass)
        self._attr_name = "{}".format(word)
        self._attr_unit_of_measurement = "KRW"
        self._attr_extra_state_attributes = {}
        self._attr_unit_of_measurement = unit
        self._refresh_period = refresh_period
        self._attr_entity_picture = image if image != "" else None
        # self._device_class = SENSOR_TYPES[sensor_type][0]
        self._device = device
        
        self._url = CONF_URL + str(self._word) + "시세"
        self._attr_extra_state_attributes["URL"] = self._url

        self._device.add_entity(word, self)

        self._loop = asyncio.get_event_loop()
        Timer(1, self.refreshTimer).start()
    
    def refreshTimer(self):
        self._loop.create_task(self.get_price())
        Timer(self._refresh_period*60, self.refreshTimer).start()


    async def get_price(self):
        try:
            custom_ssl_context = ssl.create_default_context(ssl.Purpose.SERVER_AUTH)
            custom_ssl_context.options |= 0x00040000

            connector = aiohttp.TCPConnector(ssl=custom_ssl_context)
            async with aiohttp.ClientSession(connector=connector) as session:
                async with session.get(self._url) as response:
                    raw_data = await response.read()
                    soup = bs(raw_data, 'html.parser')
                    price = soup.select_one(".spt_con strong").text
                    text = soup.select_one(".spt_con").select_one(".n_ch").select_one(".blind").text
                    updown = soup.select_one(".spt_con").select_one(".n_ch").select_one(".ico").text
                    beforeday = text + " " + soup.select_one(".spt_con").select_one(".n_ch").select("em")[0].text + (self._attr_unit_of_measurement if self._attr_unit_of_measurement is not None else "") + updown + soup.select_one(".spt_con").select_one(".n_ch").select("em")[1].text
                    self._attr_native_value = price.replace(",", "")
                    self._attr_extra_state_attributes["before_day"] = beforeday

            self._attr_extra_state_attributes["last_refresh_time"] = datetime.now().strftime("%Y-%m-%d %H:%M")
            self._attr_extra_state_attributes["refresh_period"] = self._refresh_period
            self._device.publish_updates()
        except Exception as e:
            _LOGGER.error("get price error : " + traceback.format_exc())

        finally:
            """"""
            
    """Sensor Properties"""
    @property
    def entity_picture(self):
        return self._attr_entity_picture

    @property
    def native_unit_of_measurement(self) -> str | None:
        return self._attr_unit_of_measurement
