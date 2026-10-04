# Object Storage Setup — GeoAI on Render

Generated GLB/PDF files **must** live outside Render’s ephemeral disk. This app uses **S3-compatible storage** via boto3 (AWS S3, Cloudflare R2, or MinIO).

After setup, verify:

```bash
curl https://geoai-api-91oc.onrender.com/api/system/status
# expect: "storage_mode": "s3"
# expect: no critical "local_storage" warning
```

---

## Recommendation: Cloudflare R2

| | **Cloudflare R2** | **AWS S3** |
|---|-------------------|------------|
| Egress fees | Free | Paid (can add up for 3D GLB downloads) |
| Setup complexity | Low | Medium (IAM + bucket policy) |
| Render region | Works globally | Prefer `us-west-2` (near Render Oregon) |
| Free tier | 10 GB storage / month | 5 GB (12 months) |

**Use R2** unless you already run everything on AWS.

---

## Option A — Cloudflare R2 (recommended)

### 1. Create bucket

1. [Cloudflare Dashboard](https://dash.cloudflare.com) → **R2** → **Create bucket**
2. Name: `geoai-files` (or any name — match `S3_BUCKET` below)
3. Location: **Automatic** or **US** (Render Oregon is `us-west`)

### 2. Create API token

1. R2 → **Manage R2 API Tokens** → **Create API token**
2. Permissions: **Object Read & Write** on your bucket (or Admin Read & Write for simplicity)
3. Copy **Access Key ID** and **Secret Access Key** (secret shown once)

### 3. CORS (required for 3D GLB in browser)

R2 bucket → **Settings** → **CORS policy** → add:

```json
[
  {
    "AllowedOrigins": [
      "https://flourishing-mochi-432285.netlify.app",
      "http://localhost:3000"
    ],
    "AllowedMethods": ["GET", "HEAD"],
    "AllowedHeaders": ["*"],
    "ExposeHeaders": ["ETag"],
    "MaxAgeSeconds": 3600
  }
]
```

Add your custom domain later if you add one.

### 4. Render env vars

In Render → **Environment Groups** → `geoai-backend` (applies to **geoai-api** + **geoai-worker**):

| Key | Value |
|-----|--------|
| `S3_ENDPOINT` | `https://<ACCOUNT_ID>.r2.cloudflarestorage.com` |
| `S3_BUCKET` | `geoai-files` |
| `S3_ACCESS_KEY` | R2 access key ID |
| `S3_SECRET_KEY` | R2 secret access key |
| `S3_REGION` | `auto` |
| `PUBLIC_API_URL` | `https://geoai-api-91oc.onrender.com` |

Find `<ACCOUNT_ID>` in R2 overview (“Account ID”) or the endpoint shown when creating the token.

**Do not set** `S3_ENDPOINT` empty for R2 — it is required.

### 5. Redeploy

Save env vars → **Manual Deploy** both **geoai-api** and **geoai-worker** (or wait for auto-deploy).

Check logs for: `Using S3 storage (https://...r2.cloudflarestorage.com, bucket=geoai-files)`

---

## Option B — AWS S3

### 1. Create bucket

1. AWS Console → **S3** → **Create bucket**
2. Name: `geoai-files-prod` (globally unique)
3. Region: **US West (Oregon) `us-west-2`** (same region as Render)
4. Block public access: **On** (app uses presigned URLs — no public bucket needed)

### 2. IAM user for Render

1. **IAM** → **Users** → **Create user** → `geoai-render-storage`
2. Attach inline policy (replace bucket name):

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": ["s3:PutObject", "s3:GetObject", "s3:HeadBucket", "s3:ListBucket"],
      "Resource": [
        "arn:aws:s3:::geoai-files-prod",
        "arn:aws:s3:::geoai-files-prod/*"
      ]
    }
  ]
}
```

3. **Security credentials** → **Create access key** → Application running outside AWS
4. Copy Access Key ID + Secret

### 3. CORS on bucket

S3 bucket → **Permissions** → **CORS**:

```json
[
  {
    "AllowedHeaders": ["*"],
    "AllowedMethods": ["GET", "HEAD"],
    "AllowedOrigins": [
      "https://flourishing-mochi-432285.netlify.app",
      "http://localhost:3000"
    ],
    "ExposeHeaders": ["ETag"],
    "MaxAgeSeconds": 3600
  }
]
```

### 4. Render env vars

| Key | Value |
|-----|--------|
| `S3_BUCKET` | `geoai-files-prod` |
| `S3_ACCESS_KEY` | IAM access key ID |
| `S3_SECRET_KEY` | IAM secret |
| `S3_REGION` | **Must match bucket region** — e.g. `us-west-2` (Oregon) or `eu-north-1` (Stockholm) |
| `PUBLIC_API_URL` | `https://geoai-api-91oc.onrender.com` |

**Leave `S3_ENDPOINT` unset** for native AWS S3.

### 5. Redeploy

Same as R2 — redeploy API + worker after saving vars.

---

## Verify end-to-end

```bash
# 1. Storage mode
curl -s https://geoai-api-91oc.onrender.com/api/system/status | jq '.storage_mode, .production.warnings'

# 2. Full smoke (register → generate → model URL)
python backend/scripts/production_smoke.py --base-url https://geoai-api-91oc.onrender.com
```

In the app:

1. Log in on Netlify
2. Create or open a project → **AI Studio** → generate design
3. Open **3D Model** — GLB should load (presigned R2/S3 URL in Network tab)

---

## Troubleshooting

| Symptom | Fix |
|---------|-----|
| `storage_mode: local` in status | Check all `S3_*` vars on **both** API and worker; redeploy; read Render logs for `S3 unreachable` |
| GLB 404 in browser | CORS on bucket; regenerate design after S3 was enabled |
| Smoke: model URL 404 | Old jobs used local disk — run a **new** generation after S3 is live |
| `S3 bucket not found` (AWS) | Create bucket in console first; match `S3_BUCKET` and `S3_REGION` |
| Worker saves but API can’t read | Both services must share the **same** env group / S3 credentials |

---

## Local dev (MinIO)

Docker Compose already includes MinIO. From repo root:

```bash
docker compose up -d
```

`.env`:

```env
S3_ENDPOINT=http://localhost:9000
S3_BUCKET=geoai-files
S3_ACCESS_KEY=geoai
S3_SECRET_KEY=geoai-secret
```

MinIO console: http://localhost:9001
