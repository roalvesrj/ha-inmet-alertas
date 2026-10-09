# Changelog

## v1.16.0 - 09/10/2026 (em desenvolvimento — develop)

### 🗺️ Camadas de mapa (plugin ha-map-card)
- **Seleção de severidade**: controle "Camadas INMET" no mapa (ligar/desligar Grande Perigo/Perigo/Perigo Potencial, com contagem de polígonos) + opção YAML `severidades`
- **Seleção de mapa base sem API key**: Cartográfico (OSM), Satélite (Esri) e Topográfico (OpenTopoMap), via controle e opção `basemap`
- Plugin limpo: removidos o render duplo por ciclo de atualização e o debug hardcoded (RJ/MG/ES); logs via Logger
- Testes JS com `node --test` (`tests/js`, 14 casos) + job no CI

### 🥈 Base para o tier Silver
- `PARALLEL_UPDATES = 0` na plataforma sensor
- `log-when-unavailable`: o coordenador registra indisponibilidade e recuperação **uma única vez** (+ testes)
- Documentação de parâmetros de configuração/instalação e seção Silver no `quality_scale.yaml`
- Testes: mock de `sys.modules` removido (guia oficial de review desaconselha); suíte única combinada com **59% de cobertura** (era 36%)

### 🐛 Correções
- Feed vazio ou com namespace não quebra mais o parsing do RSS (o caminho XPath `local-name()` não é suportado pelo ElementTree) — regressão coberta por teste

## v1.15.0 - 07/10/2026

### 🏆 Qualidade (Integration Quality Scale — Bronze)
- `runtime_data` tipado: o coordenador vive em `entry.runtime_data` (fim do `hass.data`)
- Teste de conexão no config flow (`cannot_connect`/`unknown`) e no setup (`async_config_entry_first_refresh` → `ConfigEntryNotReady` + retry do HA)
- `has_entity_name` padronizado nas 4 entidades; serviço com schema e `ServiceValidationError`
- Config flow v2: `data` guarda apenas o estado; notificações e intervalo vão para `options` — entradas v1 migram automaticamente
- Suíte de testes reorganizada: `tests/unit` (lógica pura) e `tests/integration` (harness do HA) com **100% de cobertura do config flow**; CI com hassfest + HACS + pytest
- `quality_scale.yaml` com as 20 regras do tier Bronze (done/exempt justificados)
- `brand/` completo: `icon.png`, `logo.png` e `logo@2x.png` (brands locais — suportados a partir do HA 2026.3)

### 🐛 Correções
- **Sensor de mapa**: campos `evento` e `descricao` dos polígonos voltam a ser preenchidos (antes liam chaves inexistentes)
- Entidades não reportam mais estado falso ("Nenhum alerta ativo"/0) antes do primeiro ciclo — ficam `unavailable`
- Diagnóstico: status de rate limiting/erro agora reflete o **último ciclo** (flags `ultimo_ciclo_*`), sem travar em `rate_limit` para sempre
- Reload da entrada usa o fluxo padrão do HA (`config_entries.async_reload`)
- Rota estática do plugin usa a API suportada (`async_register_static_paths`) e é registrada uma única vez
- Notificação persistente não adiciona mais "..." em descrições curtas

### 🧹 Manutenção
- Removidos módulos mortos (`rss_parser`, `data_processor`, `notification_manager`) e 12 scripts standalone obsoletos
- `requirements` do manifest esvaziado (aiohttp é core; feedparser não era usado em runtime)
- Headers HTTP centralizados em `const.py`; chaves de configuração unificadas; import não usados removidos
- Atributos do sensor principal não duplicam mais a geometria (exposta apenas no sensor de mapa)
- Compatibilidade mínima ajustada para Home Assistant 2026.3 (e HACS 2.x)

## v1.14.0 - 19/07/2026

### ✨ Novos Recursos
- **Sensor de Diagnóstico** `sensor.inmet_alertas_diagnostico_[estado]` — exibe status HTTP, contagem de rate limits, CAPs pendentes, último erro e ciclo atual
- **Configuração dinâmica via Options Flow** — `update_interval` e `notificacoes_perigo` agora podem ser alterados sem reinstalar a integração

### 🐛 Correções de Erros
- Corrigido ciclo de leitura que impedia alertas de serem detectados durante rate limiting persistente — CAPs pendentes não são mais descartados, e a fila foi deduplicada para evitar retry duplicado
- Aumentado limite de CAPs processados por ciclo de 20 para 50, reduzindo chances de alertas ficarem de fora
- Retry count de pending CAPs agora é resetado ao obter sucesso, and fresh attempts não incrementam mais o contador de retry

### 🧪 Testes
- Estrutura de testes migrada para pytest com fixtures compartilhadas
- 28 testes unitários para `check_state_affected`, `filter_state_municipalities` e `GeoProcessor`
- Mock de dependências Home Assistant para execução standalone

## v1.13.1 - 17/07/2026

### 🐛 Correções de Erros
- Corrigido import incorreto em `__init__.py` que impedia a integração de carregar no Home Assistant (`voluptuous as cv` → `homeassistant.helpers.config_validation as cv`)

## v1.13.0 - 16/07/2026

### ✨ Novos Recursos
- Suporte a repositório oficial HACS - estrutura de publicação oficial
- `hacs.json` com configurações para descoberta no HACS
- `brand/icon.png` - logotipo nos padrões Home Assistant

### 🐛 Correções de Erros
- README duplicado removido de dentro da pasta `custom_components/`
- Caminho da logo corrigido (agora aponta para `brand/icon.png`)
- Documentação atualizada com sensores de mapa e eventos faltantes

## v1.12.0

### ✨ Novos Recursos
- **Sensor de Mapa Geográfico** - `sensor.inmet_alertas_mapa_[estado]` para cada estado configurado
- **Polígonos Reais** - extração automática de coordenadas geográficas dos alertas INMET
- **Cálculo de Área** - área total afetada em km² usando algoritmo Shoelace
- **Zoom Inteligente** - zoom automático ideal para visualização no mapa
- **Plugin Leaflet** - `plugin_inmet_polygons.js` para ha-map-card com cores por severidade
- **Camadas por Severidade** - polígonos organizados por Grande Perigo, Perigo e Perigo Potencial

### 🐛 Correções de Erros
- Notificações duplicadas entre estados resolvidas
- Rate limiting tratado com fila de retry inteligente
- Persistência de alertas entre ciclos de atualização mantida
- Limpeza automática de notificações expiradas
- Terminologia de severidade padronizada (Perigo, Grande Perigo)

## v1.7.0

### ✨ Novos Recursos
- Arquitetura modular com helpers especializados (RSSParser, DataProcessor, NotificationManager)
- Documentação expandida em pasta dedicada (`docs/`)
- Suporte multilíngue (Português e Inglês)
- Testes automatizados organizados em estrutura própria
- Eventos personalizados (`inmet_novo_alerta`, `inmet_alerta_perigoso`)
- Constantes centralizadas para melhor manutenção
- Serviço `atualizar_alertas` para atualização manual

### 🐛 Correções de Erros
- Logs estruturados para facilitar troubleshooting
- Tratamento robusto de erros em todas as operações com RSS

## v1.0.2

### ✨ Novos Recursos
- Primeira versão pública da integração
- Monitoramento em tempo real de alertas do INMET
- Configuração por estado brasileiro
- Sensor principal com detalhes dos alertas
- Sensor de contagem de alertas
- Suporte a múltiplos estados
- Notificações persistentes para alertas de Perigo e Grande Perigo
- Interface em português brasileiro
- Integração via HACS (repositório personalizado)
