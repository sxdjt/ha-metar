# HAMETAR Integration Scorecard

Test run: 2026-03-14 23:50:00 PDT

## Test Suite - 126 / 126 Passed

| Module | Tests | Status |
|---|---|---|
| `test_config_flow.py` | 22 | Pass |
| `test_coordinator.py` | 37 | Pass |
| `test_diagnostics.py` | 3 | Pass |
| `test_init.py` | 13 | Pass |
| `test_sensor.py` | 49 | Pass |
| **Total** | **126** | **All passing** |

---

### test_config_flow.py (22 tests)

| Test | Status |
|---|---|
| `test_validate_station_bad_format` | Pass |
| `test_validate_station_cannot_connect` | Pass |
| `test_validate_station_not_found` | Pass |
| `test_validate_station_non_list_response` | Pass |
| `test_validate_station_http_error` | Pass |
| `test_validate_station_204_no_content` | Pass |
| `test_validate_station_success` | Pass |
| `test_validate_station_strips_and_uppercases` | Pass |
| `test_step_user_shows_form_on_first_call` | Pass |
| `test_step_user_creates_entry_on_valid_input` | Pass |
| `test_step_user_shows_error_on_invalid_station` | Pass |
| `test_step_user_abort_on_duplicate` | Pass |
| `test_step_user_shows_form_on_cannot_connect` | Pass |
| `test_async_get_options_flow` | Pass |
| `test_reconfigure_shows_form_with_current_station` | Pass |
| `test_reconfigure_success` | Pass |
| `test_reconfigure_shows_error_on_invalid_station` | Pass |
| `test_reconfigure_aborts_on_duplicate` | Pass |
| `test_reconfigure_schema_station_only` | Pass |
| `test_options_flow_shows_form` | Pass |
| `test_options_flow_saves_new_interval` | Pass |
| `test_options_flow_uses_options_as_default` | Pass |

---

### test_coordinator.py (37 tests)

| Test | Status |
|---|---|
| `test_parse_visibility[10+-10.0]` | Pass |
| `test_parse_visibility[10-10.0]` (x2) | Pass |
| `test_parse_visibility[6-6.0]` | Pass |
| `test_parse_visibility[1/2-0.5]` | Pass |
| `test_parse_visibility[1/4-0.25]` | Pass |
| `test_parse_visibility[1 1/2-1.5]` | Pass |
| `test_parse_visibility[1 3/4-1.75]` | Pass |
| `test_parse_visibility[P6SM-None]` | Pass |
| `test_parse_visibility[None-None]` | Pass |
| `test_parse_visibility[-None]` | Pass |
| `test_parse_altimeter_hpa_a_group` | Pass |
| `test_parse_altimeter_hpa_q_group` | Pass |
| `test_parse_altimeter_hpa_falls_back_to_api_value` | Pass |
| `test_parse_altimeter_hpa_no_raw_no_api` | Pass |
| `test_parse_altimeter_hpa_kord_real` | Pass |
| `test_parse_altimeter_hpa_yssy_real` | Pass |
| `test_extract_ceiling` (8 cases) | Pass |
| `test_obs_time_to_dt_valid` | Pass |
| `test_obs_time_to_dt_none` | Pass |
| `test_obs_time_to_dt_invalid_value` | Pass |
| `test_obs_time_to_dt_overflow` | Pass |
| `test_normalize_standard` | Pass |
| `test_normalize_lifr` | Pass |
| `test_normalize_variable_wind` | Pass |
| `test_normalize_altimeter_q_group` | Pass |
| `test_normalize_altimeter_a_group` | Pass |
| `test_update_raises_on_timeout` | Pass |
| `test_update_raises_on_http_error_status` | Pass |
| `test_update_raises_on_client_error` | Pass |
| `test_update_raises_when_empty_response` | Pass |
| `test_update_success` | Pass |

---

### test_diagnostics.py (3 tests)

| Test | Status |
|---|---|
| `test_diagnostics_returns_config_and_data` | Pass |
| `test_diagnostics_uses_options_scan_interval` | Pass |
| `test_diagnostics_when_coordinator_data_none` | Pass |

---

### test_init.py (13 tests)

| Test | Status |
|---|---|
| `test_setup_entry_stores_coordinator_in_runtime_data` | Pass |
| `test_setup_entry_calls_first_refresh` | Pass |
| `test_setup_entry_forwards_to_sensor_platform` | Pass |
| `test_setup_entry_uses_data_scan_interval` | Pass |
| `test_setup_entry_options_override_data_scan_interval` | Pass |
| `test_setup_entry_uses_default_scan_interval_when_absent` | Pass |
| `test_setup_entry_registers_options_listener` | Pass |
| `test_unload_entry_returns_true_on_success` | Pass |
| `test_unload_entry_calls_unload_platforms` | Pass |
| `test_unload_entry_returns_false_when_platform_unload_fails` | Pass |
| `test_migrate_entity_ids_renames_old_format` | Pass |
| `test_migrate_entity_ids_skips_already_migrated` | Pass |
| `test_update_listener_reloads_entry` | Pass |

---

### test_sensor.py (49 tests)

| Test | Status |
|---|---|
| `test_c_to_f` (4 parametrized cases) | Pass |
| `test_c_to_f_none` | Pass |
| `test_hpa_to_inhg_normal` | Pass |
| `test_hpa_to_inhg_none` | Pass |
| `test_sensor_unique_id` | Pass |
| `test_sensor_unique_id_uses_station_id` | Pass |
| `test_sensor_name_is_entity_portion_only` | Pass |
| `test_sensor_station_name_field_label_only` | Pass |
| `test_sensor_suggested_object_id` | Pass |
| `test_sensor_suggested_object_id_different_station` | Pass |
| `test_sensor_suggested_object_id_no_station_prefix` | Pass |
| `test_native_value_temperature` | Pass |
| `test_native_value_when_data_is_none` | Pass |
| `test_native_value_when_field_missing` | Pass |
| `test_native_value_temperature_f` | Pass |
| `test_native_value_dewpoint_f` | Pass |
| `test_native_value_altimeter_hpa` | Pass |
| `test_native_value_altimeter_inhg` | Pass |
| `test_native_value_flight_category` | Pass |
| `test_native_value_visibility` | Pass |
| `test_native_value_max_temp_6hr_f` | Pass |
| `test_native_value_min_temp_6hr_f` | Pass |
| `test_native_value_max_temp_24hr_f` | Pass |
| `test_native_value_min_temp_24hr_f` | Pass |
| `test_native_value_obs_time` | Pass |
| `test_native_value_obs_time_none` | Pass |
| `test_native_value_obs_time_local` | Pass |
| `test_native_value_obs_time_local_none` | Pass |
| `test_native_value_time_since_obs` | Pass |
| `test_native_value_time_since_obs_none` | Pass |
| `test_extra_attrs_when_data_none` | Pass |
| `test_extra_attrs_flight_category` | Pass |
| `test_extra_attrs_wind_direction_not_variable` | Pass |
| `test_extra_attrs_wind_direction_variable` | Pass |
| `test_extra_attrs_cloud_cover` | Pass |
| `test_extra_attrs_raw_metar` | Pass |
| `test_extra_attrs_elevation` | Pass |
| `test_extra_attrs_default_empty_for_other_sensors` | Pass |
| `test_extra_attrs_temperature_no_extras` | Pass |
| `test_sensor_descriptions_are_non_empty` | Pass |
| `test_all_descriptions_have_callable_value_fn` | Pass |
| `test_all_descriptions_have_unique_keys` | Pass |
| `test_all_descriptions_have_name` | Pass |
| `test_rarely_reported_sensors_disabled_by_default` | Pass |
| `test_primary_sensors_enabled_by_default` | Pass |
| `test_async_setup_entry_creates_all_sensors` | Pass |

---

## Integration Quality Scale

### Bronze

| Rule | Status |
|---|---|
| action-setup | Exempt |
| appropriate-polling | Done |
| brands | * TO DO * |
| common-modules | Done |
| config-flow | Done |
| config-flow-test-coverage | Done |
| dependency-transparency | Done |
| docs-actions | Exempt |
| docs-high-level-description | Done |
| docs-installation-instructions | Done |
| docs-removal-instructions | Done |
| entity-event-setup | Done |
| entity-unique-id | Done |
| has-entity-name | Done |
| runtime-data | Done |
| test-before-configure | Done |
| test-before-setup | Done |
| unique-config-entry | Done |

### Silver

| Rule | Status |
|---|---|
| action-exceptions | Exempt |
| config-entry-unloading | Done |
| docs-configuration-parameters | Done |
| docs-installation-parameters | Done |
| entity-unavailable | Done |
| integration-owner | Done |
| log-when-unavailable | Done |
| parallel-updates | Done |
| reauthentication-flow | Exempt |
| test-coverage | Done |

### Gold

| Rule | Status |
|---|---|
| devices | Done |
| diagnostics | Done |
| discovery | Exempt |
| discovery-update-info | Exempt |
| docs-data-update | Done |
| docs-examples | Done |
| docs-known-limitations | Done |
| docs-supported-devices | Exempt |
| docs-supported-functions | Done |
| docs-troubleshooting | Done |
| docs-use-cases | Done |
| dynamic-devices | Exempt |
| entity-category | Done |
| entity-device-class | Done |
| entity-disabled-by-default | Done |
| entity-translations | Done |
| exception-translations | Exempt |
| icon-translations | Done |
| reconfiguration-flow | Done |
| repair-issues | Exempt |
| stale-devices | Exempt |

---

**Summary:** 126/126 tests passing. Bronze complete except `brands` (requires a separate PR to home-assistant/brands). Silver complete. Gold complete except `brands` (requires a separate PR to home-assistant/brands).
