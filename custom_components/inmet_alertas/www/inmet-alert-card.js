/**
 * Card de alertas do INMET por severidade.
 *
 * Design inspirado no projeto `seevee/weather_alerts_card` (MIT):
 * https://github.com/seevee/weather_alerts_card
 * Adaptado para os sensores da integração `inmet_alertas` (atributo `alertas`),
 * sem dependências externas e sem etapa de build.
 *
 * Uso (Lovelace → Recursos → adicionar `/inmet_alertas/inmet-alert-card.js`):
 *
 *   type: custom:inmet-alert-card
 *   estado: RJ                # sigla do estado configurado na integração
 *   severidade: Perigo        # Perigo | Grande Perigo | Perigo Potencial | todas
 *   titulo: Alertas de Perigo
 */

export const SEVERIDADES = ['Grande Perigo', 'Perigo', 'Perigo Potencial'];

export const CORES_SEVERIDADE = {
  'Grande Perigo': '#F80703',
  'Perigo': '#FF8C00',
  'Perigo Potencial': '#FFFF00',
};

const ICONES_PADRAO = {
  'Grande Perigo': 'mdi:alert-octagon',
  'Perigo': 'mdi:alert',
  'Perigo Potencial': 'mdi:alert-outline',
};

const MINUTO_MS = 60 * 1000;

/** Normaliza a sigla do estado (ex.: "SP", "sp", "São Paulo" → "SP"/"sp"). */
export function normalizarSigla(valor) {
  const texto = String(valor ?? '').trim();
  if (!texto) {
    return '';
  }
  // Sigla com 2 letras é o formato canônico da integração.
  return texto.length === 2 ? texto.toUpperCase() : texto.toLowerCase();
}

/** Entity ID do sensor principal para a sigla/estado informado. */
export function entidadeDoEstado(estado) {
  const sigla = normalizarSigla(estado);
  return sigla ? `sensor.alertas_meteorologicos_${sigla.toLowerCase()}` : '';
}

/** Normaliza a severidade pedida no card ('todas' quando ausente/inválida). */
export function normalizarSeveridade(valor) {
  const texto = String(valor ?? '').trim();
  if (!texto || texto.toLowerCase() === 'todas' || texto.toLowerCase() === 'all') {
    return 'todas';
  }
  const encontrada = SEVERIDADES.find(
    (severidade) => severidade.toLowerCase() === texto.toLowerCase(),
  );
  return encontrada || 'todas';
}

/** Filtra os alertas pela severidade configurada (case-insensitive). */
export function filtrarAlertas(alertas, severidade) {
  const lista = Array.isArray(alertas) ? alertas : [];
  const alvo = normalizarSeveridade(severidade);
  if (alvo === 'todas') {
    return lista;
  }
  return lista.filter(
    (alerta) =>
      String(alerta?.severidade ?? '').toLowerCase() === alvo.toLowerCase(),
  );
}

/** Cor oficial da severidade (fallback cinza). */
export function corDaSeveridade(severidade) {
  const encontrada = SEVERIDADES.find(
    (valor) => valor.toLowerCase() === String(severidade ?? '').toLowerCase(),
  );
  return CORES_SEVERIDADE[encontrada] || '#808080';
}

/** Ícone do alerta: usa o do feed quando for mdi:, senão um padrão por severidade. */
export function iconeDoAlerta(alerta) {
  const icone = String(alerta?.icone ?? '').trim();
  if (icone.startsWith('mdi:')) {
    return icone;
  }
  return ICONES_PADRAO[alerta?.severidade] || 'mdi:alert-outline';
}

/** Converte um timestamp ISO em ms (0 quando inválido/ausente). */
export function paraTimestamp(iso) {
  const texto = String(iso ?? '').trim();
  if (!texto) {
    return 0;
  }
  const ms = Date.parse(texto);
  return Number.isFinite(ms) ? ms : 0;
}

/** Formata um timestamp ISO em "dd/mm/aaaa HH:MM" (fuso local). */
export function formatarDataHora(iso, locale = 'pt-BR') {
  const ms = paraTimestamp(iso);
  if (!ms) {
    return '';
  }
  return new Intl.DateTimeFormat(locale, {
    day: '2-digit',
    month: '2-digit',
    year: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
  }).format(new Date(ms));
}

/** Formata a duração restante de forma curta: "2d 3h", "1h 30m", "12m". */
export function formatarRestante(ms) {
  if (!Number.isFinite(ms) || ms <= 0) {
    return 'expirado';
  }
  const totalMinutos = Math.floor(ms / MINUTO_MS);
  const dias = Math.floor(totalMinutos / (60 * 24));
  const horas = Math.floor((totalMinutos % (60 * 24)) / 60);
  const minutos = totalMinutos % 60;

  if (dias > 0) {
    return horas > 0 ? `${dias}d ${horas}h` : `${dias}d`;
  }
  if (horas > 0) {
    return minutos > 0 ? `${horas}h ${minutos}m` : `${horas}h`;
  }
  return `${minutos}m`;
}

/** Fração decorrida do alerta (0–1); null quando não há período válido. */
export function progressoAlerta(onsetIso, expiresIso, agora = Date.now()) {
  const inicio = paraTimestamp(onsetIso);
  const fim = paraTimestamp(expiresIso);
  if (!inicio || !fim || fim <= inicio) {
    return null;
  }
  if (agora <= inicio) {
    return 0;
  }
  if (agora >= fim) {
    return 1;
  }
  return (agora - inicio) / (fim - inicio);
}

/** Texto curto dos municípios (primeiros N + "e mais X"). */
export function resumirMunicipios(alertas, limite = 3) {
  const vistos = new Set();
  for (const alerta of Array.isArray(alertas) ? alertas : []) {
    for (const municipio of alerta?.municipios_estado || []) {
      const nome = String(municipio ?? '').trim();
      if (nome) {
        vistos.add(nome);
      }
    }
  }
  const lista = [...vistos];
  if (lista.length <= limite) {
    return lista.join(', ');
  }
  return `${lista.slice(0, limite).join(', ')} e mais ${lista.length - limite}`;
}

/** Resumo da descrição, cortado em palavra inteira e com reticências. */
export function resumirDescricao(texto, limite = 220) {
  const limpo = String(texto ?? '')
    .replace(/\s+/g, ' ')
    .trim();
  if (limpo.length <= limite) {
    return limpo;
  }
  const corte = limpo.lastIndexOf(' ', limite);
  const base = corte > limite * 0.6 ? limpo.slice(0, corte) : limpo.slice(0, limite);
  return `${base.trimEnd()}…`;
}

/** Fatia a lista de alertas em uma página (com limites normalizados). */
export function paginarAlertas(alertas, pagina = 0, porPagina = 1) {
  const lista = Array.isArray(alertas) ? alertas : [];
  const tamanho = Math.max(1, Math.floor(Number(porPagina) || 1));
  const totalPaginas = Math.max(1, Math.ceil(lista.length / tamanho));
  const indicePedido = Math.floor(Number(pagina) || 0);
  const atual = Math.min(Math.max(0, indicePedido), totalPaginas - 1);
  return {
    itens: lista.slice(atual * tamanho, atual * tamanho + tamanho),
    pagina: atual,
    totalPaginas,
    total: lista.length,
  };
}

/** Aplica padrões e valida a configuração do card. */
export function normalizarConfig(config = {}) {
  const entidade =
    String(config.entidade ?? '').trim() ||
    entidadeDoEstado(config.estado);
  if (!entidade) {
    throw new Error(
      'inmet-alert-card: informe "estado" (sigla, ex.: RJ) ou "entidade".',
    );
  }
  const maxAlertas = Number(config.maxAlertas);
  const itensPorPagina = Number(config.itensPorPagina);
  return {
    entidade,
    severidade: normalizarSeveridade(config.severidade),
    titulo: String(config.titulo ?? '').trim(),
    maxAlertas: Number.isFinite(maxAlertas) && maxAlertas > 0 ? maxAlertas : 5,
    paginacao: config.paginacao === true,
    itensPorPagina:
      Number.isFinite(itensPorPagina) && itensPorPagina > 0
        ? Math.floor(itensPorPagina)
        : 1,
    mostrarVazio: config.mostrarVazio === true,
    mostrarMunicipios: config.mostrarMunicipios !== false,
    mostrarDetalhes: config.mostrarDetalhes !== false,
    mostrarProgresso: config.mostrarProgresso !== false,
  };
}

const ESTILOS = `
  :host { display: block; }
  ha-card {
    padding: 0;
    overflow: hidden;
    border: 1px solid var(--divider-color, rgba(0,0,0,.12));
    border-left: 4px solid var(--inmet-cor, #808080);
  }
  .inmet-alerta {
    padding: 14px 16px 12px;
    border-bottom: 1px solid var(--divider-color, rgba(0,0,0,.12));
  }
  .inmet-alerta:last-of-type { border-bottom: 0; }
  .cabecalho { display: flex; gap: 12px; align-items: flex-start; }
  .icone {
    flex: 0 0 auto;
    display: grid;
    place-items: center;
    width: 44px;
    height: 44px;
    border-radius: 50%;
    border: 1px solid var(--inmet-cor, #808080);
    background: color-mix(in srgb, var(--inmet-cor, #808080) 12%, transparent);
    color: var(--inmet-cor, #808080);
  }
  .titulo {
    margin: 0;
    font-size: 17px;
    font-weight: 600;
    line-height: 1.3;
    color: var(--primary-text-color, #212121);
  }
  .descricao-curta {
    margin: 4px 0 0;
    font-size: 14px;
    line-height: 1.4;
    color: var(--secondary-text-color, #727272);
    display: -webkit-box;
    -webkit-line-clamp: 3;
    -webkit-box-orient: vertical;
    overflow: hidden;
  }
  .local {
    display: flex;
    gap: 4px;
    align-items: flex-start;
    margin: 6px 0 0;
    font-size: 13px;
    color: var(--secondary-text-color, #727272);
  }
  .local ha-icon { --mdc-icon-size: 16px; flex: 0 0 auto; }
  .chips { display: flex; flex-wrap: wrap; gap: 6px; margin: 10px 0 0; }
  .chip {
    display: inline-flex;
    align-items: center;
    gap: 4px;
    padding: 2px 8px;
    border-radius: 999px;
    font-size: 11px;
    font-weight: 700;
    letter-spacing: .06em;
    text-transform: uppercase;
  }
  .chip-severidade {
    border: 1px solid var(--inmet-cor, #808080);
    color: var(--inmet-cor, #808080);
    background: color-mix(in srgb, var(--inmet-cor, #808080) 14%, transparent);
  }
  .chip-evento {
    border: 1px solid var(--divider-color, rgba(0,0,0,.2));
    color: var(--secondary-text-color, #727272);
  }
  .tempos {
    display: grid;
    grid-template-columns: 1fr auto 1fr;
    gap: 8px;
    margin: 12px 0 0;
    font-size: 12px;
  }
  .tempos .rotulo {
    display: block;
    font-size: 10px;
    font-weight: 700;
    letter-spacing: .08em;
    text-transform: uppercase;
    color: var(--secondary-text-color, #727272);
  }
  .tempos .valor {
    display: block;
    margin-top: 2px;
    font-size: 13px;
    color: var(--primary-text-color, #212121);
    white-space: nowrap;
  }
  .tempos .centro { text-align: center; }
  .tempos .direita { text-align: right; }
  .restante { color: var(--inmet-cor, #808080); font-weight: 700; }
  .barra {
    height: 3px;
    margin-top: 8px;
    border-radius: 2px;
    background: var(--divider-color, rgba(0,0,0,.12));
    overflow: hidden;
  }
  .barra > span {
    display: block;
    height: 100%;
    background: var(--inmet-cor, #808080);
  }
  details {
    margin-top: 12px;
    border-top: 1px solid var(--divider-color, rgba(0,0,0,.12));
    padding-top: 8px;
  }
  summary {
    cursor: pointer;
    font-size: 14px;
    color: var(--primary-text-color, #212121);
    list-style: none;
  }
  summary::-webkit-details-marker { display: none; }
  summary::after { content: " ▾"; color: var(--secondary-text-color, #727272); }
  details[open] summary::after { content: " ▴"; }
  .detalhes { font-size: 13px; line-height: 1.5; color: var(--secondary-text-color, #727272); }
  .detalhes p { margin: 8px 0 0; white-space: pre-line; }
  .detalhes .rotulo { font-weight: 700; color: var(--primary-text-color, #212121); }
  .detalhes a { color: var(--primary-color, #03a9f4); }
  .vazio {
    padding: 16px;
    font-size: 14px;
    color: var(--secondary-text-color, #727272);
  }
  .titulo-card {
    padding: 14px 16px 6px;
    font-size: 12px;
    font-weight: 700;
    letter-spacing: .06em;
    text-transform: uppercase;
    color: var(--secondary-text-color, #727272);
  }
  .aviso {
    border-left-color: var(--warning-color, #ff9800);
  }
  .aviso .inmet-alerta { color: var(--secondary-text-color, #727272); }
  .paginacao {
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 8px;
    padding: 6px 10px;
    border-top: 1px solid var(--divider-color, rgba(0,0,0,.12));
    font-size: 12px;
    color: var(--secondary-text-color, #727272);
  }
  .paginacao button {
    display: grid;
    place-items: center;
    width: 32px;
    height: 28px;
    padding: 0;
    border: 0;
    border-radius: 6px;
    cursor: pointer;
    background: transparent;
    color: var(--primary-text-color, #212121);
  }
  .paginacao button:hover {
    background: var(--secondary-background-color, rgba(0,0,0,.06));
  }
  .paginacao ha-icon { --mdc-icon-size: 20px; }
`;

const Base = typeof HTMLElement === 'undefined' ? class {} : HTMLElement;

export class InmetAlertCard extends Base {
  constructor() {
    super();
    this._config = null;
    this._hass = null;
    this._intervalId = null;
    this._pagina = 0;
    this._totalPaginas = 1;
    this._root = this.attachShadow
      ? this.attachShadow({ mode: 'open' })
      : null;
    // Delegação: o innerHTML é recriado a cada render.
    this._root?.addEventListener('click', (evento) => this._aoClicar(evento));
  }

  static getStubConfig() {
    return { estado: 'RJ', severidade: 'Perigo', paginacao: true };
  }

  setConfig(config) {
    this._config = normalizarConfig(config);
    this._pagina = 0;
    this._render();
  }

  _aoClicar(evento) {
    const botao = evento.target?.closest?.('[data-pagina]');
    if (!botao) {
      return;
    }
    const delta = botao.dataset.pagina === 'proxima' ? 1 : -1;
    const total = Math.max(1, this._totalPaginas);
    this._pagina = (this._pagina + delta + total) % total;
    this._render();
  }

  set hass(hass) {
    this._hass = hass;
    // Evita re-render a cada atualização global do hass: só quando o sensor muda.
    const estado = hass?.states?.[this._config?.entidade];
    const assinatura = estado
      ? `${estado.state}|${estado.last_updated}|${JSON.stringify(estado.attributes?.alertas ?? [])}`
      : 'ausente';
    if (assinatura === this._assinatura) {
      return;
    }
    this._assinatura = assinatura;
    this._render();
  }

  connectedCallback() {
    if (this._intervalId) {
      return;
    }
    // Atualiza o "expira em" e a barra de progresso uma vez por minuto.
    this._intervalId = setInterval(() => this._render(), MINUTO_MS);
  }

  disconnectedCallback() {
    if (this._intervalId) {
      clearInterval(this._intervalId);
      this._intervalId = null;
    }
  }

  getCardSize() {
    return 3 + (this._alertas() || []).length * 3;
  }

  _alertas() {
    if (!this._config || !this._hass) {
      return [];
    }
    const estado = this._hass.states?.[this._config.entidade];
    const lista = estado?.attributes?.alertas;
    return filtrarAlertas(lista, this._config.severidade);
  }

  _render() {
    if (!this._root || !this._config) {
      return;
    }
    const { entidade } = this._config;
    const estado = this._hass?.states?.[entidade];

    if (!estado) {
      this._root.innerHTML = this._moldura(
        `<div class="vazio">Entidade <code>${entidade}</code> não encontrada. Confira o estado configurado na integração.</div>`,
        { aviso: true },
      );
      return;
    }

    if (estado.state === 'unavailable' || estado.state === 'unknown') {
      this._root.innerHTML = this._moldura(
        '<div class="vazio">Dados do INMET indisponíveis no momento.</div>',
        { aviso: true },
      );
      return;
    }

    const alertas = this._alertas().slice(0, this._config.maxAlertas);
    if (!alertas.length) {
      this._root.innerHTML = this._config.mostrarVazio
        ? this._moldura(
            '<div class="vazio">Nenhum alerta ativo para esta severidade.</div>',
          )
        : '';
      return;
    }

    const agora = Date.now();
    const titulo = this._config.titulo
      ? `<div class="titulo-card">${this._escapar(this._config.titulo)}</div>`
      : '';

    if (!this._config.paginacao) {
      this._totalPaginas = 1;
      const blocos = alertas.map((alerta) => this._renderAlerta(alerta, agora));
      this._root.innerHTML = this._moldura(titulo + blocos.join(''));
      return;
    }

    const pagina = paginarAlertas(
      alertas,
      this._pagina,
      this._config.itensPorPagina,
    );
    this._pagina = pagina.pagina;
    this._totalPaginas = pagina.totalPaginas;

    const blocos = pagina.itens.map((alerta) => this._renderAlerta(alerta, agora));
    const navegacao =
      pagina.totalPaginas > 1
        ? `<div class="paginacao">
             <button type="button" data-pagina="anterior" aria-label="Alerta anterior">
               <ha-icon icon="mdi:chevron-left"></ha-icon>
             </button>
             <span>${pagina.pagina + 1} de ${pagina.totalPaginas}</span>
             <button type="button" data-pagina="proxima" aria-label="Próximo alerta">
               <ha-icon icon="mdi:chevron-right"></ha-icon>
             </button>
           </div>`
        : '';

    this._root.innerHTML = this._moldura(titulo + blocos.join('') + navegacao);
  }

  _moldura(conteudo, { aviso = false } = {}) {
    return `<style>${ESTILOS}</style><ha-card class="${aviso ? 'aviso' : ''}">${conteudo}</ha-card>`;
  }

  _renderAlerta(alerta, agora) {
    const severidade = String(alerta?.severidade ?? '');
    const cor = corDaSeveridade(severidade);
    const icone = iconeDoAlerta(alerta);
    const titulo = this._escapar(alerta?.titulo || alerta?.evento || 'Alerta INMET');
    const evento = this._escapar(alerta?.evento || '');
    const descricao = this._escapar(alerta?.descricao || '');
    const curta = this._escapar(
      resumirDescricao(alerta?.descricao || '', 220),
    );
    const local = this._local(alerta);
    const inicio = formatarDataHora(alerta?.onset) || alerta?.inicio || '';
    const fim = formatarDataHora(alerta?.expires) || alerta?.fim || '';
    const restanteMs = paraTimestamp(alerta?.expires) - agora;
    const restante = alerta?.expires
      ? formatarRestante(restanteMs)
      : (alerta?.fim || '');
    const progresso = this._config.mostrarProgresso
      ? progressoAlerta(alerta?.onset, alerta?.expires, agora)
      : null;

    const barra =
      progresso === null
        ? ''
        : `<div class="barra" role="progressbar" aria-valuemin="0" aria-valuemax="100"
             aria-valuenow="${Math.round(progresso * 100)}">
             <span style="width:${(progresso * 100).toFixed(1)}%"></span>
           </div>`;

    const detalhes = this._config.mostrarDetalhes
      ? this._detalhes(alerta, descricao)
      : '';

    return `
      <div class="inmet-alerta" style="--inmet-cor:${cor}">
        <div class="cabecalho">
          <div class="icone"><ha-icon icon="${this._escapar(icone)}"></ha-icon></div>
          <div style="min-width:0">
            <h3 class="titulo">${titulo}</h3>
            ${curta ? `<p class="descricao-curta">${curta}</p>` : ''}
            ${local}
          </div>
        </div>
        <div class="chips">
          <span class="chip chip-severidade">${this._escapar(severidade || 'Alerta')}</span>
          ${evento ? `<span class="chip chip-evento">${evento}</span>` : ''}
        </div>
        <div class="tempos">
          <div>
            <span class="rotulo">Início</span>
            <span class="valor">${this._escapar(inicio || '—')}</span>
          </div>
          <div class="centro">
            <span class="rotulo">Expira em</span>
            <span class="valor restante">${this._escapar(restante || '—')}</span>
          </div>
          <div class="direita">
            <span class="rotulo">Fim</span>
            <span class="valor">${this._escapar(fim || '—')}</span>
          </div>
        </div>
        ${barra}
        ${detalhes}
      </div>`;
  }

  _local(alerta) {
    if (!this._config.mostrarMunicipios) {
      return '';
    }
    const municipios = resumirMunicipios([alerta]);
    const area = String(alerta?.area_desc ?? '').trim();
    const texto = municipios || area;
    if (!texto) {
      return '';
    }
    return `<p class="local"><ha-icon icon="mdi:map-marker"></ha-icon><span>${this._escapar(texto)}</span></p>`;
  }

  _detalhes(alerta, descricao) {
    const instrucoes = this._escapar(alerta?.instrucoes || '');
    const municipios = resumirMunicipios([alerta], 8);
    const link = String(alerta?.link ?? '').trim();
    const linkSeguro = /^https?:\/\//i.test(link)
      ? `<p class="rotulo">Fonte: <a href="${this._escapar(link)}" target="_blank" rel="noopener noreferrer">abrir alerta no INMET</a></p>`
      : '';

    return `
      <details>
        <summary>Ler detalhes</summary>
        <div class="detalhes">
          ${descricao ? `<p><span class="rotulo">Descrição:</span> ${descricao}</p>` : ''}
          ${instrucoes ? `<p><span class="rotulo">Instruções:</span> ${instrucoes}</p>` : ''}
          ${municipios ? `<p><span class="rotulo">Municípios:</span> ${this._escapar(municipios)}</p>` : ''}
          ${linkSeguro}
        </div>
      </details>`;
  }

  _escapar(valor) {
    return String(valor ?? '')
      .replaceAll('&', '&amp;')
      .replaceAll('<', '&lt;')
      .replaceAll('>', '&gt;')
      .replaceAll('"', '&quot;')
      .replaceAll("'", '&#39;');
  }
}

if (typeof customElements !== 'undefined' && !customElements.get('inmet-alert-card')) {
  customElements.define('inmet-alert-card', InmetAlertCard);
}

if (typeof window !== 'undefined') {
  window.customCards = window.customCards || [];
  if (!window.customCards.some((card) => card.type === 'inmet-alert-card')) {
    window.customCards.push({
      type: 'inmet-alert-card',
      name: 'INMET Alert Card',
      description:
        'Alertas do INMET por severidade, com progresso e detalhes (Perigo, Grande Perigo).',
      preview: true,
    });
  }
}
