# Tenda Router Configuration Automation

This project contains a Python script to automatically configure Tenda routers using Selenium for browser automation.

## Requirements

- Python 3.x
- Selenium WebDriver
- ChromeDriver

### Installation

1. Install the required Python packages:

    ```bash
    pip install selenium
    ```

2. Download and install [ChromeDriver](https://sites.google.com/chromium.org/driver/).

### Usage

1. Edit the `router_config.py` file with your router's IP, WiFi SSID, and password.
2. Run the script:

    ```bash
    python router_config.py
    ```

The script will automatically log into the Tenda router admin page and configure the WiFi settings.

---

### Example

To configure a Tenda router with IP `192.168.0.1`, SSID `MyTendaNetwork`, and password `mySecurePassword`, simply edit the script and run it.
