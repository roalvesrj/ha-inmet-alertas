/**
 * Testes do card de alertas INMET (lógica pura; sem DOM).
 *
 * O visual permanece com verificação manual no Home Assistant.
 */
import assert from 'node:assert/strict';
import test from 'node:test';

globalThis.window = undefined;
globalThis.customElements = undefined;

const moduleUrl = new URL(
  '../../custom_components/inmet_alertas/www/inmet-alert-card.js',
  import.meta.url,
);
const {
  corDaSeveridade,
  entidadeDoEstado,
  filtrarAlertas,
  formatarDataHora,
  formatarRestante,
  iconeDoAlerta,
  normalizarConfig,
  normalizarSeveridade,
  normalizarSigla,
  paraTimestamp,
  progressoAlerta,
  resumirMunicipios,
} = await import(moduleUrl.href);

const ALERTAS = [
  { severidade: 'Grande Perigo', titulo: 'Chuvas extremas' },
  { severidade: 'Perigo', titulo: 'Vendaval' },
  { severidade: 'Perigo', titulo: 'Chuva intensa' },
  { severidade: 'Perigo Potencial', titulo: 'Neblina' },
];

test('normaliza sigla do estado', () => {
  assert.equal(normalizarSigla('rj'), 'RJ');
  assert.equal(normalizarSigla(' RJ '), 'RJ');
  assert.equal(normalizarSigla('rio_de_janeiro'), 'rio_de_janeiro');
  assert.equal(normalizarSigla(''), '');
  assert.equal(normalizarSigla(undefined), '');
});

test('monta o entity_id a partir do estado', () => {
  assert.equal(entidadeDoEstado('GO'), 'sensor.alertas_meteorologicos_go');
  assert.equal(entidadeDoEstado('sp'), 'sensor.alertas_meteorologicos_sp');
  assert.equal(entidadeDoEstado(''), '');
});

test('normaliza a severidade pedida', () => {
  assert.equal(normalizarSeveridade('Perigo'), 'Perigo');
  assert.equal(normalizarSeveridade('grande perigo'), 'Grande Perigo');
  assert.equal(normalizarSeveridade('todas'), 'todas');
  assert.equal(normalizarSeveridade('all'), 'todas');
  assert.equal(normalizarSeveridade(''), 'todas');
  assert.equal(normalizarSeveridade('invalida'), 'todas');
});

test('filtra alertas por severidade', () => {
  assert.equal(filtrarAlertas(ALERTAS, 'Perigo').length, 2);
  assert.equal(filtrarAlertas(ALERTAS, 'Grande Perigo').length, 1);
  assert.equal(filtrarAlertas(ALERTAS, 'todas').length, 4);
  assert.equal(filtrarAlertas(ALERTAS, 'perigo')[0].titulo, 'Vendaval');
  assert.deepEqual(filtrarAlertas(null, 'Perigo'), []);
});

test('cor e ícone por severidade', () => {
  assert.equal(corDaSeveridade('Grande Perigo'), '#F80703');
  assert.equal(corDaSeveridade('Perigo'), '#FF8C00');
  assert.equal(corDaSeveridade('Perigo Potencial'), '#FFFF00');
  assert.equal(corDaSeveridade('Outra'), '#808080');

  assert.equal(iconeDoAlerta({ icone: 'mdi:weather-pouring' }), 'mdi:weather-pouring');
  assert.equal(iconeDoAlerta({ icone: '🌧️' }), 'mdi:alert-outline');
  assert.equal(iconeDoAlerta({ severidade: 'Grande Perigo' }), 'mdi:alert-octagon');
  assert.equal(iconeDoAlerta({ severidade: 'Perigo' }), 'mdi:alert');
});

test('converte e formata datas ISO', () => {
  assert.equal(paraTimestamp(''), 0);
  assert.equal(paraTimestamp('lixo'), 0);
  assert.ok(paraTimestamp('2026-10-25T12:00:00-03:00') > 0);

  const formatado = formatarDataHora('2026-10-25T12:00:00-03:00');
  assert.match(formatado, /25\/10\/2026/);
  assert.equal(formatarDataHora(''), '');
});

test('formata o tempo restante', () => {
  const minuto = 60 * 1000;
  assert.equal(formatarRestante(90 * minuto), '1h 30m');
  assert.equal(formatarRestante(4 * 60 * minuto), '4h');
  assert.equal(formatarRestante(12 * minuto), '12m');
  assert.equal(formatarRestante(26 * 60 * minuto), '1d 2h');
  assert.equal(formatarRestante(0), 'expirado');
  assert.equal(formatarRestante(-1000), 'expirado');
});

test('calcula o progresso do alerta', () => {
  const inicio = '2026-10-25T10:00:00-03:00';
  const fim = '2026-10-25T14:00:00-03:00';
  const meio = Date.parse('2026-10-25T12:00:00-03:00');

  assert.equal(progressoAlerta(inicio, fim, meio), 0.5);
  assert.equal(progressoAlerta(inicio, fim, Date.parse(inicio) - 1000), 0);
  assert.equal(progressoAlerta(inicio, fim, Date.parse(fim) + 1000), 1);
  assert.equal(progressoAlerta('', fim, meio), null);
  assert.equal(progressoAlerta(inicio, inicio, meio), null);
});

test('resume municípios sem repetir', () => {
  const alertas = [
    { municipios_estado: ['Niterói - RJ', 'São Gonçalo - RJ'] },
    { municipios_estado: ['Niterói - RJ', 'Maricá - RJ'] },
  ];
  assert.equal(resumirMunicipios(alertas), 'Niterói - RJ, São Gonçalo - RJ, Maricá - RJ');
  assert.equal(resumirMunicipios(alertas, 1), 'Niterói - RJ e mais 2');
  assert.equal(resumirMunicipios([]), '');
});

test('normaliza a configuração do card', () => {
  const padrao = normalizarConfig({ estado: 'rj' });
  assert.equal(padrao.entidade, 'sensor.alertas_meteorologicos_rj');
  assert.equal(padrao.severidade, 'todas');
  assert.equal(padrao.maxAlertas, 5);
  assert.equal(padrao.mostrarDetalhes, true);
  assert.equal(padrao.mostrarProgresso, true);
  assert.equal(padrao.mostrarVazio, false);

  const custom = normalizarConfig({
    entidade: 'sensor.custom',
    severidade: 'Grande Perigo',
    maxAlertas: 2,
    mostrarVazio: true,
    titulo: 'Grande Perigo',
  });
  assert.equal(custom.entidade, 'sensor.custom');
  assert.equal(custom.severidade, 'Grande Perigo');
  assert.equal(custom.maxAlertas, 2);
  assert.equal(custom.mostrarVazio, true);
  assert.equal(custom.titulo, 'Grande Perigo');

  assert.throws(() => normalizarConfig({}), /informe "estado"/);
});
