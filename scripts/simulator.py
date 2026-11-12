import argparse
import random
import time
from datetime import datetime, timezone

import httpx


def generate_reading(device_id: str) -> dict[str, object]:
    return {
        "device_id": device_id,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "temperature": round(random.gauss(70, 5), 2),
        "humidity": round(random.uniform(35, 75), 2),
        "pressure": round(random.gauss(1013, 8), 2),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Invia telemetria simulata alla API")
    parser.add_argument("--api-url", default="http://localhost:8000")
    parser.add_argument("--device-id", default="machine-001")
    parser.add_argument("--interval", type=float, default=2.0)
    args = parser.parse_args()

    endpoint = f"{args.api_url.rstrip('/')}/api/telemetry"
    with httpx.Client(timeout=10) as client:
        while True:
            response = client.post(endpoint, json=generate_reading(args.device_id))
            response.raise_for_status()
            print(response.json())
            time.sleep(args.interval)


if __name__ == "__main__":
    main()
