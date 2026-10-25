"""
Módulo para processamento de dados geográficos dos alertas INMET.
Processa coordenadas de polígonos, calcula áreas e centros geográficos.
"""
import logging
import math
from typing import List, Dict, Any, Optional

_LOGGER = logging.getLogger(__name__)

# Constantes para cálculos geodésicos
RAIO_TERRA_KM = 6371.0  # Raio médio da Terra em km


class GeoProcessor:
    """Processador de dados geográficos para alertas INMET."""
    
    @staticmethod
    def parse_coordenadas_cap(polygon_text: str) -> Optional[List[List[float]]]:
        """
        Converte string de polígono CAP em lista de coordenadas.
        
        Args:
            polygon_text: String do formato "-15.277958,-46.131592 -14.973107,-46.365051 ..."
            
        Returns:
            Lista de coordenadas [[lat, lon], [lat, lon], ...] ou None se inválido
        """
        try:
            if not polygon_text or not polygon_text.strip():
                return None
                
            # Dividir por espaços e processar cada ponto
            pontos = polygon_text.strip().split()
            coordenadas = []
            
            for ponto in pontos:
                if ',' in ponto:
                    lat_str, lon_str = ponto.split(',', 1)
                    try:
                        lat = float(lat_str)
                        lon = float(lon_str)
                        
                        # Validar coordenadas brasileiras
                        if -34 <= lat <= 5 and -74 <= lon <= -32:
                            coordenadas.append([lat, lon])
                        else:
                            _LOGGER.warning(f"Coordenada fora do Brasil ignorada: {lat}, {lon}")
                            
                    except ValueError:
                        _LOGGER.warning(f"Coordenada inválida ignorada: {ponto}")
                        continue
            
            # Verificar se temos pelo menos 3 pontos para formar um polígono
            if len(coordenadas) >= 3:
                # Garantir que o polígono está fechado
                if coordenadas[0] != coordenadas[-1]:
                    coordenadas.append(coordenadas[0])
                    
                _LOGGER.debug(f"Polígono processado com {len(coordenadas)} pontos")
                return coordenadas
            else:
                _LOGGER.warning(f"Polígono inválido - apenas {len(coordenadas)} pontos válidos")
                return None
                
        except Exception as e:
            _LOGGER.error(f"Erro ao processar coordenadas CAP: {e}")
            return None
    
    @staticmethod
    def calcular_area_poligono(coordenadas: List[List[float]]) -> float:
        """
        Calcula área de polígono em km² usando algoritmo Shoelace geodésico.
        
        Args:
            coordenadas: Lista de pontos [[lat, lon], ...]
            
        Returns:
            Área em quilômetros quadrados
        """
        try:
            if not coordenadas or len(coordenadas) < 3:
                return 0.0
                
            # Algoritmo Shoelace adaptado para coordenadas geodésicas
            area = 0.0
            n = len(coordenadas)
            
            for i in range(n - 1):
                lat1, lon1 = math.radians(coordenadas[i][0]), math.radians(coordenadas[i][1])
                lat2, lon2 = math.radians(coordenadas[i + 1][0]), math.radians(coordenadas[i + 1][1])
                
                # Fórmula de área esférica aproximada
                area += (lon2 - lon1) * (2 + math.sin(lat1) + math.sin(lat2))
            
            area = abs(area) * RAIO_TERRA_KM * RAIO_TERRA_KM / 2.0
            
            _LOGGER.debug(f"Área calculada: {area:.2f} km²")
            return area
            
        except Exception as e:
            _LOGGER.error(f"Erro ao calcular área: {e}")
            return 0.0
    
    @staticmethod
    def calcular_centro_geografico(coordenadas: List[List[float]]) -> Optional[List[float]]:
        """
        Calcula centro geográfico (centroide) de um polígono.
        
        Args:
            coordenadas: Lista de pontos [[lat, lon], ...]
            
        Returns:
            Centro como [lat, lon] ou None se inválido
        """
        try:
            if not coordenadas or len(coordenadas) < 3:
                return None
                
            # Calcular centroide simples (média das coordenadas)
            total_lat = sum(ponto[0] for ponto in coordenadas[:-1])  # Excluir último ponto duplicado
            total_lon = sum(ponto[1] for ponto in coordenadas[:-1])
            n = len(coordenadas) - 1
            
            centro = [total_lat / n, total_lon / n]
            
            _LOGGER.debug(f"Centro geográfico: {centro[0]:.6f}, {centro[1]:.6f}")
            return centro
            
        except Exception as e:
            _LOGGER.error(f"Erro ao calcular centro geográfico: {e}")
            return None
    
    @staticmethod
    def calcular_bounding_box(coordenadas: List[List[float]]) -> Optional[Dict[str, float]]:
        """
        Calcula bounding box (caixa delimitadora) de um polígono.
        
        Args:
            coordenadas: Lista de pontos [[lat, lon], ...]
            
        Returns:
            Dict com min_lat, max_lat, min_lon, max_lon ou None
        """
        try:
            if not coordenadas:
                return None
                
            lats = [ponto[0] for ponto in coordenadas]
            lons = [ponto[1] for ponto in coordenadas]
            
            bbox = {
                "min_lat": min(lats),
                "max_lat": max(lats),
                "min_lon": min(lons), 
                "max_lon": max(lons)
            }
            
            _LOGGER.debug(f"Bounding box: {bbox}")
            return bbox
            
        except Exception as e:
            _LOGGER.error(f"Erro ao calcular bounding box: {e}")
            return None
    
    @staticmethod
    def calcular_zoom_recomendado(bbox: Dict[str, float]) -> int:
        """
        Calcula nível de zoom recomendado baseado no bounding box.
        
        Args:
            bbox: Bounding box do polígono
            
        Returns:
            Nível de zoom de 1 a 18
        """
        try:
            if not bbox:
                return 8  # Zoom padrão
                
            # Calcular extensão em graus
            extensao_lat = bbox["max_lat"] - bbox["min_lat"]
            extensao_lon = bbox["max_lon"] - bbox["min_lon"]
            extensao_max = max(extensao_lat, extensao_lon)
            
            # Mapear extensão para zoom (aproximado)
            if extensao_max > 10:
                zoom = 5
            elif extensao_max > 5:
                zoom = 6
            elif extensao_max > 2:
                zoom = 7
            elif extensao_max > 1:
                zoom = 8
            elif extensao_max > 0.5:
                zoom = 9
            elif extensao_max > 0.2:
                zoom = 10
            else:
                zoom = 11
                
            _LOGGER.debug(f"Zoom recomendado: {zoom} (extensão: {extensao_max:.3f}°)")
            return zoom
            
        except Exception as e:
            _LOGGER.error(f"Erro ao calcular zoom: {e}")
            return 8
    
    @staticmethod
    def processar_poligono_completo(polygon_text: str, alerta_id: str) -> Optional[Dict[str, Any]]:
        """
        Processa completamente um polígono CAP com todos os cálculos.
        
        Args:
            polygon_text: String de coordenadas do CAP
            alerta_id: ID do alerta para logs
            
        Returns:
            Dict completo com dados geográficos ou None
        """
        try:
            coordenadas = GeoProcessor.parse_coordenadas_cap(polygon_text)
            if not coordenadas:
                return None
                
            area = GeoProcessor.calcular_area_poligono(coordenadas)
            centro = GeoProcessor.calcular_centro_geografico(coordenadas)
            bbox = GeoProcessor.calcular_bounding_box(coordenadas)
            zoom = GeoProcessor.calcular_zoom_recomendado(bbox) if bbox else 8
            
            resultado = {
                "coordenadas": coordenadas,
                "area_km2": round(area, 2),
                "centro": centro,
                "bounding_box": bbox,
                "zoom_recomendado": zoom,
                "total_pontos": len(coordenadas) - 1  # Excluir ponto de fechamento
            }
            
            _LOGGER.info(f"Polígono processado para alerta {alerta_id}: "
                        f"{resultado['total_pontos']} pontos, "
                        f"{resultado['area_km2']} km²")
            
            return resultado
            
        except Exception as e:
            _LOGGER.error(f"Erro ao processar polígono completo do alerta {alerta_id}: {e}")
            return None
    
    @staticmethod
    def combinar_poligonos_estado(poligonos: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Combina múltiplos polígonos de um estado em dados unificados.
        
        Args:
            poligonos: Lista de polígonos processados
            
        Returns:
            Dados combinados do estado
        """
        try:
            if not poligonos:
                return {
                    "area_total_km2": 0.0,
                    "centro_estado": None,
                    "bounding_box_estado": None,
                    "zoom_estado": 8,
                    "total_poligonos": 0
                }
            
            # Combinar áreas
            area_total = sum(p.get("area_km2", 0) for p in poligonos)
            
            # Calcular centro médio ponderado por área
            centros_validos = [p for p in poligonos if p.get("centro")]
            if centros_validos:
                peso_total = sum(p.get("area_km2", 1) for p in centros_validos)
                if peso_total > 0:
                    centro_lat = sum(p["centro"][0] * p.get("area_km2", 1) for p in centros_validos) / peso_total
                    centro_lon = sum(p["centro"][1] * p.get("area_km2", 1) for p in centros_validos) / peso_total
                    centro_estado = [centro_lat, centro_lon]
                else:
                    centro_estado = centros_validos[0]["centro"]
            else:
                centro_estado = None
            
            # Combinar bounding boxes
            bboxes_validos = [p["bounding_box"] for p in poligonos if p.get("bounding_box")]
            if bboxes_validos:
                bbox_estado = {
                    "min_lat": min(b["min_lat"] for b in bboxes_validos),
                    "max_lat": max(b["max_lat"] for b in bboxes_validos),
                    "min_lon": min(b["min_lon"] for b in bboxes_validos),
                    "max_lon": max(b["max_lon"] for b in bboxes_validos)
                }
                zoom_estado = GeoProcessor.calcular_zoom_recomendado(bbox_estado)
            else:
                bbox_estado = None
                zoom_estado = 8
            
            resultado = {
                "area_total_km2": round(area_total, 2),
                "centro_estado": centro_estado,
                "bounding_box_estado": bbox_estado,
                "zoom_estado": zoom_estado,
                "total_poligonos": len(poligonos)
            }
            
            _LOGGER.info(f"Dados combinados do estado: "
                        f"{resultado['total_poligonos']} polígonos, "
                        f"{resultado['area_total_km2']} km² total")
            
            return resultado
            
        except Exception as e:
            _LOGGER.error(f"Erro ao combinar polígonos do estado: {e}")
            return {
                "area_total_km2": 0.0,
                "centro_estado": None,
                "bounding_box_estado": None,
                "zoom_estado": 8,
                "total_poligonos": 0
            }