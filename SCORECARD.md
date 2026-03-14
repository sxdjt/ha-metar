# HAMETAR Integration Scorecard

## Test Suite - 109 / 109 Passed

| Module | Tests | Status |
|---|---|---|
| `test_config_flow.py` | 21 | PASS |
| `test_coordinator.py` | 31 | PASS |
| `test_diagnostics.py` | 3 | PASS |
| `test_init.py` | 11 | PASS |
| `test_sensor.py` | 43 | PASS |
| **Total** | **109** | **All passing** |

---

### test_config_flow.py (21 tests)

| Test | Status |
|---|---|
| `test_validate_station_bad_format` | PASS |
| `test_validate_station_cannot_connect` | PASS |
| `test_validate_station_not_found` | PASS |
| `test_validate_station_non_list_response` | PASS |
| `test_validate_station_http_error` | PASS |
| `test_validate_station_success` | PASS |
| `test_validate_station_strips_and_uppercases` | PASS |
| `test_step_user_shows_form_on_first_call` | PASS |
| `test_step_user_creates_entry_on_valid_input` | PASS |
| `test_step_user_shows_error_on_invalid_station` | PASS |
| `test_step_user_abort_on_duplicate` | PASS |
| `test_step_user_shows_form_on_cannot_connect` | PASS |
| `test_async_get_options_flow` | PASS |
| `test_reconfigure_shows_form_with_current_station` | PASS |
| `test_reconfigure_success` | PASS |
| `test_reconfigure_shows_error_on_invalid_station` | PASS |
| `test_reconfigure_aborts_on_duplicate` | PASS |
| `test_reconfigure_schema_station_only` | PASS |
| `test_options_flow_shows_form` | PASS |
| `test_options_flow_saves_new_interval` | PASS |
| `test_options_flow_uses_options_as_default` | PASS |

---

### test_coordinator.py (31 tests)

| Test | Status |
|---|---|
| `test_parse_visibility[10+-10.0]` | PASS |
| `test_parse_visibility[10-10.0]` (x2) | PASS |
| `test_parse_visibility[6-6.0]` | PASS |
| `test_parse_visibility[1/2-0.5]` | PASS |
| `test_parse_visibility[1/4-0.25]` | PASS |
| `test_parse_visibility[1 1/2-1.5]` | PASS |
| `test_parse_visibility[1 3/4-1.75]` | PASS |
| `test_parse_visibility[P6SM-None]` | PASS |
| `test_parse_visibility[None-None]` | PASS |
| `test_parse_visibility[-None]` | PASS |
| `test_extract_ceiling` (8 cases) | PASS |
| `test_obs_time_to_dt_valid` | PASS |
| `test_obs_time_to_dt_none` | PASS |
| `test_obs_time_to_dt_invalid_value` | PASS |
| `test_obs_time_to_dt_overflow` | PASS |
| `test_normalize_standard` | PASS |
| `test_normalize_lifr` | PASS |
| `test_normalize_variable_wind` | PASS |
| `test_update_raises_on_timeout` | PASS |
| `test_update_raises_on_http_error_status` | PASS |
| `test_update_raises_on_client_error` | PASS |
| `test_update_raises_when_empty_response` | PASS |
| `test_update_success` | PASS |

---

### test_diagnostics.py (3 tests)

| Test | Status |
|---|---|
| `test_diagnostics_returns_config_and_data` | PASS |
| `test_diagnostics_uses_options_scan_interval` | PASS |
| `test_diagnostics_when_coordinator_data_none` | PASS |

---

### test_init.py (11 tests)

| Test | Status |
|---|---|
| `test_setup_entry_stores_coordinator_in_runtime_data` | PASS |
| `test_setup_entry_calls_first_refresh` | PASS |
| `test_setup_entry_forwards_to_sensor_platform` | PASS |
| `test_setup_entry_uses_data_scan_interval` | PASS |
| `test_setup_entry_options_override_data_scan_interval` | PASS |
| `test_setup_entry_uses_default_scan_interval_when_absent` | PASS |
| `test_setup_entry_registers_options_listener` | PASS |
| `test_unload_entry_returns_true_on_success` | PASS |
| `test_unload_entry_calls_unload_platforms` | PASS |
| `test_unload_entry_returns_false_when_platform_unload_fails` | PASS |
| `test_update_listener_reloads_entry` | PASS |

---

### test_sensor.py (43 tests)

| Test | Status |
|---|---|
| `test_c_to_f` (4 parametrized cases) | PASS |
| `test_c_to_f_none` | PASS |
| `test_hpa_to_inhg_normal` | PASS |
| `test_hpa_to_inhg_none` | PASS |
| `test_sensor_unique_id` | PASS |
| `test_sensor_unique_id_uses_station_id` | PASS |
| `test_sensor_name_is_entity_portion_only` | PASS |
| `test_sensor_station_name_field_label_only` | PASS |
| `test_sensor_suggested_object_id` | PASS |
| `test_sensor_suggested_object_id_different_station` | PASS |
| `test_sensor_suggested_object_id_no_station_prefix` | PASS |
| `test_native_value_temperature` | PASS |
| `test_native_value_when_data_is_none` | PASS |
| `test_native_value_when_field_missing` | PASS |
| `test_native_value_temperature_f` | PASS |
| `test_native_value_dewpoint_f` | PASS |
| `test_native_value_altimeter_hpa` | PASS |
| `test_native_value_altimeter_inhg` | PASS |
| `test_native_value_flight_category` | PASS |
| `test_native_value_visibility` | PASS |
| `test_native_value_max_temp_6hr_f` | PASS |
| `test_native_value_min_temp_6hr_f` | PASS |
| `test_native_value_max_temp_24hr_f` | PASS |
| `test_native_value_min_temp_24hr_f` | PASS |
| `test_extra_attrs_when_data_none` | PASS |
| `test_extra_attrs_flight_category` | PASS |
| `test_extra_attrs_wind_direction_not_variable` | PASS |
| `test_extra_attrs_wind_direction_variable` | PASS |
| `test_extra_attrs_cloud_cover` | PASS |
| `test_extra_attrs_raw_metar` | PASS |
| `test_extra_attrs_elevation` | PASS |
| `test_extra_attrs_default_empty_for_other_sensors` | PASS |
| `test_extra_attrs_temperature_no_extras` | PASS |
| `test_sensor_descriptions_are_non_empty` | PASS |
| `test_all_descriptions_have_callable_value_fn` | PASS |
| `test_all_descriptions_have_unique_keys` | PASS |
| `test_all_descriptions_have_name` | PASS |
| `test_rarely_reported_sensors_disabled_by_default` | PASS |
| `test_primary_sensors_enabled_by_default` | PASS |
| `test_async_setup_entry_creates_all_sensors` | PASS |

---

## Integration Quality Scale

### Bronze

| Rule | Status |
|---|---|
| action-setup | exempt |
| appropriate-polling | done |
| brands | **TO DO**  |
| common-modules | done |
| config-flow | done |
| config-flow-test-coverage | done |
| dependency-transparency | done |
| docs-actions | exempt |
| docs-high-level-description | done |
| docs-installation-instructions | done |
| docs-removal-instructions | done |
| entity-event-setup | done |
| entity-unique-id | done |
| has-entity-name | done |
| runtime-data | done |
| test-before-configure | done |
| test-before-setup | done |
| unique-config-entry | done |

### Silver

| Rule | Status |
|---|---|
| action-exceptions | exempt |
| config-entry-unloading | done |
| docs-configuration-parameters | done |
| docs-installation-parameters | done |
| entity-unavailable | done |
| integration-owner | done |
| log-when-unavailable | done |
| parallel-updates | done |
| reauthentication-flow | exempt |
| test-coverage | done |

### Gold

| Rule | Status |
|---|---|
| devices | done |
| diagnostics | done |
| discovery | exempt |
| discovery-update-info | exempt |
| docs-data-update | **TO DO** |
| docs-examples | **TO DO** |
| docs-known-limitations | **TO DO** |
| docs-supported-devices | **TO DO** |
| docs-supported-functions | **TO DO** |
| docs-troubleshooting | **TO DO** |
| docs-use-cases | **TO DO** |
| dynamic-devices | exempt |
| entity-category | done |
| entity-device-class | done |
| entity-disabled-by-default | done |
| entity-translations | **TO DO** |
| exception-translations | exempt |
| icon-translations | **TO DO** |
| reconfiguration-flow | done |
| repair-issues | exempt |
| stale-devices | exempt |

---

**Summary:** 109/109 tests passing. Bronze complete except `brands` (requires a separate PR to home-assistant/brands). Silver complete. Gold has 9 remaining items: 7 documentation rules plus `entity-translations` and `icon-translations`.
