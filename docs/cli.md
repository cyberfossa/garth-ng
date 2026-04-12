# CLI Reference

`garth` ships with a command-line client for Garmin Connect. All commands
output JSON, making them easy to pipe into `jq` or other tools.

## Installation

Install with the `[cli]` extra to pull in [Typer](https://typer.tiangolo.com/):

```bash
pip install garth-ng[cli]
```

```bash
uv add garth-ng[cli]
```

!!! note "Optional dependency"
    The base `garth-ng` install does not include Typer. The CLI is only
    available when the `[cli]` extra is installed.

## Global Options

These options apply to every command and must come before the subcommand.

| Option | Short | Default | Description |
|--------|-------|---------|-------------|
| `--domain` | `-d` | `garmin.com` | Garmin Connect domain |
| `--token-dir` | | `.garth` | Directory with saved tokens |

```bash
garth --domain garmin.cn data weight list
garth --token-dir ~/.garth stats steps daily
```

## Authentication

```bash
garth login
```

Prompts for your email, password, and MFA code (if enabled). Saves tokens to
`--token-dir` and prints the session JSON to stdout.

```bash
garth --domain garmin.cn login
```

!!! tip "Generate a GARTH_TOKEN"
    Pipe the output directly into an environment variable for use in scripts
    or CI pipelines:

    ```bash
    export GARTH_TOKEN=$(garth login)
    ```

See [Getting Started](getting-started.md) for Python-based auth and full
session management options.

## Data Commands

The `data` subcommand groups all raw data retrieval from Garmin Connect. Each
data type is a further subcommand with its own `get` and/or `list` commands.

### activity

The only data type with a write command (`update`).

| Command | Arguments | Options | Description |
|---------|-----------|---------|-------------|
| `list` | | `--limit INT` (default `20`), `--start INT` (default `0`) | List activities |
| `get` | `ACTIVITY_ID` (required) | | Get a single activity |
| `update` | `ACTIVITY_ID` (required) | `--name TEXT`, `--description TEXT` | Update activity name or description |

```bash
garth data activity list --limit 5
garth data activity get 12345678
garth data activity update 12345678 --name "Morning Run"
```

!!! note "update requires at least one option"
    `--name` or `--description` must be provided; passing neither is an error.

### body-battery

| Command | Options | Description |
|---------|---------|-------------|
| `get` | `--day TEXT` (YYYY-MM-DD, defaults to today) | Get body battery for a single day |
| `list` | `--days INT` (default `7`), `--end TEXT` (YYYY-MM-DD) | List body battery readings |

```bash
garth data body-battery get --day 2024-03-15
garth data body-battery list --days 14
```

### body-battery-stress

| Command | Options | Description |
|---------|---------|-------------|
| `get` | `--day TEXT` (YYYY-MM-DD, defaults to today) | Get body battery stress for a single day |
| `list` | `--days INT` (default `7`), `--end TEXT` (YYYY-MM-DD) | List body battery stress readings |

```bash
garth data body-battery-stress list --days 7 --end 2024-03-15
```

### daily-summary

| Command | Options | Description |
|---------|---------|-------------|
| `get` | `--day TEXT` (YYYY-MM-DD, defaults to today) | Get daily summary for a single day |
| `list` | `--days INT` (default `7`), `--end TEXT` (YYYY-MM-DD) | List daily summaries |

```bash
garth data daily-summary get
garth data daily-summary list --days 30
```

### fitness-activity

List only, no `get` command.

| Command | Options | Description |
|---------|---------|-------------|
| `list` | `--days INT` (default `7`), `--end TEXT` (YYYY-MM-DD) | List fitness activities |

```bash
garth data fitness-activity list --days 14
```

### garmin-scores

| Command | Options | Description |
|---------|---------|-------------|
| `get` | `--day TEXT` (YYYY-MM-DD, defaults to today) | Get Garmin scores for a single day |
| `list` | `--days INT` (default `7`), `--end TEXT` (YYYY-MM-DD) | List Garmin scores |

```bash
garth data garmin-scores list --days 7
```

### heart-rate

| Command | Options | Description |
|---------|---------|-------------|
| `get` | `--day TEXT` (YYYY-MM-DD, defaults to today) | Get heart rate data for a single day |
| `list` | `--days INT` (default `7`), `--end TEXT` (YYYY-MM-DD) | List heart rate readings |

```bash
garth data heart-rate get --day 2024-03-15
garth data heart-rate list --days 7
```

### hrv

| Command | Options | Description |
|---------|---------|-------------|
| `get` | `--day TEXT` (YYYY-MM-DD, defaults to today) | Get HRV data for a single day |
| `list` | `--days INT` (default `7`), `--end TEXT` (YYYY-MM-DD) | List HRV readings |

```bash
garth data hrv list --days 7
```

### morning-readiness

| Command | Options | Description |
|---------|---------|-------------|
| `get` | `--day TEXT` (YYYY-MM-DD, defaults to today) | Get morning readiness for a single day |
| `list` | `--days INT` (default `7`), `--end TEXT` (YYYY-MM-DD) | List morning readiness readings |

```bash
garth data morning-readiness list
```

### sleep

| Command | Options | Description |
|---------|---------|-------------|
| `get` | `--day TEXT` (YYYY-MM-DD, defaults to today) | Get sleep data for a single night |
| `list` | `--days INT` (default `7`), `--end TEXT` (YYYY-MM-DD) | List sleep records |

```bash
garth data sleep get --day 2024-03-15
garth data sleep list --days 14
```

### sleep-detail

Detailed sleep data with configurable buffer around the sleep window.

| Command | Options | Description |
|---------|---------|-------------|
| `get` | `--day TEXT` (YYYY-MM-DD, defaults to today), `--buffer-minutes INT` (default `60`) | Get detailed sleep data for a single night |
| `list` | `--days INT` (default `7`), `--end TEXT` (YYYY-MM-DD) | List detailed sleep records |

```bash
garth data sleep-detail get
garth data sleep-detail get --day 2024-03-15 --buffer-minutes 30
garth data sleep-detail list --days 7
```

!!! tip "Buffer minutes"
    `--buffer-minutes` controls how much time before and after the detected
    sleep window is included in the movement data. The default of 60 minutes
    captures any restless periods around falling asleep or waking up.

### training-readiness

| Command | Options | Description |
|---------|---------|-------------|
| `get` | `--day TEXT` (YYYY-MM-DD, defaults to today) | Get training readiness for a single day |
| `list` | `--days INT` (default `7`), `--end TEXT` (YYYY-MM-DD) | List training readiness readings |

```bash
garth data training-readiness list --days 7
```

### weight

List only, no `get` command.

| Command | Options | Description |
|---------|---------|-------------|
| `list` | `--days INT` (default `1`), `--end TEXT` (YYYY-MM-DD) | List weight entries |

```bash
garth data weight list
garth data weight list --days 30
```

!!! tip "Default covers today only"
    `--days` defaults to `1`, returning only today's weight entry. Pass a
    larger value to retrieve a longer history.

## Stats Commands

The `stats` subcommand groups aggregated statistics. Each stat type offers
`daily`, `weekly`, and/or `monthly` granularities.

### steps

| Command | Options | Description |
|---------|---------|-------------|
| `daily` | `--days INT` (default `7`), `--end TEXT` (YYYY-MM-DD) | Daily step counts |
| `weekly` | `--days INT` (default `7`), `--end TEXT` (YYYY-MM-DD) | Weekly step totals |

```bash
garth stats steps daily --days 14
garth stats steps weekly
```

### stress

| Command | Options | Description |
|---------|---------|-------------|
| `daily` | `--days INT` (default `7`), `--end TEXT` (YYYY-MM-DD) | Daily stress levels |
| `weekly` | `--days INT` (default `7`), `--end TEXT` (YYYY-MM-DD) | Weekly stress summary |

```bash
garth stats stress daily --days 7
```

### hydration

| Command | Arguments | Options | Description |
|---------|-----------|---------|-------------|
| `daily` | | `--days INT` (default `7`), `--end TEXT` (YYYY-MM-DD) | Daily hydration levels |
| `log` | `VALUE_IN_ML` (required float) | | Log a hydration entry |

```bash
garth stats hydration daily --days 7
garth stats hydration log 500.0
```

!!! tip "Only write command in stats"
    `hydration log` is the only command in the entire `stats` group that
    writes data. All other stats commands are read-only.

### sleep (stats)

Daily granularity only.

| Command | Options | Description |
|---------|---------|-------------|
| `daily` | `--days INT` (default `7`), `--end TEXT` (YYYY-MM-DD) | Daily sleep stats |

```bash
garth stats sleep daily --days 14
```

### hrv (stats)

Daily granularity only, with a longer default window.

| Command | Options | Description |
|---------|---------|-------------|
| `daily` | `--days INT` (default `28`), `--end TEXT` (YYYY-MM-DD) | Daily HRV stats |

```bash
garth stats hrv daily
garth stats hrv daily --days 7
```

!!! tip "Default covers 4 weeks"
    `--days` defaults to `28` for HRV because meaningful trends require a
    longer baseline. A single week is often too short to detect changes.

### intensity-minutes

| Command | Options | Description |
|---------|---------|-------------|
| `daily` | `--days INT` (default `7`), `--end TEXT` (YYYY-MM-DD) | Daily intensity minutes |
| `weekly` | `--days INT` (default `7`), `--end TEXT` (YYYY-MM-DD) | Weekly intensity minutes |

```bash
garth stats intensity-minutes daily --days 30
garth stats intensity-minutes weekly
```

### training-status

Three granularities available. All use `--days` as the window size.

| Command | Options | Description |
|---------|---------|-------------|
| `daily` | `--days INT` (default `7`), `--end TEXT` (YYYY-MM-DD) | Daily training status |
| `weekly` | `--days INT` (default `7`), `--end TEXT` (YYYY-MM-DD) | Weekly training status |
| `monthly` | `--days INT` (default `7`), `--end TEXT` (YYYY-MM-DD) | Monthly training status |

```bash
garth stats training-status daily
garth stats training-status weekly --days 28
garth stats training-status monthly
```

## Users Commands

```bash
garth users profile
garth users settings
```

| Command | Description |
|---------|-------------|
| `profile` | Get user profile |
| `settings` | Get user settings |

## Direct API Access

Call any Garmin Connect API endpoint directly:

```bash
garth api PATH
```

| Option | Short | Default | Description |
|--------|-------|---------|-------------|
| `--method` | `-m` | `GET` | HTTP method |
| `--data` | | | JSON request body |

```bash
garth api /userprofile-service/userprofile/personal-information
garth api /modern/proxy/userstats-service/goals -m POST --data '{"goal": "steps"}'
```

## File Upload

Upload a `.fit` or other activity file to Garmin Connect:

```bash
garth upload PATH
```

The file at `PATH` must exist. Garth validates this before making the request.

```bash
garth upload activity.fit
garth upload ~/Downloads/morning_run.fit
```
