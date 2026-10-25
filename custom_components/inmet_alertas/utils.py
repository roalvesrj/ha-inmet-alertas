"""Utilitários para a integração INMET Alertas."""
from datetime import datetime
from typing import Dict, List, Any
import logging

from homeassistant.util import dt as dt_util
from .const import MICRORREGIOES_ESTADOS

_LOGGER = logging.getLogger(__name__)


def format_datetime(iso_datetime: str) -> str:
    """Formatar datetime ISO para formato brasileiro usando timezone local."""
    if not iso_datetime:
        return ""
    
    try:
        # Parse ISO datetime e converter para timezone local
        dt = dt_util.parse_datetime(iso_datetime)
        if dt:
            # Converter para timezone local do HA
            dt_local = dt_util.as_local(dt)
            # Formato brasileiro
            return dt_local.strftime("%d/%m/%Y %H:%M")
        else:
            return iso_datetime
    except Exception:
        return iso_datetime


def is_alert_active(cap_data: Dict[str, Any], now: datetime = None) -> bool:
    """Verificar se o alerta está ativo no momento atual."""
    if now is None:
        now = dt_util.now()
    
    inicio_iso = cap_data.get('onset', '')
    fim_iso = cap_data.get('expires', '')
    
    if not inicio_iso or not fim_iso:
        return True  # Assume ativo se não há data
    
    try:
        # Converter datas ISO para timezone local do HA
        inicio = dt_util.parse_datetime(inicio_iso)
        fim = dt_util.parse_datetime(fim_iso)
        
        if inicio and fim:
            # Comparar usando timezone local
            return inicio <= now <= fim
        else:
            _LOGGER.warning(f"Erro ao processar datas: inicio={inicio_iso}, fim={fim_iso}")
            return True
            
    except Exception as e:
        _LOGGER.warning(f"Erro ao verificar período do alerta: {e}")
        return True  # Assume ativo em caso de erro


def check_state_affected(cap_data: Dict[str, Any], estado: str) -> bool:
    """Verificar se o alerta afeta o estado especificado.
    
    Verifica tanto microrregiões INMET quanto municípios individuais.
    """
    if not estado:
        return True
        
    municipios = cap_data.get('municipios', '')
    if not municipios:
        return False
    
    # Método 1: Verificar microrregiões INMET
    # Dividir o texto por vírgulas para obter cada área/microrregião
    areas = [area.strip() for area in municipios.split(',')]
    
    for area in areas:
        # Verificar se a área/microrregião pertence ao estado
        if area in MICRORREGIOES_ESTADOS:
            if MICRORREGIOES_ESTADOS[area] == estado:
                return True
    
    # Método 2: Verificar municípios individuais com padrão " - UF "
    estado_tag = f" - {estado} "
    if estado_tag in municipios:
        return True
    
    return False


def filter_state_municipalities(municipios_text: str, estado: str) -> List[str]:
    """Filtrar municípios e microrregiões do estado especificado."""
    if not municipios_text:
        return []
    
    resultado = []
    areas = [area.strip() for area in municipios_text.split(",")]
    
    for area in areas:
        # Verificar se é uma microrregião do estado
        if area in MICRORREGIOES_ESTADOS and MICRORREGIOES_ESTADOS[area] == estado:
            resultado.append(area)
        # Verificar se é um município individual do estado
        elif f" - {estado} " in area:
            resultado.append(area)
    
    return resultado

    return resultado
