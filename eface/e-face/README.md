# e-face

Questo repository contiene un add-on sperimentale chiamato `e-face`: una interfaccia utente completamente personalizzata per il controllo del sistema.

Caratteristiche incluse in questa scaffolding:

- Frontend: Vue 3 + Vite (interfaccia demo con login, dashboard e impostazioni avanzate)
- Backend (opzionale): FastAPI che fornisce autenticazione token, endpoint di configurazione e serve i file statici del frontend
- Dockerfile per creare un'immagine che costruisce il frontend e avvia il backend (per test come container)
- `docker-compose.yml` per avviare in locale in modo rapido

Eseguire in locale (PowerShell):

1) Avviare il backend e frontend in sviluppo separati:

```
# nella cartella backend
python -m venv .venv; .\.venv\Scripts\Activate; pip install -r requirements.txt; uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# nella cartella frontend
cd frontend; npm install; npm run dev
```

2) Eseguire via Docker Compose (costruisce l'immagine che include frontend built):

```
docker compose build
docker compose up
```

Add-on note:
- Aggiunto `run.sh` per avviare l'API quando installato come add-on/container.
- L'add-on è pensato per essere avviato come container; se vuoi io posso adattare il `config.json` e i file di packaging per il formato esatto del tuo host add-on (fammi sapere quale piattaforma di addon usare).
Nota: questa è una scaffolding di base pensata per test e sviluppo locale. Se vuoi che impacchetti ed estenda l'addon per un ambiente di produzione/container specifico, dimmi e procedo.
