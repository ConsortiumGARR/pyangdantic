import os
import sys
import logging
import importlib
from pathlib import Path
from dotenv import load_dotenv

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


IP =   os.environ["DEVICE_IP"]
PORT = os.environ["RESTCONF_PORT"]
USER = os.environ["DEVICE_USER"]
PASS = os.environ["DEVICE_PASS"]
DEVICE_NAME = os.environ["DEVICE_NAME"]

# Dynamic import with importlib
sys.path.append(str(script_path.parent.parent))
module_path = f"temp.restconf_clients.{DEVICE_NAME}"

try:
    module = importlib.import_module(module_path)
    DeviceClient = module.RestconfClient
    logger.debug(f"Successfully imported module: {module_path}")
except ImportError as e:
    logger.error(f"Failed to import module {module_path}: {e}")
    sys.exit(1)

client = DeviceClient(
    management_ip=IP,
    port=int(PORT),
    username=USER,
    password=PASS,
    verify=False
)

# Extract all data node properties and test retrieval + pydantic validation
for attr_name, prop in vars(type(client.data)).items():
    if isinstance(prop, property):
        navigator = prop.fget(client.data)
        print(f"Testing retrieval + validation of {navigator._path}")
        logger.info(f"Testing retrieval + validation of {navigator._path}")
        
        try:
            pydantic_instance = navigator.retrieve(content="config", depth="unbounded")
            print(f"OK: loaded into Pydantic model {pydantic_instance.__class__.__name__}")
            logger.info(f"OK: loaded into Pydantic model {pydantic_instance.__class__.__name__}")
            logger.debug(f"Data received: {pydantic_instance.model_dump_json()[:200]}...")
        except Exception as e:
            logger.error(f"FAIL: {navigator._path} - Error: {e}", exc_info=True)
            print(f"FAIL: {navigator._path} - Error: {e}", exc_info=True)