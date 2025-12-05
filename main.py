from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import requests
import os
from typing import Dict, List, Optional
import uvicorn

app = FastAPI(
    title="Fulltrack Alerts API",
    description="API para buscar e enriquecer alertas do Fulltrack com informações de motoristas",
    version="2.1.0"
)

# Configurar CORS para permitir requisições de qualquer origem
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- Configurações da API ---
API_KEY = os.getenv("FULLTRACK_API_KEY", "84c8dfe7fd5045dad5816baeb9809608e70a38c7")
SECRET_KEY = os.getenv("FULLTRACK_SECRET_KEY", "4f17a2fd1646d0c42324c2248d6aaca5896b0246")
BASE_URL = "https://ws.fulltrack2.com"

HEADERS = {
    "Content-Type": "application/json",
    "ApiKey": API_KEY,
    "SecretKey": SECRET_KEY,
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
}

# Cache para armazenar informações do veículo por ID
VEHICLE_INFO_CACHE = {}

def get_alerts():
    """Busca todos os eventos de alertas em aberto."""
    url = f"{BASE_URL}/alerts/all"
    try:
        response = requests.get(url, headers=HEADERS, timeout=30)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.HTTPError as e:
        return {"status": False, "message": str(e), "data": []}
    except requests.exceptions.RequestException as e:
        return {"status": False, "message": str(e), "data": []}

def get_vehicle_info(vehicle_id: int) -> Dict:
    """Busca informações completas do veículo incluindo motorista, placa e nome do veículo."""
    
    # Verificar o cache
    if vehicle_id in VEHICLE_INFO_CACHE:
        return VEHICLE_INFO_CACHE[vehicle_id]

    # Fazer a requisição
    url = f"{BASE_URL}/events/single/id/{vehicle_id}"
    
    try:
        response = requests.get(url, headers=HEADERS, timeout=10)
        response.raise_for_status()
        data = response.json()
        
        if data.get("status") and data.get("data") and len(data["data"]) > 0:
            event_data = data["data"][0]
            
            vehicle_info = {
                "driver_name": event_data.get("ras_mot_nome", "Não informado"),
                "vehicle_name": event_data.get("ras_vei_veiculo", "Não informado"),
                "vehicle_plate": event_data.get("ras_vei_placa", "Não informado")
            }
            
            # Atualizar o cache
            VEHICLE_INFO_CACHE[vehicle_id] = vehicle_info
            return vehicle_info
        
        # Se a requisição foi bem-sucedida, mas não retornou dados
        default_info = {
            "driver_name": "Não informado",
            "vehicle_name": "Não informado",
            "vehicle_plate": "Não informado"
        }
        VEHICLE_INFO_CACHE[vehicle_id] = default_info
        return default_info

    except requests.exceptions.RequestException:
        error_info = {
            "driver_name": "Erro ao buscar",
            "vehicle_name": "Erro ao buscar",
            "vehicle_plate": "Erro ao buscar"
        }
        VEHICLE_INFO_CACHE[vehicle_id] = error_info
        return error_info

def create_google_maps_link(latitude: str, longitude: str) -> str:
    """Cria um link do Google Maps com base na latitude e longitude."""
    if latitude and longitude:
        try:
            # Converter para float para validar
            lat = float(latitude)
            lng = float(longitude)
            return f"https://www.google.com/maps?q={lat},{lng}"
        except (ValueError, TypeError):
            return "Coordenadas inválidas"
    return "Não disponível"

def enrich_alerts_simplified(alerts_data: Dict) -> Dict:
    """Processa alertas e retorna apenas os campos solicitados."""
    
    if not alerts_data.get("status") or not alerts_data.get("data"):
        return {"status": False, "message": "Nenhum alerta encontrado", "data": []}

    simplified_alerts = []
    
    for alert in alerts_data["data"]:
        vehicle_id = alert.get("ras_eal_id_veiculo")
        latitude = alert.get("ras_eal_latitude", "")
        longitude = alert.get("ras_eal_longitude", "")
        horario = alert.get("ras_eal_data_alerta", "Não informado")
        
        # Buscar informações do veículo
        vehicle_info = {
            "driver_name": "Não informado",
            "vehicle_name": "Não informado",
            "vehicle_plate": "Não informado"
        }
        
        if vehicle_id:
            try:
                vehicle_info = get_vehicle_info(int(vehicle_id))
            except (ValueError, TypeError):
                pass
        
        # Criar link do Google Maps
        maps_link = create_google_maps_link(latitude, longitude)
        
        # Montar objeto simplificado
        simplified_alert = {
            "motorista": vehicle_info["driver_name"],
            "veiculo": vehicle_info["vehicle_name"],
            "placa": vehicle_info["vehicle_plate"],
            "latitude": latitude if latitude else "Não disponível",
            "longitude": longitude if longitude else "Não disponível",
            "link_localizacao": maps_link,
            "horario_alerta": horario
        }
        
        simplified_alerts.append(simplified_alert)

    return {
        "status": True,
        "message": f"{len(simplified_alerts)} alertas processados com sucesso",
        "total": len(simplified_alerts),
        "data": simplified_alerts
    }

@app.get("/")
async def root():
    """Endpoint raiz com informações da API."""
    return {
        "message": "Fulltrack Alerts API v2.1",
        "version": "2.1.0",
        "endpoints": {
            "/alerts": "Busca alertas formatados com campos específicos (motorista, veículo, placa, lat/long, link, horário)",
            "/alerts/raw": "Busca alertas sem processamento (dados brutos)",
            "/health": "Verifica o status da API",
            "/cache/clear": "Limpa o cache de veículos"
        },
        "campos_retornados": [
            "motorista",
            "veiculo",
            "placa",
            "latitude",
            "longitude",
            "link_localizacao",
            "horario_alerta"
        ]
    }

@app.get("/health")
async def health_check():
    """Endpoint de health check."""
    return {"status": "healthy", "service": "fulltrack-alerts-api", "version": "2.1.0"}

@app.get("/alerts")
async def get_formatted_alerts():
    """Busca alertas formatados com campos específicos."""
    alerts = get_alerts()
    
    if not alerts.get("status"):
        raise HTTPException(status_code=500, detail=alerts.get("message", "Erro ao buscar alertas"))
    
    formatted = enrich_alerts_simplified(alerts)
    return formatted

@app.get("/alerts/raw")
async def get_raw_alerts():
    """Busca todos os alertas sem processamento (dados brutos da API Fulltrack)."""
    alerts = get_alerts()
    
    if not alerts.get("status"):
        raise HTTPException(status_code=500, detail=alerts.get("message", "Erro ao buscar alertas"))
    
    return alerts

@app.get("/alerts/vehicle/{vehicle_id}")
async def get_vehicle_info_endpoint(vehicle_id: int):
    """Busca informações do veículo para um ID específico."""
    info = get_vehicle_info(vehicle_id)
    
    return {
        "vehicle_id": vehicle_id,
        "driver_name": info["driver_name"],
        "vehicle_name": info["vehicle_name"],
        "vehicle_plate": info["vehicle_plate"]
    }

@app.post("/cache/clear")
async def clear_cache():
    """Limpa o cache de informações de veículos."""
    VEHICLE_INFO_CACHE.clear()
    return {"message": "Cache limpo com sucesso", "status": True}

@app.get("/cache/stats")
async def cache_stats():
    """Retorna estatísticas do cache."""
    return {
        "cached_vehicles": len(VEHICLE_INFO_CACHE),
        "cache_size_kb": len(str(VEHICLE_INFO_CACHE)) / 1024
    }

if __name__ == "__main__":
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
