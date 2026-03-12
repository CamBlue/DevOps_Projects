"""
SSL Certificate Monitor — hardened, pyOpenSSL-free version.
Uses only stdlib `ssl` + `cryptography` for certificate parsing.
"""

import ssl
import socket
import logging
import os
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

import requests
from dotenv import load_dotenv
import argparse
from cryptography import x509

# ---------------------------------------------------------------------------
# Logging setup
# ---------------------------------------------------------------------------
logger = logging.getLogger("ssl_monitor")
logger.setLevel(logging.DEBUG)

console_handler = logging.StreamHandler()
console_handler.setLevel(logging.INFO)
console_handler.setFormatter(
    logging.Formatter("%(asctime)s  %(levelname)-8s  %(message)s", datefmt="%Y-%m-%d %H:%M:%S")
)
logger.addHandler(console_handler)

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------
ALLOWED_DOMAINS_DIR = Path(__file__).resolve().parent  # restrict file access
SOCKET_TIMEOUT = 10  # seconds
ALERT_COOLDOWN = 3600  # seconds between duplicate alerts for the same domain
_alert_cache: dict[str, float] = {}  # domain -> last alert timestamp


# ============================= SSLChecker ==================================
class SSLChecker:
    """Retrieve and inspect a remote host's TLS certificate."""

    def __init__(self, hostname: str, port: int = 443):
        self.hostname = hostname.strip().lower()
        self.port = port

    # ----- certificate retrieval -------------------------------------------
    def get_certificate(self) -> x509.Certificate | None:
        """Connect via TLS, pull the DER cert, and parse with *cryptography*."""
        context = ssl.create_default_context()

        try:
            with socket.create_connection(
                (self.hostname, self.port), timeout=SOCKET_TIMEOUT
            ) as sock:
                with context.wrap_socket(sock, server_hostname=self.hostname) as ssock:
                    cert_der = ssock.getpeercert(binary_form=True)
                    if cert_der is None:
                        logger.warning("No certificate returned by %s", self.hostname)
                        return None
                    return x509.load_der_x509_certificate(cert_der)

        except (socket.timeout, socket.gaierror) as exc:
            logger.error("Network error for %s — %s", self.hostname, exc)
        except ssl.SSLCertVerificationError as exc:
            logger.error("TLS verification failed for %s — %s", self.hostname, exc)
        except ssl.SSLError as exc:
            logger.error("TLS error for %s — %s", self.hostname, exc)
        except OSError as exc:
            logger.error("Connection error for %s — %s", self.hostname, exc)
        return None

    # ----- cert info -------------------------------------------------------
    def get_cert_info(self) -> dict | None:
        cert = self.get_certificate()
        if cert is None:
            return None

        expiry_date = cert.not_valid_after_utc
        days_remaining = (expiry_date - datetime.now(timezone.utc)).days

        # Extract CN from subject / issuer (fall back gracefully)
        subject_cn = self._get_cn(cert.subject) or str(cert.subject)
        issuer_cn = self._get_cn(cert.issuer) or str(cert.issuer)

        return {
            "hostname": self.hostname,
            "issuer": issuer_cn,
            "subject": subject_cn,
            "expiry_date": expiry_date,
            "days_remaining": days_remaining,
            "serial": cert.serial_number,
            "status": self.get_status(days_remaining),
        }

    # ----- helpers ---------------------------------------------------------
    @staticmethod
    def _get_cn(name: x509.Name) -> str | None:
        attrs = name.get_attributes_for_oid(x509.oid.NameOID.COMMON_NAME)
        return attrs[0].value if attrs else None

    @staticmethod
    def get_status(days_remaining: int) -> str:
        if days_remaining < 0:
            return "EXPIRED"
        elif days_remaining < 7:
            return "CRITICAL"
        elif days_remaining < 30:
            return "WARNING"
        return "OK"


# ======================== Domain file handling ==============================
def load_domains(domains_file: str) -> list[str]:
    """Read and validate the domains file, returning a clean list."""
    path = Path(domains_file).resolve()

    # Restrict to the project directory to avoid arbitrary file reads
    if ALLOWED_DOMAINS_DIR not in path.parents and path.parent != ALLOWED_DOMAINS_DIR:
        logger.error(
            "Domains file must be inside the project directory (%s)", ALLOWED_DOMAINS_DIR
        )
        sys.exit(1)

    if not path.is_file():
        logger.error("Domains file not found: %s", path)
        sys.exit(1)

    try:
        text = path.read_text(encoding="utf-8")
    except PermissionError:
        logger.error("Cannot read domains file (permission denied): %s", path)
        sys.exit(1)

    domains: list[str] = []
    for lineno, raw_line in enumerate(text.splitlines(), start=1):
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        # Basic hostname validation
        if any(ch in line for ch in (" ", "/", ":", "@")):
            logger.warning("Skipping invalid hostname on line %d: %s", lineno, line)
            continue
        domains.append(line)

    if not domains:
        logger.error("No valid domains found in %s", path)
        sys.exit(1)

    return domains


# ========================= Multi-domain check ==============================
def check_multiple_domains(domains: list[str]) -> list[dict]:
    results: list[dict] = []
    logger.info("Checking %d domain(s)...", len(domains))

    status_emoji = {
        "OK": "✓",
        "WARNING": "⚠️",
        "CRITICAL": "🔥",
        "EXPIRED": "❌",
    }

    for domain in domains:
        checker = SSLChecker(domain)
        info = checker.get_cert_info()
        if info:
            results.append(info)
            logger.info(
                "  %s  %s — %d days remaining  [%s]",
                status_emoji.get(info["status"], "?"),
                domain,
                info["days_remaining"],
                info["status"],
            )
        else:
            logger.warning("  ✗  %s — FAILED to retrieve cert", domain)

    return results


# ============================= Report ======================================
def generate_report(results: list[dict]) -> None:
    if not results:
        logger.info("No results to report.")
        return

    results.sort(key=lambda r: r["days_remaining"])

    print("\n" + "=" * 80)
    print("  SSL Certificate Status Report")
    print("=" * 80)

    for r in results:
        print(f"""
  Domain:         {r['hostname']}
  Subject:        {r['subject']}
  Issuer:         {r['issuer']}
  Expiry:         {r['expiry_date'].strftime('%Y-%m-%d %H:%M UTC')}
  Days Remaining: {r['days_remaining']}
  Status:         {r['status']}""")

    print("\n  " + "-" * 40)
    status_counts: dict[str, int] = {}
    for r in results:
        status_counts[r["status"]] = status_counts.get(r["status"], 0) + 1
    for status, count in status_counts.items():
        print(f"  {status}: {count}")
    print()


# ============================= Alerting ====================================
load_dotenv()


def _should_alert(domain: str) -> bool:
    """Rate-limit: allow one alert per domain per ALERT_COOLDOWN seconds."""
    now = time.time()
    last = _alert_cache.get(domain, 0.0)
    if now - last < ALERT_COOLDOWN:
        logger.debug("Alert for %s suppressed (cooldown active)", domain)
        return False
    _alert_cache[domain] = now
    return True


def send_alert(result: dict) -> None:
    if result["status"] in ("CRITICAL", "EXPIRED"):
        if _should_alert(result["hostname"]):
            send_slack_alert(result)


def send_slack_alert(result: dict) -> None:
    webhook_url = os.getenv("SLACK_WEBHOOK_URL")
    if not webhook_url:
        logger.warning("SLACK_WEBHOOK_URL not set — skipping alert for %s", result["hostname"])
        return

    message = {
        "text": "🚨 SSL Certificate Alert",
        "attachments": [
            {
                "color": "danger",
                "fields": [
                    {"title": "Domain", "value": result["hostname"]},
                    {"title": "Status", "value": result["status"]},
                    {"title": "Days Remaining", "value": str(result["days_remaining"])},
                    {
                        "title": "Expiry Date",
                        "value": result["expiry_date"].strftime("%Y-%m-%d"),
                    },
                ],
            }
        ],
    }

    try:
        resp = requests.post(webhook_url, json=message, timeout=15)
        if not resp.ok:
            logger.error(
                "Slack alert failed for %s — HTTP %d: %s",
                result["hostname"],
                resp.status_code,
                resp.text[:200],
            )
        else:
            logger.info("Slack alert sent for %s", result["hostname"])
    except requests.RequestException as exc:
        logger.error("Slack alert request error for %s — %s", result["hostname"], exc)


# ============================= CLI =========================================
def main() -> None:
    parser = argparse.ArgumentParser(description="SSL Certificate Monitor")
    parser.add_argument(
        "--domains", default="domains.txt", help="Path to file with domain list"
    )
    parser.add_argument(
        "--alert", action="store_true", help="Send Slack alerts for expiring certs"
    )
    parser.add_argument(
        "--threshold", type=int, default=30, help="Alert threshold in days (default: 30)"
    )
    args = parser.parse_args()

    domains = load_domains(args.domains)
    results = check_multiple_domains(domains)
    generate_report(results)

    if args.alert:
        for result in results:
            if result["days_remaining"] < args.threshold:
                send_alert(result)


if __name__ == "__main__":
    main()