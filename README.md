# Guida all'avvio del progetto IoT Telemetries

Questa guida descrive passo passo come avviare API FastAPI, database PostgreSQL, simulatore IoT e dashboard Streamlit.

## 1. Prerequisiti

Installa e verifica:

- Python 3.11 o superiore
- Docker Desktop
- Docker Compose, incluso in Docker Desktop
- Visual Studio o un altro editor di testo a tua scelta (opzionale)

Verifica:

```powershell
python --version
docker --version
docker compose version
```

## 2. Apri la cartella del progetto

Apri PowerShell e posizionati nella directory corretta:

```powershell
cd C:\Users\Emma\source\repos\IoT-Telemetries
```

Verifica di essere nella directory corretta:

```powershell
Get-ChildItem
```

Dovresti vedere `pyproject.toml`, `docker-compose.yml`, `app`, `dashboard` e `scripts`.

## 3. Crea l'ambiente virtuale Python

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

Se PowerShell blocca l'attivazione degli script, esegui una volta:

```powershell
Set-ExecutionPolicy -Scope CurrentUser RemoteSigned
```

Poi ripeti:

```powershell
.\.venv\Scripts\Activate.ps1
```

Il terminale dovrebbe mostrare `(.venv)` all'inizio della riga.

## 4. Installa le dipendenze

```powershell
python -m pip install --upgrade pip
pip install -e ".[dev]"
```

## 5. Crea il file `.env`

```powershell
Copy-Item .env.example .env
```

Il file conterrà:

```plaintext
DATABASE_URL=postgresql+psycopg://iot:iot@localhost:5432/iot
API_URL=http://localhost:8000
```

## 6. Avvia PostgreSQL

Assicurati che Docker Desktop sia in esecuzione:

```powershell
docker compose up -d
docker compose ps
```

Il servizio `postgres` dovrebbe risultare attivo. Per vedere i log:

```powershell
docker compose logs postgres
```

## 7. Avvia l'API FastAPI

Apri un secondo terminale PowerShell e attiva l'ambiente virtuale:

```powershell
cd C:\Users\Emma\source\repos\IoT-Telemetries
.\.venv\Scripts\Activate.ps1
uvicorn app.main:app --reload
```

L'API sarà disponibile su `http://localhost:8000` e la documentazione su `http://localhost:8000/docs`.

## 8. Verifica l'API

Da un altro terminale PowerShell:

```powershell
Invoke-RestMethod http://localhost:8000/health
```

Risultato atteso: `status: ok`.

Puoi inviare manualmente un dato:

```powershell
$payload = @{
    device_id = "machine-001"
    timestamp = (Get-Date).ToUniversalTime().ToString("o")
    temperature = 72.5
    humidity = 48.2
    pressure = 1014.3
} | ConvertTo-Json

Invoke-RestMethod `
    -Uri "http://localhost:8000/api/telemetry" `
    -Method Post `
    -ContentType "application/json" `
    -Body $payload
```

La prima richiesta avviata dall'API crea automaticamente la tabella `telemetry`.

## 9. Avvia il simulatore

Apri un terzo terminale:

```powershell
cd C:\Users\Emma\source\repos\IoT-Telemetries
.\.venv\Scripts\Activate.ps1
python -m scripts.simulator
```

Il simulatore invia un dato ogni due secondi. Per usare un dispositivo diverso:

```powershell
python -m scripts.simulator --device-id machine-002
```

Per cambiare intervallo:

```powershell
python -m scripts.simulator --interval 5
```

Per fermarlo, premi `CTRL+C`.

## 10. Avvia la dashboard Streamlit

Apri un quarto terminale:

```powershell
cd C:\Users\Emma\source\repos\IoT-Telemetries
.\.venv\Scripts\Activate.ps1
streamlit run dashboard/streamlit_app.py
```

La dashboard sarà disponibile su `http://localhost:8501`. Apri l'indirizzo nel browser e premi **Aggiorna dati**.

## Ordine corretto di avvio

1. Avvia Docker Desktop.
2. Avvia PostgreSQL con `docker compose up -d`.
3. Avvia FastAPI con `uvicorn app.main:app --reload`.
4. Avvia il simulatore con `python -m scripts.simulator`.
5. Avvia Streamlit con `streamlit run dashboard/streamlit_app.py`.

## Arresto del progetto

Nei terminali di FastAPI, simulatore e Streamlit premi `CTRL+C`. Poi arresta PostgreSQL:

```powershell
docker compose down
```

Per eliminare anche i dati persistiti:

```powershell
docker compose down -v
```

Il comando `down -v` elimina il volume del database e deve essere usato con attenzione.