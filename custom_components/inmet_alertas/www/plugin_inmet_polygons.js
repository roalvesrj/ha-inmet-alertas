/**
 * Plugin INMET para ha-map-card.
 *
 * Desenha os polígonos dos alertas do INMET e oferece seleção de camadas:
 * - Severidade (Grande Perigo / Perigo / Perigo Potencial) via opção
 *   `severidades` e via controle no mapa.
 * - Basemap (Cartográfico / Satélite / Topográfico, sem API key) via opção
 *   `basemap` e via controle no mapa — inspirado no `map_style` do card do
 *   Flightradar24.
 *
 * Opções (todas opcionais):
 *   states            array de estados em snake_case (padrão: ['rio_de_janeiro'])
 *   entityPrefix      prefixo das entidades (padrão: 'sensor.inmet_alertas_mapa_')
 *   updateInterval    intervalo de atualização em ms (padrão: 60000)
 *   showLabels        tooltip por polígono (padrão: true)
 *   autoFocus         centraliza o mapa no estado com dados (padrão: true)
 *   colors            { grandePerigo, perigo, perigoPotencial }
 *   fillOpacity       opacidade do preenchimento (padrão: 0.5)
 *   strokeOpacity     opacidade da borda (padrão: 0.8)
 *   strokeWeight      espessura da borda (padrão: 2)
 *   severidades       lista/string das severidades visíveis (padrão: todas)
 *   basemap           'cartografico' | 'satelite' | 'topografico'
 *                     (padrão: mantém o mapa base do cartão)
 *   showLayerControl  exibe o controle de camadas (padrão: true)
 *   basemaps          estende/sobrescreve as definições de basemap
 *
 * @param L Leaflet library
 * @param pluginBase Base plugin class
 * @param Logger Logger utility
 */

export const SEVERIDADES = ['Grande Perigo', 'Perigo', 'Perigo Potencial'];

export const CORES_SEVERIDADE = {
  'Grande Perigo': '#F80703',
  'Perigo': '#FF8C00',
  'Perigo Potencial': '#FFFF00',
};

export const BASEMAPS = {
  cartografico: {
    nome: 'Cartográfico (Esri)',
    url: 'https://server.arcgisonline.com/ArcGIS/rest/services/World_Street_Map/MapServer/tile/{z}/{y}/{x}',
    attribution: 'Tiles &copy; Esri',
    maxZoom: 19,
  },
  satelite: {
    nome: 'Satélite (Esri)',
    url: 'https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}',
    attribution: 'Tiles &copy; Esri',
    maxZoom: 19,
  },
  topografico: {
    nome: 'Topográfico (Esri)',
    url: 'https://server.arcgisonline.com/ArcGIS/rest/services/World_Topo_Map/MapServer/tile/{z}/{y}/{x}',
    attribution: 'Tiles &copy; Esri',
    maxZoom: 19,
  },
};
// Nota: tiles do OpenStreetMap (osm.wiki/Blocked) bloqueiam aplicativos;
// os presets usam a Esri, que permite uso keyless com atribuição.

/**
 * Normaliza a opção `severidades` em um mapa severidade → visível.
 * Sem a opção, todas ficam visíveis; com lista/string, apenas as citadas.
 */
export function normalizarSeveridades(valor) {
  if (valor === undefined || valor === null) {
    return Object.fromEntries(SEVERIDADES.map((severidade) => [severidade, true]));
  }
  const lista = Array.isArray(valor) ? valor : [valor];
  return Object.fromEntries(
    SEVERIDADES.map((severidade) => [severidade, lista.includes(severidade)]),
  );
}

/**
 * Escapa texto para interpolação segura em HTML (dados de feed externo).
 */
export function escaparHtml(valor) {
  return String(valor ?? '')
    .replaceAll('&', '&amp;')
    .replaceAll('<', '&lt;')
    .replaceAll('>', '&gt;')
    .replaceAll('"', '&quot;')
    .replaceAll("'", '&#39;');
}

export const PRESETS_SEVERIDADE = {
  todas: [...SEVERIDADES],
  gp_perigo: ['Grande Perigo', 'Perigo'],
  grande: ['Grande Perigo'],
  perigo: ['Perigo'],
  potencial: ['Perigo Potencial'],
};

const PRESET_ROTULOS = {
  todas: 'Todas',
  gp_perigo: 'Grande Perigo + Perigo',
  grande: 'Só Grande Perigo',
  perigo: 'Só Perigo',
  potencial: 'Só Perigo Potencial',
};

/** Converte um preset em mapa severidade → visível. */
export function presetParaVisibilidade(preset) {
  const lista = PRESETS_SEVERIDADE[preset] || [];
  return Object.fromEntries(
    SEVERIDADES.map((severidade) => [severidade, lista.includes(severidade)]),
  );
}

/** Descobre o preset correspondente (ou null quando a seleção é personalizada). */
export function visibilidadeParaPreset(visibilidade) {
  for (const [preset, lista] of Object.entries(PRESETS_SEVERIDADE)) {
    if (
      SEVERIDADES.every(
        (severidade) => visibilidade[severidade] === lista.includes(severidade),
      )
    ) {
      return preset;
    }
  }
  return null;
}

export default function (L, pluginBase, Logger) {
  return class INMETPolygonsPlugin extends pluginBase {
    constructor(map, name, options = {}) {
      super(map, name, options);

      this._isUpdating = false;
      this._hasLoggedNoHass = false;
      this.intervalId = null;

      this.entityPrefix = options.entityPrefix || 'sensor.inmet_alertas_mapa_';
      this.updateInterval = options.updateInterval || 60000;
      this.showLabels = options.showLabels !== false;
      this.autoFocus = options.autoFocus !== false;
      this.showLayerControl = options.showLayerControl !== false;

      this.severityColors = {
        'Grande Perigo': options.colors?.grandePerigo || CORES_SEVERIDADE['Grande Perigo'],
        'Perigo': options.colors?.perigo || CORES_SEVERIDADE['Perigo'],
        'Perigo Potencial':
          options.colors?.perigoPotencial || CORES_SEVERIDADE['Perigo Potencial'],
      };

      this.fillOpacity = options.fillOpacity ?? 0.5;
      this.strokeOpacity = options.strokeOpacity ?? 0.8;
      this.strokeWeight = options.strokeWeight || 2;

      this.basemaps = { ...BASEMAPS };
      for (const [chave, definicao] of Object.entries(options.basemaps || {})) {
        this.basemaps[chave] = { ...(this.basemaps[chave] || {}), ...definicao };
      }

      this.stateMapping = {
        acre: 'ac', alagoas: 'al', amapa: 'ap', amazonas: 'am',
        bahia: 'ba', ceara: 'ce', distrito_federal: 'df', espirito_santo: 'es',
        goias: 'go', maranhao: 'ma', mato_grosso: 'mt', mato_grosso_do_sul: 'ms',
        minas_gerais: 'mg', para: 'pa', paraiba: 'pb', parana: 'pr',
        pernambuco: 'pe', piaui: 'pi', rio_de_janeiro: 'rj', rio_grande_do_norte: 'rn',
        rio_grande_do_sul: 'rs', rondonia: 'ro', roraima: 'rr', santa_catarina: 'sc',
        sao_paulo: 'sp', sergipe: 'se', tocantins: 'to',
      };

      this.states = options.states || ['rio_de_janeiro'];

      // Camadas por severidade (visibilidade controlável individualmente)
      this.layerVisibility = normalizarSeveridades(options.severidades);
      this.severityLayerGroups = Object.fromEntries(
        SEVERIDADES.map((severidade) => [severidade, L.layerGroup()]),
      );
      this._severityCounts = Object.fromEntries(
        SEVERIDADES.map((severidade) => [severidade, 0]),
      );
      this._groupsOnMap = Object.fromEntries(
        SEVERIDADES.map((severidade) => [severidade, false]),
      );

      // Basemap
      this._basemapAtual = null;
      this._basemapLayer = null;
      this._camadasBaseDoCartao = null;

      // Controle de camadas (criado sob demanda, quando há mapa/pronto)
      this._layerControl = null;
      this._controleEl = null;
      this._controleExpandido = false;
      this._retryTimeoutId = null;
      this._unlockTimeoutId = null;
      this._destruido = false;

      if (options.basemap) {
        this.setBasemap(options.basemap);
      }

      Logger.debug(
        `[INMETPolygonsPlugin] Inicializado: ${this.name} (${this.states.length} estados)`,
      );
    }

    async init() {
      this.waitForHomeAssistant();
    }

    async waitForHomeAssistant() {
      let attempts = 0;
      const maxAttempts = 30; // ~1 minuto

      const checkHass = () => {
        if (this._destruido) {
          return;
        }
        attempts++;

        let hass = null;
        if (this.hass && this.hass.states) {
          hass = this.hass;
        } else if (typeof window !== 'undefined' && window.hass?.states) {
          hass = window.hass;
        } else if (typeof document !== 'undefined') {
          const homeAssistant = document.querySelector('home-assistant');
          if (homeAssistant?.hass?.states) {
            hass = homeAssistant.hass;
          }
        }

        if (hass) {
          this._hassRef = hass;
          this.update();

          if (!this.intervalId) {
            this.intervalId = setInterval(() => this.update(), this.updateInterval);
          }
        } else if (attempts < maxAttempts) {
          this._retryTimeoutId = setTimeout(checkHass, 2000);
        } else {
          Logger.warn(
            '[INMETPolygonsPlugin] Home Assistant não encontrado após 1 minuto',
          );
        }
      };

      checkHass();
    }

    async renderMap() {
      await this.updatePolygons();
    }

    async update() {
      if (this._destruido || this._isUpdating) {
        return;
      }
      this._isUpdating = true;

      try {
        const hass = this._obterHass();
        if (!hass || !hass.states) {
          if (!this._hasLoggedNoHass) {
            Logger.debug('[INMETPolygonsPlugin] Aguardando Home Assistant...');
            this._hasLoggedNoHass = true;
          }
          return;
        }
        this._hasLoggedNoHass = false;
        await this.updatePolygons();
      } catch (error) {
        Logger.error('[INMETPolygonsPlugin] Erro no update:', error);
      } finally {
        this._unlockTimeoutId = setTimeout(() => {
          this._isUpdating = false;
        }, 500);
      }
    }

    _obterHass() {
      if (this._hassRef || this.hass) {
        return this._hassRef || this.hass;
      }
      if (typeof window !== 'undefined') {
        return window.hass;
      }
      return null;
    }

    async updatePolygons() {
      try {
        this.clearPolygons();

        const hass = this._obterHass();
        if (!hass || !hass.states) {
          Logger.debug('[INMETPolygonsPlugin] Home Assistant states indisponível');
          return;
        }

        let totalPolygons = 0;

        for (const estadoNome of this.states) {
          const estadoSigla = this.stateMapping[estadoNome];
          if (!estadoSigla) {
            Logger.warn(`[INMETPolygonsPlugin] Estado não mapeado: ${estadoNome}`);
            continue;
          }

          const entityId = `${this.entityPrefix}${estadoSigla}`;
          const entity = hass.states[entityId];
          if (!entity) {
            Logger.debug(`[INMETPolygonsPlugin] Entidade não encontrada: ${entityId}`);
            continue;
          }

          totalPolygons += this.processStateEntity(estadoNome, estadoSigla, entity);
        }

        // Aplica visibilidade das camadas e atualiza o controle
        this.aplicarVisibilidade();

        // Com basemap ativo, captura/oculta tiles que o cartão possa recriar
        if (this._basemapAtual) {
          this._ocultarCamadasBaseDoCartao();
        }
        this._criarAtualizarControle();

        if (this.autoFocus && totalPolygons > 0) {
          this._autoFocusMap();
        }

        Logger.debug(
          `[INMETPolygonsPlugin] Atualização completa - ${totalPolygons} polígonos`,
        );
      } catch (error) {
        Logger.error('[INMETPolygonsPlugin] Erro na atualização:', error);
      }
    }

    processStateEntity(estadoNome, estadoSigla, entity) {
      const attributes = entity.attributes || {};

      if (!attributes.camadas_por_severidade) {
        Logger.debug(
          `[INMETPolygonsPlugin] Sem dados geográficos para ${estadoNome} (${estadoSigla})`,
        );
        return 0;
      }

      const camadasData = attributes.camadas_por_severidade;
      let polygonCount = 0;

      for (const severity of SEVERIDADES) {
        const camadaInfo = camadasData[severity];
        if (camadaInfo?.poligonos?.length > 0) {
          polygonCount += this.createPolygonLayer(
            estadoNome,
            estadoSigla,
            severity,
            camadaInfo.poligonos,
          );
        }
      }

      return polygonCount;
    }

    createPolygonLayer(estadoNome, estadoSigla, severity, polygons) {
      const color = this.severityColors[severity];
      if (!color) {
        Logger.warn(`[INMETPolygonsPlugin] Cor não definida para severidade: ${severity}`);
        return 0;
      }

      const grupo = this.severityLayerGroups[severity];
      let polygonsAdded = 0;

      polygons.forEach((polygon, index) => {
        if (!Array.isArray(polygon.coordenadas) || polygon.coordenadas.length < 3) {
          Logger.debug(
            `[INMETPolygonsPlugin] Coordenadas insuficientes para polígono ${index}`,
          );
          return;
        }

        try {
          const polygonOptions = {
            color,
            weight: this.strokeWeight,
            opacity: this.strokeOpacity,
            fillColor: color,
            fillOpacity: this.fillOpacity,
            interactive: true,
            bubblingMouseEvents: false,
          };

          const leafletPolygon = L.polygon(polygon.coordenadas, polygonOptions);
          leafletPolygon.setStyle({
            fillOpacity: this.fillOpacity,
            opacity: this.strokeOpacity,
          });

          leafletPolygon.bindPopup(
            this.createPopupContent(estadoNome, estadoSigla, severity, polygon),
          );

          if (this.showLabels) {
            leafletPolygon.bindTooltip(`${severity} - ${estadoNome}`, {
              permanent: false,
              direction: 'center',
              className: 'inmet-polygon-tooltip',
            });
          }

          grupo.addLayer(leafletPolygon);
          this._severityCounts[severity] += 1;
          polygonsAdded++;
        } catch (polygonError) {
          Logger.error(
            `[INMETPolygonsPlugin] Erro criando polígono ${index} para ${estadoNome}/${severity}:`,
            polygonError,
          );
        }
      });

      return polygonsAdded;
    }

    createPopupContent(estadoNome, estadoSigla, severity, polygon) {
      const estadoFormatado = escaparHtml(
        estadoNome.charAt(0).toUpperCase() + estadoNome.slice(1).replace(/_/g, ' '),
      );

      const icons = {
        'Grande Perigo': '🔴',
        'Perigo': '🟠',
        'Perigo Potencial': '🟡',
      };
      const icon = icons[severity] || '⚠️';

      let content = `
        <div class="inmet-popup" style="min-width: 250px;">
          <h3 style="margin: 0 0 10px 0; color: ${escaparHtml(this.severityColors[severity])};">
            ${icon} ${severity}
          </h3>
          <div style="font-size: 13px; line-height: 1.4;">
            <p style="margin: 5px 0;"><strong>Estado:</strong> ${estadoFormatado} (${escaparHtml(estadoSigla.toUpperCase())})</p>
            <p style="margin: 5px 0;"><strong>Evento:</strong> ${escaparHtml(polygon.evento || 'Alerta Meteorológico')}</p>
            <p style="margin: 5px 0;"><strong>Área:</strong> ${polygon.area_km2?.toFixed(1) || 'N/A'} km²</p>
      `;

      if (polygon.centro && Array.isArray(polygon.centro) && polygon.centro.length >= 2) {
        content += `<p style="margin: 5px 0;"><strong>Centro:</strong> ${polygon.centro[0].toFixed(4)}, ${polygon.centro[1].toFixed(4)}</p>`;
      }

      if (polygon.inicio && polygon.fim) {
        content += `
          <p style="margin: 5px 0;"><strong>Início:</strong> ${escaparHtml(polygon.inicio)}</p>
          <p style="margin: 5px 0;"><strong>Fim:</strong> ${escaparHtml(polygon.fim)}</p>
        `;
      }

      if (polygon.descricao) {
        const descricao = escaparHtml(polygon.descricao);
        const shortDesc =
          descricao.length > 120 ? descricao.substring(0, 120) + '...' : descricao;
        content += `<p style="margin: 5px 0;"><strong>Descrição:</strong> ${shortDesc}</p>`;
      }

      if (polygon.municipios && Array.isArray(polygon.municipios) && polygon.municipios.length > 0) {
        const municipios = polygon.municipios.map((municipio) => escaparHtml(municipio));
        const municipiosText =
          municipios.length > 3
            ? municipios.slice(0, 3).join(', ') + ` e mais ${municipios.length - 3}`
            : municipios.join(', ');
        content += `<p style="margin: 5px 0;"><strong>Municípios:</strong> ${municipiosText}</p>`;
      }

      content += `
          </div>
          <div style="margin-top: 10px; padding-top: 8px; border-top: 1px solid #eee; font-size: 11px; color: #666;">
            INMET - Instituto Nacional de Meteorologia
          </div>
        </div>`;

      return content;
    }

    /**
     * Liga/desliga uma camada de severidade (API pública, usada pelo controle).
     */
    setLayerVisibility(severity, visivel) {
      if (!SEVERIDADES.includes(severity)) {
        return;
      }
      this.layerVisibility[severity] = !!visivel;
      this.aplicarVisibilidade();
      this._atualizarControleValores();
    }

    /**
     * Define quais severidades ficam visíveis de uma vez (usado pelo seletor).
     */
    setSeveridades(severidades) {
      const lista = Array.isArray(severidades) ? severidades : [severidades];
      for (const severidade of SEVERIDADES) {
        this.layerVisibility[severidade] = lista.includes(severidade);
      }
      this.aplicarVisibilidade();
      this._atualizarControleValores();
    }

    /**
     * Aplica a visibilidade atual de todas as camadas ao mapa (idempotente).
     */
    aplicarVisibilidade() {
      for (const severity of SEVERIDADES) {
        const grupo = this.severityLayerGroups?.[severity];
        if (!grupo || !this.map) {
          continue;
        }
        const visivel = this.layerVisibility[severity];
        const estaNoMapa = this._groupsOnMap[severity];

        if (visivel && !estaNoMapa) {
          this.map.addLayer(grupo);
          this._groupsOnMap[severity] = true;
        } else if (!visivel && estaNoMapa) {
          this.map.removeLayer(grupo);
          this._groupsOnMap[severity] = false;
        }
      }
    }

    /**
     * Troca o mapa base (null volta para o mapa padrão do cartão).
     * Os tiles originais do cartão são ocultados e restaurados.
     */
    setBasemap(id) {
      const alvo = id === null || id === undefined || id === 'padrao' ? null : id;

      if (alvo !== null && !this.basemaps[alvo]) {
        Logger.warn(`[INMETPolygonsPlugin] Basemap desconhecido: ${id}`);
        return;
      }
      if (alvo === this._basemapAtual && (alvo === null || this._basemapLayer)) {
        return;
      }

      if (alvo === null) {
        if (this._basemapLayer) {
          this.map.removeLayer(this._basemapLayer);
          this._basemapLayer = null;
        }
        this._basemapAtual = null;
        this._restaurarCamadasBaseDoCartao();
      } else {
        this._ocultarCamadasBaseDoCartao();
        if (this._basemapLayer) {
          this.map.removeLayer(this._basemapLayer);
        }
        const definicao = this.basemaps[alvo];
        this._basemapLayer = L.tileLayer(definicao.url, {
          attribution: definicao.attribution,
          maxZoom: definicao.maxZoom,
        });
        this.map.addLayer(this._basemapLayer);
        this._basemapAtual = alvo;
      }

      this._atualizarControleValores();
    }

    _ocultarCamadasBaseDoCartao() {
      if (this._camadasBaseDoCartao === null) {
        this._camadasBaseDoCartao = [];
      }
      this.map.eachLayer((layer) => {
        if (
          layer instanceof L.TileLayer &&
          layer !== this._basemapLayer &&
          !this._camadasBaseDoCartao.includes(layer)
        ) {
          this._camadasBaseDoCartao.push(layer);
          this.map.removeLayer(layer);
        }
      });
    }

    _restaurarCamadasBaseDoCartao() {
      if (!this._camadasBaseDoCartao) {
        return;
      }
      for (const layer of this._camadasBaseDoCartao) {
        this.map.addLayer(layer);
      }
      this._camadasBaseDoCartao = null;
    }

    _autoFocusMap() {
      try {
        const hass = this._obterHass();
        if (!hass || !hass.states) {
          return;
        }

        let bestEntity = null;
        for (const estadoNome of this.states) {
          const estadoSigla = this.stateMapping[estadoNome];
          if (!estadoSigla) {
            continue;
          }
          const entity = hass.states[`${this.entityPrefix}${estadoSigla}`];
          if (entity?.attributes?.centro_geografico) {
            bestEntity = entity;
            break;
          }
        }

        if (!bestEntity) {
          return;
        }

        const attrs = bestEntity.attributes;
        let center = attrs.centro_geografico;
        const zoom = attrs.zoom_recomendado;

        if (!center && attrs.bounding_box) {
          const bb = attrs.bounding_box;
          center = [(bb.min_lat + bb.max_lat) / 2, (bb.min_lon + bb.max_lon) / 2];
        }

        if (center && Array.isArray(center) && center.length >= 2) {
          this.map.setView(center, zoom || 8);
        }
      } catch (error) {
        Logger.error('[INMETPolygonsPlugin] Erro no autoFocus:', error);
      }
    }

    // --- Controle de camadas (UI) ---

    _criarAtualizarControle() {
      if (!this.showLayerControl || typeof document === 'undefined') {
        return;
      }

      if (!this._layerControl) {
        const control = L.control({ position: 'topright' });
        control.onAdd = () => this._montarControle();
        control.onRemove = () => {
          this._controleEl = null;
        };
        this._layerControl = control;
        this.map.addControl(control);
      }

      this._atualizarControleValores();
    }

    _montarControle() {
      const el = document.createElement('div');
      el.className = 'inmet-camadas';

      const opcoesBasemap = [
        '<option value="padrao">Padrão do cartão</option>',
        ...Object.entries(this.basemaps).map(
          ([chave, definicao]) =>
            `<option value="${escaparHtml(chave)}">${escaparHtml(definicao.nome)}</option>`,
        ),
      ].join('');

      const opcoesSeveridade = [
        `<option value="todas">${PRESET_ROTULOS.todas}</option>`,
        `<option value="gp_perigo">${PRESET_ROTULOS.gp_perigo}</option>`,
        `<option value="grande">${PRESET_ROTULOS.grande}</option>`,
        `<option value="perigo">${PRESET_ROTULOS.perigo}</option>`,
        `<option value="potencial">${PRESET_ROTULOS.potencial}</option>`,
        '<option value="personalizado" disabled>Personalizado (YAML)</option>',
      ].join('');

      el.innerHTML = `
        <style>
          .inmet-camadas {
            display: flex;
            flex-direction: column;
            align-items: flex-end;
            gap: 6px;
          }
          .inmet-camadas-botao {
            position: relative;
            display: inline-flex;
            align-items: center;
            justify-content: center;
            width: 34px;
            height: 34px;
            padding: 0;
            border: 0;
            border-radius: 8px;
            cursor: pointer;
            background: var(--card-background-color, #fff);
            color: var(--primary-text-color, #212121);
            box-shadow: 0 1px 5px rgba(0, 0, 0, 0.4);
          }
          .inmet-camadas-botao:hover {
            background: var(--secondary-background-color, #f2f2f2);
          }
          .inmet-camadas-contagem {
            position: absolute;
            top: -4px;
            right: -4px;
            min-width: 15px;
            height: 15px;
            padding: 0 3px;
            border-radius: 8px;
            background: var(--primary-color, #03a9f4);
            color: #fff;
            font-size: 9px;
            line-height: 15px;
            text-align: center;
          }
          .inmet-camadas-painel {
            display: none;
            gap: 6px;
            width: 180px;
            padding: 8px 10px;
            border-radius: 8px;
            background: var(--card-background-color, #fff);
            color: var(--primary-text-color, #212121);
            box-shadow: 0 1px 5px rgba(0, 0, 0, 0.4);
            font-size: 12px;
            line-height: 1.5;
          }
          .inmet-camadas.aberto .inmet-camadas-painel { display: grid; }
          .inmet-camadas-titulo { font-weight: 600; }
          .inmet-camadas-linha { display: grid; gap: 2px; min-width: 0; }
          .inmet-camadas-linha span { opacity: 0.7; }
          .inmet-camadas select {
            width: 100%;
            box-sizing: border-box;
            font: inherit;
            color: inherit;
            background: var(--card-background-color, #fff);
            border: 1px solid var(--divider-color, #ccc);
            border-radius: 4px;
            padding: 2px 4px;
          }
        </style>
        <button type="button" class="inmet-camadas-botao" title="Camadas INMET"
                aria-label="Camadas INMET" aria-expanded="false">
          <svg viewBox="0 0 24 24" width="18" height="18" fill="currentColor" aria-hidden="true">
            <path d="M12 2 1 8l11 6 11-6-11-6zm0 2.3L19.7 8 12 11.7 4.3 8 12 4.3zM1 12l11 6 11-6v2l-11 6L1 14v-2zm0 4 11 6 11-6v2l-11 6L1 20v-2z"/>
          </svg>
          <span class="inmet-camadas-contagem" hidden></span>
        </button>
        <div class="inmet-camadas-painel">
          <div class="inmet-camadas-titulo">Camadas INMET</div>
          <label class="inmet-camadas-linha">
            <span>Mapa base</span>
            <select data-inmet-basemap>${opcoesBasemap}</select>
          </label>
          <label class="inmet-camadas-linha">
            <span>Alertas</span>
            <select data-inmet-severidade>${opcoesSeveridade}</select>
          </label>
        </div>
      `;

      el.querySelector('.inmet-camadas-botao')?.addEventListener('click', () => {
        this._alternarControle();
      });

      const selectBasemap = el.querySelector('select[data-inmet-basemap]');
      selectBasemap?.addEventListener('change', (evento) => {
        const valor = evento.target.value;
        this.setBasemap(valor === 'padrao' ? null : valor);
      });

      const selectSeveridade = el.querySelector('select[data-inmet-severidade]');
      selectSeveridade?.addEventListener('change', (evento) => {
        const preset = evento.target.value;
        if (preset !== 'personalizado') {
          this.setSeveridades(PRESETS_SEVERIDADE[preset] || []);
        }
      });

      this._controleEl = el;
      this._atualizarControleValores();
      return el;
    }

    _alternarControle() {
      this._controleExpandido = !this._controleExpandido;
      const el = this._controleEl;
      if (!el) {
        return;
      }
      el.classList.toggle('aberto', this._controleExpandido);
      el.querySelector('.inmet-camadas-botao')?.setAttribute(
        'aria-expanded',
        String(this._controleExpandido),
      );
      this._atualizarControleValores();
    }

    _atualizarControleValores() {
      if (!this._controleEl) {
        return;
      }

      const total = SEVERIDADES.reduce(
        (soma, severidade) => soma + (this._severityCounts[severidade] || 0),
        0,
      );

      const contagem = this._controleEl.querySelector('.inmet-camadas-contagem');
      if (contagem) {
        contagem.textContent = String(total);
        contagem.hidden = total === 0;
      }

      const selectBasemap = this._controleEl.querySelector(
        'select[data-inmet-basemap]',
      );
      if (selectBasemap) {
        selectBasemap.value = this._basemapAtual || 'padrao';
      }

      const selectSeveridade = this._controleEl.querySelector(
        'select[data-inmet-severidade]',
      );
      if (selectSeveridade) {
        selectSeveridade.value = visibilidadeParaPreset(this.layerVisibility) || 'personalizado';

        for (const option of selectSeveridade.options) {
          if (option.value === 'personalizado' || !PRESETS_SEVERIDADE[option.value]) {
            continue;
          }
          const contagemPreset =
            option.value === 'todas'
              ? total
              : PRESETS_SEVERIDADE[option.value].reduce(
                  (soma, severidade) => soma + (this._severityCounts[severidade] || 0),
                  0,
                );
          option.textContent = `${PRESET_ROTULOS[option.value]} (${contagemPreset})`;
        }
      }
    }

    // --- Limpeza ---

    clearPolygons() {
      try {
        for (const severidade of SEVERIDADES) {
          const grupo = this.severityLayerGroups?.[severidade];
          if (!grupo) {
            continue;
          }
          grupo.eachLayer?.((layer) => {
            layer.closePopup?.();
            layer.unbindTooltip?.();
          });
          grupo.clearLayers();
          this._severityCounts[severidade] = 0;
        }
      } catch (error) {
        Logger.error('[INMETPolygonsPlugin] Erro limpando polígonos:', error);
      }
    }

    destroy() {
      try {
        this._destruido = true;

        if (this._retryTimeoutId) {
          clearTimeout(this._retryTimeoutId);
          this._retryTimeoutId = null;
        }
        if (this._unlockTimeoutId) {
          clearTimeout(this._unlockTimeoutId);
          this._unlockTimeoutId = null;
        }

        if (this.intervalId) {
          clearInterval(this.intervalId);
          this.intervalId = null;
        }

        this.clearPolygons();

        for (const severidade of SEVERIDADES) {
          const grupo = this.severityLayerGroups?.[severidade];
          if (grupo && this._groupsOnMap[severidade]) {
            this.map.removeLayer(grupo);
            this._groupsOnMap[severidade] = false;
          }
        }

        if (this._basemapLayer) {
          this.map.removeLayer(this._basemapLayer);
          this._basemapLayer = null;
        }
        this._restaurarCamadasBaseDoCartao();

        if (this._layerControl) {
          this.map.removeControl(this._layerControl);
          this._layerControl = null;
          this._controleEl = null;
        }

        this._hassRef = null;
        this.hass = null;
      } catch (error) {
        Logger.error('[INMETPolygonsPlugin] Erro destruindo plugin:', error);
      }
    }
  };
}
