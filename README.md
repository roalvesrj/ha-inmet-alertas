# INMET Alertas - Integração Home Assistant

<img src="custom_components/inmet_alertas/brand/logo.png" alt="INMET" width="320"/>

[![GitHub release](https://img.shields.io/github/release/roalvesrj/ha-inmet-alertas.svg)](https://github.com/roalvesrj/ha-inmet-alertas/releases)
[![GitHub issues](https://img.shields.io/github/issues/roalvesrj/ha-inmet-alertas.svg)](https://github.com/roalvesrj/ha-inmet-alertas/issues)
[![License](https://img.shields.io/github/license/roalvesrj/ha-inmet-alertas.svg)](LICENSE)
[![HACS](https://img.shields.io/badge/HACS-Custom-orange.svg)](https://github.com/custom-components/hacs)

Uma integração profissional para Home Assistant que monitora alertas meteorológicos do Instituto Nacional de Meteorologia (INMET) do Brasil.

## 🌦️ Funcionalidades

- **Monitoramento em tempo real** de alertas meteorológicos do INMET
- **Filtragem por estado brasileiro** - configure para receber apenas alertas do seu estado
- **Notificações automáticas** para alertas de alta severidade (Perigo e Grande Perigo)
- **Limpeza automática** de notificações quando alertas expiram
- **Suporte a múltiplos estados** - configure diferentes estados simultaneamente
- **Múltiplos sensores**:
  - Sensor principal com detalhes dos alertas ativos
  - Sensor de contagem de alertas
  - Sensor de mapa geográfico com polígonos e áreas afetadas
  - Sensor de diagnóstico com status HTTP, rate limits e erros
- **Processamento geográfico** - áreas em km², centro geográfico, zoom inteligente
- **Plugin Leaflet/Mapa** para visualização de polígonos reais no mapa
- **Eventos personalizados** para automações avançadas
- **Interface totalmente em português brasileiro**

## 🏗️ Arquitetura Profissional

A integração foi desenvolvida seguindo as melhores práticas de desenvolvimento:

### 📁 Estrutura Modular
```
inmet_alertas/
├── 📄 __init__.py        # Setup/unload, serviço de atualização e migração
├── 📄 coordinator.py     # Busca RSS/CAP, rate limiting e persistência de alertas
├── 📄 entity.py          # Classe base das entidades (nome + atribuição)
├── 📄 sensor.py          # Os 4 sensores (principal, contagem, mapa, diagnóstico)
├── 📄 config_flow.py     # Config flow v2 (data = estado; options = ajustes)
├── 📄 const.py           # Constantes centralizadas
├── 📁 helpers/           # Lógica pura e testável
│   ├── 📄 geo_processor.py   # Polígonos, áreas e zoom
│   ├── 📄 sensor_data.py     # Atributos e resumos dos sensores
│   └── 📄 persistence.py     # Merge/expiração de alertas persistentes
├── 📁 docs/              # Documentação detalhada
├── 📁 translations/      # Suporte multilíngue (PT/EN)
├── 📁 brand/             # Ícone da integração
└── 📁 www/               # Plugin Leaflet para ha-map-card
tests/                    # Testes: unit (lógica pura) e integration (harness do HA)
```

### 🔧 Componentes Especializados
- **INMETDataUpdateCoordinator**: busca o RSS/CAP, trata rate limiting com fila de retry e dispara eventos/notificações
- **Entidades finas**: `entity.py` define a base; `sensor.py` apenas monta o estado
- **Helpers puros**: `geo_processor`, `sensor_data` e `persistence` concentram a lógica testável sem o HA
- **Constantes Centralizadas**: configurações organizadas em `const.py`

### 📋 Padrões de Qualidade
- **Código documentado** com docstrings em português
- **Tratamento robusto de erros** em todas as operações
- **Logs estruturados** para facilitar troubleshooting
- **Testes automatizados**: `tests/unit` (lógica pura) e `tests/integration` (harness do HA, com 100% de cobertura do config flow)
- **Integration Quality Scale**: tier Bronze declarado em `quality_scale.yaml`

## 📦 Instalação

### 🚀 Instalação Rápida via HACS

[![Abrir no Home Assistant](https://my.home-assistant.io/badges/hacs_repository.svg)](https://my.home-assistant.io/redirect/hacs_repository/?category=integration&repository=roalvesrj%2Fha-inmet-alertas)

**OU**

1. Abra o **HACS** → **Integrações** → **Menu ⋮** → **Repositórios Personalizados**
2. Adicione: `https://github.com/roalvesrj/ha-inmet-alertas`
3. Procure por **"INMET Alertas"** e instale
4. **Reinicie o Home Assistant**

### 📖 Documentação Completa

Para instruções detalhadas, consulte:
- 📥 **[Guia de Instalação](custom_components/inmet_alertas/docs/INSTALACAO.md)** - Instruções passo-a-passo
- ⚙️ **[Guia de Configuração](custom_components/inmet_alertas/docs/CONFIGURACAO.md)** - Configuração completa
- 🎨 **[Exemplos de Automações](custom_components/inmet_alertas/examples/automations.md)** - Exemplos de automações
- 🔧 **[Solução de Problemas](custom_components/inmet_alertas/docs/CONFIGURACAO.md#🆘-resolução-de-problemas)** - Resolução de issues

### 🗑️ Remover a integração

1. **Remover cada estado**: **Configurações** → **Dispositivos e Serviços** → **INMET Alertas** → menu **⋮** → **Excluir** (repita para cada estado configurado)
2. **Se instalado via HACS**: **HACS** → **Integrações** → **INMET Alertas** → menu **⋮** → **Remover**
3. **Se instalado manualmente**: apague a pasta `custom_components/inmet_alertas` do diretório de configuração
4. **Reinicie o Home Assistant**

As notificações persistentes criadas pela integração podem ser dispensadas na sineta de notificações do HA.

## ⚙️ Configuração

1. Vá para **Configurações** → **Dispositivos e Serviços**
2. Clique em **Adicionar Integração**
3. Procure por "INMET Alertas"
4. Selecione o seu estado brasileiro
5. Configure as opções:
   - **Notificações de Perigo**: Ativa notificações automáticas para alertas Perigo e Grande Perigo
   - **Intervalo de Atualização**: Tempo entre verificações (5-120 minutos)

### 🌎 Configurando Múltiplos Estados

Você pode configurar a integração para monitorar diferentes estados simultaneamente:

1. **Primeira configuração**: Configure normalmente para o primeiro estado (ex: GO)
2. **Estados adicionais**: Repita o processo de configuração para cada estado desejado
3. **Notificações independentes**: Cada estado terá suas próprias notificações e sensores
4. **IDs únicos**: As notificações incluem o código do estado para evitar conflitos

**Exemplo de configuração múltipla:**
- `sensor.alertas_meteorologicos_go` (Goiás)
- `sensor.alertas_meteorologicos_rj` (Rio de Janeiro)
- `sensor.alertas_meteorologicos_sp` (São Paulo)

**Notificações por estado:**
- `inmet_alert_GO_12345` (Alerta para Goiás)
- `inmet_alert_RJ_12345` (Mesmo alerta, mas para Rio de Janeiro)

## 📊 Sensores Criados

### `sensor.alertas_meteorologicos_[ESTADO]`
- **Estado**: Nome do alerta ativo ou "Nenhum alerta ativo"
- **Atributos**:
  - `total_alertas`: Número total de alertas ativos
  - `alertas`: Lista detalhada de todos os alertas
  - `alertas_por_severidade`: Contagem por nível de severidade
  - `estado`: Estado configurado
  - `ultima_atualizacao`: Timestamp da última atualização

### `sensor.quantidade_de_alertas_[ESTADO]`
- **Estado**: Número de alertas ativos
- **Unidade**: alertas

### `sensor.inmet_alertas_mapa_[ESTADO]`
- **Estado**: Número de polígonos geográficos ativos
- **Unidade**: polígonos
- **Atributos**:
  - `area_total_afetada_km2`: Área total coberta pelos alertas em km²
  - `centro_geografico`: Coordenadas do centro das áreas afetadas
  - `zoom_recomendado`: Nível de zoom ideal para visualização no mapa
  - `camadas_por_severidade`: Polígonos organizados por severidade com cores oficiais
  - `total_alertas_com_geo`: Quantos alertas possuem dados geográficos
  - `poligonos`: Lista detalhada de todos os polígonos

### `sensor.inmet_alertas_diagnostico_[ESTADO]`
- **Estado**: Status do último ciclo (`ok`, `rate_limit`, `erro`, `desconhecido`)
- **Atributos**:
  - `ultimo_http_status`: Código HTTP da última requisição ao INMET
  - `rate_limit_hits`: Quantas vezes o rate limiting foi acionado
  - `pending_caps`: CAPs aguardando retry na fila
  - `ultimo_erro`: Mensagem do último erro (se houver)
  - `total_alertas_api`: Total de alertas retornados pela API no último ciclo
  - `ciclo_atual`: Timestamp ISO do início do último ciclo de atualização
  - `ultimo_ciclo_com_erro`: Se o último ciclo terminou com erro
  - `ultimo_ciclo_rate_limited`: Se o último ciclo sofreu rate limiting

## 🔔 Notificações

A integração cria automaticamente notificações persistentes para alertas de alta severidade:

- **🟠 Alertas Perigo**: Notificação com detalhes do alerta
- **🔴 Alertas Grande Perigo**: Notificação com detalhes do alerta

## 🎯 Eventos

### `inmet_novo_alerta`
Disparado quando um novo alerta é detectado.

**Dados do evento**:
```yaml
alert_id: "CAP-BR-INMET-000001"
titulo: "Chuvas Intensas"
severidade: "Perigo Potencial"
evento: "Chuva"
estado: "SP"
inicio: "21/09/2025 10:00"
fim: "21/09/2025 18:00"
```

### `inmet_alerta_perigoso`
Disparado especificamente para alertas de severidade **Perigo** ou **Grande Perigo**. Contém os mesmos dados do `inmet_novo_alerta`.

### `inmet_alerta_expirado`
Disparado quando um alerta existente é removido por expiração.

## 🤖 Automações

A integração dispara eventos que podem ser usados em automações do Home Assistant. Existem duas formas de criar automações:

### 📝 **Diferença entre os Formatos:**

1. **configuration.yaml**: Para quem prefere editar arquivos YAML
   - Adicione no arquivo `configuration.yaml`
   - Reinicie o Home Assistant após mudanças
   - Formato com `automation:` no início

2. **Interface do Home Assistant**: Mais visual e fácil
   - Vá em Configurações → Automações → Criar Automação
   - Cole o código YAML no editor
   - Salve diretamente pela interface

### Exemplo de Automação

**Para configuration.yaml:**
```yaml
automation:
  - alias: "Notificar Alerta INMET"
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
            Estado: {{ trigger.event.data.estado }}
            Período: {{ trigger.event.data.inicio }} até {{ trigger.event.data.fim }}
```

**Para Interface do Home Assistant (Configurações → Automações → Criar):**
```yaml
alias: Notificar Alerta INMET
description: Envia notificação para alertas de Perigo e Grande Perigo
trigger:
  - platform: event
    event_type: inmet_novo_alerta
condition:
  - condition: template
    value_template: "{{ trigger.event.data.severidade in ['Perigo', 'Grande Perigo'] }}"
action:
  - service: notify.mobile_app_meu_celular
    data:
      title: 🚨 Alerta Meteorológico
      message: >
        {{ trigger.event.data.titulo }}
        
        Severidade: {{ trigger.event.data.severidade }}
        Estado: {{ trigger.event.data.estado }}
        Período: {{ trigger.event.data.inicio }} até {{ trigger.event.data.fim }}
mode: single
```

### Automação Alternativa (usando mudança de sensor)

**Para configuration.yaml:**
```yaml
automation:
  - alias: "Alerta INMET - Mudança de Estado"
    trigger:
      - platform: state
        entity_id: sensor.alertas_meteorologicos_go  # Altere para seu estado
        not_from: "Nenhum alerta ativo"
        not_to: "Nenhum alerta ativo"
    condition:
      - condition: template
        value_template: "{{ states('sensor.quantidade_de_alertas_go') | int > 0 }}"
    action:
      - service: notify.mobile_app_meu_celular
        data:
          title: "🌦️ Novo Alerta Meteorológico"
          message: >
            {% set alertas = state_attr('sensor.alertas_meteorologicos_go', 'alertas') %}
            {% if alertas %}
            {% for alerta in alertas %}
            {{ alerta.icone }} {{ alerta.titulo }}
            Severidade: {{ alerta.severidade }}
            Período: {{ alerta.inicio }} até {{ alerta.fim }}
            {% if not loop.last %}---{% endif %}
            {% endfor %}
            {% endif %}
```

**Para Interface do Home Assistant:**
```yaml
alias: Alerta INMET - Mudança de Estado
description: Notifica quando há mudança nos alertas meteorológicos
trigger:
  - platform: state
    entity_id: sensor.alertas_meteorologicos_go
    not_from: Nenhum alerta ativo
    not_to: Nenhum alerta ativo
condition:
  - condition: template
    value_template: "{{ states('sensor.quantidade_de_alertas_go') | int > 0 }}"
action:
  - service: notify.mobile_app_meu_celular
    data:
      title: 🌦️ Novo Alerta Meteorológico
      message: >
        {% set alertas = state_attr('sensor.alertas_meteorologicos_go', 'alertas') %}
        {% if alertas %}
        {% for alerta in alertas %}
        {{ alerta.icone }} {{ alerta.titulo }}
        Severidade: {{ alerta.severidade }}
        Período: {{ alerta.inicio }} até {{ alerta.fim }}
        {% if not loop.last %}---{% endif %}
        {% endfor %}
        {% endif %}
mode: single
```

### Automação para Tipos Específicos de Alerta

**Para Interface do Home Assistant - Alerta de Vendaval:**
```yaml
alias: Alerta INMET - Vendaval
description: Notificação específica para alertas de vendaval
trigger:
  - platform: event
    event_type: inmet_novo_alerta
condition:
  - condition: template
    value_template: "{{ 'Vendaval' in trigger.event.data.evento }}"
action:
  - service: notify.family_group
    data:
      title: 💨 Alerta de Vendaval
      message: >
        ⚠️ {{ trigger.event.data.titulo }}
        
        🏠 Feche portas e janelas!
        🚗 Evite estacionar sob árvores!
        
        Período: {{ trigger.event.data.inicio }} até {{ trigger.event.data.fim }}
        Municípios afetados: {{ trigger.event.data.municipios }}
mode: single
```

**Para Interface do Home Assistant - Alerta de Chuva:**
```yaml
alias: Alerta INMET - Chuva Intensa
description: Notificação específica para alertas de chuva
trigger:
  - platform: event
    event_type: inmet_novo_alerta
condition:
  - condition: template
    value_template: "{{ 'Chuva' in trigger.event.data.evento }}"
action:
  - service: script.preparar_casa_chuva  # Script personalizado (opcional)
  - service: notify.mobile_app_meu_celular
    data:
      title: 🌧️ Alerta de Chuva
      message: >
        {{ trigger.event.data.titulo }}
        Severidade: {{ trigger.event.data.severidade }}
        Período: {{ trigger.event.data.inicio }} até {{ trigger.event.data.fim }}
mode: single
```
```

## 🛠️ Serviços

### `inmet_alertas.atualizar_alertas`
Força a atualização dos alertas.

**Parâmetros**:
- `estado` (opcional): Atualizar apenas alertas de um estado específico

```yaml
service: inmet_alertas.atualizar_alertas
data:
  estado: "SP"  # Opcional
```

## 🎨 Interface Lovelace

### Cartão de Alertas Simples

```yaml
type: entities
title: Alertas Meteorológicos
entities:
  - sensor.alertas_meteorologicos_sp
  - sensor.quantidade_de_alertas_sp
```

### Cartão Detalhado com Instruções Completas

Este cartão mostra alertas ativos apenas quando existem e exibe informações detalhadas:

```yaml
type: conditional
conditions:
  - entity: sensor.quantidade_de_alertas_sp  # ⚠️ ALTERE 'sp' para seu estado (ex: 'go', 'rj', 'mg')
    state_not: "0"
card:
  type: markdown
  content: >
    ## 🌦️ Alertas Ativos - {{ state_attr('sensor.alertas_meteorologicos_sp', 'estado') }}
    
    **{{ states('sensor.quantidade_de_alertas_sp') }} alerta(s) ativo(s)**
    
    {% for alerta in state_attr('sensor.alertas_meteorologicos_sp', 'alertas') %}
    ### {{ alerta.icone }} {{ alerta.titulo }}
    
    **🏷️ Tipo:** {{ alerta.evento }}  
    **⚠️ Severidade:** {{ alerta.severidade }}  
    **⏰ Início:** {{ alerta.inicio }}  
    **⏱️ Fim:** {{ alerta.fim }}  
    **📍 Municípios:** {{ alerta.total_municipios_estado }} afetados
    
    **📝 Descrição:**  
    {{ alerta.descricao }}
    
    {% if alerta.instrucoes %}
    **📋 Instruções:**  
    {{ alerta.instrucoes }}
    {% endif %}
    
    {% if alerta.municipios_estado and alerta.municipios_estado | length <= 10 %}
    **🏘️ Municípios afetados:**  
    {{ alerta.municipios_estado | join(', ') }}
    {% elif alerta.municipios_estado and alerta.municipios_estado | length > 10 %}
    **🏘️ Municípios afetados:** {{ alerta.municipios_estado | length }} municípios (muitos para listar)
    {% endif %}
    
    ---
    {% endfor %}
    
    *Última atualização: {{ state_attr('sensor.alertas_meteorologicos_sp', 'ultima_atualizacao') }}*
```

### Como Personalizar o Cartão

1. **Alterar o Estado**: Substitua `sp` pelos códigos do seu estado:
   ```yaml
   # Exemplos para diferentes estados:
   sensor.alertas_meteorologicos_go  # Goiás
   sensor.alertas_meteorologicos_rj  # Rio de Janeiro  
   sensor.alertas_meteorologicos_mg  # Minas Gerais
   sensor.alertas_meteorologicos_rs  # Rio Grande do Sul
   ```

2. **Personalizar Informações Exibidas**: Remova ou adicione campos conforme necessário:
   ```yaml
   # Campos disponíveis em cada alerta:
   {{ alerta.titulo }}                    # Nome do alerta
   {{ alerta.evento }}                    # Tipo de evento (Chuva, Vendaval, etc.)
   {{ alerta.severidade }}                    # Perigo Potencial, Perigo, Grande Perigo
   {{ alerta.inicio }}                    # Data/hora de início
   {{ alerta.fim }}                       # Data/hora de fim
   {{ alerta.descricao }}                 # Descrição detalhada
   {{ alerta.instrucoes }}                # Instruções de segurança
   {{ alerta.municipios_estado }}         # Lista de municípios afetados no estado
   {{ alerta.total_municipios_estado }}   # Número de municípios afetados
   {{ alerta.icone }}                     # Ícone do alerta
   {{ alerta.area_desc }}                 # Descrição da área afetada
   {{ alerta.publicado }}                 # Data de publicação
   {{ alerta.link }}                      # Link para detalhes do alerta
   ```

3. **Cartão Sempre Visível** (mesmo sem alertas):
   ```yaml
   type: markdown
   content: >
     ## 🌦️ Alertas Meteorológicos - {{ state_attr('sensor.alertas_meteorologicos_sp', 'estado') }}
     
     {% if states('sensor.quantidade_de_alertas_sp') == "0" %}
     ✅ **Nenhum alerta ativo no momento**
     {% else %}
     **{{ states('sensor.quantidade_de_alertas_sp') }} alerta(s) ativo(s)**
     
     {% for alerta in state_attr('sensor.alertas_meteorologicos_sp', 'alertas') %}
     ### {{ alerta.icone }} {{ alerta.titulo }}
     **Severidade:** {{ alerta.severidade }} | **Período:** {{ alerta.inicio }} até {{ alerta.fim }}
     {{ alerta.descricao }}
     ---
     {% endfor %}
     {% endif %}
   ```

### Cartão Compacto para Dashboard

```yaml
type: glance
title: Alertas INMET
entities:
  - entity: sensor.alertas_meteorologicos_sp  # ⚠️ ALTERE para seu estado
    name: Status
  - entity: sensor.quantidade_de_alertas_sp   # ⚠️ ALTERE para seu estado  
    name: Quantidade
    icon: mdi:weather-cloudy-alert
```

## 🗺️ Mapas Geográficos dos Alertas

A partir da versão 1.12.0, cada estado configurado ganha automaticamente um sensor de mapa:
- `sensor.inmet_alertas_mapa_[estado]` (ex: `sensor.inmet_alertas_mapa_go`)

### Cartão de Mapa Básico

```yaml
type: map
title: Alertas Meteorológicos
entities:
  - sensor.inmet_alertas_mapa_go  # Altere para seu estado
default_zoom: 8
aspect_ratio: "16:9"
```

### Mapa com Polígonos Reais (ha-map-card)

Para visualizar os polígonos reais dos alertas, instale o **ha-map-card** via HACS e use o plugin incluso:

```yaml
type: custom:map-card
title: Alertas INMET com Polígonos
zoom: 6
card_size: 8
x: -15.7998  # Latitude do centro
y: -47.8645  # Longitude do centro
plugins:
  - name: inmet_polygons
    url: /hacsfiles/inmet_alertas/plugin_inmet_polygons.js
    options:
      states: ["goias", "sao_paulo"]  # Estados em formato snake_case
      fillOpacity: 0.3
      strokeOpacity: 0.8
```

O plugin está disponível automaticamente em `/hacsfiles/inmet_alertas/plugin_inmet_polygons.js` após a instalação via HACS.

> **Nota**: O sensor de mapa fornece os atributos `area_total_afetada_km2`, `centro_geografico`, `zoom_recomendado` e `camadas_por_severidade` para uso em automações e cards personalizados.

## 🔧 Solução de Problemas

### Alertas não aparecem
1. Verifique se o estado está configurado corretamente
2. Consulte os logs: **Configurações** → **Sistema** → **Logs**
3. Procure por mensagens com `inmet_alertas`

### Notificações não funcionam
1. Verifique se as notificações estão habilitadas na configuração
2. Confirme se há alertas de severidade Perigo ou Grande Perigo ativo

### Logs Úteis
```yaml
# configuration.yaml
logger:
  logs:
    custom_components.inmet_alertas: debug
```

## 📅 Níveis de Severidade

- **🟡 Perigo Potencial**: Atenção - Condições meteorológicas que podem causar danos
- **🟠 Perigo**: Cuidado - Condições meteorológicas perigosas  
- **🔴 Grande Perigo**: Perigo - Condições meteorológicas muito perigosas

## 📈 Versionamento

Este projeto segue o [Versionamento Semântico](https://semver.org/):

- **MAJOR**: Mudanças incompatíveis com versões anteriores
- **MINOR**: Novas funcionalidades compatíveis
- **PATCH**: Correções de bugs compatíveis

### 🆕 Changelog v1.14.0

#### ✨ Novos Recursos
- **Sensor de Diagnóstico** `sensor.inmet_alertas_diagnostico_[estado]`
- **Options Flow** — `update_interval` e `notificacoes_perigo` configuráveis dinamicamente

#### 🐛 Correções
- **Rate limiting persistente** — CAPs pendentes não são mais descartados
- **Limite de CAPs** aumentado de 20 para 50 por ciclo
- **Retry resetado** ao obter sucesso

#### 🧪 Testes
- Migração para **pytest** com fixtures e HA mock
- **28 testes unitários** para `check_state_affected`, `GeoProcessor`

### 🆕 Changelog v1.12.0

#### 🗺️ Fase Geográfica (v2.0+)
- **Sensor de Mapa** `sensor.inmet_alertas_mapa_[estado]` com dados geográficos
- **Processamento de Polígonos** - extração e cálculo de áreas afetadas em km²
- **Zoom Inteligente** - cálculo automático do zoom ideal para visualização
- **Centro Geográfico** - determinação automática do centro das áreas afetadas
- **Plugin Leaflet** - plugin `plugin_inmet_polygons.js` para ha-map-card

#### 🎉 Melhorias Anteriores
- **Arquitetura profissional** com módulos especializados (GeoProcessor, RSSParser, etc.)
- **Documentação expandida** em pasta dedicada
- **Suporte multilíngue** (Português/Inglês)
- **Testes organizados** em estrutura própria
- **Constantes centralizadas** para melhor manutenção

#### 🐛 Correções
- **Notificações duplicadas** entre estados resolvidas
- **Rate limiting** tratado com fila de retry inteligente
- **Persistência de alertas** entre ciclos de atualização
- **Limpeza automática** de notificações expiradas

## 📊 Estatísticas do Projeto

- **~2.100 linhas** de código Python (produto) + **~600 linhas** de testes automatizados
- **+30 arquivos** organizados em estrutura modular
- **100% em português** (documentação e interface)
- **Compatibilidade** com Home Assistant 2026.3+
- **Plugin de mapa** para visualização de polígonos geográficos
- **Suporte ativo** da comunidade brasileira

## 🤝 Contribuindo

Contribuições são bem-vindas! Por favor:

1. Faça um fork do projeto
2. Crie uma branch para sua feature (`git checkout -b feature/nova-funcionalidade`)
3. Commit suas mudanças (`git commit -am 'Adiciona nova funcionalidade'`)
4. Push para a branch (`git push origin feature/nova-funcionalidade`)
5. Abra um Pull Request

## 📄 Licença

Este projeto está licenciado sob a Licença MIT - veja o arquivo [LICENSE](LICENSE) para detalhes.

## ⚠️ Disclaimer

Esta integração não é oficial e não é afiliada ao INMET. Os dados são obtidos a partir do feed RSS público do INMET.

---

**Desenvolvido com ❤️ para a comunidade brasileira do Home Assistant**