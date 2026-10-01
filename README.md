# Loan Register Cleaner
Backend: FastAPI (Python). Frontend: Next.js. Rules = deterministic; RAG = review-step suggestions only.

## Run
    cd backend && pip install -r requirements.txt && uvicorn app.main:app --reload      # :8000
    npx create-next-app@latest frontend --ts --app --no-tailwind --src-dir=false --import-alias "@/*"
    cp -r frontend-src/* frontend/ && cd frontend && npm run dev                          # :3000
    python backend/test_sample.py <your.xlsx>                                              # API smoke test


## New branch / vendor
Add a `Tenant` in backend/app/config.py (branches, header aliases, date order, brand) and upload with ?tenant=<name>.
