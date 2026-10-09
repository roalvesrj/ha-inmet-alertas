/**
 * Smoke test do plugin do mapa INMET (roda com `node --test`, sem browser).
 *
 * Cobre a lógica pura e de roteamento:
 * - normalização da opção `severidades`
 * - criação dos grupos de camada por severidade
 * - visibilidade (add/remove layer) e idempotência
 * - roteamento de polígonos para o grupo correto + contagem
 * - seleção de basemap (cartográfico/satélite/topográfico) e retorno ao padrão
 * - limpeza
 *
 * O visual (controle no mapa, popups) permanece com verificação manual.
 */
import assert from 'node:assert/strict';
import test from 'node:test';

// Stubs mínimos de browser antes de carregar o módulo do plugin
globalThis.window = { customCards: [] };
globalThis.document = undefined;

const moduleUrl = new URL(
  '../../custom_components/inmet_alertas/www/plugin_inmet_polygons.js',
  import.meta.url,
);
const {
  default: criarPlugin,
  BASEMAPS,
  escaparHtml,
  normalizarSeveridades,
  SEVERIDADES,
} = await import(moduleUrl.href);

class PluginBase {
  constructor(map, name, options) {
    this.map = map;
    this.name = name;
    this.options = options;
  }
}

const logger = { debug() {}, warn() {}, error() {} };

class TileLayerStub {
  constructor(url, options = {}) {
    this._url = url;
    this.options = options;
  }

  getUrl() {
    return this._url;
  }
}

function criarGrupoStub() {
  return {
    camadas: [],
    addLayer(layer) {
      this.camadas.push(layer);
    },
    removeLayer(layer) {
      this.camadas = this.camadas.filter((item) => item !== layer);
    },
    clearLayers() {
      this.camadas = [];
    },
  };
}

function criarMapStub() {
  const camadas = [];
  return {
    camadas,
    calls: [],
    addLayer(layer) {
      camadas.push(layer);
      this.calls.push(['add', layer]);
    },
    removeLayer(layer) {
      const indice = camadas.indexOf(layer);
      if (indice >= 0) {
        camadas.splice(indice, 1);
      }
      this.calls.push(['remove', layer]);
    },
    eachLayer(fn) {
      [...camadas].forEach(fn);
    },
    addControl() {},
    removeControl() {},
    setView() {},
    temCamada(layer) {
      return camadas.includes(layer);
    },
  };
}

function criarLStub() {
  return {
    layerGroup: () => criarGrupoStub(),
    polygon: (coordenadas, opcoes) => {
      const poligono = {
        coordenadas,
        options: { ...opcoes },
        bindPopup() {
          return poligono;
        },
        bindTooltip() {
          return poligono;
        },
        setStyle() {
          return poligono;
        },
        closePopup() {},
        unbindTooltip() {},
      };
      return poligono;
    },
    tileLayer: (url, options) => new TileLayerStub(url, options),
    TileLayer: TileLayerStub,
    control: () => ({ addTo() {}, remove() {} }),
  };
}

function criarInstancia(options = {}) {
  const L = criarLStub();
  const InmetPlugin = criarPlugin(L, PluginBase, logger);
  const map = criarMapStub();
  return { plugin: new InmetPlugin(map, 'inmet', options), map, L };
}

function poligonoValido(area = 10) {
  return {
    coordenadas: [
      [-22.9, -43.2],
      [-22.9, -43.4],
      [-23.0, -43.4],
    ],
    area_km2: area,
    evento: 'Chuva',
    descricao: 'Teste',
  };
}

test('SEVERIDADES contém as três severidades oficiais', () => {
  assert.deepEqual(SEVERIDADES, [
    'Grande Perigo',
    'Perigo',
    'Perigo Potencial',
  ]);
});

test('normalizarSeveridades: ausente = todas visíveis', () => {
  assert.deepEqual(normalizarSeveridades(undefined), {
    'Grande Perigo': true,
    'Perigo': true,
    'Perigo Potencial': true,
  });
});

test('normalizarSeveridades: lista restringe as visíveis', () => {
  assert.deepEqual(normalizarSeveridades(['Perigo']), {
    'Grande Perigo': false,
    'Perigo': true,
    'Perigo Potencial': false,
  });
});

test('normalizarSeveridades: string única é aceita; lista vazia = nenhuma', () => {
  assert.deepEqual(normalizarSeveridades('Perigo Potencial'), {
    'Grande Perigo': false,
    'Perigo': false,
    'Perigo Potencial': true,
  });
  assert.deepEqual(normalizarSeveridades([]), {
    'Grande Perigo': false,
    'Perigo': false,
    'Perigo Potencial': false,
  });
});

test('construtor: grupos por severidade e controle habilitados por padrão', () => {
  const { plugin } = criarInstancia();

  assert.equal(plugin.showLayerControl, true);
  for (const severidade of SEVERIDADES) {
    assert.ok(plugin.severityLayerGroups[severidade], `grupo ${severidade}`);
  }
  assert.deepEqual(plugin.layerVisibility, {
    'Grande Perigo': true,
    'Perigo': true,
    'Perigo Potencial': true,
  });
});

test('aplicar visibilidade respeita a opção severidades (e é idempotente)', () => {
  const { plugin, map } = criarInstancia({ severidades: ['Perigo Potencial'] });

  plugin.aplicarVisibilidade();

  const grupos = plugin.severityLayerGroups;
  assert.equal(map.temCamada(grupos['Perigo Potencial']), true);
  assert.equal(map.temCamada(grupos['Perigo']), false);
  assert.equal(map.temCamada(grupos['Grande Perigo']), false);

  const chamadasAntes = map.calls.length;
  plugin.aplicarVisibilidade();
  assert.equal(map.calls.length, chamadasAntes, 'não deve readicionar');
});

test('setLayerVisibility liga/desliga a camada no mapa', () => {
  const { plugin, map } = criarInstancia();
  plugin.aplicarVisibilidade();

  const grupoPerigo = plugin.severityLayerGroups['Perigo'];

  plugin.setLayerVisibility('Perigo', false);
  assert.equal(map.temCamada(grupoPerigo), false);

  plugin.setLayerVisibility('Perigo', true);
  assert.equal(map.temCamada(grupoPerigo), true);
});

test('createPolygonLayer roteia polígonos para o grupo da severidade', () => {
  const { plugin } = criarInstancia();

  const adicionados = plugin.createPolygonLayer('rio_de_janeiro', 'rj', 'Perigo', [
    poligonoValido(10),
    poligonoValido(20),
  ]);

  assert.equal(adicionados, 2);
  assert.equal(plugin.severityLayerGroups['Perigo'].camadas.length, 2);
  assert.equal(plugin.severityLayerGroups['Grande Perigo'].camadas.length, 0);
  assert.equal(plugin._severityCounts['Perigo'], 2);
});

test('clearPolygons limpa todos os grupos e zera contagens', () => {
  const { plugin } = criarInstancia();

  plugin.createPolygonLayer('rio_de_janeiro', 'rj', 'Perigo', [poligonoValido()]);
  plugin.createPolygonLayer('rio_de_janeiro', 'rj', 'Grande Perigo', [
    poligonoValido(),
  ]);

  plugin.clearPolygons();

  for (const severidade of SEVERIDADES) {
    assert.equal(plugin.severityLayerGroups[severidade].camadas.length, 0);
    assert.equal(plugin._severityCounts[severidade], 0);
  }
});

test('BASEMAPS: opções keyless com url, atribuição e maxZoom', () => {
  assert.ok(BASEMAPS.cartografico.url.includes('openstreetmap'));
  assert.ok(BASEMAPS.satelite.url.includes('arcgisonline'));
  assert.ok(BASEMAPS.topografico.url.includes('opentopomap'));
  for (const definicao of Object.values(BASEMAPS)) {
    assert.ok(definicao.nome && definicao.attribution && definicao.maxZoom);
  }
});

test('setBasemap troca a imagem e oculta a camada padrão do cartão', () => {
  const { plugin, map, L } = criarInstancia();
  const camadaDoCartao = new L.TileLayer('https://carto.example/{z}/{x}/{y}.png');
  map.addLayer(camadaDoCartao);

  plugin.setBasemap('satelite');

  assert.equal(map.temCamada(camadaDoCartao), false, 'camada do cartão ocultada');
  assert.ok(plugin._basemapLayer, 'tile layer criada');
  assert.ok(plugin._basemapLayer.getUrl().includes('arcgisonline'));
  assert.equal(map.temCamada(plugin._basemapLayer), true);
});

test('setBasemap(null) volta ao mapa padrão do cartão', () => {
  const { plugin, map, L } = criarInstancia();
  const camadaDoCartao = new L.TileLayer('https://carto.example/{z}/{x}/{y}.png');
  map.addLayer(camadaDoCartao);

  plugin.setBasemap('topografico');
  plugin.setBasemap(null);

  assert.equal(map.temCamada(camadaDoCartao), true, 'camada original restaurada');
  assert.equal(plugin._basemapAtual, null);
});

test('setBasemap é idempotente e ignora chave inválida', () => {
  const { plugin, map } = criarInstancia();

  plugin.setBasemap('cartografico');
  const camadasAntes = map.camadas.length;

  plugin.setBasemap('cartografico');
  assert.equal(map.camadas.length, camadasAntes);

  plugin.setBasemap('inexistente');
  assert.equal(map.camadas.length, camadasAntes);
  assert.equal(plugin._basemapAtual, 'cartografico');
});

test('opção basemap é aplicada no construtor', () => {
  const { plugin } = criarInstancia({ basemap: 'satelite' });
  assert.equal(plugin._basemapAtual, 'satelite');
  assert.ok(plugin._basemapLayer);
});

test('escaparHtml neutraliza tags, aspas e &', () => {
  assert.equal(
    escaparHtml('<b>"x"</b> & \'y\''),
    '&lt;b&gt;&quot;x&quot;&lt;/b&gt; &amp; &#39;y&#39;',
  );
  assert.equal(escaparHtml(null), '');
  assert.equal(escaparHtml(undefined), '');
});

test('popup escapa dados vindos do feed', () => {
  const { plugin } = criarInstancia();

  const html = plugin.createPopupContent('rio_de_janeiro', 'rj', 'Perigo', {
    coordenadas: [
      [-22.9, -43.2],
      [-22.9, -43.4],
      [-23.0, -43.4],
    ],
    area_km2: 10,
    evento: '<script>alert(1)</script>',
    descricao: '<img src=x onerror=alert(1)>',
    inicio: '01/10 10:00',
    fim: '01/10 18:00',
    municipios: ['Rio <b>de</b> Janeiro - RJ'],
  });

  assert.ok(!html.includes('<script>'), 'script não deve passar cru');
  assert.ok(!html.includes('<img'), 'img não deve passar cru');
  assert.ok(html.includes('&lt;script&gt;'));
});

test('destroy cancela o retry e marca a instância como destruída', async () => {
  const { plugin } = criarInstancia();

  await plugin.waitForHomeAssistant();
  assert.ok(plugin._retryTimeoutId, 'retry agendado enquanto HA não aparece');

  plugin.destroy();

  assert.equal(plugin._retryTimeoutId, null);
  assert.equal(plugin._destruido, true);
});
