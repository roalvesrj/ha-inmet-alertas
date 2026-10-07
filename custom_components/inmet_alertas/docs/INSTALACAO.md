# 📦 Instalação da Integração INMET Alertas

## 🎯 Pré-requisitos

- Home Assistant 2026.3 ou superior
- HACS (Home Assistant Community Store) instalado
- Conexão com internet estável

## 📥 Instalação via HACS (Recomendado)

### 1. Adicionar Repositório Personalizado

1. Abra o **HACS** no seu Home Assistant
2. Clique em **"Integrações"**
3. Clique no menu **⋮** (três pontos) no canto superior direito
4. Selecione **"Repositórios Personalizados"**
5. Adicione a URL: `https://github.com/roalvesrj/ha-inmet-alertas`
6. Selecione a categoria **"Integração"**
7. Clique em **"Adicionar"**

### 2. Instalar a Integração

1. Procure por **"INMET Alertas"** na lista de integrações
2. Clique em **"Instalar"**
3. Aguarde o download e instalação
4. **Reinicie o Home Assistant**

## 📥 Instalação Manual

### 1. Download dos Arquivos

1. Baixe a versão mais recente do [repositório GitHub](https://github.com/roalvesrj/ha-inmet-alertas)
2. Extraia o arquivo ZIP

### 2. Copiar Arquivos

1. Localize a pasta `custom_components` no seu diretório de configuração do Home Assistant
   - Se não existir, crie a pasta
2. Copie a pasta `inmet_alertas` para `custom_components/`
3. A estrutura final deve ser:
   ```
   config/
   └── custom_components/
       └── inmet_alertas/
           ├── __init__.py
           ├── manifest.json
           ├── sensor.py
           └── ... (outros arquivos)
   ```

### 3. Reiniciar

1. **Reinicie o Home Assistant** completamente
2. Verifique os logs para confirmar que não há erros de carregamento

## ✅ Verificação da Instalação

1. Vá para **Configurações** → **Dispositivos e Serviços**
2. Clique em **"Adicionar Integração"**
3. Procure por **"INMET Alertas"**
4. Se aparecer na lista, a instalação foi bem-sucedida!

## 🔧 Resolução de Problemas

### Integração não aparece na lista

1. Verifique se todos os arquivos foram copiados corretamente
2. Confirme que o Home Assistant foi reiniciado
3. Verifique os logs em **Configurações** → **Sistema** → **Logs**

### Erro de dependências

1. Verifique sua conexão com internet
2. A integração usa apenas bibliotecas já incluídas no Home Assistant — nenhuma dependência externa precisa ser instalada
3. Reinicie o Home Assistant se necessário

### Arquivos corrompidos

1. Remova a pasta `inmet_alertas` de `custom_components/`
2. Reinstale pelos métodos acima
3. Reinicie o Home Assistant

## 📞 Suporte

- **Issues GitHub**: [Reportar problemas](https://github.com/roalvesrj/ha-inmet-alertas/issues)
- **Documentação**: Consulte os outros arquivos da pasta `docs/`
- **Comunidade**: Fóruns do Home Assistant Brasil