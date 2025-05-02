# Transit Time Calculator

This desktop tool estimates freight transit time, driving shifts, and LTL density using NMFC logic and overlength thresholds.  
It supports both planning by departure and planning by required arrival, and includes a Smart ETA engine that accounts for weather and live traffic.

## Features

- GUI for pallet-based density and freight class calculation  
- Basic and HOS-aware ETA estimation  
- Smart ETA with NOAA weather alerts and Google Maps traffic data  
- Per-carrier overlength rules with grouped visual alerts  
- Configuration files saved in %USERPROFILE%\Documents\Transit Time Calculator

## Usage

Install dependencies:
pip install -r requirements.txt


Run the application:
python src/main.py


## Required Configuration

This project uses placeholder values for sensitive keys.  
You'll need to replace all "REPLACE_ME" strings in the code with valid values or environment variables:

| Field                    | Function Name                      | Description |
|--------------------------|------------------------------------|-------------|
| GOOGLE_MAPS_API_KEY      | global (main.py)                   | Google Maps Directions API key used for route calculations |
| ICON_BASE64              | global (main.py)                   | Optional base64-encoded icon for the application window |
| LOGO_BASE64              | global (main.py)                   | Optional base64 logo used for GUI header or branding |
| User-Agent (Weather API) | get_weather_alerts()               | Required by NOAA — replace with an email or domain for identification |
| mailto: links            | contact_help(), open_help_window() | Pre-filled support email link — replace with your actual support email |


## Requirements

See `requirements.txt` for the full list.

Key libraries:
- Python 3.10+
- requests
- geopy
- python-dateutil
- numpy
- fpdf

## Optional: Code Signing

The internal build pipeline uses Cosign for signing and verifying builds.  
Cosign is not required for using this application, but may be helpful in a CI/CD environment.

## License

MIT License — see `LICENSE` for full terms.

Built and maintained by Buddha-Code
2025
