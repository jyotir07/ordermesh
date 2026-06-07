# Deployment Guide

This guide deploys the platform to a single Linux VM running the full Docker
Compose stack behind a Caddy reverse proxy with automatic HTTPS.

It targets **Oracle Cloud's "Always Free" Arm VM** (free forever, 4 cores / 24 GB
RAM), but the steps work on **any** Ubuntu VM — AWS EC2, DigitalOcean, Hetzner,
Linode, Azure, etc. Just skip Step 1 if you already have a server.

## What gets deployed

```
                 Internet
                    │  (ports 80 / 443)
                    ▼
              ┌───────────┐
              │   Caddy   │  ← automatic Let's Encrypt TLS
              └─────┬─────┘
                    ▼ (compose network)
              ┌───────────┐
              │  gateway  │  ← the only service Caddy talks to
              └─────┬─────┘
        ┌───────────┼───────────┬─────────────┐
        ▼           ▼           ▼             ▼
     order     inventory    shipping    notification
        └───────────┴───────────┴─────────────┘
                    │
        postgres · redis · rabbitmq   (private, never exposed to the host)
```

The production overlay (`docker-compose.prod.yml`) keeps Postgres, Redis,
RabbitMQ, and the gateway off the host network — only Caddy is reachable from the
internet.

---

## Step 1 — Create the free VM (Oracle Cloud)

1. Sign up at <https://cloud.oracle.com> and create a compartment/tenancy.
2. **Compute → Instances → Create Instance.**
   - **Image:** Canonical Ubuntu 24.04
   - **Shape:** `VM.Standard.A1.Flex` (Ampere/Arm) — pick **2 OCPU / 12 GB** (well
     within the Always Free allowance). The Arm shape matters: our images are
     multi-arch and build fine on Arm.
   - Add your SSH public key.
3. After it boots, note the **public IP**.
4. **Open the firewall ports.** Two layers must allow 80/443:
   - **Cloud security list / NSG:** add ingress rules for TCP **80** and **443**
     (and **22** for SSH) from `0.0.0.0/0`.
   - **OS firewall** (Oracle Ubuntu images ship with strict iptables):
     ```bash
     sudo iptables -I INPUT 6 -m state --state NEW -p tcp --dport 80 -j ACCEPT
     sudo iptables -I INPUT 6 -m state --state NEW -p tcp --dport 443 -j ACCEPT
     sudo netfilter-persistent save
     ```
   > ⚠️ Do **not** open 5432 / 6379 / 5672 / 8000 / 15672. They stay internal.

> **Any other provider:** create an Ubuntu 24.04 VM (2 GB RAM minimum, 4 GB
> comfortable), open inbound TCP 80, 443, 22, and SSH in.

---

## Step 2 — Install Docker

SSH into the VM, then:

```bash
curl -fsSL https://get.docker.com | sh
sudo usermod -aG docker "$USER"
# log out and back in so the group change takes effect
exit
```

Reconnect and verify:

```bash
docker --version
docker compose version   # must be v2.24+ for the prod overlay
```

---

## Step 3 — Get the code

```bash
git clone https://github.com/jyotir07/<your-repo>.git
cd <your-repo>
```

---

## Step 4 — Configure production secrets

Create `.env` from the example and **change every default secret**:

```bash
cp .env.example .env
nano .env
```

Set strong values (generate them with the commands below):

| Variable | What to set |
|---|---|
| `POSTGRES_PASSWORD` | a long random string |
| `RABBITMQ_DEFAULT_PASS` | a long random string |
| `RABBITMQ_URL` | must contain the same user/password as above |
| `JWT_SECRET` | a long random string (see command below) |
| `SITE_ADDRESS` | your domain, e.g. `api.example.com` — or `:80` if IP-only |

Generate secrets:

```bash
python3 -c "import secrets; print(secrets.token_urlsafe(48))"   # run once per secret
```

> `SITE_ADDRESS` is new in the prod overlay. Add it to `.env`:
> - **With a domain:** `SITE_ADDRESS=api.example.com` → Caddy auto-issues a free
>   Let's Encrypt certificate (HTTPS).
> - **IP only (no domain):** `SITE_ADDRESS=:80` → plain HTTP on the public IP.

Keep the internal URLs (`ORDER_SERVICE_URL=http://order:8000`, etc.) and
`POSTGRES_HOST=postgres` as-is — those are compose-network names.

---

## Step 5 — (Optional) Point a domain at the VM

HTTPS needs a domain. A **free** option:

- **DuckDNS** (<https://duckdns.org>): sign in, create a subdomain
  (e.g. `mylogistics.duckdns.org`), set its IP to your VM's public IP.
- Then set `SITE_ADDRESS=mylogistics.duckdns.org` in `.env`.

Any registrar works too — just create an **A record** pointing at the VM IP.
Wait for DNS to propagate (a minute or two) before the next step so Caddy can
validate the certificate.

---

## Step 6 — Deploy

```bash
chmod +x deploy.sh
./deploy.sh
```

This builds the images, runs each service's Alembic migrations, and starts the
full stack with the production overlay. First build takes a few minutes on Arm.

Check status:

```bash
docker compose -f docker-compose.yml -f docker-compose.prod.yml ps
```

All services should be `running`/`healthy`.

---

## Step 7 — Verify it's live

Replace `<host>` with your domain (https) or `http://<ip>`:

```bash
# Interactive API docs
open https://<host>/docs        # or just visit it in a browser

# Register an admin and a customer
curl -X POST https://<host>/auth/register \
  -H 'Content-Type: application/json' \
  -d '{"email":"admin@x.com","password":"secret123","role":"ADMIN"}'

curl -X POST https://<host>/auth/register \
  -H 'Content-Type: application/json' \
  -d '{"email":"cust@x.com","password":"secret123","role":"CUSTOMER"}'

# Log in to get a JWT
curl -X POST https://<host>/auth/login \
  -H 'Content-Type: application/json' \
  -d '{"email":"cust@x.com","password":"secret123"}'
```

Then exercise the full flow (seed a product as admin → place an order as the
customer → watch it move PENDING → CONFIRMED → SHIPPED). See the README's
end-to-end walkthrough for the exact requests.

---

## Updating after a code change

Push to your repo, then on the VM:

```bash
./deploy.sh
```

It pulls, rebuilds, re-runs migrations, and restarts changed services. Data
persists in the `pgdata` volume across deploys.

---

## Operations cheat sheet

```bash
# from the repo root on the VM
COMPOSE="docker compose -f docker-compose.yml -f docker-compose.prod.yml"

$COMPOSE ps                 # status
$COMPOSE logs -f gateway    # follow one service's logs
$COMPOSE logs -f            # follow everything
$COMPOSE restart order      # restart a single service
$COMPOSE down               # stop the stack (keeps the database volume)
$COMPOSE down -v            # stop AND wipe all data (Postgres volume)
```

**Reach the RabbitMQ management UI** (kept private) via an SSH tunnel from your
laptop:

```bash
ssh -L 15672:localhost:15672 ubuntu@<vm-ip>
# then temporarily publish it, or exec rabbitmqctl inside the container
```

---

## Security checklist

- [ ] Every secret in `.env` changed from its default
- [ ] Cloud security list **and** OS firewall allow only 22 / 80 / 443
- [ ] `.env` is git-ignored (it already is) and never committed
- [ ] Using a domain + HTTPS for anything beyond a throwaway demo
- [ ] SSH locked to key-based auth (disable password login)

---

## Troubleshooting

| Symptom | Fix |
|---|---|
| `docker compose` rejects `!reset` | Compose too old; reinstall via `get.docker.com` (needs v2.24+). |
| Caddy can't get a certificate | DNS not pointing at the VM yet, or ports 80/443 blocked in the cloud security list / OS firewall. |
| Site loads on `:8000` but not 80/443 | You ran the base file only — include `-f docker-compose.prod.yml` (use `deploy.sh`). |
| A service restarts repeatedly | `…logs -f <service>` — usually a bad `DATABASE_URL`/`RABBITMQ_URL` in `.env`. |
| Build is slow / OOM on a tiny VM | Use a VM with ≥ 2 GB RAM, or add swap. |
