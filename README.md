# garth-ng

[![PyPI version](https://img.shields.io/pypi/v/garth-ng.svg?logo=python&logoColor=brightgreen&color=brightgreen)](https://pypi.org/project/garth-ng/)
[![CI](https://github.com/cyberfossa/garth-ng/actions/workflows/ci.yml/badge.svg)](https://github.com/cyberfossa/garth-ng/actions/workflows/ci.yml)
[![Python](https://img.shields.io/pypi/pyversions/garth-ng.svg)](https://pypi.org/project/garth-ng/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://github.com/cyberfossa/garth-ng/blob/main/LICENSE)

Garmin SSO auth + Connect Python client — maintained fork of [matin/garth](https://github.com/matin/garth)

## About this fork

`garth-ng` is a maintained continuation of the original `garth` library by
[Matin Tamizi](https://github.com/matin). The original project was deprecated
after Garmin changed their auth flow. This fork restores compatibility and
continues active development. The package name changed to `garth-ng` but the
import stays `import garth` — same as Pillow keeping `from PIL import Image`.

## Migrating from garth

Both packages install into the same `site-packages/garth/` directory. You
must uninstall the original first:

```bash
pip uninstall garth
pip install garth-ng
```

Your code stays unchanged. `import garth` works exactly as before.

## Installation

```bash
pip install garth-ng
```

```bash
uv add garth-ng
```

The `garth` CLI command is included in the base install — no extras needed.

## Quick Start

### Login and save session

```python
import garth
from getpass import getpass

garth.login(input("Email: "), getpass("Password: "))
garth.save("~/.garth")
```

MFA is handled automatically with a terminal prompt. Pass a custom handler if
you need one:

```python
garth.login(email, password, prompt_mfa=lambda: input("MFA code: "))
```

### Resume a saved session

```python
import garth

garth.resume("~/.garth")
print(garth.client.username)
```

### Auto-load from environment

```bash
export GARTH_HOME=~/.garth
```

```python
import garth

print(garth.client.username)  # loaded automatically
```

Or use a base64 token (useful in CI/containers):

```bash
export GARTH_TOKEN="eyJvYXV0aF90b2tlbi..."
```

Generate a token with the CLI:

```bash
garth login
```

For China region:

```bash
garth --domain garmin.cn login
```

### Direct API calls

```python
sleep = garth.connectapi(
    f"/wellness-service/wellness/dailySleepData/{garth.client.username}",
    params={"date": "2023-07-05", "nonSleepBufferMinutes": 60},
)
```

### Stats and data

```python
# Daily steps for the last 7 days
garth.DailySteps.list(period=7)

# Stress levels
garth.DailyStress.list("2023-07-23", 2)

# Weekly HRV
garth.DailyHRV.list(period=7)

# Sleep quality
garth.DailySleep.list(period=7)
```

Available stat types: `DailySteps`, `WeeklySteps`, `DailyStress`,
`WeeklyStress`, `DailyHRV`, `DailySleep`, `DailyHydration`,
`DailyIntensityMinutes`, `WeeklyIntensityMinutes`, `DailyTrainingStatus`,
`WeeklyTrainingStatus`, `MonthlyTrainingStatus`

Available data types: `SleepData`, `HRVData`, `WeightData`, `DailyHeartRate`,
`BodyBatteryData`, `DailyBodyBatteryStress`, `DailySleepData`, `DailySummary`,
`Activity`, `FitnessActivity`, `GarminScoresData`, `TrainingReadinessData`,
`MorningTrainingReadinessData`, `BloodPressure`, `NutritionLog`,
`NutritionSettings`, `NutritionStatus`, `PersonalRecord`, `PersonalRecordType`,
`WeightGoal`, `StepsGoal`

`Activity` includes sub-endpoint methods: `details()`, `rounds()`, `exercise_sets()`,
`hr_time_in_zones()`, `map_details()`, `workouts()`, `activity_types()`

### Upload an activity

```python
with open("activity.fit", "rb") as f:
    garth.upload(f)
```

### Configuration

```python
garth.configure(domain="garmin.cn")        # China region
garth.configure(timeout=30)                # Request timeout (seconds)
garth.configure(retries=5, backoff_factor=1.0)  # Retry behavior
garth.configure(proxies={"https": "http://localhost:8888"}, ssl_verify=False)  # Proxy
```

## License

MIT. Original library by [Matin Tamizi](https://github.com/matin). Fork
maintained by [CyberFossa](https://github.com/cyberfossa).
