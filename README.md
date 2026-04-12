# HomematicCCU – Enigma2 Plugin

Homematic CCU3 device viewer and controller for Enigma2. Displays all
Homematic devices and system variables on the TV screen. Allows changing
values directly from the remote: thermostat temperatures, switches on/off,
dimmer levels, roller shutter positions and system variables.
Requires a Homematic CCU3 in the local network with JSON-RPC API enabled.

---

## Features

| Button | Action |
|--------|--------|
| **Red** | Close / Back |
| **Green** | Refresh device list |
| **Yellow** | Open Information screen |
| **Blue** | Open Settings |
| **OK** | Open device detail / control view |

### Supported device/channel types
- Thermostats (read + set target temperature)
- Switches / plugs (on/off)
- Dimmers (set level 0–100 %)
- Roller shutters (set position)
- Temperature sensors
- Humidity sensors
- Smoke detectors / alarm sensors
- System variables (bool, integer, float, enum)

---

## Requirements

- Homematic CCU3 with JSON-RPC API accessible in the local network
- CCU3 user account (default user: Admin)

---

## Build & deploy

```bash
# 1. Copy .env.example to .env and enter your box and CCU credentials
cp .env.example .env

# 2. Build the .ipk package
make build

# 3. Build, upload and install on the box
make install

# 4. Restart Enigma2
make restart

# 5. Or do all three steps at once
make deploy
```

The package is placed in `build/enigma2-plugin-extensions-homematicccu_1.0.0_all.ipk`.

---

## Settings

| Setting | Default | Description |
|---------|---------|-------------|
| CCU host | `192.168.1.100` | IP or hostname of the CCU3 |
| CCU user | `Admin` | CCU3 user name |
| CCU password | _(empty)_ | CCU3 password |
| Polling interval | 60 s | Background refresh interval |

---

## 📜 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

## 🤝 Contributing

Found a bug or have a suggestion for improvement? Please create an issue or pull request.

I appreciate everyone who supports me and the project! For any requests and suggestions, feel free to provide feedback.

<p>
  <a href="https://www.buymeacoffee.com/madoe21">
    <img src="https://cdn.buymeacoffee.com/buttons/default-orange.png" height="50" alt="Buy Me a Coffee">
  </a>

  <a href="https://ko-fi.com/madoe21">
    <img src="https://storage.ko-fi.com/cdn/kofi3.png?v=3" height="50" alt="Ko-fi">
  </a>

  <a href="https://paypal.me/MartinD809">
    <img src="https://www.paypalobjects.com/webstatic/mktg/logo/pp_cc_mark_111x69.jpg" height="50" alt="PayPal">
  </a>
</p>
