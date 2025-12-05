# Fulltrack Alerts API

API REST para buscar e enriquecer alertas do Fulltrack com informações de motoristas.

## Endpoints Disponíveis

### 1. **GET /** - Informações da API
Retorna informações básicas sobre a API e seus endpoints.

**Exemplo de resposta:**
```json
{
  "message": "Fulltrack Alerts API",
  "version": "1.0.0",
  "endpoints": {
    "/alerts": "Busca alertas sem enriquecimento",
    "/alerts/enriched": "Busca alertas enriquecidos com nome do motorista",
    "/health": "Verifica o status da API"
  }
}
```

### 2. **GET /health** - Health Check
Verifica se a API está funcionando.

**Exemplo de resposta:**
```json
{
  "status": "healthy",
  "service": "fulltrack-alerts-api"
}
```

### 3. **GET /alerts** - Buscar Alertas
Busca todos os alertas sem enriquecimento (dados brutos da API Fulltrack).

**Exemplo de resposta:**
```json
{
  "status": true,
  "message": "Success",
  "data": [
    {
      "ras_eal_id_veiculo": 501141,
      "ras_eal_placa": "GFC-1C63",
      ...
    }
  ]
}
```

### 4. **GET /alerts/enriched** - Buscar Alertas Enriquecidos ⭐
Busca todos os alertas e adiciona o nome do motorista associado a cada veículo.

**Exemplo de resposta:**
```json
{
  "status": true,
  "message": "Alertas enriquecidos com sucesso.",
  "data": [
    {
      "ras_eal_id_veiculo": 501141,
      "ras_eal_placa": "GFC-1C63",
      "motorista_associado": "ANDRE GOMES MARTINS",
      ...
    }
  ]
}
```

### 5. **GET /alerts/vehicle/{vehicle_id}** - Buscar Motorista por Veículo
Busca o nome do motorista para um ID de veículo específico.

**Exemplo:**
```
GET /alerts/vehicle/501141
```

**Resposta:**
```json
{
  "vehicle_id": 501141,
  "driver_name": "ANDRE GOMES MARTINS"
}
```

### 6. **POST /cache/clear** - Limpar Cache
Limpa o cache de motoristas armazenado em memória.

**Resposta:**
```json
{
  "message": "Cache limpo com sucesso",
  "status": true
}
```

## Como Usar

### Exemplo com cURL:
```bash
# Buscar alertas enriquecidos
curl https://sua-api.onrender.com/alerts/enriched

# Buscar motorista de um veículo específico
curl https://sua-api.onrender.com/alerts/vehicle/501141
```

### Exemplo com Python:
```python
import requests

# Buscar alertas enriquecidos
response = requests.get("https://sua-api.onrender.com/alerts/enriched")
data = response.json()

for alert in data["data"]:
    print(f"Veículo: {alert['ras_eal_placa']} - Motorista: {alert['motorista_associado']}")
```

### Exemplo com n8n:
1. Use o node **HTTP Request**
2. Configure:
   - **Method**: GET
   - **URL**: `https://sua-api.onrender.com/alerts/enriched`
3. Os dados retornarão no formato JSON pronto para uso

## Variáveis de Ambiente

Para maior segurança, você pode configurar as chaves de API como variáveis de ambiente:

- `FULLTRACK_API_KEY` - Chave de API do Fulltrack
- `FULLTRACK_SECRET_KEY` - Chave secreta do Fulltrack
- `PORT` - Porta do servidor (padrão: 8000)

## Deploy

Esta API pode ser deployada em:
- **Render** (recomendado - gratuito)
- **Railway**
- **Heroku**
- **Google Cloud Run**
- **AWS Lambda** (com adaptação)

## Tecnologias

- **FastAPI** - Framework web moderno e rápido
- **Uvicorn** - Servidor ASGI de alta performance
- **Requests** - Cliente HTTP para consumir a API Fulltrack

## Licença

MIT
