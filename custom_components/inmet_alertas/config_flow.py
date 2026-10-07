"""Config flow para INMET Alertas (fluxo v2: data = conexão, options = ajustes)."""
from __future__ import annotations

import logging
from typing import Any

import voluptuous as vol
from homeassistant.config_entries import (
    ConfigEntry,
    ConfigFlow,
    ConfigFlowResult,
    OptionsFlow,
)
from homeassistant.core import callback

from .const import (
    CONF_ESTADO,
    CONF_NOTIFICACOES_PERIGO,
    CONF_UPDATE_INTERVAL,
    DEFAULT_NOTIFICACOES_PERIGO,
    DEFAULT_UPDATE_INTERVAL,
    DOMAIN,
    ESTADOS_BRASILEIROS,
    MAX_UPDATE_INTERVAL,
    MIN_UPDATE_INTERVAL,
)
from .coordinator import async_verificar_feed

_LOGGER = logging.getLogger(__name__)


class InmetAlertasConfigFlow(ConfigFlow, domain=DOMAIN):
    """Config flow do INMET Alertas."""

    VERSION = 2

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Primeiro (e único) passo do fluxo."""
        errors: dict[str, str] = {}

        if user_input is not None:
            estado = user_input[CONF_ESTADO].upper()

            if estado not in ESTADOS_BRASILEIROS:
                errors[CONF_ESTADO] = "invalid_state"
            else:
                await self.async_set_unique_id(f"{DOMAIN}_{estado}")
                self._abort_if_unique_id_configured()

                try:
                    conectado = await async_verificar_feed(self.hass)
                except Exception:  # noqa: BLE001 — inesperado vira "unknown"
                    _LOGGER.exception(
                        "Erro inesperado ao verificar o feed do INMET"
                    )
                    errors["base"] = "unknown"
                else:
                    if conectado:
                        return self.async_create_entry(
                            title=f"INMET Alertas - {ESTADOS_BRASILEIROS[estado]}",
                            data={CONF_ESTADO: estado},
                            options={
                                CONF_NOTIFICACOES_PERIGO: user_input.get(
                                    CONF_NOTIFICACOES_PERIGO,
                                    DEFAULT_NOTIFICACOES_PERIGO,
                                ),
                                CONF_UPDATE_INTERVAL: user_input.get(
                                    CONF_UPDATE_INTERVAL, DEFAULT_UPDATE_INTERVAL
                                ),
                            },
                        )
                    errors["base"] = "cannot_connect"

        estado_options = {
            sigla: f"{sigla} - {nome}"
            for sigla, nome in ESTADOS_BRASILEIROS.items()
        }
        data_schema = vol.Schema(
            {
                vol.Required(CONF_ESTADO, default="SP"): vol.In(estado_options),
                vol.Optional(
                    CONF_NOTIFICACOES_PERIGO, default=DEFAULT_NOTIFICACOES_PERIGO
                ): bool,
                vol.Optional(
                    CONF_UPDATE_INTERVAL, default=DEFAULT_UPDATE_INTERVAL
                ): vol.All(
                    vol.Coerce(int),
                    vol.Range(min=MIN_UPDATE_INTERVAL, max=MAX_UPDATE_INTERVAL),
                ),
            }
        )

        return self.async_show_form(
            step_id="user",
            data_schema=data_schema,
            errors=errors,
        )

    @staticmethod
    @callback
    def async_get_options_flow(config_entry: ConfigEntry) -> InmetAlertasOptionsFlow:
        """Cria o fluxo de opções."""
        return InmetAlertasOptionsFlow()


class InmetAlertasOptionsFlow(OptionsFlow):
    """Opções: notificações de perigo e intervalo de atualização."""

    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Gerenciar as opções."""
        if user_input is not None:
            return self.async_create_entry(title="", data=user_input)

        options = self.config_entry.options
        return self.async_show_form(
            step_id="init",
            data_schema=vol.Schema(
                {
                    vol.Optional(
                        CONF_NOTIFICACOES_PERIGO,
                        default=options.get(
                            CONF_NOTIFICACOES_PERIGO, DEFAULT_NOTIFICACOES_PERIGO
                        ),
                    ): bool,
                    vol.Optional(
                        CONF_UPDATE_INTERVAL,
                        default=options.get(
                            CONF_UPDATE_INTERVAL, DEFAULT_UPDATE_INTERVAL
                        ),
                    ): vol.All(
                        vol.Coerce(int),
                        vol.Range(min=MIN_UPDATE_INTERVAL, max=MAX_UPDATE_INTERVAL),
                    ),
                }
            ),
        )
