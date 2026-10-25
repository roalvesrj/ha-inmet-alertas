# Plugin ha-map-card para INMET Alertas

Este plugin permite visualizar polígonos de alertas meteorológicos do INMET em mapas usando o ha-map-card, com **seleção de camadas** por severidade e de **mapa base** (sem API key).

## Instalação Automática

O plugin é instalado automaticamente quando você instala a integração INMET Alertas via HACS.

## Uso

```yaml
type: custom:map-card
title: "Alertas INMET"
zoom: 6
x: -15.7998  # Coordenada obrigatória
y: -47.8645  # Coordenada obrigatória

plugins:
  - name: inmet_polygons
    url: /inmet_alertas/plugin_inmet_polygons.js  # URL servida pela integração
    options:
      states: ["rio_de_janeiro"]  # Seus estados
      # severidades: ["Grande Perigo", "Perigo"]  # opcional (padrão: todas)
      # basemap: satelite                          # opcional (padrão: mapa do cartão)
```

## Controle "Camadas INMET" no mapa

Um **botão de camadas** no canto do mapa (com badge da contagem de polígonos) que **expande ao clicar**, com **um seletor para cada grupo**:

- **Mapa base**: Padrão do cartão, Cartográfico, Satélite e Topográfico — tiles da **Esri**, **sem API key**;
- **Alertas**: Todas, Grande Perigo + Perigo ou somente uma severidade — com contagem de polígonos em cada opção;
- **Clima**: Nenhuma, Chuva (radar) ou Nuvens (satélite) — overlay keyless do [RainViewer](https://www.rainviewer.com/); atualiza a cada 5 min e o polling só roda com um overlay ativo (opções sem frame aparecem como "— indisponível").

## Opções

| Opção | Tipo | Padrão | Descrição |
|---|---|---|---|
| `states` | lista | `["rio_de_janeiro"]` | Estados monitorados (snake_case) |
| `entityPrefix` | string | `sensor.inmet_alertas_mapa_` | Prefixo das entidades |
| `updateInterval` | número | `60000` | Intervalo de atualização (ms) |
| `showLabels` | bool | `true` | Tooltip por polígono |
| `autoFocus` | bool | `true` | Centraliza o mapa na área com alertas |
| `colors` | objeto | cores oficiais | `{ grandePerigo, perigo, perigoPotencial }` |
| `fillOpacity` | número | `0.5` | Opacidade do preenchimento |
| `strokeOpacity` | número | `0.8` | Opacidade da borda |
| `strokeWeight` | número | `2` | Espessura da borda |
| `severidades` | lista/string | todas | Severidades visíveis |
| `basemap` | string | mapa do cartão | `cartografico`, `satelite` ou `topografico` |
| `clima` | string | nenhuma | `radar` ou `nuvens` (overlay do RainViewer) |
| `climaOpacidade` | número | `0.6` | Opacidade do overlay de clima (0.1–1) |
| `showLayerControl` | bool | `true` | Exibe o controle de camadas |
| `basemaps` | objeto | — | Estende/sobrescreve definições de basemap |

## Card de alertas (`inmet-alert-card.js`)

O mesmo pacote inclui um card de alertas por severidade (sem dependências, sem build), **registrado automaticamente** pela integração como recurso do Lovelace. Use um card por severidade:

```yaml
type: custom:inmet-alert-card
estado: RJ
severidade: Perigo
titulo: Alertas de Perigo
```

```yaml
type: custom:inmet-alert-card
estado: RJ
severidade: Grande Perigo
titulo: Alertas de Grande Perigo
```

Opções: `estado` (ou `entidade`), `severidade` (`Perigo`, `Grande Perigo`, `Perigo Potencial`, `todas`), `titulo`, `maxAlertas` (5), `paginacao` (false), `itensPorPagina` (1), `mostrarVazio` (false), `mostrarDetalhes` (true), `mostrarProgresso` (true), `mostrarMunicipios` (true).

Com vários alertas, `paginacao: true` mostra um por vez com navegação (‹ 1 de N ›). A descrição é resumida em até 3 linhas; o texto completo fica em **Ler detalhes**.

Visual inspirado no [weather_alerts_card](https://github.com/seevee/weather_alerts_card) (MIT), adaptado ao formato de dados da integração.

## Dependências
- Home Assistant
- HACS
- ha-map-card (instalado via HACS)
- Integração INMET Alertas

## Suporte

Para dúvidas sobre o plugin, abra um issue no repositório da integração INMET Alertas.
