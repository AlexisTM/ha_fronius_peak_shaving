# Fronius GEN24 peak shaving for Home Assistant

A switch to turn peak shaving on/off on a Fronius GEN24, with a configurable grid power target.

## Why the web API and not Modbus

The Fronius integration uses Modbus (SunSpec), which only exposes battery limits. There's no register for a grid power target (`HYB_EM_MODE` / `HYB_EM_POWER`). That setting only exists in the inverter's web API.

Faking it over Modbus means HA rewriting discharge limits every few seconds: too slow for short peaks, and stuck if HA goes down. Through the web API the inverter enforces the target itself.

The web API uses a non-standard digest login, so a small Python script handles it instead of `rest_command`.

## Files

| File | Install to |
|---|---|
| `scripts/fronius_battery.py` | `/config/scripts/` |
| `packages/fronius_peak_shaving.yaml` | `/config/packages/` |

## Entities

- `switch.fronius_peak_shaving`: on = Manual with target, off = Automatic. State read from the inverter.
- `input_number.fronius_peak_shaving_power`: target, 250–2420 W. Applied immediately if the switch is on.
- `sensor.fronius_peak_shaving_power_setpoint`: value stored on the inverter.

## Install

1. Copy both files to HA with the Terminal & SSH or File editor add-on. The config folder is `/homeassistant` or `/config` depending on the add-on.
2. Add to `secrets.yaml`:
   ```yaml
   fronius_password: <customer password>
   ```
3. Enable packages in `configuration.yaml` (under the existing `homeassistant:` block if there is one):
   ```yaml
   homeassistant:
     packages: !include_dir_named packages
   ```
4. Developer tools → YAML → Check configuration, then Restart.

The inverter IP (`192.168.178.85`, Ethernet) and user (`customer`) are set at the top of `fronius_battery.py`.

## Testing from another machine

Needs a `secrets.yaml` one folder above the script.

```
python3 scripts/fronius_battery.py get
python3 scripts/fronius_battery.py set '{"HYB_EM_MODE":1,"HYB_EM_POWER":2420}'
python3 scripts/fronius_battery.py set '{"HYB_EM_MODE":0}'
```

## Troubleshooting

- **Switch unavailable**: wrong IP or password, or the inverter is unreachable. Check `sensor.fronius_battery_config` and the logs.
- **Authentication failed**: check the password. If `customer` is refused, try `technician`.
- **Fronius integration slow or on the wrong IP**: disable WLAN on the inverter so DHCP discovery can't move it to the WiFi address.
