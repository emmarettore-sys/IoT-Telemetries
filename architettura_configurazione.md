# Architettura e configurazione

Questo documento descrive l'architettura del progetto **IoT Telemetries**, il ruolo di ogni componente e le impostazioni che è possibile personalizzare.

## 1. Obiettivo del progetto

Il progetto acquisisce dati di telemetria da uno o più dispositivi, li valida tramite una API REST, li salva in PostgreSQL e li visualizza con una dashboard Streamlit.

Il flusso applicativo è:

```text
Simulatore o dispositivo IoT
		  |
		  | POST /api/telemetry
		  v
	  FastAPI
		  |
		  | validazione Pydantic
		  v
	  SQLAlchemy
		  |
		  | INSERT / SELECT
		  v
	  PostgreSQL
		  ^
		  |
		  | GET /api/telemetry/latest
		  |
	  Streamlit
```

La dashboard utilizza attualmente il polling manuale: il pulsante **Aggiorna dati** ripete la richiesta HTTP all'API.

## 2. Struttura delle directory

```text
IoT&Telemetries/
|
|-- app/
|   |-- main.py                         # Entrypoint FastAPI
|   |-- core/
|   |   `-- config.py                   # Configurazione applicativa
|   |-- db/
|   |   `-- session.py                  # Engine, sessioni e Base ORM
|   |-- models/
|   |   `-- telemetry.py                # Modello SQLAlchemy
|   |-- schemas/
|   |   `-- telemetry.py                # Schemi Pydantic
|   `-- api/routes/
|       `-- telemetry.py                # Endpoint REST
|-- dashboard/
|   `-- streamlit_app.py                # Interfaccia Streamlit
|-- scripts/
|   `-- simulator.py                    # Generatore dati
|-- docker-compose.yml                  # PostgreSQL locale
|-- Dockerfile                          # Immagine applicativa
|-- pyproject.toml                      # Dipendenze e build Python
|-- .env.example                        # Configurazione di esempio
|-- README.md                           # Guida rapida
`-- Guida.md                            # Guida operativa dettagliata
```

I file `__init__.py` presenti nei package permettono a Python di importarli correttamente.

## 3. Configurazione dell'ambiente

### 3.1 File `.env`

Il file `.env` viene letto da `app/core/config.py` e contiene i parametri dell'applicazione:

```dotenv
DATABASE_URL=postgresql+psycopg://iot:iot@localhost:5432/iot
API_URL=http://localhost:8000
```

`DATABASE_URL` ha questa struttura:

```text
postgresql+psycopg://utente:password@host:porta/database
```

Esempio per un database diverso:

```dotenv
DATABASE_URL=postgresql+psycopg://telemetry_user:password@db.example.com:5432/telemetry
API_URL=https://api.example.com
```

Non committare `.env` in Git. Il file è escluso da `.gitignore`; è possibile condividere `.env.example` senza password reali.

### 3.2 `app/core/config.py`

La classe `Settings` definisce i valori predefiniti:

```python
class Settings(BaseSettings):
	database_url: str = "postgresql+psycopg://iot:iot@localhost:5432/iot"
	api_url: str = "http://localhost:8000"
```

Le variabili d'ambiente usano automaticamente il nome maiuscolo del campo:

- `database_url` -> `DATABASE_URL`
- `api_url` -> `API_URL`

`get_settings()` è decorata con `lru_cache`, quindi la configurazione viene caricata una sola volta durante il processo. Dopo aver modificato `.env`, riavvia FastAPI e Streamlit.

Per aggiungere una nuova impostazione, per esempio un limite applicativo:

```python
class Settings(BaseSettings):
	database_url: str = "postgresql+psycopg://iot:iot@localhost:5432/iot"
	api_url: str = "http://localhost:8000"
	latest_limit: int = 20
```

Nel file `.env` si potrà usare:

```dotenv
LATEST_LIMIT=50
```

Attualmente l'endpoint `/latest` usa il valore fisso `20`; per usare la nuova impostazione occorre anche iniettarla nella route.

## 4. Dipendenze Python e `pyproject.toml`

`pyproject.toml` definisce il progetto e le versioni compatibili:

| Dipendenza | Funzione |
|---|---|
| `fastapi` | Framework per API REST e documentazione OpenAPI |
| `uvicorn` | Server ASGI che esegue FastAPI |
| `sqlalchemy` | ORM e accesso al database |
| `psycopg[binary]` | Driver PostgreSQL |
| `pydantic-settings` | Lettura e validazione della configurazione |
| `httpx` | Client HTTP usato dal simulatore e dalla dashboard |
| `streamlit` | Dashboard Python |
| `pandas` | Elaborazione tabellare dei dati |

Le dipendenze opzionali `dev` installano:

- `pytest`
- `ruff`

Installazione:

```powershell
pip install -e ".[dev]"
```

Per aggiornare una versione, modifica il relativo vincolo in `pyproject.toml`, poi esegui nuovamente:

```powershell
pip install -e ".[dev]"
```

Il progetto richiede Python `3.11` o superiore. La configurazione Ruff imposta lunghezza massima delle righe a 100 caratteri e target Python `3.11`.

## 5. PostgreSQL e Docker Compose

### 5.1 Configurazione attuale

`docker-compose.yml` avvia PostgreSQL 16 Alpine:

```yaml
services:
  postgres:
	image: postgres:16-alpine
	environment:
	  POSTGRES_DB: iot
	  POSTGRES_USER: iot
	  POSTGRES_PASSWORD: iot
	ports:
	  - "5432:5432"
```

Il volume `postgres_data` mantiene i dati anche dopo il riavvio del container.

Avvio e verifica:

```powershell
docker compose up -d
docker compose ps
docker compose logs postgres
```

Arresto senza cancellare i dati:

```powershell
docker compose down
```

Arresto con cancellazione del volume e dei dati:

```powershell
docker compose down -v
```

### 5.2 Personalizzare il database

Per cambiare nome database, utente o password, modifica `docker-compose.yml` e `.env` con valori coerenti:

```yaml
environment:
  POSTGRES_DB: telemetry
  POSTGRES_USER: telemetry_user
  POSTGRES_PASSWORD: cambia-questa-password
```

Nel file `.env`:

```dotenv
DATABASE_URL=postgresql+psycopg://telemetry_user:cambia-questa-password@localhost:5432/telemetry
```

Se il volume è già stato creato, cambiare solo le variabili non riconfigura automaticamente un database inizializzato. In ambiente di sviluppo si può ricreare tutto con:

```powershell
docker compose down -v
docker compose up -d
```

In produzione non usare `down -v`: applica una procedura di migrazione e backup.

### 5.3 Personalizzare porta e volume

Per esporre PostgreSQL su una porta Windows diversa:

```yaml
ports:
  - "5433:5432"
```

In questo caso `.env` deve usare `localhost:5433`, mentre la porta interna del container resta `5432`:

```dotenv
DATABASE_URL=postgresql+psycopg://iot:iot@localhost:5433/iot
```

La porta `5432` è la porta interna del servizio PostgreSQL; la prima porta è quella dell'host.

### 5.4 Health check

Il controllo:

```yaml
healthcheck:
  test: ["CMD-SHELL", "pg_isready -U iot -d iot"]
```

verifica che PostgreSQL accetti connessioni. Se si cambiano utente o database, aggiornare anche questo comando.

## 6. Accesso al database: `app/db/session.py`

Il modulo crea:

- `engine`: connessione SQLAlchemy configurata con `DATABASE_URL`
- `Base`: classe base per tutti i modelli ORM
- `SessionLocal`: factory delle sessioni
- `get_db()`: dipendenza FastAPI che apre e chiude una sessione

Configurazione attuale:

```python
engine = create_engine(get_settings().database_url, pool_pre_ping=True)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)
```

`pool_pre_ping=True` verifica che una connessione del pool sia ancora attiva prima di usarla.

### Personalizzare il pool

Per un carico maggiore si possono configurare pool e timeout:

```python
engine = create_engine(
	get_settings().database_url,
	pool_pre_ping=True,
	pool_size=10,
	max_overflow=20,
	pool_timeout=30,
)
```

I valori devono essere dimensionati in base al numero di worker FastAPI e al limite massimo di connessioni PostgreSQL. Non aumentare indiscriminatamente il pool.

## 7. Modello ORM: `app/models/telemetry.py`

La classe `Telemetry` rappresenta la tabella `telemetry`:

| Campo | Tipo | Descrizione |
|---|---|---|
| `id` | intero | Chiave primaria |
| `device_id` | stringa, max 100 | Identificativo del dispositivo |
| `timestamp` | datetime con timezone | Momento della misurazione |
| `temperature` | float | Temperatura |
| `humidity` | float | Umidità |
| `pressure` | float | Pressione |
| `created_at` | datetime con timezone | Momento di inserimento |

`device_id` e `timestamp` hanno un indice per rendere più veloci i filtri e l'ordinamento.

### Personalizzare i sensori

Per aggiungere un campo, ad esempio `vibration`:

1. aggiungi la colonna al modello SQLAlchemy;
2. aggiungi il campo a `TelemetryCreate` e `TelemetryRead`;
3. aggiorna il simulatore;
4. aggiorna la dashboard;
5. in produzione crea una migrazione database.

Esempio di colonna:

```python
vibration: Mapped[float] = mapped_column(Float)
```

La chiamata `Base.metadata.create_all()` crea le tabelle mancanti, ma non gestisce in modo completo l'evoluzione di tabelle già esistenti. Per modifiche strutturali usare Alembic in una fase successiva.

## 8. Validazione Pydantic: `app/schemas/telemetry.py`

`TelemetryCreate` valida i dati in ingresso:

```python
device_id: str = Field(min_length=1, max_length=100)
temperature: float = Field(ge=-100, le=200)
humidity: float = Field(ge=0, le=100)
pressure: float = Field(ge=0, le=2000)
```

Parametri personalizzabili:

- `min_length` e `max_length`: dimensione dell'identificativo;
- `ge`: valore minimo incluso;
- `le`: valore massimo incluso.

Esempio per limitare la temperatura industriale tra `0` e `120` gradi:

```python
temperature: float = Field(ge=0, le=120)
```

I limiti Pydantic devono essere coerenti con il dominio reale e con eventuali limiti del database. Una richiesta non valida riceve HTTP `422`.

`TelemetryRead` eredita i campi di `TelemetryCreate` e aggiunge `id` e `created_at`. `from_attributes=True` consente di trasformare direttamente un oggetto SQLAlchemy nella risposta API.

## 9. Applicazione FastAPI: `app/main.py`

L'oggetto principale è:

```python
app = FastAPI(
	title="IoT Telemetry API",
	version="0.1.0",
	lifespan=lifespan,
)
```

È possibile personalizzare titolo e versione:

```python
app = FastAPI(
	title="Industrial Monitoring API",
	version="1.0.0",
	description="API per la telemetria degli impianti",
	lifespan=lifespan,
)
```

Il router viene esposto con prefisso `/api`, quindi la route definita come `/telemetry` diventa `/api/telemetry`.

Per cambiare il prefisso:

```python
app.include_router(telemetry_router, prefix="/v1")
```

In questo caso gli endpoint diventerebbero `/v1/telemetry`.

### Avvio del server

Sviluppo:

```powershell
uvicorn app.main:app --reload
```

Ascolto su tutte le interfacce e porta personalizzata:

```powershell
uvicorn app.main:app --host 0.0.0.0 --port 8080
```

`--reload` è utile in sviluppo, ma non va usato in produzione.

### Creazione delle tabelle

Nel `lifespan` viene eseguito:

```python
Base.metadata.create_all(bind=engine)
```

Questo è comodo per il prototipo. Per produzione è preferibile usare migrazioni versionate con Alembic, evitando modifiche automatiche non tracciate allo schema.

## 10. Endpoint REST: `app/api/routes/telemetry.py`

### POST `/api/telemetry`

Inserisce una misurazione:

```json
{
  "device_id": "machine-001",
  "timestamp": "2025-01-01T10:00:00Z",
  "temperature": 72.5,
  "humidity": 48.2,
  "pressure": 1014.3
}
```

Il flusso è:

1. FastAPI riceve il JSON;
2. Pydantic lo valida;
3. viene creato l'oggetto `Telemetry`;
4. SQLAlchemy esegue `commit()`;
5. l'API restituisce il record salvato.

### GET `/api/telemetry`

Restituisce i campioni ordinati dal più recente:

```text
GET /api/telemetry?limit=100
GET /api/telemetry?device_id=machine-001&limit=20
```

`limit` è compreso tra `1` e `1000`. Per cambiare questi limiti modifica:

```python
limit: int = Query(default=100, ge=1, le=1000)
```

### GET `/api/telemetry/latest`

Restituisce gli ultimi 20 record, usati dalla dashboard. Per modificare il numero di record:

```python
.limit(20)
```

È consigliabile trasformare il valore in una proprietà di `Settings` se deve essere configurabile senza modificare il codice.

### Aggiungere un filtro

Per aggiungere, ad esempio, un filtro `from_timestamp`, occorre:

1. aggiungere il parametro alla funzione;
2. applicare una condizione SQLAlchemy;
3. documentare il nuovo parametro;
4. aggiungere un test.

## 11. Simulatore: `scripts/simulator.py`

Il simulatore genera:

```python
temperature = random.gauss(70, 5)
humidity = random.uniform(35, 75)
pressure = random.gauss(1013, 8)
```

Significato:

- temperatura: distribuzione normale con media 70 e deviazione 5;
- umidità: distribuzione uniforme tra 35 e 75;
- pressione: distribuzione normale con media 1013 e deviazione 8.

### Personalizzare il simulatore

Modifica le distribuzioni in `generate_reading()`:

```python
temperature = round(random.gauss(50, 2), 2)
humidity = round(random.uniform(20, 60), 2)
pressure = round(random.gauss(1000, 4), 2)
```

Parametri da riga di comando:

```powershell
python -m scripts.simulator --api-url http://localhost:8000
python -m scripts.simulator --device-id machine-002
python -m scripts.simulator --interval 5
```

`--interval` è espresso in secondi. Il simulatore non implementa attualmente retry automatici: se l'API non è disponibile, `raise_for_status()` interrompe il processo. Per un ambiente più robusto si può aggiungere un ciclo di retry con backoff.

## 12. Dashboard Streamlit: `dashboard/streamlit_app.py`

La dashboard legge `API_URL` direttamente dall'ambiente:

```python
API_URL = os.getenv("API_URL", "http://localhost:8000")
```

Per collegarla a un'API diversa, modificare `.env` o impostare la variabile prima dell'avvio:

```powershell
$env:API_URL = "http://localhost:8080"
streamlit run dashboard/streamlit_app.py
```

La pagina è configurata così:

```python
st.set_page_config(
	page_title="IoT Telemetry",
	page_icon="📡",
	layout="wide",
)
```

È possibile cambiare titolo, icona e layout (`centered` oppure `wide`).

Il timeout della richiesta HTTP è di 5 secondi:

```python
httpx.get(url, timeout=5)
```

Aumentarlo può aiutare in una rete lenta, ma maschera eventuali problemi dell'API. La dashboard mostra gli ultimi 20 record perché questo è il limite dell'endpoint `/latest`.

Per aggiungere un grafico, includere una colonna nel DataFrame e passarla a `st.line_chart()` oppure usare componenti Streamlit più avanzati.

## 13. Dockerfile

Il `Dockerfile`:

1. parte da Python 3.12 slim;
2. imposta `/app` come directory di lavoro;
3. copia `pyproject.toml`;
4. installa il progetto;
5. copia codice API, dashboard e simulatori;
6. espone la porta 8000;
7. avvia Uvicorn.

Build e avvio:

```powershell
docker build -t iot-telemetries-api .
docker run --rm -p 8000:8000 --env-file .env iot-telemetries-api
```

Se PostgreSQL è eseguito in Docker Compose, `localhost` dentro il container API non indica il container PostgreSQL. Per una configurazione completamente containerizzata occorre usare il nome del servizio, ad esempio `postgres`, nella connection string e aggiungere l'API a `docker-compose.yml`.

## 14. Sicurezza e produzione

La configurazione attuale è adatta a sviluppo e dimostrazione. Prima della produzione considerare:

- password PostgreSQL tramite secret manager, non hardcoded;
- autenticazione e autorizzazione degli endpoint;
- HTTPS tramite reverse proxy;
- CORS configurato esplicitamente se esiste un frontend separato;
- rate limiting e limiti sulla dimensione delle richieste;
- logging strutturato e monitoraggio;
- migrazioni Alembic invece di `create_all()`;
- backup PostgreSQL;
- gestione retry e timeout per i client;
- validazione più specifica per ogni tipo di dispositivo;
- separazione dei container e utente non root;
- configurazioni diverse per sviluppo, test e produzione.

Non esporre direttamente PostgreSQL a Internet. In produzione la porta del database dovrebbe essere accessibile solo dalla rete privata dell'applicazione.

## 15. Procedura di personalizzazione consigliata

Quando si modifica il progetto, seguire questo ordine:

1. definire il nuovo requisito del sensore o del dispositivo;
2. aggiornare il modello SQLAlchemy;
3. aggiornare gli schemi Pydantic e i limiti di validazione;
4. aggiornare gli endpoint;
5. aggiornare il simulatore;
6. aggiornare la dashboard;
7. aggiungere o aggiornare i test;
8. applicare la migrazione del database;
9. verificare `/health`, inserimento e lettura dati;
10. aggiornare README e questa guida.

Dopo ogni modifica eseguire almeno:

```powershell
python -m compileall -q app dashboard scripts
```

E, se disponibili, i test:

```powershell
pytest
```

## 16. Riepilogo dei parametri principali

| Parametro | Dove si modifica | Valore attuale |
|---|---|---|
| URL PostgreSQL | `.env` / `Settings` | `localhost:5432/iot` |
| URL API dashboard | `.env` / ambiente | `http://localhost:8000` |
| Porta PostgreSQL host | `docker-compose.yml` | `5432` |
| Immagine PostgreSQL | `docker-compose.yml` | `postgres:16-alpine` |
| Numero record lista | `telemetry.py` | default 100, max 1000 |
| Numero record latest | `telemetry.py` | 20 |
| Intervallo simulatore | `simulator.py` | 2 secondi |
| Timeout simulatore | `simulator.py` | 10 secondi |
| Timeout dashboard | `streamlit_app.py` | 5 secondi |
| Limite temperatura | `schemas/telemetry.py` | -100 / 200 |
| Limite umidità | `schemas/telemetry.py` | 0 / 100 |
| Limite pressione | `schemas/telemetry.py` | 0 / 2000 |
