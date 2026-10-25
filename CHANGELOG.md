# Changelog

## v1.16.2 - 24/10/2026

### 🐛 Correções
- README: imagens e links em **URLs absolutas** — o logo volta a aparecer na página de detalhes do HACS (caminho relativo não resolvia no renderizador do HACS).
- Plugin do mapa: `plugin_path.is_dir()` agora roda em `async_add_executor_job` — acesso a filesystem fora do event loop (review do HACS).

### 📖 Documentação
- README: badge de **downloads** (soma dos zips dos releases) e badge **HACS Default** (substitui "Custom"); links de docs/CHANGELOG/LICENSE absolutos.
- AGENTS: novas regras — rota estática sempre no namespace da integração (`/{DOMAIN}`, nunca `/hacsfiles/`) e acesso a filesystem em async via executor.

> Nota: o ícone na **lista do HACS 2.0.5** usa um caminho legado de brands e exibe um placeholder (limitação do HACS). O ícone está publicado em `brands.home-assistant.io/marketplace/inmet_alertas/` e será usado pelo novo Marketplace do Home Assistant.

## v1.16.1 - 20/10/2026

### 🐛 Correções
- Rota estática do plugin movida para o namespace da integração: **`/inmet_alertas/plugin_inmet_polygons.js`** (antes `/hacsfiles/inmet_alertas/...`) — o prefixo `/hacsfiles/` pertence ao HACS e não deve ser usado por integrações (review do HACS). **Atualize a URL do plugin no card do ha-map-card.**
- README: a instalação agora lidera pela busca no HACS, com repositório personalizado como alternativa.

### 📖 Documentação
- `www/README.md` alinhado à integração (sem a seção de clima, ainda não lançada) e com a nova URL do plugin.

## v2.0.0 - 25/10/2026 (develop)

### 🌦️ Clima no mapa (radar e satélite)
- Overlay de **radar de chuva** e de **nuvens por satélite** ([RainViewer](https://www.rainviewer.com/), keyless) selecionável no controle ("Clima")
- Atualização automática a cada 5 min (frame mais recente), opacidade configurável e atribuição ao RainViewer no mapa
- Opções YAML: `clima` (`radar` | `nuvens`) e `climaOpacidade` (0.1–1, padrão 0.6)
- **Sem telefone oculto**: o polling só roda quando há overlay ativo — quem não usa o clima não gera requests periódicos; a verificação inicial é única
- **Um fetch por dashboard**: cache compartilhado entre instâncias do plugin (vários cards = um request por janela), com guarda de requisição em voo
- Opções indisponíveis ficam desabilitadas e rotuladas ("— indisponível"); falha de rede avisa uma única vez no console
- Popup robusto: área/centro inválidos do feed não quebram mais o polígono

### 🐛 Correções
- Tooltip do polígono escapa o nome do estado (Leaflet insere string como HTML)
- Overlay de clima não é mais capturado/removido pelo controle de mapa base a cada ciclo
- Serviço `atualizar_alertas` usa `async_refresh()` — a falha real da atualização agora chega ao chamador como `HomeAssistantError`
- Recuperação durante rate limiting tem mensagem própria ("voltou a responder (com rate limiting)") em vez de "normalmente"
- Removido `calculate_summary` (código morto, duplicava `helpers/sensor_data.py`)

### 🧪 Testes e CI
- 14 novos testes JS: ciclo de vida completo do clima (fetch injetado, sucesso, `!ok`, rejeição, cache compartilhado, voo em andamento, timer no `destroy`, labels "— indisponível", robustez do popup)
- 21 novos testes Python: migração (falha/no-op), `ConfigEntryNotReady` no setup, branch de rate limiting, evento de expiração (sem re-disparo, sem disparo em falha de merge), sensores com dados e sem dados, agregação de polígonos, `utils` de data e fuso ingênuo
- Cobertura do pacote: **60% → 72%** (`persistence` 100%, `sensor` 96%, `geo_processor` 77%, `utils` 88%)
- CI: `timeout-minutes` nos jobs e piso de regressão de cobertura (`--cov-fail-under=71`)

### 📖 Documentação
- README repaginado: alinhado à integração (entity_id correto do sensor de diagnóstico, mapa base Esri, sem promessas de "tempo real") e sem seções infladas

### 🃏 Card de alertas por severidade
- Novo `www/inmet-alert-card.js` (`custom:inmet-alert-card`): um card para cada severidade (Perigo / Grande Perigo / Perigo Potencial), com barra de progresso, contagem regressiva, chips e detalhes expansíveis
- **Registrado automaticamente** pela integração como recurso do Lovelace (URL versionada, sem passo manual)
- Visual inspirado no [weather_alerts_card](https://github.com/seevee/weather_alerts_card) (MIT), adaptado ao atributo `alertas` dos nossos sensores — sem dependências e sem build
- Feed fora do ar mostra "Dados do INMET indisponíveis" (nunca "nenhum alerta")
- 10 testes novos (`node --test`) para filtro, datas, progresso, resumo de municípios e configuração

## v1.16.0 - 19/10/2026

### 🗺️ Camadas de mapa (plugin ha-map-card)
- **Seleção de severidade**: controle "Camadas INMET" no mapa (ligar/desligar Grande Perigo/Perigo/Perigo Potencial, com contagem de polígonos) + opção YAML `severidades`
- **Seleção de mapa base sem API key**: Cartográfico, Satélite e Topográfico — tiles da **Esri** (keyless com atribuição), via controle e opção `basemap`
- Plugin limpo: removidos o render duplo por ciclo de atualização e o debug hardcoded (RJ/MG/ES); logs via Logger
- Testes JS com `node --test` (`tests/js`, 20 casos) + job no CI

### 🥈 Base para o tier Silver
- `PARALLEL_UPDATES = 0` na plataforma sensor
- `log-when-unavailable`: o coordenador registra indisponibilidade e recuperação **uma única vez** (+ testes)
- Documentação de parâmetros de configuração/instalação e seção Silver no `quality_scale.yaml`
- Testes: mock de `sys.modules` removido (guia oficial de review desaconselha); suíte única combinada com **59% de cobertura** (era 36%)

### 🐛 Correções
- Feed vazio ou com namespace não quebra mais o parsing do RSS (o caminho XPath `local-name()` não é suportado pelo ElementTree) — regressão coberta por teste
- Evento `inmet_alerta_expirado` agora é disparado de verdade na expiração de um alerta (estava documentado, mas nunca existiu) — coberto por teste
- Serviço `atualizar_alertas` levanta `HomeAssistantError` quando a atualização falha (regra `action-exceptions`)
- Plugin do mapa: HTML de popups/controle escapado (`escaparHtml`) — dados do feed não são mais interpolados crus; timers (retry/interval/unlock) cancelados no `destroy`; estilo injetado uma única vez por página
- Controle de camadas redesenhado: **botão de camadas recolhível** (expande ao clicar, com badge de contagem) e um **seletor** para Mapa base e para Alertas (com contagens); estilo aplicado **dentro do card** (corrige a renderização sem CSS em shadow DOM)
- Mapas base trocados para tiles da **Esri** (Cartográfico/Satélite/Topográfico, keyless com atribuição) — o OpenStreetMap bloqueia uso por aplicativos ("Access blocked", osm.wiki/Blocked)

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
- Documentação: parâmetros de configuração no README e parâmetros de instalação no `docs/INSTALACAO.md`

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
