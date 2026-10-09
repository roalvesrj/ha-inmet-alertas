# SPEC — INMET Alertas: evolução para Bronze (v1.15.0)

| Campo | Valor |
|---|---|
| Status | ✅ v1.15.0 implementada e publicada · 🚧 v1.16.0 em andamento (develop) |
| Data | 2026-10-07 (v1.15.0) · 2026-10-09 (v1.16.0) |
| Base normativa | [Home Assistant Integration Quality Scale — regras Bronze](https://developers.home-assistant.io/docs/core/integration-quality-scale/) (verificada via Context7 em 2026-10-07) |
| Referências | Review pente-fino (sessão de 2026-10-07); skills do repo em `.agents/skills/` |
| Versão alvo | 1.16.0 (somente `develop`; sem release até decisão do usuário) |

---

## 🚧 v1.16.0 (em andamento — develop)

**Escopo**: camadas de mapa no plugin do ha-map-card + base do tier **Silver**.

- **Plugin** (`www/plugin_inmet_polygons.js`): seleção de severidade (controle "Camadas INMET" + opção `severidades`), seleção de basemap keyless (Cartográfico/Satélite/Topográfico via controle + opção `basemap`), contagem de polígonos por camada; removidos o render duplo por ciclo e o debug hardcoded (RJ/MG/ES).
- **Testes JS**: `tests/js/plugin_inmet_polygons.test.mjs` via `node --test` — 14 casos (severidade, basemap, roteamento, limpeza) + job no CI.
- **Silver (base)**: `PARALLEL_UPDATES = 0`; `log-when-unavailable` no coordenador (+ testes); docs de parâmetros de configuração/instalação; `quality_scale.yaml` com a seção Silver.
- **Bug real encontrado por teste novo**: feed vazio/namespace quebrava o parsing (`local-name()` não suportado pelo ElementTree) — corrigido com fallback namespace-agnóstico + regressão.
- **Test-coverage (Silver, ≥95%)**: baseline **59%** na suíte combinada (era 36%); mock de `sys.modules` removido (guia oficial de review desaconselha). Próximo passo dedicado: coordinator (parsing/rate-limit/merge), entidades e `__init__`.

---

## 1. Objetivo

Elevar a integração `inmet_alertas` ao tier **Bronze** do Integration Quality Scale do Home Assistant: cumprir as 20 regras do tier (implementadas ou `exempt` com justificativa), fechar lacunas de teste do config flow, eliminar código morto e corrigir os bugs confirmados no review — sem quebrar instalações existentes (migração de config entry obrigatória).

## 2. Escopo

### 2.1 Em escopo (v1.15.0)

| Grupo | Itens |
|---|---|
| Bronze (regras) | `runtime-data`, `test-before-setup`, `test-before-configure`, `config-flow-test-coverage`, `config-flow` (subchecks `data_description` + `data`/`options`), `has-entity-name`, `dependency-transparency`, `action-setup` (validação), `docs-removal-instructions`, artefato `quality_scale.yaml`, `common-modules`, `appropriate-polling` (unificação de defaults) |
| Bugs | M1 (chaves erradas no sensor de mapa), M3 (estado falso antes do 1º refresh), M4 (reload manual), M6 (static path via router aiohttp), M7 (serviço sem validação), M8 (diagnóstico travado), M9 (código morto/duplicado) |
| Melhorias | M2 parcial (remover geometria duplicada do sensor principal), extração de lógica pura testável, sincronização de traduções, README/CHANGELOG/docs, CI, bump de versão |

### 2.2 Fora de escopo (backlog P1/P2 — seção 10)

defusedxml, rate limit via HTTP 429/Retry-After, cache compartilhada de CAPs entre entries, redesenho profundo dos atributos (endpoint/serviço para geometria), limpeza massiva do ruff, portes adicionais dos scripts standalone, regras Silver/Gold.

## 3. Matriz Bronze — definição de pronto

| # | Regra | Antes | Depois (DoD) |
|---|---|---|---|
| 1 | `action-setup` | ⚠️ sem validação | Serviço registrado em `async_setup` com `vol.Schema`; handler valida estado e levanta `ServiceValidationError` |
| 2 | `appropriate-polling` | ✅ c/ defaults divergentes | Default único (`DEFAULT_UPDATE_INTERVAL = 45`) usado em const/flow/coordinator; `SCAN_INTERVAL` morto removido |
| 3 | `brands` | ✅ | `brand/icon.png` 256×256 mantido; logo/dark documentados no backlog |
| 4 | `common-modules` | ⚠️ | `coordinator.py`, `entity.py`, `helpers/sensor_data.py`, `helpers/persistence.py`; módulos mortos deletados |
| 5 | `config-flow-test-coverage` | ❌ | `tests/integration/test_config_flow.py` + `test_init.py`; gate `--cov-fail-under=100` no arquivo `config_flow.py` |
| 6 | `config-flow` | ❌ subchecks | `data_description` em `strings.json` e traduções; settings só em `options`; migração v1→v2 |
| 7 | `dependency-transparency` | ❌ | `requirements` vazio (aiohttp é core; feedparser só servia módulo morto); sem pino desnecessário |
| 8 | `docs-actions` | ✅ | Serviço documentado no README/`services.yaml`; seção de serviço adicionada às traduções pt |
| 9 | `docs-triggers` | n/a | `exempt` com justificativa no `quality_scale.yaml` |
| 10 | `docs-conditions` | n/a | `exempt` com justificativa |
| 11 | `docs-high-level-description` | ✅ | README mantido |
| 12 | `docs-installation-instructions` | ✅ | README + `docs/INSTALACAO.md` atualizados |
| 13 | `docs-removal-instructions` | ⚠️ | Seção "Remover a integração" no README (UI + HACS + manual) |
| 14 | `entity-event-setup` | n/a | `exempt` (entidades não assinam eventos) |
| 15 | `entity-unique-id` | ✅ | IDs atuais preservados (sem quebra de registry) |
| 16 | `has-entity-name` | ❌ | Base `INMETBaseSensor` com `_attr_has_entity_name = True` em todas as entidades |
| 17 | `runtime-data` | ❌ | `entry.runtime_data` tipado (`InmetAlertasConfigEntry`); zero `hass.data[DOMAIN]` |
| 18 | `test-before-configure` | ❌ | `async_step_user` testa `URL_RSS`; erros `cannot_connect`/`unknown`; teste de recuperação |
| 19 | `test-before-setup` | ❌ | `await coordinator.async_config_entry_first_refresh()` no `async_setup_entry` |
| 20 | `unique-config-entry` | ✅ | Mantido (`async_set_unique_id` + abort), com validação de estado antes |

## 4. Inventário de problemas (do review)

### 4.1 Bloqueadores Bronze
- **B1** `runtime-data`: `hass.data` em `__init__.py`/`sensor.py`.
- **B2** `test-before-setup`: task de fundo engole falha; entidades criadas sem dados.
- **B3** `test-before-configure`: nenhuma checagem de conectividade; `cannot_connect` nunca usado.
- **B4** cobertura de teste do config flow: zero.
- **B5** `data_description` ausente; settings em `data` (duplicados em `options`).
- **B6** `has-entity-name`: sensor de mapa sem `_attr_has_entity_name`.
- **B7** `requirements`: `aiohttp` (não deve) + `feedparser` (só módulo morto).
- **B8** docs de remoção ausentes no README.
- **B9** `action-setup`: serviço sem schema/`ServiceValidationError`.
- **B10** `quality_scale.yaml` inexistente.

### 4.2 Bugs (MAJOR)
- **M1** `sensor.py:1018,1027` — `alerta.get("event")`/`get("description")` ≠ chaves reais `evento`/`descricao` → campos vazios nos polígonos do mapa.
- **M2** atributos com geometria duplicada no sensor principal (risco >16 KB / recorder) — correção parcial: remover `dados_geograficos` do atributo `alertas`; mapa segue expondo geometria para o plugin.
- **M3** `native_value` retorna `"Nenhum alerta ativo"`/`0` sem dados (deveria ser `None`/`unavailable`).
- **M4** reload feito à mão (`unload`+`setup`) em vez de `hass.config_entries.async_reload`.
- **M5** `hacs.json` mínimo 2024.1 × padrão OptionsFlow pós-2024.11 → mínimo elevado para 2026.3.0 (brands locais ≥ 2026.3; e HACS 2.x).
- **M6** rota estática via `hass.http.app.router.add_static` + flag de falha silenciosa → `async_register_static_paths`/`StaticPathConfig` em `async_setup` com `dependencies: ["http"]`.
- **M7** serviço sem validação de `estado`.
- **M8** `rate_limit_hits` monotônico trava estado em `rate_limit`; `ultimo_erro` nunca limpa estado; `ciclo_atual` é timestamp (README diz número) → flags de ciclo (`ultimo_ciclo_rate_limited`, `ultimo_ciclo_com_erro`).
- **M9** código morto (`helpers/rss_parser.py`, `data_processor.py`, `notification_manager.py` — 676 linhas) + constantes duplicadas + imports sem uso + `feedparser`.

### 4.3 Menores (resumo)
Traduções fora de sincronia (`strings.json` sem config/options; serviços ausentes em pt); 12 scripts `standalone_test_*.py` obsoletos/duplicados versionados; XML remoto sem defusedxml; detecção de rate limit por string; escala de severidade não re-notifica; `_pending_caps` só em memória; UA estático desatualizado; sem CI.

## 5. Design da solução

### 5.1 Estrutura final

```
custom_components/inmet_alertas/
├── __init__.py          # setup/unload, serviço, static path, migração
├── coordinator.py       # INMETDataUpdateCoordinator + verificação de feed
├── entity.py            # INMETBaseSensor (has_entity_name, attribution)
├── sensor.py            # 4 entidades (finas, delegam dados a helpers)
├── config_flow.py       # fluxo v2 (data/options separados) + options
├── const.py             # constantes puras (sem imports do HA)
├── helpers/
│   ├── geo_processor.py   # (mantido)
│   ├── sensor_data.py     # NOVO: atributos/resumos puros
│   └── persistence.py     # NOVO: merge/expiração puros
├── quality_scale.yaml   # NOVO: rastreio das 20 regras bronze
├── www/, translations/, brand/, docs/...
└── (deletados: rss_parser.py, data_processor.py, notification_manager.py)
```

### 5.2 Runtime data
- `coordinator.py` define `type InmetAlertasConfigEntry = ConfigEntry[INMETDataUpdateCoordinator]`.
- `async_setup_entry`: cria coordinator, `await coordinator.async_config_entry_first_refresh()`, `entry.runtime_data = coordinator`, forward platforms.
- Serviço itera `hass.config_entries.async_entries(DOMAIN)` e acessa `entry.runtime_data` apenas de entries `ConfigEntryState.LOADED`.

### 5.3 Entidades
- `INMETBaseSensor(CoordinatorEntity[INMETDataUpdateCoordinator], SensorEntity)` com `_attr_has_entity_name = True` e `_attr_attribution` (remove `attribution` manual dos dicts).
- Unique IDs atuais preservados **exatamente** (incl. `inmet_alertas_mapa_{estado}`) para não órfãos no registry.
- `native_value` retorna `None` quando não há dados (unknown), nunca estado falso.
- Atributos montados pelos helpers puros (5.4).

### 5.4 Helpers puros (testáveis sem harness HA)
- `helpers/sensor_data.py`: `preparar_alertas_para_atributos()` (remove `dados_geograficos`), `calcular_resumo()`, `construir_atributos_mapa()`.
- `helpers/persistence.py`: `alerta_ainda_valido()`, `mesclar_alertas()` (stdlib datetime; sem import do HA).
- Justificativa (skill design-patterns): SRP (entidade não tem lógica de dados), Rule of Three (mesma montagem reutilizada), deletar-antes-de-abstrair (helpers mortos saem, lógica viva é extraída).

### 5.5 Config flow v2 + migração
- `VERSION = 2`; `data = {"estado"}`, `options = {"notificacoes_perigo", "update_interval"}`.
- `async_migrate_entry` move v1 `data.notificacoes_perigo/update_interval` → `options` (sem perda) e retorna `False` em entry corrompida.
- `async_step_user`: valida estado → unique id/abort → testa feed (`cannot_connect`/`unknown`) → cria entry.
- Options flow moderno (`OptionsFlow` sem construir com `config_entry`).

### 5.6 Serviço
- `SCHEMA = vol.Schema({vol.Optional("estado"): vol.In(sorted(ESTADOS_BRASILEIROS))})` em `async_setup`.
- Sem entries carregadas compatíveis com `estado` informado → `ServiceValidationError`.

### 5.7 Strings/traduções
- `strings.json` = fonte EN completa (config, options, data_description, services, entity) e `en.json` espelho fiel.
- `pt.json`/`pt-BR.json` traduzidos (incl. `data_description` e `services`).

### 5.8 Manifest/HACS
- `manifest.json`: remove `requirements`; adiciona `integration_type: "service"`; `dependencies: ["http"]`; mantém `after_dependencies` (`persistent_notification`).
- `hacs.json`: `"homeassistant": "2026.3.0"` + `"hacs": "2.0.0"` (mínimo real para o padrão OptionsFlow/APIs usados e para brands locais `brand/`; era 2024.1/1.32).
- Release automatizado: GitHub Release (`published`) → workflow `.github/workflows/release.yml` sincroniza a versão do manifest com a tag e anexa `inmet_alertas.zip` (zip flat, exigido pelo `zip_release` + `filename`).

---

## 6. Metodologia TDD (regra do projeto)

> Regra geral: **nenhuma mudança de comportamento entra sem um teste que falharia antes dela.** O Bronze já exige cobertura do config flow; adotamos TDD como mecanismo padrão para fechar e manter isso.

### 6.1 Fluxo obrigatório
1. **Red** — escrever o teste que descreve o comportamento desejado e vê-lo falhar pelo motivo certo.
2. **Green** — implementação mínima para passar.
3. **Refactor** — melhorar mantendo verde.

### 6.2 O que exige teste primeiro
- Steps de config flow/options flow (incl. erro e recuperação) — obrigatório e com **100% de cobertura** do `config_flow.py`.
- Lógica do coordinator: parsing CAP, merge/persistência, expiração, diagnóstico.
- Serviços: validação de entrada e `ServiceValidationError`.
- Helpers puros (`sensor_data`, `persistence`, `geo_processor`, `utils`).
- Correções de bug: **teste de regressão que reproduz o bug antes da correção** (ver 6.4).

### 6.3 Exceções pragmáticas (documentar no PR)
- `www/plugin_inmet_polygons.js` (JS do mapa) — sem harness JS no repo; validação manual registrada.
- Documentação/traduções/CHANGELOG — sem teste automatizado.
- Wiring puro de API do HA sem decisão própria (ex.: registrar entidade) — coberto por teste de integração do fluxo quando relevante.

### 6.4 Bug fix = teste de regressão
Exemplo canônico desta release (M1): primeiro um teste que espera `evento`/`descricao` preenchidos nos polígonos do mapa — ele falha contra o código atual; só então a correção. O teste permanece na suíte permanentemente.

### 6.5 Onde cada teste mora
| Camada | Local | Roda onde |
|---|---|---|
| Lógica pura (sem HA) | `tests/unit/` | Windows e Linux (`PYTEST_DISABLE_PLUGIN_AUTOLOAD=1`) |
| Integração HA (flows, setup, entidades) | `tests/integration/` | Linux/CI (e Windows via stub local, quando possível) |

### 6.6 Comandos

```powershell
# Unit (Windows OK)
$env:PYTEST_DISABLE_PLUGIN_AUTOLOAD="1"; python -m pytest tests/unit -q
# Integração (Linux/WSL/CI)
python -m pytest tests/integration -q
# Gate Bronze do config flow
python -m pytest tests/integration --cov=custom_components.inmet_alertas.config_flow --cov-fail-under=100
```

> Ambiente de validação: **Home Assistant 2026.9.4** + `pytest-homeassistant-custom-component==0.13.367` (Python 3.14). O plugin mais recente (0.13.370) pina um HA beta (2026.10.0b4) — não usar.

---

## 7. Critérios de aceite

1. Matriz da seção 3 toda ✅/exempt com evidência no `quality_scale.yaml`.
2. `tests/unit` e `tests/integration` verdes; `config_flow.py` 100% coberto.
3. Migração v1→v2 testada (`test_init.py`) e sem perda de opções.
4. M1–M9 corrigidos com teste de regressão onde aplicável.
5. `ruff check` sem novos erros nos arquivos tocados (mass fix fica no P2).
6. README/CHANGELOG/INSTALACAO atualizados; versão 1.15.0 em `manifest.json` e `const.py`.
7. CI configurada (hassfest + HACS + pytest em Ubuntu).

## 8. Plano de testes (por cenário)

**Happy path**: config flow cria entry (`data`=estado, `options`=settings); options flow salva; setup cria 4 entidades; novo alerta → evento + notificação; expiração remove notificação.

**Alternativos**: segundo estado; troca de options recarrega; migrate v1→v2.

**Edge**: feed vazio/malformado; rate limit com HTTP 200; CAP sem `<info>`; polígono < 3 pontos; alerta sem `expires`; atributos grandes; entrada duplicada.

**Erros**: feed inacessível no configure → `cannot_connect` + recuperação; falha no 1º refresh → `ConfigEntryNotReady`; serviço com estado inválido → `ServiceValidationError`; estado inválido no flow.

## 9. Riscos e mitigação

| Risco | Mitigação |
|---|---|
| Quebra de registry (unique IDs) | IDs congelados; teste de migração |
| Dashboards usando atributos atuais | manter campos documentados; só `dados_geograficos` sai do sensor principal |
| Mudança de headers/UA gerar 403 | headers centralizados sem alterar semântica validada em produção |
| `runtime_data` + primeira refresh mudar timing do setup | testes de integração + `ConfigEntryNotReady` documentado |
| Windows não roda harness HA | stub `fcntl` local (fora do repo) + CI Ubuntu como fonte de verdade |

## 10. Backlog priorizado (pós-Bronze)

**P1**: defusedxml (+`requirements`), rate limit via 429/Retry-After, cache compartilhada de CAPs, atributos enxutos (serviço/endpoint para geometria), testes de persistência adicionais, `entity_category` no diagnóstico, `always_update=False`.
**P2**: limpeza ruff completa (1.264 findings), integração de `_pending_caps` persistente, re-notificação em escalada de severidade, variantes dark do brand (`dark_icon`/`dark_logo`), **plugin JS: remover debug hardcoded (RJ/MG/ES) e `console.log` de produção**, CI de cobertura global (Silver), upgrade do ambiente de testes para o HA 2026.10 quando a versão estável sair.

**Feature anotada (D1 pendente) — camadas de mapa estilo FR24**: card próprio `custom:inmet-alertas-card` com seleção de camadas por severidade na UI e basemap keyless (`osm`/`satellite`/`topo`) + `interactive_map`; registro automático via pacote `frontend/` + recurso Lovelace (`async_create_item`/`async_update_item` com `?v=`, aguardando `resources.loaded`). Referências: release FR24 v2.3.0 (card próprio) e `frontend/__init__.py` do repo deles. Plano B: evoluir o plugin ha-map-card atual com filtro `severities`.
**Silver/Gold roadmap**: `entity-unavailable` explícito, `devices`/device_info, `diagnostics`, `reconfiguration-flow`, `entity-translations`, reparos (`repair-issues`).
