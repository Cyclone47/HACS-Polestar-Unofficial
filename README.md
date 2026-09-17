<p align="center">
  <img src="https://raw.githubusercontent.com/Cyclone47/HACS-Polestar-Unofficial/main/images/logo.png" width="140" alt="Polestar Logo">
</p>

# Polestar Data Portal — Home Assistant Integration (EU Data Act)

[![HACS Badge](https://img.shields.io/badge/HACS-Custom-orange.svg?style=for-the-badge)](https://github.com/hacs/default)
[![Home Assistant](https://img.shields.io/badge/Home%20Assistant-2024.1%2B-blue.svg?style=for-the-badge)](https://www.home-assistant.io/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg?style=for-the-badge)](https://github.com/Cyclone47/HACS-Polestar-Unofficial/blob/main/LICENSE)

[![Open your Home Assistant instance and open a repository inside the Home Assistant Community Store.](https://my.home-assistant.io/badges/hacs_repository.svg)](https://my.home-assistant.io/redirect/hacs_repository/?owner=Cyclone47&repository=HACS-Polestar-Unofficial&category=integration)
[![Open your Home Assistant instance and start setting up a new integration.](https://my.home-assistant.io/badges/config_flow_start.svg)](https://my.home-assistant.io/redirect/config_flow_start/?domain=polestar_data_portal)

A native, cloud-direct Home Assistant custom integration that communicates with Polestar's newly released **Polestar Data Portal M2M API** established under the **European Union Data Act (EU Data Act)**.

Compatible with **Polestar 2**, **Polestar 3**, **Polestar 4**, and **Polestar 5** vehicles registered in the EU / EEA.

---

## 📖 Background: Why this Integration Exists

On **September 17, 2026**, Polestar officially unlocked direct telematics access for vehicle owners and third-party developers through the launch of the **[Polestar Data Portal](https://data-portal.polestar.com)**, complying with the EU Data Act.

### The Problem with Old Solutions
For years, the Home Assistant community had to rely on reverse-engineered consumer app APIs (such as the legacy `polestar_api`). Those integrations came with severe pain points:
- ❌ Required entering personal Polestar ID email/passwords into third-party code.
- ❌ Constantly broke whenever Polestar changed internal GraphQL endpoints or mobile app headers.
- ❌ Triggered aggressive Cloudflare captchas, 2FA prompt timeouts, and temporary account locks.
- ❌ Risked security issues and account bans.

### The Solution: Official Machine-to-Machine (M2M) API
With Polestar opening the EU Data Act Developer Portal, we now have a **legal, official, and permanently supported** developer interface:
- ✅ **Dedicated M2M Credentials**: Authenticates via OAuth2 client credentials (`clientId` + `clientSecret` + `x-client-id`).
- ✅ **Zero Scraping & Zero Captchas**: Direct JSON REST API hosted in AWS EU-North (Stockholm).
- ✅ **Official Rate Limits**: 10,000 API requests/day with a 100 requests/minute burst limit.
- ✅ **Rich Vehicle Telematics**: Real-time access to high-voltage battery status, odometer, tyre pressures, fluid warnings, doors/windows/locks, cabin air purification (CleanZone), GPS location, and scheduled climate timers.

> [!NOTE]
> Under the EU Data Act provisions, Polestar currently provides **telemetry and status monitoring** (`GET` endpoints). The Data Portal does not yet expose remote vehicle control commands (e.g. remotely triggering door lock/unlock or climate activation on-demand). This integration focuses on 100% reliable, official vehicle monitoring.

---

## 🚘 What's Possible? (Over 40 Native Entities)

### 🔋 Battery & Charging
| Entity | Platform | Description |
|---|---|---|
| `sensor.polestar_battery_level` | Sensor | Battery state of charge (`%`) |
| `sensor.polestar_estimated_range` | Sensor | Driving range in kilometers (`km`) |
| `sensor.polestar_estimated_full_charge_range` | Sensor | Calculated theoretical driving range at 100% battery (`km`) |
| `sensor.polestar_estimated_range_miles` | Sensor | Driving range in miles (`mi`) |
| `sensor.polestar_average_energy_consumption` | Sensor | Average consumption (`kWh/100km`) |
| `sensor.polestar_estimated_charging_time_to_full` | Sensor | Time remaining until 100% (`min`) |
| `sensor.polestar_estimated_charging_end_time` | Sensor | Calculated completion timestamp when charging completes (`timestamp`) |
| `sensor.polestar_last_telemetry_update` | Sensor | Timestamp when telemetry was received from the vehicle (`timestamp`) |
| `sensor.polestar_charging_status` | Sensor | Upstream charging status enum (e.g. `CHARGING_STATUS_V2_IDLE`) |
| `sensor.polestar_charging_type` | Sensor | Charging mode (`AC`, `DC`, `NONE`) |
| `sensor.polestar_charging_power` | Sensor | Instantaneous power delivered during charging (`W`) |
| `sensor.polestar_charging_current` | Sensor | Charging current (`A`) |
| `sensor.polestar_charging_voltage` | Sensor | Charging voltage (`V`) |
| `sensor.polestar_target_state_of_charge` | Sensor | Configured target charge percentage limit (`%`) |
| `sensor.polestar_charging_amp_limit` | Sensor | Configured maximum charging current limit (`A`) |
| `binary_sensor.polestar_charger_connected` | Binary Sensor | Charging cable plugged into vehicle |
| `binary_sensor.polestar_charging` | Binary Sensor | Battery actively receiving charge |
| `binary_sensor.polestar_charge_now_active` | Binary Sensor | "Charge Now" timer override active |
| `binary_sensor.polestar_global_charge_timer_active` | Binary Sensor | Scheduled charge timer active |

### 🚗 Exterior & Security
| Entity | Platform | Description |
|---|---|---|
| `binary_sensor.polestar_central_lock` | Binary Sensor | Central lock state (on = unlocked, off = locked) |
| `binary_sensor.polestar_tailgate_lock` | Binary Sensor | Trunk / tailgate lock state |
| `binary_sensor.polestar_alarm` | Binary Sensor | Vehicle anti-theft alarm trigger status |
| `binary_sensor.polestar_front_left_door` | Binary Sensor | Front left door open / closed |
| `binary_sensor.polestar_front_right_door` | Binary Sensor | Front right door open / closed |
| `binary_sensor.polestar_rear_left_door` | Binary Sensor | Rear left door open / closed |
| `binary_sensor.polestar_rear_right_door` | Binary Sensor | Rear right door open / closed |
| `binary_sensor.polestar_front_left_window` | Binary Sensor | Front left window open / closed |
| `binary_sensor.polestar_front_right_window` | Binary Sensor | Front right window open / closed |
| `binary_sensor.polestar_rear_left_window` | Binary Sensor | Rear left window open / closed |
| `binary_sensor.polestar_rear_right_window` | Binary Sensor | Rear right window open / closed |
| `binary_sensor.polestar_hood` | Binary Sensor | Frunk / Hood open / closed |
| `binary_sensor.polestar_tailgate` | Binary Sensor | Trunk / Tailgate open / closed |
| `binary_sensor.polestar_charge_port_flap` | Binary Sensor | Charging socket flap open / closed |

### 📍 GPS & Vehicle Tracking
| Entity | Platform | Description |
|---|---|---|
| `device_tracker.polestar_location` | Device Tracker | Real-time vehicle GPS tracking (latitude, longitude, altitude, heading in degrees, speed in km/h, and battery percentage). Supports Home Assistant map, zones, and home/away automations. |

### 🛠️ Odometer & Service Health
| Entity | Platform | Description |
|---|---|---|
| `sensor.polestar_odometer` | Sensor | Total vehicle mileage (`km`) |
| `sensor.polestar_trip_meter_manual` | Sensor | Manual trip distance (`km`) |
| `sensor.polestar_trip_meter_automatic` | Sensor | Automatic trip distance (`km`) |
| `sensor.polestar_average_speed_manual` | Sensor | Average speed manual (`km/h`) |
| `sensor.polestar_average_speed_automatic` | Sensor | Average speed automatic (`km/h`) |
| `sensor.polestar_days_to_service` | Sensor | Remaining days until required maintenance |
| `sensor.polestar_distance_to_service` | Sensor | Remaining distance until required maintenance (`km`) |
| `sensor.polestar_tyre_pressure_front_left` | Sensor | Front left tyre pressure (`kPa`) |
| `sensor.polestar_tyre_pressure_front_right` | Sensor | Front right tyre pressure (`kPa`) |
| `sensor.polestar_tyre_pressure_rear_left` | Sensor | Rear left tyre pressure (`kPa`) |
| `sensor.polestar_tyre_pressure_rear_right` | Sensor | Rear right tyre pressure (`kPa`) |
| `binary_sensor.polestar_service_warning` | Binary Sensor | General service alert |
| `binary_sensor.polestar_brake_fluid_warning` | Binary Sensor | Brake fluid level low alert |
| `binary_sensor.polestar_engine_coolant_warning`| Binary Sensor | Coolant level abnormal alert |
| `binary_sensor.polestar_oil_level_warning` | Binary Sensor | Oil level abnormal alert |
| `binary_sensor.polestar_washer_fluid_warning` | Binary Sensor | Washer fluid low alert |
| `binary_sensor.polestar_12v_battery_warning` | Binary Sensor | 12V auxiliary battery alert |
| `binary_sensor.polestar_tyre_pressure_warning` | Binary Sensor | Any tyre pressure abnormal alert |
| `binary_sensor.polestar_exterior_light_warning`| Binary Sensor | Any exterior bulb or indicator failure |

### ❄️ Climate & CleanZone Air Quality
| Entity | Platform | Description |
|---|---|---|
| `sensor.polestar_compartment_temperature` | Sensor | Cabin interior temperature (`°C`) |
| `sensor.polestar_requested_climate_temperature` | Sensor | Climate setpoint temperature (`°C`) |
| `sensor.polestar_climate_runtime_left` | Sensor | Remaining parking climatization minutes (`min`) |
| `sensor.polestar_cabin_air_quality_index` | Sensor | Cabin Air Quality Index (`AQI`) |
| `sensor.polestar_cabin_pm2_5_particulate_matter` | Sensor | Particulate matter PM2.5 (`µg/m³`) |
| `binary_sensor.polestar_parking_climate` | Binary Sensor | Parking climate currently active |
| `binary_sensor.polestar_interior_pre_cleaning` | Binary Sensor | Interior air pre-cleaning active |
| `binary_sensor.polestar_vehicle_availability` | Binary Sensor | Vehicle cloud connectivity status |

### 🔘 Buttons & Controls
| Entity | Platform | Description |
|---|---|---|
| `button.polestar_refresh_data` | Button | Manually triggers an immediate cloud update without waiting for the next poll interval |

---

## 🔑 Step 1: Getting your Polestar Data Portal Credentials

1. Navigate to **[data-portal.polestar.com](https://data-portal.polestar.com/)** and sign in with your **Polestar ID**.
2. Go to the **Credential** tab:
   - Copy your **App client ID** (`clientId`).
   - Copy your **Client secret** (`clientSecret`).
3. Click on the **API Documentation** tab (next to Credential):
   - Near the top below the Base URL, copy your **Account ID / x-client-id** (in UUID format, e.g. `xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx`).

---

## 📥 Step 2: Installation

### Method 1: Via HACS (Recommended)

[![Open your Home Assistant instance and open a repository inside the Home Assistant Community Store.](https://my.home-assistant.io/badges/hacs_repository.svg)](https://my.home-assistant.io/redirect/hacs_repository/?owner=Cyclone47&repository=HACS-Polestar-Unofficial&category=integration)

1. Click the badge above, or open **HACS** in your Home Assistant instance.
2. In HACS, click the **three dots** in the upper right corner and select **Custom repositories**.
3. Fill in:
   - **Repository**: `Cyclone47/HACS-Polestar-Unofficial`
   - **Category**: `Integration`
4. Click **Add**.
5. Search for **Polestar Data Portal (EU Data Act)** and click **Download**.
6. **Restart Home Assistant**.

---

### Method 2: Manual Installation
1. Download the latest release from the [Releases page](https://github.com/Cyclone47/HACS-Polestar-Unofficial/releases).
2. Copy the `custom_components/polestar_data_portal` folder into your Home Assistant `<config>/custom_components/` directory.
3. **Restart Home Assistant**.

---

## ⚙️ Step 3: Configuration

> [!IMPORTANT]
> **A Home Assistant restart is required before configuration!**
> After downloading via HACS, you **must restart Home Assistant** (*Settings* -> *System* -> *Restart*) before clicking the button below. Home Assistant cannot load the UI setup wizard or integration icons until it has restarted.

[![Open your Home Assistant instance and start setting up a new integration.](https://my.home-assistant.io/badges/config_flow_start.svg)](https://my.home-assistant.io/redirect/config_flow_start/?domain=polestar_data_portal)

1. After restarting, click the badge above, or in Home Assistant go to **Settings** -> **Devices & Services**.
2. Click **+ Add Integration** and search for **Polestar Data Portal**.
3. Enter the credentials from Step 1:
   - **App client ID**: from the *Credential* tab.
   - **Client secret**: from the *Credential* tab.
   - **Account ID / x-client-id**: from the *API Documentation* tab.
4. Click **Submit**. The integration will automatically authenticate, discover your vehicle's VIN, and create all device entities.

### Polling & Rate Limits
Polestar imposes a generous rate limit of **10,000 API calls per day** per client.
- The integration defaults to polling every **300 seconds (5 minutes)** (~4,032 calls/day), ensuring you stay safely within the quota.
- You can change the polling interval anytime by clicking **Configure** on the integration card in Home Assistant (range: 60s to 3600s).

---

## 📊 Dashboard Examples

### Lovelace Card Example (Mushroom & Standard Cards)

```yaml
type: vertical-stack
cards:
  - type: custom:mushroom-template-card
    primary: Polestar 2
    secondary: >
      {{ states('sensor.polestar_battery_level') }}% · {{ states('sensor.polestar_estimated_range') }} km
    icon: mdi:car-electric
    icon_color: "{{ 'green' if is_state('binary_sensor.polestar_charging', 'on') else 'blue' }}"

  - type: gauge
    entity: sensor.polestar_battery_level
    name: Battery Level
    needle: true
    severity:
      green: 50
      yellow: 20
      red: 0

  - type: entities
    title: Vehicle State
    entities:
      - entity: binary_sensor.polestar_charger_connected
      - entity: binary_sensor.polestar_central_lock
      - entity: sensor.polestar_odometer
      - entity: sensor.polestar_compartment_temperature
      - entity: sensor.polestar_days_to_service
      - entity: button.polestar_refresh_data

  - type: map
    entities:
      - device_tracker.polestar_location
    default_zoom: 14
    hours_to_show: 1
```

---

## ❓ FAQ & Troubleshooting

<details>
<summary><b>Why doesn't the API support remote unlocking or starting climate?</b></summary>
Under the EU Data Act Developer Portal, Polestar currently exposes vehicle telemetry and diagnostic data (GET endpoints). Remote control endpoints are part of the consumer mobile app backend and are not currently open in the M2M Data Portal API. If Polestar adds write/control scopes in the future, support will be added immediately.
</details>

<details>
<summary><b>Is this available outside of the EU / EEA?</b></summary>
The Polestar Data Portal was created to comply with the European Union Data Act regulations. It is officially available for vehicles registered and delivered in the EU and EEA.
</details>

<details>
<summary><b>Does this conflict with the old polestar_api integration?</b></summary>
No! This integration uses domain <code>polestar_data_portal</code> and can run alongside or completely replace the older integration without entity ID conflicts.
</details>

<details>
<summary><b>How do I export diagnostic logs for troubleshooting?</b></summary>
Go to <b>Settings</b> -> <b>Devices & Services</b> -> <b>Polestar Data Portal</b> -> click the three dots on your vehicle -> <b>Download Diagnostics</b>. Sensitive data (client secrets, token strings, and VINs) are automatically redacted.
</details>

---

## 📜 License
Distributed under the [MIT License](LICENSE).
*Polestar is a registered trademark of Polestar Performance AB. This project is an independent open-source custom integration developed under the European Union Data Act provisions.*
