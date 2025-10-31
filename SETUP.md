Setup and quick run (Windows PowerShell)

1. Create & activate virtualenv

```powershell
cd "C:\Users\LENOVO\Downloads\Data-20250917T054840Z-1-005\Data\Practice\CRM.Api-main\CRM.Api-main"
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

2. Install dependencies

```powershell
pip install -r requirements.txt
```

3. Start the server (module may be `app.main:app`)

```powershell
uvicorn app.main:app --reload --host 127.0.0.1 --port 8006
```

4. Generate a JWT without hitting the API (uses `.env` when present)

```powershell
python scripts/generate_token.py --sub admin --minutes 30
```

Notes
- If the app relies on additional services (MongoDB), ensure connection strings are correct in `.env`.
- If you get import errors, install the missing package into the `.venv`.
