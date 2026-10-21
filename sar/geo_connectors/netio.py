"""Shared HTTP for the geo connectors: host allowlist, timeouts, retry with exponential backoff.

No connector here ever falls back to invented data. On failure it raises ConnectorError."""
import json
import random
import time
import urllib.error
import urllib.parse
import urllib.request

ALLOWED_HOSTS = {
    "earth-search.aws.element84.com",
    "cmr.earthdata.nasa.gov",
    "elevation.nationalmap.gov",
    "web.archive.org",
    "sampleserver6.arcgisonline.com",
}
RETRY_STATUS = {429, 500, 502, 503, 504}
USER_AGENT = "forensicfinders-sar-geo-connectors/1.0"


class ConnectorError(RuntimeError):
    pass


def allow_host(host):
    """Add an extra host (e.g. a municipal ArcGIS server) to the allowlist."""
    ALLOWED_HOSTS.add(host.lower())


def _check(url):
    u = urllib.parse.urlparse(url)
    if u.scheme != "https":
        raise ConnectorError(f"https only: {url}")
    if (u.hostname or "").lower() not in ALLOWED_HOSTS:
        raise ConnectorError(f"host not allowlisted: {u.hostname} (use http.allow_host)")


def request(url, params=None, body=None, timeout=30, retries=4, backoff=1.0, opener=None, sleep=time.sleep, max_bytes=200 * 2**20):
    """Return response bytes. body (dict) => POST JSON. Retries network errors and 429/5xx."""
    if params:
        url = url + ("&" if "?" in url else "?") + urllib.parse.urlencode(params)
    _check(url)
    data = None
    headers = {"User-Agent": USER_AGENT, "Accept": "application/json, */*"}
    if body is not None:
        data = json.dumps(body).encode()
        headers["Content-Type"] = "application/json"
    open_ = opener or urllib.request.urlopen
    last = None
    for attempt in range(retries + 1):
        try:
            req = urllib.request.Request(url, data=data, headers=headers, method="POST" if data else "GET")
            with open_(req, timeout=timeout) as r:
                _check(r.geturl() if hasattr(r, "geturl") else url)  # redirect target must be allowlisted too
                raw = r.read(max_bytes + 1)
                if len(raw) > max_bytes:
                    raise ConnectorError(f"response over {max_bytes} bytes")
                return raw
        except urllib.error.HTTPError as e:
            last = e
            if e.code not in RETRY_STATUS:
                detail = e.read(500).decode("utf-8", "replace") if hasattr(e, "read") else ""
                raise ConnectorError(f"HTTP {e.code} from {url}: {detail}") from e
        except (urllib.error.URLError, TimeoutError, ConnectionError, OSError) as e:
            if isinstance(e, ConnectorError):
                raise
            last = e
        if attempt < retries:
            sleep(backoff * (2 ** attempt) + random.uniform(0, backoff / 4))
    raise ConnectorError(f"gave up after {retries + 1} attempts: {url}: {last}")


def request_json(url, **kw):
    raw = request(url, **kw)
    try:
        return json.loads(raw)
    except ValueError as e:
        raise ConnectorError(f"non-JSON response from {url}: {raw[:200]!r}") from e
