import os
import sys
import urllib.request


def main() -> int:
    url = None
    if len(sys.argv) > 1:
        url = sys.argv[1]
    url = url or os.getenv('HEALTHCHECK_URL')
    if not url:
        return 1
    try:
        with urllib.request.urlopen(url, timeout=2) as response:
            return 0 if response.status == 200 else 1
    except Exception:
        return 1


if __name__ == '__main__':
    sys.exit(main())
