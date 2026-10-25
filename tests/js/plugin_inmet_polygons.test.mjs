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
import { readFileSync } from 'node:fs';
import { beforeEach, test } from 'node:test';

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
  extrairCamadasClima,
  formatarArea,
  formatarCentro,
  normalizarClima,
  normalizarOpacidade,
  normalizarSeveridades,
  presetParaVisibilidade,
  reiniciarClimaCompartilhado,
  SEVERIDADES,
  VERSAO_PLUGIN,
  visibilidadeParaPreset,
} = await import(moduleUrl.href);

class PluginBase {
  constructor(map, name, options) {
    this.map = map;
    this.name = name;
    this.options = options;
  }
}

const logger = { debug() {}, warn() {}, error() {} };

// O cache de clima é estado de módulo: cada teste começa com ele limpo
beforeEach(() => {
  reiniciarClimaCompartilhado();
});

class TileLayerStub {
  constructor(url, options = {}) {
    this._url = url;
    this.options = { ...options };
  }

  getUrl() {
    return this._url;
  }

  setUrl(url) {
    this._url = url;
    return this;
  }

  setOpacity(opacidade) {
    this.options.opacity = opacidade;
    return this;
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
    hasLayer(layer) {
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
        bindTooltip(texto, opcoes) {
          poligono.tooltipBinds = poligono.tooltipBinds || [];
          poligono.tooltipBinds.push({ texto, opcoes });
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
  return {
    plugin: new InmetPlugin(map, 'inmet', {
      // Stub padrão: evita rede real nos testes que não injetam o próprio
      climaFetch: async () => ({ ok: true, json: async () => ({}) }),
      ...options,
    }),
    map,
    L,
  };
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
  assert.ok(BASEMAPS.cartografico.url.includes('World_Street_Map'));
  assert.ok(BASEMAPS.satelite.url.includes('World_Imagery'));
  assert.ok(BASEMAPS.topografico.url.includes('World_Topo_Map'));
  for (const definicao of Object.values(BASEMAPS)) {
    assert.ok(definicao.nome && definicao.attribution && definicao.maxZoom);
  }
});

test('BASEMAPS não usa tiles do OSM (apps são bloqueados pela política)', () => {
  for (const definicao of Object.values(BASEMAPS)) {
    assert.ok(
      !definicao.url.includes('openstreetmap'),
      `${definicao.nome} usa tiles do OSM (osm.wiki/Blocked)`,
    );
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
    inicio: 'INICIO<tag>',
    fim: 'FIM<tag>',
    municipios: ['Rio <b>de</b> Janeiro - RJ'],
  });

  assert.ok(!html.includes('<script>'), 'script não deve passar cru');
  assert.ok(!html.includes('<img'), 'img não deve passar cru');
  assert.ok(!html.includes('<tag>'), 'tags não devem passar cruas');
  assert.ok(html.includes('&lt;script&gt;'));
  assert.ok(html.includes('INICIO&lt;tag&gt;'), 'início deve ser escapado');
  assert.ok(html.includes('FIM&lt;tag&gt;'), 'fim deve ser escapado');
});

test('tooltip do polígono escapa o estado (Leaflet insere string como HTML)', () => {
  const { plugin } = criarInstancia();
  plugin.createPolygonLayer('estado<x>', 'xx', 'Perigo', [poligonoValido()]);

  const camada = plugin.severityLayerGroups['Perigo'].camadas[0];
  assert.ok(camada, 'polígono criado');
  assert.equal(camada.tooltipBinds?.length, 1, 'um tooltip vinculado');
  assert.ok(
    camada.tooltipBinds[0].texto.includes('estado&lt;x&gt;'),
    'estado do tooltip deve ser escapado',
  );
});

test('destroy cancela o retry e marca a instância como destruída', async () => {
  const { plugin } = criarInstancia();

  await plugin.waitForHomeAssistant();
  assert.ok(plugin._retryTimeoutId, 'retry agendado enquanto HA não aparece');

  plugin.destroy();

  assert.equal(plugin._retryTimeoutId, null);
  assert.equal(plugin._destruido, true);
});

test('presets de severidade: ida e volta', () => {
  assert.deepEqual(presetParaVisibilidade('perigo'), {
    'Grande Perigo': false,
    'Perigo': true,
    'Perigo Potencial': false,
  });
  assert.equal(visibilidadeParaPreset(presetParaVisibilidade('todas')), 'todas');
  assert.equal(visibilidadeParaPreset(presetParaVisibilidade('gp_perigo')), 'gp_perigo');
  assert.equal(visibilidadeParaPreset(presetParaVisibilidade('potencial')), 'potencial');
  assert.equal(
    visibilidadeParaPreset({
      'Grande Perigo': true,
      'Perigo': false,
      'Perigo Potencial': true,
    }),
    null,
    'combinação fora dos presets → personalizado',
  );
});

test('setSeveridades aplica a visibilidade e as camadas no mapa', () => {
  const { plugin, map } = criarInstancia();
  plugin.aplicarVisibilidade(); // todas visíveis

  plugin.setSeveridades(['Perigo']);

  assert.equal(plugin.layerVisibility['Perigo'], true);
  assert.equal(plugin.layerVisibility['Grande Perigo'], false);
  assert.equal(plugin.layerVisibility['Perigo Potencial'], false);
  assert.equal(map.temCamada(plugin.severityLayerGroups['Perigo']), true);
  assert.equal(map.temCamada(plugin.severityLayerGroups['Grande Perigo']), false);
});

test('normalizarClima aceita radar/nuvens e rejeita o resto', () => {
  assert.equal(normalizarClima('radar'), 'radar');
  assert.equal(normalizarClima('nuvens'), 'nuvens');
  assert.equal(normalizarClima('nenhuma'), null);
  assert.equal(normalizarClima(undefined), null);
  assert.equal(normalizarClima('qualquer'), null);
});

test('normalizarOpacidade limita entre 0.1 e 1', () => {
  assert.equal(normalizarOpacidade(0.6), 0.6);
  assert.equal(normalizarOpacidade(0), 0.1);
  assert.equal(normalizarOpacidade(5), 1);
  assert.equal(normalizarOpacidade('x'), 0.6);
  assert.equal(normalizarOpacidade(undefined, 0.4), 0.4);
});

test('extrairCamadasClima monta as URLs do frame mais recente', () => {
  const dados = {
    host: 'https://tilecache.rainviewer.com',
    radar: { past: [{ path: '/v2/radar/old' }, { path: '/v2/radar/novo' }] },
    satellite: { infrared: [{ path: '/v2/satellite/ir1' }] },
  };

  const urls = extrairCamadasClima(dados);

  assert.equal(
    urls.radar,
    'https://tilecache.rainviewer.com/v2/radar/novo/256/{z}/{x}/{y}/2/1_1.png',
  );
  assert.equal(
    urls.nuvens,
    'https://tilecache.rainviewer.com/v2/satellite/ir1/256/{z}/{x}/{y}/0/0_0.png',
  );
});

test('extrairCamadasClima degrada com segurança', () => {
  const semNuvens = extrairCamadasClima({
    host: 'https://tilecache.rainviewer.com',
    radar: { past: [{ path: '/v2/radar/a' }] },
    satellite: { infrared: [] },
  });
  assert.ok(semNuvens.radar);
  assert.equal(semNuvens.nuvens, null);

  assert.deepEqual(extrairCamadasClima({ host: 'http://inseguro', radar: { past: [] } }), {
    radar: null,
    nuvens: null,
  });
  assert.deepEqual(extrairCamadasClima(undefined), { radar: null, nuvens: null });

  const caminhoRuim = extrairCamadasClima({
    host: 'https://tilecache.rainviewer.com',
    radar: { past: [{ path: 'sem-barra' }] },
  });
  assert.equal(caminhoRuim.radar, null);
});

test('setClima aplica, troca de frame e remove o overlay', () => {
  const { plugin, map } = criarInstancia();
  plugin._climaUrls = {
    radar: 'https://tilecache.rainviewer.com/v2/radar/a/256/{z}/{x}/{y}/2/1_1.png',
    nuvens: null,
  };

  plugin.setClima('radar');
  assert.ok(plugin._climaLayer, 'camada de radar criada');
  assert.equal(map.temCamada(plugin._climaLayer), true);
  assert.ok(plugin._climaLayer.getUrl().includes('/v2/radar/a/'));
  assert.ok(plugin._climaLayer.options.attribution.includes('RainViewer'));

  plugin.setClima('nuvens'); // indisponível → remove
  assert.equal(plugin._climaLayer, null);
  assert.equal(map.camadas.length, 0);

  plugin.setClima('radar');
  plugin._climaUrls.radar =
    'https://tilecache.rainviewer.com/v2/radar/b/256/{z}/{x}/{y}/2/1_1.png';
  plugin.setClima('radar');
  assert.ok(
    plugin._climaLayer.getUrl().includes('/v2/radar/b/'),
    'novo frame aplicado via setUrl',
  );

  plugin.destroy();
});

test('overlay de clima não é capturado como camada do cartão (basemap)', () => {
  const { plugin, map, L } = criarInstancia();
  const camadaDoCartao = new L.TileLayer('https://carto.example/{z}/{x}/{y}.png');
  map.addLayer(camadaDoCartao);

  plugin._climaUrls = {
    radar: 'https://tilecache.rainviewer.com/v2/radar/a/256/{z}/{x}/{y}/2/1_1.png',
    nuvens: null,
  };

  // Com basemap ativo, o ciclo de atualização oculta as camadas do cartão...
  plugin.setBasemap('cartografico');
  plugin.setClima('radar');
  plugin._ocultarCamadasBaseDoCartao(); // simula o que updatePolygons faz a cada ciclo

  assert.equal(map.temCamada(plugin._climaLayer), true, 'clima permanece no mapa');
  assert.equal(map.temCamada(camadaDoCartao), false, 'camada do cartão segue ocultada');
  assert.equal(map.temCamada(plugin._basemapLayer), true, 'basemap ativo permanece');

  plugin.destroy();
});

test('VERSAO_PLUGIN em sincronia com manifest.json e const.VERSION', () => {
  const raiz = new URL('../../', import.meta.url);
  const manifest = JSON.parse(
    readFileSync(new URL('custom_components/inmet_alertas/manifest.json', raiz), 'utf8'),
  );
  const constPy = readFileSync(
    new URL('custom_components/inmet_alertas/const.py', raiz),
    'utf8',
  );
  const versaoConst = constPy.match(/VERSION[^=]*=\s*"([^"]+)"/)?.[1];

  assert.equal(VERSAO_PLUGIN, manifest.version, 'banner x manifest.json');
  assert.equal(VERSAO_PLUGIN, versaoConst, 'banner x const.VERSION');
});

// --- Ciclo de vida do clima (fetch injetado via opção `climaFetch`) ---

const drenar = () => new Promise((resolve) => setTimeout(resolve, 0));

function criarFetchStub(resposta) {
  const chamadas = [];
  const stub = async (url) => {
    chamadas.push(url);
    return resposta;
  };
  stub.chamadas = chamadas;
  return stub;
}

const payloadClimaOk = () => ({
  ok: true,
  json: async () => ({
    host: 'https://tilecache.rainviewer.com',
    radar: { past: [{ time: 1, path: '/v2/radar/a' }] },
    satellite: { infrared: [{ time: 1, path: '/v2/satellite/b' }] },
  }),
});

test('_atualizarClima usa o fetch injetado e aplica as URLs extraídas', async () => {
  const fetchStub = criarFetchStub(payloadClimaOk());
  const { plugin } = criarInstancia({ climaFetch: fetchStub });

  await plugin._atualizarClima();

  assert.equal(fetchStub.chamadas.length, 1, 'uma chamada à API do RainViewer');
  assert.equal(
    plugin._climaUrls.radar,
    'https://tilecache.rainviewer.com/v2/radar/a/256/{z}/{x}/{y}/2/1_1.png',
  );
  assert.equal(
    plugin._climaUrls.nuvens,
    'https://tilecache.rainviewer.com/v2/satellite/b/256/{z}/{x}/{y}/0/0_0.png',
  );
});

test('_atualizarClima trata resposta não-ok como falha', async () => {
  const fetchStub = criarFetchStub({ ok: false, status: 503 });
  const { plugin } = criarInstancia({ climaFetch: fetchStub });

  await plugin._atualizarClima();

  assert.equal(plugin._climaUrls.radar, null, 'sem URLs após falha HTTP');
});

test('_atualizarClima engole rejeição de rede sem estourar', async () => {
  const fetchStub = async () => {
    throw new Error('offline');
  };
  const { plugin } = criarInstancia({ climaFetch: fetchStub });

  await plugin._atualizarClima();

  assert.equal(plugin._climaUrls.radar, null);
});

test('init sem overlay ativo não agenda polling do clima', async () => {
  const fetchStub = criarFetchStub(payloadClimaOk());
  const { plugin } = criarInstancia({ climaFetch: fetchStub });

  await plugin.init();
  await drenar();

  assert.equal(fetchStub.chamadas.length, 1, 'apenas a verificação inicial');
  assert.equal(plugin._climaIntervalId, null, 'sem polling sem overlay ativo');

  plugin.destroy();
});

test('init com overlay ativo agenda polling do clima', async () => {
  const fetchStub = criarFetchStub(payloadClimaOk());
  const { plugin } = criarInstancia({ clima: 'radar', climaFetch: fetchStub });

  await plugin.init();
  assert.ok(plugin._climaIntervalId, 'polling ativo com overlay ligado');

  plugin.destroy();
  assert.equal(plugin._climaIntervalId, null, 'destroy encerra o polling');
});

test('setClima(radar) inicia o polling; setClima(null) encerra', () => {
  const fetchStub = criarFetchStub(payloadClimaOk());
  const { plugin } = criarInstancia({ climaFetch: fetchStub });

  plugin.setClima('radar');
  assert.ok(plugin._climaIntervalId, 'poll iniciado ao ligar o overlay');

  plugin.setClima(null);
  assert.equal(plugin._climaIntervalId, null, 'poll encerrado ao desligar');
});

test('opções de clima ficam desabilitadas e rotuladas quando indisponíveis', () => {
  const { plugin } = criarInstancia();
  const opcoes = {
    'option[value="radar"]': { disabled: false, textContent: '' },
    'option[value="nuvens"]': { disabled: false, textContent: '' },
  };
  plugin._controleEl = {
    querySelector: (seletor) =>
      seletor === 'select[data-inmet-clima]'
        ? { value: 'nenhuma', querySelector: (opt) => opcoes[opt] || null }
        : null,
  };

  plugin._climaUrls = { radar: null, nuvens: null };
  plugin._atualizarControleValores();
  assert.equal(opcoes['option[value="radar"]'].disabled, true);
  assert.equal(
    opcoes['option[value="radar"]'].textContent,
    'Chuva (radar) — indisponível',
  );
  assert.equal(
    opcoes['option[value="nuvens"]'].textContent,
    'Nuvens (satélite) — indisponível',
  );

  plugin._climaUrls = { radar: 'https://x/radar', nuvens: null };
  plugin._atualizarControleValores();
  assert.equal(opcoes['option[value="radar"]'].disabled, false);
  assert.equal(opcoes['option[value="radar"]'].textContent, 'Chuva (radar)');
});

test('setClima(null) remove o overlay do mapa', () => {
  const { plugin, map } = criarInstancia();
  plugin._climaUrls = {
    radar: 'https://tilecache.rainviewer.com/v2/radar/a/256/{z}/{x}/{y}/2/1_1.png',
    nuvens: null,
  };

  plugin.setClima('radar');
  assert.ok(map.temCamada(plugin._climaLayer), 'overlay no mapa');

  plugin.setClima(null);
  assert.equal(plugin._climaLayer, null);
  assert.equal(map.temCamada(plugin._climaLayer), false);
});

test('opacidade configurada chega à camada de clima', () => {
  const { plugin } = criarInstancia({ climaOpacidade: 0.2 });
  plugin._climaUrls = {
    radar: 'https://tilecache.rainviewer.com/v2/radar/a/256/{z}/{x}/{y}/2/1_1.png',
    nuvens: null,
  };

  plugin.setClima('radar');
  assert.equal(plugin._climaLayer.options.opacity, 0.2);

  plugin.destroy();
});

test('popup sobrevive a área e centro inválidos vindos do feed', () => {
  const { plugin } = criarInstancia();

  const html = plugin.createPopupContent('rio_de_janeiro', 'rj', 'Perigo', {
    coordenadas: [
      [-22.9, -43.2],
      [-22.9, -43.4],
      [-23.0, -43.4],
    ],
    area_km2: 'muito',
    centro: ['norte', 'sul'],
    evento: 'Chuva',
  });

  assert.ok(html.includes('Área:</strong> N/A'), 'área inválida vira N/A');
  assert.ok(!html.includes('Centro:'), 'centro inválido não é renderizado');
  assert.ok(html.includes('Chuva'), 'demais campos seguem presentes');
});

test('duas instâncias compartilham um único fetch (cache de módulo)', async () => {
  const fetchStub = criarFetchStub(payloadClimaOk());
  const a = criarInstancia({ climaFetch: fetchStub });
  const b = criarInstancia({ climaFetch: fetchStub });

  a.plugin._iniciarClima(); // dispara o fetch e assina
  b.plugin._iniciarClima(); // encontra o voo em andamento — não duplica
  await drenar();

  assert.equal(fetchStub.chamadas.length, 1, 'um request para as duas instâncias');
  assert.ok(a.plugin._climaUrls.radar, 'primeira instância atualizada');
  assert.ok(b.plugin._climaUrls.radar, 'segunda instância notificada');

  a.plugin.destroy();
  b.plugin.destroy();
});

test('fetch em andamento impede segundo request simultâneo', async () => {
  let chamadas = 0;
  let resolveFetch;
  const fetchStub = async () => {
    chamadas += 1;
    return new Promise((resolve) => {
      resolveFetch = resolve;
    });
  };
  const { plugin } = criarInstancia({ climaFetch: fetchStub });
  plugin._iniciarClima(); // assina + dispara o voo

  plugin._atualizarClima(); // durante o voo: sem novo request
  resolveFetch(payloadClimaOk());
  await drenar();

  assert.equal(chamadas, 1, 'apenas um request durante o voo');
  assert.ok(plugin._climaUrls.radar, 'URLs aplicadas após o voo');

  plugin.destroy();
});

test('falha repetida avisa apenas uma vez e a recuperação rearma', async () => {
  let falhas = 2;
  const fetchStub = async () => {
    if (falhas-- > 0) {
      throw new Error('offline');
    }
    return payloadClimaOk();
  };
  const { plugin } = criarInstancia({ climaFetch: fetchStub });

  const avisos = [];
  const warnOriginal = console.warn;
  console.warn = (...args) => avisos.push(args);
  try {
    await plugin._atualizarClima(); // falha 1 → avisa
    assert.equal(avisos.length, 1, 'primeira falha avisa');

    await plugin._atualizarClima(); // falha 2 → silêncio
    assert.equal(avisos.length, 1, 'falhas seguintes não repetem o aviso');

    await plugin._atualizarClima(); // sucesso → recupera
    assert.ok(plugin._climaUrls.radar, 'recuperou após as falhas');
  } finally {
    console.warn = warnOriginal;
  }
});

test('formatarArea e formatarCentro degradam com dados inválidos', () => {
  assert.equal(formatarArea(12.345), '12.3 km²');
  assert.equal(formatarArea('abc'), 'N/A');
  assert.equal(formatarArea(undefined), 'N/A');
  assert.equal(formatarCentro([-22.9, -43.2]), '-22.9000, -43.2000');
  assert.equal(formatarCentro(['x', 'y']), null);
  assert.equal(formatarCentro([1]), null);
  assert.equal(formatarCentro(undefined), null);
});
