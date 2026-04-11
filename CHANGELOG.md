# Changelog

## [1.0.0-alpha.3](https://github.com/cyberfossa/garth-ng/compare/v1.0.0-alpha.2...v1.0.0-alpha.3) (2026-04-11)


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
* **sso:** replace requests+OAuth1 with curl_cffi+DI-OAuth2, Strategy pattern ([#3](https://github.com/cyberfossa/garth-ng/issues/3)) ([bde876a](https://github.com/cyberfossa/garth-ng/commit/bde876a20197cfa350960f98bd0615856b8031fe))
