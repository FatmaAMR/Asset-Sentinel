import sys
import os
from unittest.mock import MagicMock

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'services'))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))


sys.modules['llama_cpp'] = MagicMock()
sys.modules['llama_cpp.Llama'] = MagicMock()

# Mock config
mock_settings = MagicMock()
mock_settings.MODEL_PATH = "fake/path/model.gguf"
mock_config = MagicMock()
mock_config.settings = mock_settings
sys.modules['config'] = mock_config
sys.modules['config.settings'] = mock_config