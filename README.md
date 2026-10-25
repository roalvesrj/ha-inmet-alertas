# INMET Alertas — Integração Home Assistant

<img src="https://raw.githubusercontent.com/roalvesrj/ha-inmet-alertas/main/custom_components/inmet_alertas/brand/logo.png" alt="INMET" width="320"/>

[![GitHub release](https://img.shields.io/github/release/roalvesrj/ha-inmet-alertas.svg)](https://github.com/roalvesrj/ha-inmet-alertas/releases)
[![Downloads](https://img.shields.io/github/downloads/roalvesrj/ha-inmet-alertas/total.svg)](https://github.com/roalvesrj/ha-inmet-alertas/releases)
[![GitHub issues](https://img.shields.io/github/issues/roalvesrj/ha-inmet-alertas.svg)](https://github.com/roalvesrj/ha-inmet-alertas/issues)
[![License](https://img.shields.io/github/license/roalvesrj/ha-inmet-alertas.svg)](https://github.com/roalvesrj/ha-inmet-alertas/blob/main/LICENSE)
[![HACS](https://img.shields.io/badge/HACS-Default-41BDF5.svg)](https://hacs.xyz)
[![CI](https://github.com/roalvesrj/ha-inmet-alertas/actions/workflows/ci.yml/badge.svg)](https://github.com/roalvesrj/ha-inmet-alertas/actions/workflows/ci.yml)

Integração que acompanha os alertas meteorológicos do INMET (feed público) e expõe sensores, notificações, eventos e um mapa com os polígonos dos alertas.

## ✨ Funcionalidades

- **Acompanhamento do feed público do INMET** a cada 5–120 minutos (configurável; padrão: 45 min)
- **Um estado brasileiro por configuração** — instale a integração mais de uma vez para monitorar vários estados
- **Notificações persistentes** para alertas de Perigo e Grande Perigo, com limpeza automática quando o alerta expira
- **Quatro sensores por estado**: alertas, contagem, mapa (polígonos) e diagnóstico
- **Eventos no barramento** (`inmet_novo_alerta`, `inmet_alerta_perigoso`, `inmet_alerta_expirado`) para automações
- **Mapa com polígonos** (plugin do ha-map-card): seleção de severidades e de mapa base sem API key
- **Serviço** `inmet_alertas.atualizar_alertas` para forçar uma atualização
- Interface e documentação em português do Brasil

## 📦 Instalação

[![Abrir no Home Assistant](https://my.home-assistant.io/badges/hacs_repository.svg)](https://my.home-assistant.io/redirect/hacs_repository/?category=integration&repository=roalvesrj%2Fha-inmet-alertas)

1. **HACS** → **Integrações** → busque por **"INMET Alertas"**
2. **Instalar** e **reinicie o Home Assistant**

Se a integração ainda não aparecer na busca (HACS antigo ou antes de entrar na loja padrão), use o repositório personalizado: **HACS** → **Integrações** → **⋮** → **Repositórios Personalizados** → adicione `https://github.com/roalvesrj/ha-inmet-alertas` (categoria **Integração**) → instale **"INMET Alertas"** → reinicie.

Instalação manual e detalhes: [`docs/INSTALACAO.md`](https://github.com/roalvesrj/ha-inmet-alertas/blob/main/custom_components/inmet_alertas/docs/INSTALACAO.md).

## ⚙️ Configuração

1. **Configurações** → **Dispositivos e Serviços** → **Adicionar Integração** → "INMET Alertas"
2. Selecione o **estado brasileiro** (fixo por configuração)
3. Ajuste as opções em **Configurar**:

| Parâmetro | Onde | Descrição | Padrão |
|---|---|---|---|
| `estado` | `data` (na criação) | Estado monitorado — não pode ser alterado depois | — (obrigatório) |
| `notificacoes_perigo` | `options` | Notificações persistentes para Perigo/Grande Perigo | `true` |
| `update_interval` | `options` | Intervalo entre verificações, em minutos (5–120) | `45` |

Para monitorar outro estado, repita a instalação: cada configuração tem sensores e notificações independentes.

Guia completo: [`docs/CONFIGURACAO.md`](https://github.com/roalvesrj/ha-inmet-alertas/blob/main/custom_components/inmet_alertas/docs/CONFIGURACAO.md).

## 📊 Sensores

Para cada estado configurado:

| Sensor | Estado | Atributos principais |
|---|---|---|
| `sensor.alertas_meteorologicos_[ESTADO]` | Título do alerta ativo (ou `unavailable` antes do primeiro ciclo) | `alertas`, `total_alertas`, `alertas_por_severidade`, `ultima_atualizacao` |
| `sensor.quantidade_de_alertas_[ESTADO]` | Número de alertas ativos | — |
| `sensor.inmet_alertas_mapa_[ESTADO]` | Número de polígonos ativos | `camadas_por_severidade`, `poligonos`, `area_total_afetada_km2`, `centro_geografico`, `zoom_recomendado` |
| `sensor.diagnostico_inmet_[ESTADO]` | Status do último ciclo (`ok`, `rate_limit`, `erro`, `desconhecido`) | `ultimo_http_status`, `rate_limit_hits`, `pending_caps`, `ultimo_erro` |

> Os sensores ficam `unavailable` até o primeiro ciclo de atualização — a integração não publica "zero alertas" antes de ter dados.

## 🔔 Notificações

Com `notificacoes_perigo` ativado, a integração cria notificações persistentes para alertas **Perigo** e **Grande Perigo** (título, severidade, período e municípios) e as remove quando os alertas expiram.

## 🎯 Eventos

| Evento | Quando |
|---|---|
| `inmet_novo_alerta` | Um novo alerta é detectado |
| `inmet_alerta_perigoso` | O novo alerta é de severidade Perigo ou Grande Perigo |
| `inmet_alerta_expirado` | Um alerta existente expira |

Payload: `alert_id`, `titulo`, `severidade`, `evento`, `estado`, `inicio`, `fim`, `municipios`, `area_desc`, `descricao`.

## 🛠️ Serviços

### `inmet_alertas.atualizar_alertas`

Força a atualização dos alertas. Parâmetro opcional `estado` (sigla) para atualizar apenas um estado.

```yaml
service: inmet_alertas.atualizar_alertas
data:
  estado: "SP" # opcional
```

## 🗺️ Mapa com polígonos (plugin ha-map-card)

Instale o **ha-map-card** pela HACS e aponte o plugin (a URL fica disponível automaticamente após instalar a integração):

```yaml
type: custom:map-card
zoom: 6
x: -15.7998
y: -47.8645
plugins:
  - name: inmet_polygons
    url: /inmet_alertas/plugin_inmet_polygons.js
    options:
      states: ["rio_de_janeiro"] # estados em snake_case
```

No canto do mapa há um **botão de camadas** (com a contagem de polígonos) que expande ao ser clicado, com um seletor para cada grupo:

- **Alertas**: Todas, Grande Perigo + Perigo ou apenas uma severidade — cada opção mostra a contagem de polígonos. Seleções personalizadas via YAML (`severidades`) aparecem como "Personalizado";
- **Mapa base**: Padrão do cartão, **Cartográfico**, **Satélite** ou **Topográfico** — tiles da **Esri**, sem API key (os tiles do OpenStreetMap bloqueiam aplicativos);
- **Clima**: **Nenhuma**, **Chuva (radar)** ou **Nuvens (satélite)** — overlay keyless do [RainViewer](https://www.rainviewer.com/), atualizado a cada 5 min (o polling só roda com um overlay ativo).

Opções do plugin:

| Opção | Descrição | Padrão |
|---|---|---|
| `states` | Estados monitorados (snake_case) | `["rio_de_janeiro"]` |
| `severidades` | Severidades visíveis | todas |
| `basemap` | `cartografico`, `satelite` ou `topografico` | mapa do cartão |
| `clima` | `radar` ou `nuvens` (overlay do RainViewer) | nenhuma |
| `climaOpacidade` | Opacidade do overlay de clima (0.1–1) | `0.6` |
| `showLayerControl` | Exibe o controle de camadas | `true` |
| `showLabels` | Tooltip por polígono | `true` |
| `autoFocus` | Centraliza o mapa na área com alertas | `true` |
| `colors` | Cores por severidade (`grandePerigo`, `perigo`, `perigoPotencial`) | cores oficiais |
| `fillOpacity` / `strokeOpacity` / `strokeWeight` | Estilo dos polígonos | `0.5` / `0.8` / `2` |
| `updateInterval` | Intervalo de atualização do plugin (ms) | `60000` |

Documentação do plugin: [`www/README.md`](https://github.com/roalvesrj/ha-inmet-alertas/blob/main/custom_components/inmet_alertas/www/README.md).

> Sem alertas ativos não há polígonos no mapa.

## 🤖 Automações

Exemplo — notificação apenas para alertas de Perigo/Grande Perigo (formato da interface do HA):

```yaml
alias: Notificar alerta INMET
trigger:
  - platform: event
    event_type: inmet_novo_alerta
condition:
  - condition: template
    value_template: "{{ trigger.event.data.severidade in ['Perigo', 'Grande Perigo'] }}"
action:
  - service: notify.mobile_app_meu_celular
    data:
      title: "🚨 Alerta Meteorológico"
      message: >
        {{ trigger.event.data.titulo }}
        Severidade: {{ trigger.event.data.severidade }}
        Período: {{ trigger.event.data.inicio }} até {{ trigger.event.data.fim }}
mode: single
```

Mais exemplos: [`examples/automations.md`](https://github.com/roalvesrj/ha-inmet-alertas/blob/main/custom_components/inmet_alertas/examples/automations.md).

## 🖥️ Cartões Lovelace

```yaml
type: entities
title: Alertas Meteorológicos
entities:
  - sensor.alertas_meteorologicos_sp # altere para o seu estado
  - sensor.quantidade_de_alertas_sp
```

```yaml
type: conditional
conditions:
  - entity: sensor.quantidade_de_alertas_sp # altere para o seu estado
    state_not: "0"
card:
  type: markdown
  content: >
    {% for alerta in state_attr('sensor.alertas_meteorologicos_sp', 'alertas') %}
    ### {{ alerta.icone }} {{ alerta.titulo }}
    **Severidade:** {{ alerta.severidade }} | **Período:** {{ alerta.inicio }} até {{ alerta.fim }}
    {% endfor %}
```

## 🆘 Solução de problemas

- **Alertas não aparecem**: confirme o estado configurado e veja os logs (**Configurações** → **Sistema** → **Logs**, filtrar `inmet_alertas`)
- **Notificações não chegam**: confirme `notificacoes_perigo` ativado e a existência de alertas Perigo/Grande Perigo
- **Polígonos não aparecem no mapa**: confirme o ha-map-card instalado, a URL do plugin e que há alertas ativos; use o controle "Camadas INMET" para ligar as severidades
- **Log de debug**:

```yaml
logger:
  logs:
    custom_components.inmet_alertas: debug
```

## 📈 Versionamento

[Versionamento semântico](https://semver.org/). Histórico completo: [CHANGELOG.md](https://github.com/roalvesrj/ha-inmet-alertas/blob/main/CHANGELOG.md).

**v2.0.0** — clima no mapa (radar de chuva e nuvens por satélite via RainViewer, com cache compartilhado e polling só quando ativo), tooltip/popup endurecidos, serviço com `async_refresh` e suíte ampliada (86 testes pytest + 42 node, cobertura 72%).

**v1.16.0** — seleção de camadas no mapa (severidades + mapa base Esri sem API key), base do tier Silver (`log-when-unavailable`, `PARALLEL_UPDATES`), correções no parsing do feed e no evento `inmet_alerta_expirado`.

**v1.15.0** — tier Bronze do Integration Quality Scale completo, config flow v2 com migração automática e suíte de testes com harness real do HA.

## 📄 Licença

MIT — veja [LICENSE](https://github.com/roalvesrj/ha-inmet-alertas/blob/main/LICENSE).

## ⚠️ Disclaimer

Integração não oficial, sem afiliação com o INMET. Os dados vêm do feed público de alertas do INMET.

## 🤝 Contribuindo

Fork, branch de feature, pull request. Issues são bem-vindos.
