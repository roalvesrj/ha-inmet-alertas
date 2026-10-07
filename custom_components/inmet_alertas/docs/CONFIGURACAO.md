# ⚙️ Configuração da Integração INMET Alertas

## 🚀 Configuração Inicial

### 1. Adicionar Nova Integração

1. Vá para **Configurações** → **Dispositivos e Serviços**
2. Clique em **"Adicionar Integração"**
3. Procure por **"INMET Alertas"**
4. Clique na integração para iniciar a configuração

### 2. Selecionar Estado

1. **Estado**: Escolha seu estado brasileiro na lista suspensa
   - Exemplo: `GO - Goiás`, `SP - São Paulo`, `RJ - Rio de Janeiro`
2. Clique em **"Enviar"**

### 3. Configurar Opções

1. **Notificações de Perigo**: 
   - ✅ **Ativado**: Cria notificações automáticas para alertas de "Perigo" e "Grande Perigo"
   - ❌ **Desativado**: Não cria notificações automáticas

2. **Intervalo de Atualização**: 
   - **Padrão**: 45 minutos
   - **Mínimo**: 5 minutos
   - **Máximo**: 120 minutos

## 🌎 Configuração para Múltiplos Estados

Você pode monitorar vários estados simultaneamente:

### Adicionar Estados Adicionais

1. Repita o processo de **"Adicionar Integração"**
2. Selecione um estado diferente
3. Configure as opções independentemente
4. Cada estado terá seus próprios sensores e notificações

### Exemplo de Múltiplos Estados

```
Estados Configurados:
├── Goiás (GO)
│   ├── sensor.alertas_meteorologicos_go
│   ├── sensor.quantidade_de_alertas_go
│   └── Notificações: Ativadas
├── Rio de Janeiro (RJ)
│   ├── sensor.alertas_meteorologicos_rj
│   ├── sensor.quantidade_de_alertas_rj
│   └── Notificações: Desativadas
└── São Paulo (SP)
    ├── sensor.alertas_meteorologicos_sp
    ├── sensor.quantidade_de_alertas_sp
    └── Notificações: Ativadas
```

## 🔧 Configurações Avançadas

### Alterar Configurações Existentes

1. Vá para **Configurações** → **Dispositivos e Serviços**
2. Encontre **"INMET Alertas - [Estado]"**
3. Clique em **"Configurar"**
4. Ajuste as opções conforme necessário

### Remover Estado

1. Na lista de integrações, encontre o estado que deseja remover
2. Clique no menu **⋮** (três pontos)
3. Selecione **"Excluir"**
4. Confirme a remoção

## 📊 Sensores Criados

Para cada estado configurado, são criados:

### Sensor Principal
- **Nome**: `sensor.alertas_meteorologicos_[estado]`
- **Estado**: Nome do alerta ativo ou "Nenhum alerta ativo"
- **Atributos**: Informações detalhadas dos alertas

### Sensor de Contagem
- **Nome**: `sensor.quantidade_de_alertas_[estado]`
- **Estado**: Número de alertas ativos
- **Unidade**: alertas

## 🔔 Configuração de Notificações

### Notificações Automáticas

Quando ativadas, a integração cria notificações persistentes para:
- **🟠 Alertas de Perigo**
- **🔴 Alertas de Grande Perigo**

### Características das Notificações

- **Título**: Inclui severidade e estado
- **Conteúdo**: Detalhes do alerta (título, período, municípios)
- **ID Único**: Permite múltiplos estados simultâneos
- **Limpeza Automática**: Remove quando alertas expiram

### Desabilitar Notificações

1. Acesse as configurações da integração
2. Desmarque **"Notificações de Perigo"**
3. Salve as alterações

## 🎛️ Configurações do Sistema

### Logs de Debug

Para troubleshooting, adicione ao `configuration.yaml`:

```yaml
logger:
  logs:
    custom_components.inmet_alertas: debug
```

### Personalizar Intervalo

O intervalo de atualização afeta:
- **Frequência**: Com que frequência busca novos alertas
- **Performance**: Intervalos menores = mais requisições
- **Recomendação**: 45 minutos para uso normal

## ⚠️ Considerações Importantes

### Limites e Restrições

- **Fonte de Dados**: Feed RSS público do INMET
- **Disponibilidade**: Depende da estabilidade do serviço INMET
- **Cobertura**: Apenas alertas meteorológicos oficiais

### Boas Práticas

1. **Não usar intervalos muito baixos** (< 10 minutos) para evitar sobrecarga
2. **Monitorar logs** em caso de problemas de conectividade
3. **Configurar automações** baseadas nos eventos, não apenas nos sensores

## 🆘 Resolução de Problemas

### Sensores não atualizam

1. Verifique conexão com internet
2. Consulte logs para erros específicos
3. Teste com intervalo menor temporariamente

### Notificações não aparecem

1. Confirme que estão ativadas na configuração
2. Verifique se há alertas de severidade adequada
3. Teste criando notificação manual

### Dados incorretos

1. Compare com fonte oficial: [INMET](https://alertas.inmet.gov.br/)
2. Aguarde próxima atualização
3. Reporte problemas no GitHub se persistir