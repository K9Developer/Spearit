from datetime import datetime, timedelta, timezone
from ipaddress import ip_address
from pathlib import Path
import socket

from cryptography import x509
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.x509.oid import NameOID


def _get_primary_local_ip() -> str | None:
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        sock.connect(("8.8.8.8", 80))
        return sock.getsockname()[0]
    except OSError:
        return None
    finally:
        sock.close()


def _required_san_values() -> tuple[set[str], set[str]]:
    dns_names = {"localhost"}
    ip_values = {"127.0.0.1"}
    if (primary_ip := _get_primary_local_ip()) is not None:
        ip_values.add(primary_ip)
    return dns_names, ip_values


def _cert_has_required_sans(cert_path: Path, required_dns: set[str], required_ips: set[str]) -> bool:
    if not cert_path.exists():
        return False
    try:
        cert = x509.load_pem_x509_certificate(cert_path.read_bytes())
        san_ext = cert.extensions.get_extension_for_class(x509.SubjectAlternativeName).value
    except (ValueError, x509.ExtensionNotFound):
        return False

    current_dns = set(san_ext.get_values_for_type(x509.DNSName))
    current_ips = {str(ip) for ip in san_ext.get_values_for_type(x509.IPAddress)}
    return required_dns.issubset(current_dns) and required_ips.issubset(current_ips)


def ensure_self_signed_cert(
    cert_path: Path | None = None,
    key_path: Path | None = None,
) -> tuple[str, str]:
    if cert_path is None:
        cert_path = Path("databases", "presistant", "tls", "cert.pem")
    if key_path is None:
        key_path = Path("databases", "presistant", "tls", "key.pem")

    cert_path.parent.mkdir(parents=True, exist_ok=True)
    key_path.parent.mkdir(parents=True, exist_ok=True)

    required_dns, required_ips = _required_san_values()

    if cert_path.exists() and key_path.exists() and _cert_has_required_sans(cert_path, required_dns, required_ips):
        return str(cert_path), str(key_path)

    key = rsa.generate_private_key(public_exponent=65537, key_size=2048)

    subject = issuer = x509.Name([
        x509.NameAttribute(NameOID.COUNTRY_NAME, "US"),
        x509.NameAttribute(NameOID.ORGANIZATION_NAME, "Spearit"),
        x509.NameAttribute(NameOID.COMMON_NAME, "SpearHead"),
    ])

    now = datetime.now(timezone.utc)
    san_entries: list[x509.GeneralName] = [x509.DNSName(name) for name in sorted(required_dns)]
    san_entries.extend(x509.IPAddress(ip_address(ip)) for ip in sorted(required_ips))

    cert = (
        x509.CertificateBuilder()
        .subject_name(subject)
        .issuer_name(issuer)
        .public_key(key.public_key())
        .serial_number(x509.random_serial_number())
        .not_valid_before(now - timedelta(minutes=1))
        .not_valid_after(now + timedelta(days=3650))
        .add_extension(
            x509.SubjectAlternativeName(san_entries),
            critical=False,
        )
        .sign(private_key=key, algorithm=hashes.SHA256())
    )

    key_path.write_bytes(
        key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.TraditionalOpenSSL,
            encryption_algorithm=serialization.NoEncryption(),
        )
    )
    cert_path.write_bytes(cert.public_bytes(serialization.Encoding.PEM))

    return str(cert_path), str(key_path)