import os
import sys
import logging

from pathlib import Path
from dotenv import load_dotenv
from lxml import etree
from ncclient import manager

# --- LOGGING CONFIGURATION ---
# Get the absolute path of the script, swap .py for .log
script_path = Path(__file__).resolve()
log_file = script_path.with_suffix(".log")

logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(log_file),
    ]
)
logger = logging.getLogger(__name__)
# ------------------------------

# Load .env first
load_dotenv()


ip = os.environ["DEVICE_IP"]
port = os.environ["NETCONF_PORT"]
username = os.environ["DEVICE_USER"]
password = os.environ["DEVICE_PASS"]
device_name = os.environ["DEVICE_NAME"]


class YangDownloader:
    """Downaload YANG models from a device."""

    def __init__(self, host, port, user, password, output_dir="yang_models"):
        self.host = host
        self.port = port
        self.user = user
        self.password = password
        self.output_dir = output_dir

        if not os.path.exists(self.output_dir):
            os.makedirs(self.output_dir)

    def get_schema_list(self, netconf_manager):
        """Retrieves the list of all supported schemas."""
        filter_exp = """
        <netconf-state xmlns="urn:ietf:params:xml:ns:yang:ietf-netconf-monitoring">
            <schemas/>
        </netconf-state>
        """
        response = netconf_manager.get(filter=("subtree", filter_exp))
        root = etree.fromstring(response.xml.encode())
        namespaces = {"mon": "urn:ietf:params:xml:ns:yang:ietf-netconf-monitoring"}
        return root.xpath("//mon:schema", namespaces=namespaces)

    def download_all(self):
        """Iterates and executes the get-schema operation for every identified model."""
        try:
            with manager.connect(
                host=self.host,
                port=self.port,
                username=self.user,
                password=self.password,
                hostkey_verify=False,
            ) as m:
                schemas = self.get_schema_list(m)
                print(f"[*] Found {len(schemas)} schemas. Starting extraction...")

                for schema in schemas:
                    name = schema.find(
                        "{urn:ietf:params:xml:ns:yang:ietf-netconf-monitoring}identifier"
                    ).text
                    version = schema.find(
                        "{urn:ietf:params:xml:ns:yang:ietf-netconf-monitoring}version"
                    ).text

                    filename = f"{name}@{version}.yang" if version else f"{name}.yang"
                    filepath = os.path.join(self.output_dir, filename)

                    try:
                        content = m.get_schema(identifier=name, version=version).data
                        with open(filepath, "w", encoding="utf-8") as f:
                            f.write(content)
                        print(f"[+] Saved: {filepath}")
                    except Exception as e:
                        print(f"[!] Failed to fetch {name}: {e}")

        except Exception as e:
            print(f"CRITICAL SYSTEM ERROR: {e}")


def main():
    extractor = YangDownloader(
        host=ip,
        port=port,
        user=username,
        password=password,
        output_dir=str(script_path.parent.parent / "temp" / "yang_modules" / device_name),
    )
    extractor.download_all()


if __name__ == "__main__":
    main()
