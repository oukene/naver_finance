"""Config flow for Hello World integration."""
from homeassistant.helpers import selector
from homeassistant.helpers.selector import EntityFilterSelectorConfig
import logging
import voluptuous as vol
from typing import Any, Dict, Optional
from datetime import datetime


from homeassistant.helpers import (
    device_registry as dr,
    entity_registry as er,
)

import homeassistant.helpers.config_validation as cv

from homeassistant.helpers.device_registry import (
    async_get,
    async_entries_for_config_entry
)

from .const import *

from homeassistant import config_entries, exceptions
from homeassistant.core import callback


_LOGGER = logging.getLogger(__name__)


class ConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Hello World."""

    VERSION = 1
    CONNECTION_CLASS = config_entries.CONN_CLASS_CLOUD_POLL
    data: Optional[Dict[str, Any]]

    async def async_step_user(self, user_input: Optional[Dict[str, Any]] = None):
        """Handle the initial step."""
        errors = {}
        
        #if self._async_current_entries():
            #return self.async_abort(reason="single_instance_allowed")
        #if self.hass.data.get(DOMAIN):
        #    return self.async_abort(reason="single_instance_allowed")

        if user_input is not None:
            self.data = user_input
            self.data[CONF_KEYWORDS] = []
            return self.async_create_entry(title=NAME, data=self.data)

        # If there is no user input or there were errors, show the form again, including any errors that were found with the input.
        return self.async_show_form(
            step_id="user", data_schema=vol.Schema(
                {
                }), errors=errors
        )

    @staticmethod
    @callback
    def async_get_options_flow(config_entry):
        """Handle a option flow."""
        return OptionsFlowHandler(config_entry)


class OptionsFlowHandler(config_entries.OptionsFlow):
    """Handles options flow for the component."""

    def __init__(self, config_entry) -> None:
        self.config_entry = config_entry
        self._selected_option = {}
        self.data = {}
        self.data[CONF_KEYWORDS] = config_entry.options.get(CONF_KEYWORDS, [])

    async def async_step_init(
        self, user_input: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """Manage the options for the custom component."""
        errors: Dict[str, str] = {}

        if user_input is not None:
            if not errors:
                if user_input.get(CONF_OPTION_SELECT) == CONF_OPTION_MODIFY:
                    return await self.async_step_select()
                elif user_input.get(CONF_OPTION_SELECT) == CONF_OPTION_ADD:
                    return await self.async_step_entity()

        options_schema = vol.Schema(
            {
                vol.Optional(CONF_OPTION_SELECT): selector.SelectSelector(selector.SelectSelectorConfig(options=CONF_OPTIONS, mode=selector.SelectSelectorMode.LIST, translation_key=CONF_OPTION_SELECT)),
                #vol.Optional(CONF_KEYWORDS, None): selector.EntitySelector(selector.EntitySelectorConfig(filter=EntityFilterSelectorConfig(integration=DOMAIN), multiple=False)),
                #vol.Optional(CONF_KEYWORDS, default=list(all_entities)): cv.multi_select(all_entities),
                #vol.Optional(CONF_ADD_ANODHER): cv.boolean,
            }
        )

        return self.async_show_form(
            step_id="init", data_schema=options_schema, errors=errors
        )

    async def async_step_select(
        self, user_input: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """Manage the options for the custom component."""
        errors: Dict[str, str] = {}

        if user_input is not None:
            _LOGGER.debug("user input is not None")
            if not errors:
                # index = user_input.get(CONF_OPTION_ENTITIES).split(". ")[0]
                # _LOGGER.debug("options : " + str(self._options))
                # self._selected_option = self._options[int(index)]

                entity_id = user_input.get(CONF_OPTION_ENTITIES)
                entity = er.async_get(self.hass).async_get(entity_id)
                _LOGGER.debug("entity : " + str(entity))
                conf = []
                for k in self.data[CONF_KEYWORDS]:
                    if entity.original_name == k.get(CONF_WORD):
                        conf = k
                        break
        
                # _LOGGER.debug("option delete : " + str(user_input.get(CONF_OPTION_DELETE)))
                if user_input.get(CONF_OPTION_DELETE):
                    er.async_get(self.hass).async_remove(entity_id=entity_id)

                    try:
                        self.data[CONF_KEYWORDS].remove(conf)
                    except:
                        """"""
                    _LOGGER.debug("delete option : " + str(self.data))
                    self.data["modifydatetime"] = datetime.now()
                    return self.async_create_entry(title=NAME, data=self.data)
                    

                    #self.data[CONF_KEYWORDS].remove(self._selected_option)
                    
                    # entities = er.async_entries_for_config_entry(
                    #     er.async_get(self.hass), self.config_entry.entry_id)

                    # self.data["modifydatetime"] = datetime.now()
                    # return self.async_create_entry(title=NAME, data=self.data)
                else:
                    self._selected_option = conf
                    _LOGGER.debug("selected option : " + str(self._selected_option))
                    return await self.async_step_entity()

        # keywords = []
        # index = 1
        # _LOGGER.debug("make list")
        
        # for k in self.data[CONF_KEYWORDS]:
        #     keywords.append(str(index) + ". " + k.get(CONF_WORD))
        #     self._options[index] = k
        #     ++index

        # _LOGGER.debug("keywords : " + str(keywords))
        option_entities = []
        entities = er.async_entries_for_config_entry(
            er.async_get(self.hass), self.config_entry.entry_id)
        for e in entities:
            option_entities.append(e.entity_id)
        _LOGGER.debug("entities : " + str(entities))
        options_schema = vol.Schema(
            {
                #vol.Optional(CONF_OPTION_ENTITIES): selector.SelectSelector(selector.SelectSelectorConfig(options=keywords, mode=selector.SelectSelectorMode.LIST)),
                vol.Optional(CONF_OPTION_ENTITIES): selector.EntitySelector(selector.EntitySelectorConfig(include_entities=option_entities)),
                vol.Optional(CONF_OPTION_DELETE): selector.BooleanSelector(selector.BooleanSelectorConfig())
            }
        )

        return self.async_show_form(
            step_id="select", data_schema=options_schema, errors=errors
        )

    async def async_step_entity(self, user_input: Optional[Dict[str, Any]] = None):
        """Second step in config flow to add a repo to watch."""
        errors: Dict[str, str] = {}
        if user_input is not None:
            if not errors:
                _LOGGER.debug("selected_option : " + str(self._selected_option))
                if len(self._selected_option) <= 0:
                    for k in self.data[CONF_KEYWORDS]:
                        if k.get(CONF_WORD) == user_input.get(CONF_WORD):
                            return self.async_abort(reason="already_input_keyword")
                elif self._selected_option:
                    for k in self.data[CONF_KEYWORDS]:
                        if self._selected_option.get(CONF_WORD) == k.get(CONF_WORD):
                            self.data[CONF_KEYWORDS].remove(k)
                            break

                _LOGGER.debug("user input : " + str(user_input.get(CONF_IMAGE)))
                # Input is valid, set data.
                self.data[CONF_KEYWORDS].append(
                    {
                        CONF_WORD: user_input.get(CONF_WORD),
                        CONF_UNIT: user_input.get(CONF_UNIT, None),
                        CONF_IMAGE: user_input.get(CONF_IMAGE, None),
                        CONF_REFRESH_PERIOD: user_input.get(
                            CONF_REFRESH_PERIOD, REFRESH_MIN),
                    }
                )
                _LOGGER.debug("modify data : " + str(self.data[CONF_KEYWORDS]))

                # If user ticked the box show this form again so they can add an
                # additional repo.
                # if user_input.get(CONF_OPTION_ADD, False):
                #     return await self.async_step_entity()
                # User is done adding repos, create the config entry.
                _LOGGER.debug("call async_create_entry")
                self.data["modifydatetime"] = datetime.now()
                return self.async_create_entry(title=NAME, data=self.data)

        _LOGGER.debug(
            "selected option : " + str(self._selected_option))
        return self.async_show_form(
            step_id="entity",
            data_schema=vol.Schema(
                    {
                        vol.Required(CONF_WORD, default=self._selected_option.get(CONF_WORD, None)): cv.string,
                        #vol.Optional(CONF_UNIT, default=self._selected_option.get(CONF_UNIT, "krw")): cv.string,
                        #vol.Optional(CONF_UNIT, description={"suggested_value": self._selected_option.get(CONF_UNIT, "krw")}): cv.string,

                        vol.Optional(CONF_UNIT, description={"suggested_value": self._selected_option.get(CONF_UNIT, None)}): selector.SelectSelector(selector.SelectSelectorConfig(options=CURRENCY_TYPES, custom_value=True, multiple=False,
                                                                                                                                               mode=selector.SelectSelectorMode.DROPDOWN)),

                        vol.Optional(CONF_IMAGE, description={"suggested_value": self._selected_option.get(CONF_IMAGE, None)}): cv.string,
                        #vol.Optional(CONF_IMAGE, default=self._selected_option.get(CONF_IMAGE, "")): cv.string,
                        vol.Required(CONF_REFRESH_PERIOD, default=self._selected_option.get(CONF_REFRESH_PERIOD, REFRESH_MIN)): int,
                        #vol.Optional(CONF_OPTION_ADD): selector.BooleanSelector(selector.BooleanSelectorConfig())
                    }
            ), errors=errors
        )


class CannotConnect(exceptions.HomeAssistantError):
    """Error to indicate we cannot connect."""


class InvalidHost(exceptions.HomeAssistantError):
    """Error to indicate there is an invalid hostname."""
