# PostgreSQL Setup Guide

Complete setup instructions for **macOS**, **Windows**, and **Linux (Ubuntu/Debian)**.

---

## What this project expects

- PostgreSQL 14+ running locally or on a reachable remote host
- A database named `tribot`
- A PostgreSQL role the app can log in with
- That role has permission to create and use tables in the `public` schema

The app creates all tables automatically on startup from `app/data/schema.sql` and `app/data/migrations.sql`. You do not need to run any SQL manually once the database and role exist.

---

## macOS

### 1. Install PostgreSQL

**Option A — Homebrew (recommended)**

```bash
brew install postgresql@15
brew services start postgresql@15
```

Add it to your PATH (add this to `~/.zshrc` or `~/.bash_profile`):

```bash
export PATH="/opt/homebrew/opt/postgresql@15/bin:$PATH"
```

Then reload:

```bash
source ~/.zshrc
```

**Option B — Postgres.app**

Download from [https://postgresapp.com](https://postgresapp.com), open it, and click **Initialize**. Add the CLI tools to your PATH as shown on their site.

### 2. Verify it is running

```bash
pg_isready -h localhost -p 5432
```

Expected output:
```
localhost:5432 - accepting connections
```

### 3. Open a psql shell

```bash
psql -U "$(whoami)" postgres
```

> On Homebrew installs the default superuser is your macOS username, not `postgres`.

### 4. Create the database and user

```sql
CREATE DATABASE tribot;
CREATE USER tribot_user WITH PASSWORD 'change-this-password';
GRANT ALL PRIVILEGES ON DATABASE tribot TO tribot_user;
\q
```

### 5. Grant schema permissions

```bash
psql -h localhost -U "$(whoami)" -d tribot
```

```sql
GRANT ALL ON SCHEMA public TO tribot_user;
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO tribot_user;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO tribot_user;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON TABLES TO tribot_user;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON SEQUENCES TO tribot_user;
\q
```

---

## Windows

### 1. Install PostgreSQL

Download the installer from [https://www.postgresql.org/download/windows](https://www.postgresql.org/download/windows)

During setup:
- Set a password for the `postgres` superuser — remember it
- Keep the default port `5432`
- Keep the default locale

After install, **pgAdmin** and the `psql` CLI are both available from the Start menu.

### 2. Open a psql shell

Open **SQL Shell (psql)** from the Start menu, or use:

```cmd
"C:\Program Files\PostgreSQL\15\bin\psql.exe" -U postgres -h localhost
```

Enter the password you set during installation.

### 3. Create the database and user

```sql
CREATE DATABASE tribot;
CREATE USER tribot_user WITH PASSWORD 'change-this-password';
GRANT ALL PRIVILEGES ON DATABASE tribot TO tribot_user;
\q
```

### 4. Grant schema permissions

```cmd
"C:\Program Files\PostgreSQL\15\bin\psql.exe" -U postgres -h localhost -d tribot
```

```sql
GRANT ALL ON SCHEMA public TO tribot_user;
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO tribot_user;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO tribot_user;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON TABLES TO tribot_user;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON SEQUENCES TO tribot_user;
\q
```

### 5. Verify it is running

```cmd
"C:\Program Files\PostgreSQL\15\bin\pg_isready.exe" -h localhost -p 5432
```

Expected output:
```
localhost:5432 - accepting connections
```

> **Note for Windows users:** Use `python` instead of `python3`, and use `py -m venv .venv` + `.venv\Scripts\activate` to activate the virtual environment.

---

## Linux (Ubuntu / Debian)

### 1. Install PostgreSQL

```bash
sudo apt-get update
sudo apt-get install -y postgresql postgresql-contrib
sudo systemctl enable postgresql
sudo systemctl start postgresql
```

### 2. Verify it is running

```bash
pg_isready -h localhost -p 5432
```

### 3. Open a psql shell

```bash
sudo -u postgres psql
```

### 4. Create the database and user

```sql
CREATE DATABASE tribot;
CREATE USER tribot_user WITH PASSWORD 'change-this-password';
GRANT ALL PRIVILEGES ON DATABASE tribot TO tribot_user;
\q
```

### 5. Grant schema permissions

```bash
sudo -u postgres psql -d tribot
```

```sql
GRANT ALL ON SCHEMA public TO tribot_user;
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO tribot_user;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO tribot_user;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON TABLES TO tribot_user;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON SEQUENCES TO tribot_user;
\q
```

---

## Configure the .env file (all platforms)

```bash
cp .env.example .env
```

Set these values in `.env`:

```env
DB_HOST=localhost
DB_PORT=5432
DB_NAME=tribot
DB_USER=tribot_user
DB_PASSWORD=change-this-password
```

---

## Install dependencies and start the server (all platforms)

**macOS / Linux:**

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
GLOG_minloglevel=3 uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

**Windows (Command Prompt):**

```cmd
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
set GLOG_minloglevel=3
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

**Windows (PowerShell):**

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
$env:GLOG_minloglevel = "3"
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

### Verify the server is working

```bash
curl http://127.0.0.1:8000/api/v1/health
```

Expected:
```json
{"status": "ok", "app_name": "TRIBOT Backend API", "version": "0.1.0"}
```

---

## Remote PostgreSQL (any platform)

If you prefer a hosted database (e.g. Supabase, Railway, Neon, AWS RDS), only change these values in `.env`:

```env
DB_HOST=your-remote-host
DB_PORT=5432
DB_NAME=your-database-name
DB_USER=your-database-user
DB_PASSWORD=your-database-password
```

The remote role still needs permission to create tables in the target schema.

---

## Common problems

### `role "postgres" does not exist` (macOS)

On Homebrew installs the default superuser is your macOS username, not `postgres`. Use:

```bash
psql -U "$(whoami)" postgres
```

### `database "tribot" does not exist`

Run `CREATE DATABASE tribot;` inside psql as a superuser.

### `password authentication failed`

- Check `DB_USER` and `DB_PASSWORD` in `.env`
- Test directly: `psql -h localhost -U tribot_user -d tribot -W`

### `permission denied for schema public`

Re-run the schema grants from step 5 (above) using a superuser account.

### `connection refused`

- Check PostgreSQL is running: `pg_isready -h localhost -p 5432`
- Check the port in `.env` matches your PostgreSQL port (default `5432`)

### Windows: `psql is not recognized`

Add the PostgreSQL `bin` directory to your system PATH:
`C:\Program Files\PostgreSQL\15\bin`

### Windows: virtual environment activation blocked by execution policy

```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

Then activate again:

```powershell
.venv\Scripts\Activate.ps1
```
