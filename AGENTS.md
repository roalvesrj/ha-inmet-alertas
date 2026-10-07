# AGENTS.md — instruções para agentes de código

Guia de trabalho neste repositório (integração `inmet_alertas` para Home Assistant, meta atual: **tier Bronze** do Integration Quality Scale). Leia também o `SPEC.md` — ele é a fonte de verdade da release em andamento.

## Comandos

```powershell
# Testes unitários (lógica pura, roda no Windows)
$env:PYTEST_DISABLE_PLUGIN_AUTOLOAD="1"; python -m pytest tests/unit -q

# Testes de integração (harness do HA; Linux/WSL/CI)
python -m pytest tests/integration -q

# Gate do Bronze: config flow com 100% de cobertura
python -m pytest tests/integration --cov=custom_components.inmet_alertas.config_flow --cov-report=term-missing --cov-fail-under=100

# Checagem sintática rápida
python -m compileall custom_components -q

# Lint (ainda não é gate; limpeza massiva prevista no backlog)
python -m ruff check custom_components tests
```

> No Windows, o harness do HA não carrega nativamente (`fcntl` é Unix-only). Não "conserte" isso no código do produto; a suíte de integração roda em Linux/CI.

> Ambiente de teste validado: **HA 2026.9.4** + plugin `0.13.367` (Python 3.14 — ver `requirements_test.txt`).

## Fluxo TDD (regra do projeto)

1. **Red**: escreva primeiro o teste que descreve o comportamento desejado e confirme que ele falha pelo motivo certo.
2. **Green**: implemente o mínimo para passar.
3. **Refactor**: melhore mantendo verde.
4. **Bug fix**: sempre com teste de regressão que reproduz o bug **antes** da correção.
5. Nenhuma mudança de comportamento entra sem teste correspondente.

**Exceções pragmáticas** (justificar no PR): `www/plugin_inmet_polygons.js` (sem harness JS; verificação manual), documentação, traduções e wiring puro de APIs do HA.

**Onde cada teste mora:**
- `tests/unit/` — lógica pura sem harness do HA (helpers, utils). Preferir extrair lógica para helpers puros quando isso tornar algo testável.
- `tests/integration/` — config flow, options flow, setup/unload, entidades, migração.

## Conhecimento novo → decisão do usuário (regra vigente)

Qualquer conhecimento relevante identificado durante o trabalho — comportamento de API do HA, restrições de ambiente, decisões de design, armadilhas, convenções — deve ser **apresentado ao usuário ao final do trabalho**, para ele decidir se deve ou não ser registrado neste arquivo.

- **Nunca** registrar conhecimento novo no AGENTS.md por conta própria.
- Apresentar em lista, com evidência e sugestão de redação (o que entraria, onde e por quê).
- Aguardar a decisão explícita do usuário antes de editar este arquivo.
- Conhecimento que já era regra existente pode ser mantido; a regra vale para itens novos.

## Arquitetura (v1.15.0)

```
custom_components/inmet_alertas/
├── __init__.py     # setup/unload, serviço, static path, migração de entry
├── coordinator.py  # INMETDataUpdateCoordinator (fetch, retry, notificações)
├── entity.py       # INMETBaseSensor (has_entity_name, attribution)
├── sensor.py       # entidades finas
├── config_flow.py  # fluxo v2 (data=conexão, options=ajustes)
├── const.py        # constantes puras — NÃO importar Home Assistant aqui
└── helpers/        # lógica pura: geo_processor, sensor_data, persistence
```

## Convenções

- Python: docstrings e logs em PT-BR; nomes de domínio em PT (estado, alertas), API do HA em EN.
- Logging: usar `%s` (lazy), nunca f-string em log; `_LOGGER.exception` dentro de `except`.
- Constantes: sempre em `const.py`; nunca duplicar `DOMAIN`, URLs, chaves de config.
- Config entry: `data` só para o que identifica/conecta (`estado`); ajustes em `options`.
- Entidades: `_attr_has_entity_name = True`, `_attr_attribution`, `unique_id` estável — **nunca alterar unique_id existente** (quebra o entity registry).
- Estados sem dado: `None`/`unavailable`, jamais mentir ("Nenhum alerta ativo" com feed fora do ar).
- Dependências: `aiohttp` é core do HA — nunca listar; `requirements` só com o estritamente necessário.
- Traduções: `strings.json` é a fonte em inglês; `en.json` espelha; pt/pt-BR traduzem.
- Versionamento: semver; bump em `manifest.json` + `const.VERSION` + `CHANGELOG.md` juntos.

## Fatos verificados do HA (evidências — não redescobrir)

Conhecimento validado contra fontes oficiais e/ou testes; usar direto:

- **Unload**: entidade registrada no entity registry **não sai** do state machine ao descarregar a integração — ela fica `unavailable` (`Entity.async_remove` + docs oficiais). Testes de unload devem assertar `STATE_UNAVAILABLE`, nunca ausência da entidade.
- **Coordinator**: sempre passar `config_entry=entry` ao `DataUpdateCoordinator` — ele registra `entry.async_on_unload(self.async_shutdown)` sozinho (fonte HA 2025.10+).
- **Serviços**: dados fora do schema levantam `vol.Invalid` no core; `ServiceValidationError` é para validação semântica dentro do handler (ex.: estado válido, mas não configurado).
- **Testes de flow fora do manager**: setar `flow.hass`, `flow.flow_id`, `flow.handler` e `flow.context = {"source": SOURCE_USER}` — `context` é **dict**, não `Context()`.
- **Arquivos da integração**: localizar com `Path(__file__).parent` (ex.: pasta `www/`); `hass.config.path("custom_components", ...)` aponta para o testing_config nos testes e não encontra nada.
- **Contrato do plugin de mapa**: o JS consome `camadas_por_severidade[*].poligonos` e `poligonos` do sensor de mapa — não remover/renomear sem atualizar `www/plugin_inmet_polygons.js`.
- **Ruff**: `# noqa: BLE001` é intencional (o ruleset do HA habilita BLE001); TRY003/TRY301 não são seguidos neste repo.

## Não faça

- Editar `.storage/` ou arquivos internos do HA.
- Tocar em `.agents/` (skills locais) ou `opencode.json`.
- Introduzir `hass.data[DOMAIN]` para runtime (use `entry.runtime_data`).
- Adicionar código em `helpers/` sem teste unitário correspondente.
- Deletar/mover unique IDs, entity IDs ou chaves de tradução existentes sem plano de migração.
