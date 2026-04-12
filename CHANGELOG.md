# Changelog

## [1.1.0](https://github.com/cyberfossa/garth-ng/compare/v1.0.0...v1.1.0) (2026-04-12)


### Features

* **cli:** replace Click with Typer-based CLI ([#19](https://github.com/cyberfossa/garth-ng/issues/19)) ([9200f1f](https://github.com/cyberfossa/garth-ng/commit/9200f1ff19a747581bdfe6c4f590f3a06acca3ba))
* **weight:** add body composition FIT upload ([#12](https://github.com/cyberfossa/garth-ng/issues/12)) ([44eb681](https://github.com/cyberfossa/garth-ng/commit/44eb681bc2a86afe25f6faa9bf4e6a57811f6fcd))


### Bug Fixes

* **data:** make rem_sleep_data optional in DailySleepData ([#21](https://github.com/cyberfossa/garth-ng/issues/21)) ([2611b6a](https://github.com/cyberfossa/garth-ng/commit/2611b6a0e1b9a2da2702da56dd7eee288b1e31a8))
* **lint:** exclude auto-generated CHANGELOG from markdownlint ([#16](https://github.com/cyberfossa/garth-ng/issues/16)) ([2c025c4](https://github.com/cyberfossa/garth-ng/commit/2c025c48ae9b59fa45dcd5f4f983427cf3e24e90))
* **users:** widen Pydantic types for UserProfile and UserSettings ([#22](https://github.com/cyberfossa/garth-ng/issues/22)) ([fedd1e5](https://github.com/cyberfossa/garth-ng/commit/fedd1e5a7a7833384c7518fb6178a812defa6672))

## [1.0.0](https://github.com/cyberfossa/garth-ng/compare/v1.0.0-alpha.2...v1.0.0) (2026-04-11)


### Features

* `Activity` dataclass ([#87](https://github.com/cyberfossa/garth-ng/issues/87)) ([8028441](https://github.com/cyberfossa/garth-ng/commit/8028441390b9b596edf9524f3b954da772d5ea7e))
* can resume and dump from string ([#5](https://github.com/cyberfossa/garth-ng/issues/5)) ([b36caec](https://github.com/cyberfossa/garth-ng/commit/b36caec3b4dffed0430eaa381bc6f7554a63e842))
* **ci:** unified release workflow, GitHub Pages docs, CI concurrency ([#7](https://github.com/cyberfossa/garth-ng/issues/7)) ([af5b916](https://github.com/cyberfossa/garth-ng/commit/af5b9166cb91ce591b95108a53502158d055000c))
* **data:** add Weight.create() and Weight.delete() methods ([#6](https://github.com/cyberfossa/garth-ng/issues/6)) ([a675052](https://github.com/cyberfossa/garth-ng/commit/a6750522f66a6e195f02bde9fb193032a7e253c7))


### Bug Fixes

* 69 by making profile_image_uuid nullable ([#80](https://github.com/cyberfossa/garth-ng/issues/80)) ([de386a5](https://github.com/cyberfossa/garth-ng/commit/de386a575adb564aa9b7dfbd294b7470804913f5))
* **ci:** switch to semver prerelease format for release-please compatibility ([#9](https://github.com/cyberfossa/garth-ng/issues/9)) ([1cb0f8d](https://github.com/cyberfossa/garth-ng/commit/1cb0f8d3329d53869f8fe2c4ba392efce16ec640))
* **data:** resolve ty check warnings, clean up pyproject.toml ([#4](https://github.com/cyberfossa/garth-ng/issues/4)) ([26aa20a](https://github.com/cyberfossa/garth-ng/commit/26aa20aebda83bd5e6f5851f1f5a0e4a2faef7c5))
* **http:** use CurlMime multipart for upload instead of unsupported files= ([#11](https://github.com/cyberfossa/garth-ng/issues/11)) ([6a8205d](https://github.com/cyberfossa/garth-ng/commit/6a8205daa9020e6812eb26cdfff70d6cf01ce565))
* Sometimes weight_delta is None ([#189](https://github.com/cyberfossa/garth-ng/issues/189)) ([fa5f3b0](https://github.com/cyberfossa/garth-ng/commit/fa5f3b07fe2f09a928e9b1cc93d1eda0f969ffc5))


### Refactoring

* date defaults to today when not provided ([#166](https://github.com/cyberfossa/garth-ng/issues/166)) ([c5d253c](https://github.com/cyberfossa/garth-ng/commit/c5d253ceb9a1e79f1c710564d51a120a30b335fc))
* replace dynamic version with importlib.metadata ([#15](https://github.com/cyberfossa/garth-ng/issues/15)) ([a2eb02f](https://github.com/cyberfossa/garth-ng/commit/a2eb02fc14fafa1d92bf5bf08e45127efe0094db))
* **sso:** replace requests+OAuth1 with curl_cffi+DI-OAuth2, Strategy pattern ([#3](https://github.com/cyberfossa/garth-ng/issues/3)) ([bde876a](https://github.com/cyberfossa/garth-ng/commit/bde876a20197cfa350960f98bd0615856b8031fe))


### Chores

* **release:** switch to stable versioning ([#13](https://github.com/cyberfossa/garth-ng/issues/13)) ([9c26ce4](https://github.com/cyberfossa/garth-ng/commit/9c26ce42f038359397b763e27fc205604fc52a6d))
