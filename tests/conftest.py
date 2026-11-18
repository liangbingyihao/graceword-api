import os
import sys
from pathlib import Path

os.environ.setdefault("COZE_API_TOKEN", "test-token")
os.environ.setdefault("COZE_MAIN_BOT_ID", "test-bot")
os.environ.setdefault("DATABASE_URL", "sqlite:////tmp/graceword-api-test.db")

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / 'app'))
