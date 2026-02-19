import sys
import os
from unittest.mock import MagicMock, AsyncMock, patch

# 1. Setup Paths
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

# 2. Aggressively Mock Dependent Modules needed for imports to succeed
sys.modules["motor"] = MagicMock()
sys.modules["motor.motor_asyncio"] = MagicMock()
sys.modules["app.core.config"] = MagicMock()
sys.modules["app.core.config.settings"] = MagicMock()

# Create a mock for app.core.database that has 'db'
mock_database_module = MagicMock()
mock_db_instance = MagicMock()
mock_database_module.db = mock_db_instance
sys.modules["app.core.database"] = mock_database_module

# Now we can import the target modules
# We need to make sure app.core is also happy
sys.modules["app.core"] = MagicMock()
sys.modules["app.core"].database = mock_database_module

import asyncio
# We import the file we want to test
# It will import 'app.core.database' which we have mocked in sys.modules
from app.services.templates import get_template, TEMPLATES, MeetingTemplate
from app.services.summarization import generate_summary

async def test_logic():
    print("Starting Tests...")
    
    # 1. Test Built-in
    # Mock db.get_db().templates.find_one to return None
    mock_db_instance.get_db.return_value.templates.find_one = AsyncMock(return_value=None)
    
    tmpl = await get_template("General Meeting", "en", user_id="u1")
    print(f"Built-in Check: {tmpl.name == 'General Meeting'}")
    
    # 2. Test Custom
    custom_doc = {
        "name": "Custom 1",
        "system_instruction": "Custom Sys",
        "language": "en"
    }
    mock_db_instance.get_db.return_value.templates.find_one = AsyncMock(return_value=custom_doc)
    
    tmpl = await get_template("Custom 1", "en", user_id="u1")
    print(f"Custom Check: {tmpl.name == 'Custom 1' and tmpl.system_instruction == 'Custom Sys'}")
    
    # 3. Test Summary Metadata
    print("\n--- Testing Summary Metadata ---")
    
    # We need to mock aiohttp in summarization
    with patch("aiohttp.ClientSession") as mock_session_cls:
        # Create a Mock for the context manager returned by ClientSession()
        mock_ctx_manager = MagicMock()
        mock_session_cls.return_value = mock_ctx_manager
        
        # Define mock_session and mock_response first
        mock_session = AsyncMock()
        mock_response = AsyncMock()
        mock_response.status = 200
        mock_response.json.return_value = {"response": "AI Summary"}
        
        # The context manager must have an async __aenter__
        mock_ctx_manager.__aenter__ = AsyncMock(return_value=mock_session)
        mock_ctx_manager.__aexit__ = AsyncMock(return_value=None)
        
        # The response context manager returned by session.post()
        mock_resp_ctx_manager = MagicMock()
        mock_session.post.return_value = mock_resp_ctx_manager
        mock_resp_ctx_manager.__aenter__ = AsyncMock(return_value=mock_response)
        mock_resp_ctx_manager.__aexit__ = AsyncMock(return_value=None)
        
        # We need to ensure get_template returns something valid in generate_summary
        # Let's mock get_template locally to be sure
        with patch("app.services.summarization.get_template", new_callable=AsyncMock) as mock_get_tmpl_summ:
             mock_get_tmpl_summ.return_value = MeetingTemplate("TmplName", "Inst", "Struct")
             
             summary = await generate_summary("text", user_id="u1")
             print(f"Summary Metadata Check: {'**Summary Details:**' in summary}")
             print(f"Summary Content: {summary}")

if __name__ == "__main__":
    asyncio.run(test_logic())
