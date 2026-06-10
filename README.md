# datagovuk-sandbox

This is a Flask app I've been using as a prototyping space for data.gov.uk ideas. It started as a visualisation playground, but I've now wired it up to run on AWS ECS Fargate with a proper CI and deploy pipeline — so anything merged to `main` gets automatically tested and deployed to AWS.

---

## Running it locally

> [!Important]
> I run everything through Docker so we all get the same environment. Don't run `uv sync`, `uv add`, or `flask` directly on your machine — use the `just` commands below instead.

### What you need

- Docker Desktop (or something compatible)
- [`just`](https://just.systems/) — if you haven't got it: `brew install just`

### Getting started

```bash
git clone https://github.com/alphagov/datagovuk-sandbox
cd datagovuk-sandbox
cp example.flaskenv .flaskenv
just serve
```

Once it's up, the app is at http://localhost:5050.

### `just` commands I use

| Command | What it does |
|---|---|
| `just serve` | Builds the image and starts the full stack |
| `just shell` | Opens a bash shell inside the running web container |
| `just add <package>` | Adds a Python package via `uv add` (stack needs to be running first) |

---

## How to contribute

I keep `main` protected — please don't push directly to it. The flow is:

1. Branch off main: `git checkout -b feature/DGUK-XXX-short-description`
2. Make your changes
3. Push and open a PR
4. CI has to pass before anything can merge (see below)

---

## CI — what runs on every PR

I've set up a CI workflow (`.github/workflows/ci.yml`) that runs on every pull request and every push to `main`. It does three things:

| Check | Tool | What it's catching |
|---|---|---|
| Lint | `ruff check .` | Code errors and style problems |
| Format | `ruff format --check .` | Inconsistent formatting |
| Tests | `pytest tests/ -v` | Anything broken |

If you want to run the same checks locally before pushing:

```bash
uv run ruff check .
uv run ruff format --check .
uv run pytest tests/ -v
```

---

## Deployment — how it gets to AWS

I've set up a deploy workflow (`.github/workflows/deploy.yml`) that fires automatically whenever something merges to `main`. Here's what it does:

1. Authenticates to AWS using GitHub OIDC — I'm not storing any credentials in GitHub Secrets, it uses a short-lived token instead
2. Builds the Docker image from `docker/Dockerfile`
3. Tags it with the git commit SHA and pushes it to our ECR registry — every deploy is traceable to an exact commit
4. Downloads the current ECS task definition from AWS, swaps in the new image tag
5. Registers the updated task definition and tells ECS to deploy it
6. Waits until ECS confirms the new container is healthy before finishing

I deliberately don't push a `latest` tag — ECR has immutable tags turned on so you can't overwrite an existing one anyway, and using the SHA means we always know exactly what's running.

### AWS resources

| Resource | Value |
|---|---|
| AWS account | `gds-ndl-test` — `525320085442` |
| Region | `eu-west-2` (London) |
| ECS cluster | `test` |
| ECS service | `datagovuk-sandbox` |
| ECR registry | `525320085442.dkr.ecr.eu-west-2.amazonaws.com/datagovuk-sandbox` |
| RDS (PostgreSQL 16) | `test-postgres.clwmgus4m1tq.eu-west-2.rds.amazonaws.com:5432` |
| Container logs | CloudWatch — `/ecs/test/datagovuk-sandbox` |

The app runs in a private subnet and connects to RDS using IAM authentication — no hardcoded passwords anywhere. All the underlying infrastructure (VPC, ECS cluster, RDS, ECR, IAM roles) is managed in Terraform over in the [`datagovuk-infrastructure`](https://github.com/alphagov/datagovuk-infrastructure) repo.

---

## Site checks for data.gov.uk

There's also a separate set of scripts in `scripts/` that check URLs on the data.gov.uk collection pages. They pull the list of URLs from the [datagovuk_find](https://github.com/alphagov/datagovuk_find) repo and use Playwright to verify each one is live and actually appears on the right page.

These run automatically every day at 6am via `.github/workflows/check-collection-urls.yml` and commit the results back to the repo. I wouldn't bother running them locally — just trigger a manual run from the Actions tab in GitHub if you need a fresh check.

### If you do want to run them locally

```bash
# Pull the collection URLs from the datagovuk_find repo
uv run python -m scripts.cli get-collection-urls

# Check each URL is reachable and present on the collection page
uv run python -m scripts.cli check-urls

# Flag any URLs that are missing link text
uv run python -m scripts.cli check-link-text
```

### What's in the results CSV

Results land in `testing/results/collection-check-<timestamp>.csv`:

| Column | What it means |
|---|---|
| `collection` | Collection name (e.g. `environment`) |
| `slug` | URL path segment on data.gov.uk |
| `url` | The URL being checked |
| `link-text` | The display text for the link |
| `type` | `website`, `api`, or `dataset` |
| `on-page` | Whether the URL appeared as a link on the collection page |
| `reachable` | Whether the URL loaded successfully in the browser |
