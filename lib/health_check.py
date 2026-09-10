import sys

import httpx


def health_check():
    try:
        response = httpx.get("http://localhost:8001/", timeout=5)
        if response.status_code == 200 and response.json() == {"detail": "success!"}:
            print("Health check passed.")
            sys.exit(0)  # Healthy
        else:
            print(f"Health check failed with status code: {response.status_code}")
            sys.exit(1)  # Unhealthy
    except Exception as e:
        print(f"Health check encountered an error: {e}")
        sys.exit(1)  # Unhealthy


if __name__ == "__main__":
    health_check()
