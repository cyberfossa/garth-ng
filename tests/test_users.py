from garth import UserProfile, UserSettings
from garth.http import Client
from garth.users.settings import FirstDayOfWeek, PowerFormat, UserData


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


def test_user_profile_motivation_types():
    """Test UserProfile accepts motivation/other_motivation as int, str, or
    None."""
    base = dict(
        id=1,
        profile_id=1,
        garmin_guid="guid",
        display_name="d",
        full_name="f",
        user_name="u",
        profile_image_type=None,
        profile_image_url_large=None,
        profile_image_url_medium=None,
        profile_image_url_small=None,
        location=None,
        facebook_url=None,
        twitter_url=None,
        personal_website=None,
        bio=None,
        primary_activity=None,
        favorite_activity_types=[],
        running_training_speed=0.0,
        cycling_training_speed=0.0,
        favorite_cycling_activity_types=[],
        cycling_classification=None,
        cycling_max_avg_power=0.0,
        swimming_training_speed=0.0,
        profile_visibility="p",
        activity_start_visibility="p",
        activity_map_visibility="p",
        course_visibility="p",
        activity_heart_rate_visibility="p",
        activity_power_visibility="p",
        badge_visibility="p",
        show_age=False,
        show_weight=False,
        show_height=False,
        show_weight_class=False,
        show_age_range=False,
        show_gender=False,
        show_activity_class=False,
        show_vo_2_max=False,
        show_personal_records=False,
        show_last_12_months=False,
        show_lifetime_totals=False,
        show_upcoming_events=False,
        show_recent_favorites=False,
        show_recent_device=False,
        show_recent_gear=False,
        show_badges=False,
        other_activity=None,
        other_primary_activity=None,
        user_roles=[],
        name_approved=True,
        user_profile_full_name="f",
        make_golf_scorecards_private=False,
        allow_golf_live_scoring=False,
        allow_golf_scoring_by_connections=False,
        user_level=1,
        user_point=0,
        level_update_date="2020-01-01",
        level_is_viewed=False,
        level_point_threshold=100,
        user_point_offset=0,
        user_pro=False,
    )

    # Test with motivation as int, other_motivation as int
    profile1 = UserProfile(**{**base, "motivation": 5, "other_motivation": 3})
    assert profile1.motivation == 5
    assert profile1.other_motivation == 3

    # Test with motivation as str, other_motivation as str
    profile2 = UserProfile(
        **{**base, "motivation": "cardio", "other_motivation": "fun"}
    )
    assert profile2.motivation == "cardio"
    assert profile2.other_motivation == "fun"

    # Test with motivation as None, other_motivation as None
    profile3 = UserProfile(
        **{**base, "motivation": None, "other_motivation": None}
    )
    assert profile3.motivation is None
    assert profile3.other_motivation is None


def test_user_settings_threshold_hr_nullable():
    """Test UserData accepts threshold_heart_rate_auto_detected as None."""
    pf = PowerFormat(
        format_id=1,
        format_key="k",
        min_fraction=0,
        max_fraction=2,
        grouping_used=False,
        display_format=None,
    )
    fd = FirstDayOfWeek(
        day_id=1, day_name="Monday", sort_order=1, is_possible_first_day=True
    )

    # Test with None (the bug scenario)
    ud_none = UserData(
        gender="M",
        weight=80.0,
        height=180.0,
        time_format="24h",
        birth_date="1990-01-01",
        measurement_system="metric",
        activity_level=None,
        handedness="RIGHT",
        power_format=pf,
        heart_rate_format=pf,
        first_day_of_week=fd,
        vo_2_max_running=None,
        vo_2_max_cycling=None,
        lactate_threshold_speed=None,
        lactate_threshold_heart_rate=None,
        dive_number=None,
        intensity_minutes_calc_method="AUTO",
        moderate_intensity_minutes_hr_zone=3,
        vigorous_intensity_minutes_hr_zone=4,
        hydration_measurement_unit="ml",
        hydration_containers=[],
        hydration_auto_goal_enabled=True,
        firstbeat_max_stress_score=None,
        firstbeat_cycling_lt_timestamp=None,
        firstbeat_running_lt_timestamp=None,
        threshold_heart_rate_auto_detected=None,
        ftp_auto_detected=None,
        training_status_paused_date=None,
        weather_location=None,
        golf_distance_unit=None,
        golf_elevation_unit=None,
        golf_speed_unit=None,
        external_bottom_time=None,
    )
    assert ud_none.threshold_heart_rate_auto_detected is None

    # Test with True (backward compatibility)
    ud_true = UserData(
        gender="M",
        weight=80.0,
        height=180.0,
        time_format="24h",
        birth_date="1990-01-01",
        measurement_system="metric",
        activity_level=None,
        handedness="RIGHT",
        power_format=pf,
        heart_rate_format=pf,
        first_day_of_week=fd,
        vo_2_max_running=None,
        vo_2_max_cycling=None,
        lactate_threshold_speed=None,
        lactate_threshold_heart_rate=None,
        dive_number=None,
        intensity_minutes_calc_method="AUTO",
        moderate_intensity_minutes_hr_zone=3,
        vigorous_intensity_minutes_hr_zone=4,
        hydration_measurement_unit="ml",
        hydration_containers=[],
        hydration_auto_goal_enabled=True,
        firstbeat_max_stress_score=None,
        firstbeat_cycling_lt_timestamp=None,
        firstbeat_running_lt_timestamp=None,
        threshold_heart_rate_auto_detected=True,
        ftp_auto_detected=None,
        training_status_paused_date=None,
        weather_location=None,
        golf_distance_unit=None,
        golf_elevation_unit=None,
        golf_speed_unit=None,
        external_bottom_time=None,
    )
    assert ud_true.threshold_heart_rate_auto_detected is True
