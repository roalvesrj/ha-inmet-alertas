"""Constantes para a integração INMET Alertas."""
from typing import Final

# Informações da integração
DOMAIN: Final = "inmet_alertas"
NAME: Final = "INMET Alertas"
VERSION: Final = "1.16.0"
MANUFACTURER: Final = "Instituto Nacional de Meteorologia"
MODEL: Final = "Sistema de Alertas Meteorológicos"

# Chaves de configuração (ConfigEntry.data/options)
CONF_ESTADO: Final = "estado"
CONF_NOTIFICACOES_PERIGO: Final = "notificacoes_perigo"
CONF_UPDATE_INTERVAL: Final = "update_interval"

# Atribuição exibida nas entidades
ATTRIBUTION: Final = "Dados fornecidos pelo INMET"

# URLs e endpoints
URL_RSS: Final = "https://apiprevmet3.inmet.gov.br/avisos/rss"
URL_BASE_ALERTA: Final = "https://apiprevmet3.inmet.gov.br/avisos/rss/"

# Configurações de rede
HTTP_TIMEOUT: Final = 30
HTTP_TIMEOUT_TEST: Final = 15  # segundos — teste de conectividade no config flow
MAX_RETRIES: Final = 3

# Headers centralizados para todas as requisições ao INMET.
# O User-Agent de navegador é intencional: o INMET responde 403 para UAs
# não-navegador (comportamento observado em produção — não alterar sem
# validar contra a API).
REQUEST_HEADERS: Final = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    ),
    "Accept": "application/rss+xml, application/xml, text/xml, */*",
    "Accept-Language": "pt-BR,pt;q=0.9,en;q=0.8",
    "Cache-Control": "no-cache",
    "Pragma": "no-cache",
}

# Configurações de atualização
DEFAULT_UPDATE_INTERVAL: Final = 45  # minutos (aumentado para evitar rate limiting)
MIN_UPDATE_INTERVAL: Final = 5       # minutos
MAX_UPDATE_INTERVAL: Final = 120     # minutos

# Mapeamento de severidades CAP para INMET
SEVERIDADE_CAP_MAP: Final = {
    "Minor": "Perigo Potencial",
    "Moderate": "Perigo",
    "Severe": "Perigo",
    "Extreme": "Grande Perigo"
}

# Cores/ícones por severidade
SEVERIDADE_CORES: Final = {
    "Perigo Potencial": "🟡",
    "Perigo": "🟠",
    "Grande Perigo": "🔴",
}

# Cores oficiais INMET para mapas (ColorRisk do CAP)
CORES_INMET_MAPA: Final = {
    "Perigo Potencial": "#FFFF00",  # Amarelo
    "Perigo": "#FF8C00",            # Laranja
    "Grande Perigo": "#F80703",     # Vermelho
}

# Mapeamento CAP ColorRisk para severidade
COLORISK_TO_SEVERIDADE: Final = {
    "#FFFF00": "Perigo Potencial",
    "#FF8C00": "Perigo",
    "#F80703": "Grande Perigo",
    "#FFA500": "Perigo",  # Laranja alternativo
    "#FFD700": "Perigo Potencial",  # Amarelo alternativo
}

# Configurações de mapas geográficos
MAPA_CONFIG: Final = {
    "zoom_padrao": 8,
    "opacidade_poligono": 0.6,
    "espessura_borda": 2,
    "cor_borda": "#000000",
}

# Centros geográficos dos estados (lat, lon)
CENTROS_ESTADOS: Final = {
    "AC": [-9.0238, -70.8120],
    "AL": [-9.5713, -36.7820],
    "AP": [1.4554, -51.9082],
    "AM": [-4.1431, -69.8597],
    "BA": [-12.5797, -41.7007],
    "CE": [-5.4984, -39.3206],
    "DF": [-15.7998, -47.8645],
    "ES": [-19.1834, -40.3089],
    "GO": [-15.827, -49.8362],
    "MA": [-4.9609, -45.2744],
    "MT": [-12.6819, -56.9211],
    "MS": [-20.7722, -54.7852],
    "MG": [-18.5122, -44.5550],
    "PA": [-3.9737, -52.9336],
    "PB": [-7.3349, -36.7820],
    "PR": [-24.8945, -51.4189],
    "PE": [-8.8137, -36.9541],
    "PI": [-6.6304, -42.4689],
    "RJ": [-22.3064, -42.6777],
    "RN": [-5.4026, -36.9541],
    "RS": [-30.0346, -51.2177],
    "RO": [-10.9472, -62.8429],
    "RR": [1.9981, -61.0023],
    "SC": [-27.2423, -50.2189],
    "SP": [-23.1793, -46.9194],
    "SE": [-10.5741, -37.3857],
    "TO": [-10.17528, -48.2982]
}

# Ícones por tipo de evento
EVENTO_ICONES: Final = {
    "Chuva": "🌧️",
    "Vendaval": "💨",
    "Tempestade": "⛈️",
    "Granizo": "🧊",
    "Neve": "❄️",
    "Geada": "🥶",
    "Onda de Calor": "🌡️",
    "Baixa Umidade": "🏜️",
    "default": "⚠️"
}

# Prioridades de severidade
SEVERIDADE_PRIORIDADES: Final = {
    "Grande Perigo": 3,
    "Perigo": 2,
    "Perigo Potencial": 1,
}

# Estados brasileiros
ESTADOS_BRASILEIROS: Final = {
    "AC": "Acre",
    "AL": "Alagoas",
    "AP": "Amapá",
    "AM": "Amazonas",
    "BA": "Bahia",
    "CE": "Ceará",
    "DF": "Distrito Federal",
    "ES": "Espírito Santo",
    "GO": "Goiás",
    "MA": "Maranhão",
    "MT": "Mato Grosso",
    "MS": "Mato Grosso do Sul",
    "MG": "Minas Gerais",
    "PA": "Pará",
    "PB": "Paraíba",
    "PR": "Paraná",
    "PE": "Pernambuco",
    "PI": "Piauí",
    "RJ": "Rio de Janeiro",
    "RN": "Rio Grande do Norte",
    "RS": "Rio Grande do Sul",
    "RO": "Rondônia",
    "RR": "Roraima",
    "SC": "Santa Catarina",
    "SP": "São Paulo",
    "SE": "Sergipe",
    "TO": "Tocantins"
}

# Eventos personalizados
EVENT_NOVO_ALERTA: Final = "inmet_novo_alerta"
EVENT_ALERTA_PERIGOSO: Final = "inmet_alerta_perigoso"
EVENT_ALERTA_EXPIRADO: Final = "inmet_alerta_expirado"

# Serviços
SERVICE_ATUALIZAR_ALERTAS: Final = "atualizar_alertas"

# Atributos do sensor
ATTR_TOTAL_ALERTAS: Final = "total_alertas"
ATTR_ALERTAS: Final = "alertas"
ATTR_ALERTAS_POR_SEVERIDADE: Final = "alertas_por_severidade"
ATTR_SEVERIDADE_MAXIMA: Final = "severidade_maxima"
ATTR_MUNICIPIOS_UNICOS: Final = "municipios_unicos"
ATTR_MUNICIPIOS_AFETADOS: Final = "municipios_afetados"
ATTR_ESTADO: Final = "estado"
ATTR_ULTIMA_ATUALIZACAO: Final = "ultima_atualizacao"

# Atributos específicos do sensor de mapa
ATTR_POLIGONOS: Final = "poligonos"
ATTR_AREA_TOTAL_AFETADA: Final = "area_total_afetada_km2"
ATTR_CENTRO_GEOGRAFICO: Final = "centro_geografico"
ATTR_CAMADAS_SOBREPOSTAS: Final = "camadas_sobrepostas"
ATTR_COORDENADAS_BBOX: Final = "bounding_box"
ATTR_ZOOM_RECOMENDADO: Final = "zoom_recomendado"

# Mapeamento de microrregiões INMET para estados
MICRORREGIOES_ESTADOS: Final = {
    # Acre
    "Vale do Acre": "AC",

    # Alagoas
    "Agreste Alagoano": "AL",
    "Sertão Alagoano": "AL",

    # Amazonas
    "Centro Amazonense": "AM",
    "Norte Amazonense": "AM",
    "Sudoeste Amazonense": "AM",
    "Sul Amazonense": "AM",

    # Amapá
    "Norte do Amapá": "AP",
    "Sul do Amapá": "AP",

    # Bahia
    "Centro Norte Baiano": "BA",
    "Centro Sul Baiano": "BA",
    "Extremo Oeste Baiano": "BA",
    "Nordeste Baiano": "BA",
    "Sul Baiano": "BA",
    "Vale São-Franciscano da Bahia": "BA",

    # Ceará
    "Centro-Sul Cearense": "CE",
    "Noroeste Cearense": "CE",
    "Norte Cearense": "CE",
    "Sertões Cearenses": "CE",
    "Sul Cearense": "CE",

    # Distrito Federal
    "Distrito Federal": "DF",

    # Espírito Santo
    "Central Espírito-santense": "ES",
    "Litoral Norte Espírito-santense": "ES",
    "Noroeste Espírito-santense": "ES",
    "Sul Espírito-santense": "ES",

    # Goiás
    "Centro Goiano": "GO",
    "Leste Goiano": "GO",
    "Noroeste Goiano": "GO",
    "Norte Goiano": "GO",
    "Sul Goiano": "GO",

    # Maranhão
    "Centro Maranhense": "MA",
    "Leste Maranhense": "MA",
    "Norte Maranhense": "MA",
    "Oeste Maranhense": "MA",
    "Sul Maranhense": "MA",

    # Minas Gerais
    "Central Mineira": "MG",
    "Campo das Vertentes": "MG",
    "Jequitinhonha": "MG",
    "Metropolitana de Belo Horizonte": "MG",
    "Noroeste de Minas": "MG",
    "Norte de Minas": "MG",
    "Oeste de Minas": "MG",
    "Sul/Sudoeste de Minas": "MG",
    "Triângulo Mineiro/Alto Paranaíba": "MG",
    "Vale do Mucuri": "MG",
    "Vale do Rio Doce": "MG",
    "Zona da Mata": "MG",

    # Mato Grosso do Sul
    "Centro Norte de Mato Grosso do Sul": "MS",
    "Leste de Mato Grosso do Sul": "MS",
    "Pantanais Sul Mato-grossense": "MS",
    "Sudoeste de Mato Grosso do Sul": "MS",

    # Mato Grosso
    "Centro-Sul Mato-grossense": "MT",
    "Nordeste Mato-grossense": "MT",
    "Norte Mato-grossense": "MT",
    "Sudeste Mato-grossense": "MT",
    "Sudoeste Mato-grossense": "MT",

    # Pará
    "Baixo Amazonas": "PA",
    "Marajó": "PA",
    "Metropolitana de Belém": "PA",
    "Nordeste Paraense": "PA",
    "Sudeste Paraense": "PA",
    "Sudoeste Paraense": "PA",

    # Paraíba
    "Agreste Paraibano": "PB",
    "Borborema": "PB",
    "Sertão Paraibano": "PB",

    # Pernambuco
    "Agreste Pernambucano": "PE",
    "São Francisco Pernambucano": "PE",
    "Sertão Pernambucano": "PE",

    # Piauí
    "Centro-Norte Piauiense": "PI",
    "Norte Piauiense": "PI",
    "Sudeste Piauiense": "PI",
    "Sudoeste Piauiense": "PI",

    # Paraná
    "Centro Ocidental Paranaense": "PR",
    "Centro Oriental Paranaense": "PR",
    "Centro-Sul Paranaense": "PR",
    "Metropolitana de Curitiba": "PR",
    "Noroeste Paranaense": "PR",
    "Norte Central Paranaense": "PR",
    "Norte Pioneiro Paranaense": "PR",
    "Oeste Paranaense": "PR",
    "Sudeste Paranaense": "PR",
    "Sudoeste Paranaense": "PR",

    # Rio de Janeiro
    "Baixadas": "RJ",
    "Centro Fluminense": "RJ",
    "Metropolitana do Rio de Janeiro": "RJ",
    "Noroeste Fluminense": "RJ",
    "Norte Fluminense": "RJ",
    "Sul Fluminense": "RJ",

    # Rio Grande do Norte
    "Agreste Potiguar": "RN",
    "Central Potiguar": "RN",
    "Oeste Potiguar": "RN",

    # Rondônia
    "Leste Rondoniense": "RO",
    "Madeira-Guaporé": "RO",

    # Roraima
    "Norte de Roraima": "RR",
    "Sul de Roraima": "RR",

    # Rio Grande do Sul
    "Centro Ocidental Rio-grandense": "RS",
    "Centro Oriental Rio-grandense": "RS",
    "Metropolitana de Porto Alegre": "RS",
    "Nordeste Rio-grandense": "RS",
    "Noroeste Rio-grandense": "RS",
    "Sudeste Rio-grandense": "RS",
    "Sudoeste Rio-grandense": "RS",

    # Santa Catarina
    "Grande Florianópolis": "SC",
    "Norte Catarinense": "SC",
    "Oeste Catarinense": "SC",
    "Serrana": "SC",
    "Sul Catarinense": "SC",
    "Vale do Itajaí": "SC",

    # Sergipe
    "Agreste Sergipano": "SE",
    "Sertão Sergipano": "SE",

    # São Paulo
    "Araraquara": "SP",
    "Araçatuba": "SP",
    "Assis": "SP",
    "Bauru": "SP",
    "Campinas": "SP",
    "Itapetininga": "SP",
    "Litoral Sul Paulista": "SP",
    "Macro Metropolitana Paulista": "SP",
    "Marília": "SP",
    "Metropolitana de São Paulo": "SP",
    "Piracicaba": "SP",
    "Presidente Prudente": "SP",
    "Ribeirão Preto": "SP",
    "São José do Rio Preto": "SP",
    "Vale do Paraíba Paulista": "SP",

    # Tocantins
    "Jaguaribe": "TO",
    "Ocidental do Tocantins": "TO",
    "Oriental do Tocantins": "TO",

    # Juruá (região que pode abranger múltiplos estados)
    "Vale do Juruá": "AC",  # Predominantemente Acre
}

# Configurações padrão
DEFAULT_NOTIFICACOES_PERIGO: Final = True
SEVERIDADES_NOTIFICACAO: Final = ["Perigo", "Grande Perigo"]

# Limites e validações
MAX_DESCRIPTION_LENGTH: Final = 200
MAX_MUNICIPIOS_EXIBIDOS: Final = 10
