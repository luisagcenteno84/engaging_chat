# GCP Deployment (Free Tier)

## Prereqs
- GCP project created
- `gcloud` and `firebase` CLI installed and authenticated
- Firestore enabled in Native mode
- Secret Manager enabled

## Free-Tier Guardrails (Recommended)
- Keep Cloud Run min instances at 0 to avoid paying for idle instances.
- Consider setting a max instances cap to limit surprise scaling costs (e.g., `--max 1` while testing).
- Default Cloud Run concurrency is 80 requests per instance; lower it only if your app cannot handle parallel requests.
- Cloud Run free tier (request-based billing) includes 2M requests, 180k vCPU-seconds, and 360k GiB-seconds per month (plus limited egress).
- Firestore free tier includes 1 GiB storage, 50k reads/day, 20k writes/day, 20k deletes/day, and 10 GiB egress/month (one free database per project; quotas reset daily).
- Cloud Build includes 2,500 free build-minutes per month on the default pool.

## Backend (Cloud Run)

1. Set env vars and secrets:

```bash
gcloud config set project YOUR_PROJECT_ID

gcloud secrets create gemini-api-key --data-file=- <<EOF
YOUR_GEMINI_API_KEY
EOF
```

2. Create an Artifact Registry repo (recommended) and build the container:

```bash
gcloud artifacts repositories create engagingchat \
  --repository-format=docker \
  --location=us-west4 \
  --description="EngagingChat images"

gcloud builds submit --tag us-west4-docker.pkg.dev/YOUR_PROJECT_ID/engagingchat/engagingchat-api backend
```

3. Deploy with free-tier friendly settings:

```bash
gcloud run deploy engagingchat-api \
  --image us-west4-docker.pkg.dev/YOUR_PROJECT_ID/engagingchat/engagingchat-api \
  --platform managed \
  --region us-west4 \
  --allow-unauthenticated \
  --min 0 \
  --max 1 \
  --set-env-vars APP_ENV=prod,PROJECT_ID=YOUR_PROJECT_ID,LLM_PROVIDER=gemini,GEMINI_MODEL=gemini-2.5-flash,ALLOW_GUEST=true \
  --set-secrets GEMINI_API_KEY=gemini-api-key:latest
```

If you need more capacity, raise `--max` and consider leaving `--min` at `0` to avoid idle charges.

4. Note the Cloud Run URL and use it in the frontend `API_URL`.


## Frontend (Cloud Run)

1. Build and deploy the Streamlit frontend image:

```bash
gcloud builds submit --tag us-west4-docker.pkg.dev/YOUR_PROJECT_ID/engagingchat/engagingchat-frontend frontend_streamlit

gcloud run deploy engagingchat-ui   --image us-west4-docker.pkg.dev/YOUR_PROJECT_ID/engagingchat/engagingchat-frontend   --platform managed   --region us-west4   --allow-unauthenticated   --min 0   --max 1   --set-env-vars API_URL=YOUR_BACKEND_URL
```
## Firestore Security (dev-friendly)
For a quick start, restrict to the app server with IAM. Keep Firestore rules minimal and rely on server-side access.

## Notes
- Keep Gemini API key in Secret Manager only.
- Frontend never accesses the LLM directly.
- Cloud Run deploy expects an Artifact Registry image URL like `us-west4-docker.pkg.dev/PROJECT_ID/REPO_NAME/IMAGE:TAG`.


## Cloud Build (Auto Deploy)

This repo includes two Cloud Build configs:
- `C:\git\engaging_chat\deploy\cloudbuild-backend.yaml` for the FastAPI backend
- `C:\git\engaging_chat\deploy\cloudbuild-frontend.yaml` for the Streamlit frontend

### One-time setup
1. Create an Artifact Registry repo (if you don't already have one):

```bash
gcloud artifacts repositories create engagingchat \
  --repository-format=docker \
  --location=us-west4 \
  --description="EngagingChat images"
```

2. Store the Gemini API key in Secret Manager:

```bash
gcloud secrets create gemini-api-key --data-file=- <<EOF
YOUR_GEMINI_API_KEY
EOF
```

3. Create two Cloud Build triggers (GitHub / repo-connected):
- **Backend trigger**:
  - Build config: `deploy/cloudbuild-backend.yaml`
  - Included files: `backend/**`, `deploy/cloudbuild-backend.yaml`
- **Frontend trigger**:
  - Build config: `deploy/cloudbuild-frontend.yaml`
  - Included files: `frontend_streamlit/**`, `deploy/cloudbuild-frontend.yaml`
  - Set substitution `_API_URL` to your backend Cloud Run URL

### Manual build (optional)
You can also run builds manually:

```bash
gcloud builds submit --config deploy/cloudbuild-backend.yaml .
gcloud builds submit --config deploy/cloudbuild-frontend.yaml .
```

## No-cost note
You can stay within free tiers by keeping `--min 0`, low traffic, and small images, but **no cost is guaranteed**. Set a budget + alert in Billing to avoid surprises.

