from garth import UserProfile, UserSettings
from garth.http import Client


def test_user_profile(authed_client: Client, load_cassette):
    load_cassette(
        authed_client,
        "tests/cassettes/test_user_profile.yaml",
    )
    profile = UserProfile.get(client=authed_client)
    assert profile.user_name


def test_user_settings(authed_client: Client, load_cassette):
    load_cassette(
        authed_client,
        "tests/cassettes/test_user_settings.yaml",
    )
    settings = UserSettings.get(client=authed_client)
    assert settings.user_data


def test_user_settings_sleep_windows(authed_client: Client, load_cassette):
    load_cassette(
        authed_client,
        "tests/cassettes/test_user_settings_sleep_windows.yaml",
    )
    settings = UserSettings.get(client=authed_client)
    assert settings.user_data
    assert isinstance(settings.user_sleep_windows, list)
    for window in settings.user_sleep_windows:
        assert hasattr(window, "sleep_window_frequency")
        assert hasattr(window, "start_sleep_time_seconds_from_midnight")
        assert hasattr(window, "end_sleep_time_seconds_from_midnight")
