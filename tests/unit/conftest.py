"""Configuração dos testes unitários: mocka módulos do Home Assistant.

Permite testar a lógica pura (`utils`, `helpers/*`) sem o harness completo,
que roda em `tests/integration` (Linux/CI).
"""
import sys
import types

_MOCK_HA_MODULES = {
    "homeassistant": types.ModuleType("homeassistant"),
    "homeassistant.helpers": types.ModuleType("homeassistant.helpers"),
    "homeassistant.helpers.config_validation": types.ModuleType(
        "homeassistant.helpers.config_validation"
    ),
    "homeassistant.core": types.ModuleType("homeassistant.core"),
    "homeassistant.const": types.ModuleType("homeassistant.const"),
    "homeassistant.config_entries": types.ModuleType("homeassistant.config_entries"),
    "homeassistant.exceptions": types.ModuleType("homeassistant.exceptions"),
    "homeassistant.util": types.ModuleType("homeassistant.util"),
    "homeassistant.util.dt": types.ModuleType("homeassistant.util.dt"),
    "voluptuous": types.ModuleType("voluptuous"),
}

# Atributos mínimos necessários para importar o pacote
_MOCK_HA_MODULES[
    "homeassistant.helpers.config_validation"
].config_entry_only_config_schema = lambda d: d
_MOCK_HA_MODULES["homeassistant.core"].HomeAssistant = object
_MOCK_HA_MODULES["homeassistant.core"].ServiceCall = object
_MOCK_HA_MODULES["homeassistant.config_entries"].ConfigEntry = object
_MOCK_HA_MODULES["homeassistant.config_entries"].ConfigEntryState = type(
    "ConfigEntryState", (), {"LOADED": "loaded"}
)
_MOCK_HA_MODULES["homeassistant.exceptions"].ServiceValidationError = type(
    "ServiceValidationError", (Exception,), {}
)
_MOCK_HA_MODULES["homeassistant.const"].Platform = type(
    "Platform", (), {"SENSOR": "sensor"}
)
_MOCK_HA_MODULES["voluptuous"].Schema = lambda schema: schema
_MOCK_HA_MODULES["voluptuous"].Optional = lambda key, _default=None: key
_MOCK_HA_MODULES["voluptuous"].Required = lambda key, _default=None: key
_MOCK_HA_MODULES["voluptuous"].In = lambda container, _msg=None: container

for mod_name, mod in _MOCK_HA_MODULES.items():
    sys.modules[mod_name] = mod
