# StudentIQ conference deployment

This branch adds a new web experience and API without changing the existing
Streamlit app, its entry point, or the main branch.

## Architecture

- conference/website: Next.js frontend for Vercel.
- conference/api: FastAPI health and research-summary service for Render.
- Existing Streamlit application and Spark training pipeline remain in place.

## Deploy the frontend to Vercel

1. Import Sajjanthesoul/intelligent-student-performance from GitHub.
2. Select branch conference-upgrade for the conference preview.
3. Set Root Directory to conference/website.
4. Select the Next.js framework preset and build command npm run build.
5. Add NEXT_PUBLIC_API_URL with the public URL of the Render API, such as
   https://studentiq-research-api.onrender.com.
6. Deploy as a Preview first. Do not promote to production until reviewed.

## Deploy the API to Render

1. Create a new Web Service and connect this repository.
2. Select branch conference-upgrade.
3. Set Root Directory to conference/api.
4. Build command: pip install -r requirements.txt
5. Start command: uvicorn main:app --host 0.0.0.0 --port $PORT
6. Health check path: /health.
7. Set CORS_ORIGINS to the exact Vercel preview and production origins after
   those URLs are known. The included render.yaml uses a wildcard as a starter;
   replace it with trusted frontend origins before public release.

## Research integrity

The dashboard displays the committed preliminary metrics from
artifacts/model_metrics.json. They are not a newly executed benchmark.
The current Spark pipeline uses a random 80/20 split. Before conference claims,
add course-presentation holdout evaluation, repeated seeds, macro-F1,
per-class precision/recall, confusion matrices and calibration checks.

The API intentionally refuses individual predictions until a validated model
artifact and matching feature schema are implemented and deployed. Do not
substitute simulated or fabricated predictions for research results.

## Existing app safety

The current Streamlit app remains at the repository root and is not modified
by this addition. The existing main branch is unchanged by these commits.
The current Streamlit deployment remains studentiq1.streamlit.app.
