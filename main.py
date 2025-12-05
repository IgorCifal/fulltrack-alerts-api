import requests
import json

# --- Configurações da API ---
# As chaves de API foram obtidas do código Python fornecido pelo usuário.
API_KEY = "84c8dfe7fd5045dad5816baeb9809608e70a38c7"
SECRET_KEY = "4f17a2fd1646d0c42324c2248d6aaca5896b0246"
BASE_URL = "https://ws.fulltrack2.com"

HEADERS = {
    "Content-Type": "application/json",
    "ApiKey": API_KEY,
    "SecretKey": SECRET_KEY,
    # Adicionando um User-Agent para evitar bloqueios simples
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
}

# Dicionário para armazenar o nome do motorista por ID do veículo
# Isso evita fazer a mesma requisição para o mesmo veículo várias vezes (cache)
VEHICLE_DRIVER_CACHE = {}

def get_alerts():
    """Busca todos os eventos de alertas em aberto."""
    url = f"{BASE_URL}/alerts/all"
    print(f"1. Buscando alertas em: {url}")
    try:
        response = requests.get(url, headers=HEADERS, timeout=30)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.HTTPError as e:
        print(f"Erro HTTP ao buscar alertas: {e}")
        print(f"Resposta do servidor: {response.text}")
        return {"status": False, "message": str(e), "data": []}
    except requests.exceptions.RequestException as e:
        print(f"Erro de Conexão ao buscar alertas: {e}")
        return {"status": False, "message": str(e), "data": []}

def get_driver_name_for_vehicle(vehicle_id):
    """Busca o nome do motorista para um ID de veículo/rastreador específico."""
    
    # 1. Verificar o cache
    if vehicle_id in VEHICLE_DRIVER_CACHE:
        return VEHICLE_DRIVER_CACHE[vehicle_id]

    # 2. Fazer a requisição
    # Usamos o endpoint events/single/id/:id que retorna o ras_mot_nome
    url = f"{BASE_URL}/events/single/id/{vehicle_id}"
    
    try:
        response = requests.get(url, headers=HEADERS, timeout=10)
        response.raise_for_status()
        data = response.json()
        
        if data.get("status") and data.get("data"):
            # O nome do motorista está no primeiro item da lista 'data'
            driver_name = data["data"][0].get("ras_mot_nome", "Motorista Não Encontrado")
            
            # 3. Atualizar o cache
            VEHICLE_DRIVER_CACHE[vehicle_id] = driver_name
            return driver_name
        
        # Se a requisição foi bem-sucedida, mas não retornou dados
        VEHICLE_DRIVER_CACHE[vehicle_id] = "Dados do Veículo Não Encontrados"
        return "Dados do Veículo Não Encontrados"

    except requests.exceptions.RequestException as e:
        # Em caso de erro de conexão ou timeout
        # Não imprimimos o erro aqui para não poluir o console com erros de requisições secundárias
        VEHICLE_DRIVER_CACHE[vehicle_id] = "Erro na Requisição"
        return "Erro na Requisição"

def enrich_alerts_with_drivers(alerts_data):
    """Processa a lista de alertas e adiciona o nome do motorista a cada um."""
    
    if not alerts_data.get("status") or not alerts_data.get("data"):
        print("Nenhum alerta encontrado ou erro na requisição inicial.")
        return alerts_data

    enriched_alerts = []
    total_alerts = len(alerts_data["data"])
    print(f"2. {total_alerts} alertas encontrados. Buscando nome do motorista para cada um...")

    for i, alert in enumerate(alerts_data["data"]):
        vehicle_id = alert.get("ras_eal_id_veiculo")
        
        if vehicle_id:
            driver_name = get_driver_name_for_vehicle(vehicle_id)
            
            # Adiciona o novo campo ao objeto do alerta
            alert["motorista_associado"] = driver_name
            
            # Imprime o progresso a cada 10 alertas para evitar poluição
            if (i + 1) % 10 == 0 or i == total_alerts - 1:
                print(f"   - Processando {i+1}/{total_alerts}: Veículo {vehicle_id} -> Motorista: {driver_name}")
        else:
            alert["motorista_associado"] = "ID do Veículo Ausente"
            
        enriched_alerts.append(alert)

    print("3. Processamento concluído.")
    return {"status": True, "message": "Alertas enriquecidos com sucesso.", "data": enriched_alerts}

if __name__ == "__main__":
    # 1. Busca inicial dos alertas
    alerts_response = get_alerts()
    
    # 2. Enriquecimento dos alertas
    final_result = enrich_alerts_with_drivers(alerts_response)
    
    # 3. Imprime o resultado final formatado
    print("\n--- Resultado Final (JSON Enriquecido) ---")
    print(json.dumps(final_result, indent=4, ensure_ascii=False))

    # 4. Salva o resultado em um arquivo para fácil visualização
    with open("alertas_enriquecidos.json", "w", encoding="utf-8") as f:
        json.dump(final_result, f, indent=4, ensure_ascii=False)
    
    print("\nResultado salvo em: alertas_enriquecidos.json")
