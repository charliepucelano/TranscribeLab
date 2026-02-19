import asyncio
from unittest.mock import MagicMock, AsyncMock, patch
import sys
import os

# Add project root to path
# Add backend to path to ensure app module is found
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

# Mock motor module BEFORE importing app modules
sys.modules["motor"] = MagicMock()
sys.modules["motor.motor_asyncio"] = MagicMock()

# Mock app.core.database.db
with patch("app.core.database.db") as mock_db:
    # Setup the mock to return an AsyncMock for get_db
    mock_db_instance = MagicMock()
    mock_db.get_db.return_value = mock_db_instance
    
    # Mock templates collection
    mock_templates_collection = MagicMock()
    mock_db_instance.templates = mock_templates_collection

    # Import the function AFTER mocking db
    from app.services.templates import get_template, TEMPLATES
    from app.services.summarization import generate_summary

    async def test_get_template_builtin():
        print("\n--- Testing Built-in Template ---")
        # Ensure find_one returns None (no custom template)
        mock_templates_collection.find_one = AsyncMock(return_value=None)
        
        tmpl = await get_template("General Meeting", "en", user_id="user123")
        print(f"Template Name: {tmpl.name}")
        print(f"Is Custom: {tmpl.name == 'General Meeting'}")
        assert tmpl.name == "General Meeting"
        assert "Executive Summary" in tmpl.output_structure

    async def test_get_template_custom():
        print("\n--- Testing Custom Template ---")
        # Mock a custom template return
        custom_data = {
            "name": "Custom Meeting",
            "system_instruction": "Custom Instruction",
            "language": "en",
            "user_id": "user123"
        }
        mock_templates_collection.find_one = AsyncMock(return_value=custom_data)
        
        tmpl = await get_template("Custom Meeting", "en", user_id="user123")
        print(f"Template Name: {tmpl.name}")
        print(f"System Instruction: {tmpl.system_instruction}")
        assert tmpl.name == "Custom Meeting"
        assert tmpl.system_instruction == "Custom Instruction"

    async def test_generate_summary_metadata():
        print("\n--- Testing Summary Metadata ---")
        # Mock get_template to return a simple template
        with patch("app.services.summarization.get_template", new_callable=AsyncMock) as mock_get_tmpl:
            mock_tmpl = MagicMock()
            mock_tmpl.name = "Test Template"
            mock_tmpl.system_instruction = "Sys Prompt"
            mock_tmpl.output_structure = "Struct"
            mock_get_tmpl.return_value = mock_tmpl
            
            # Mock settings and aiohttp
            with patch("app.services.summarization.settings") as mock_settings, \
                 patch("aiohttp.ClientSession") as mock_session_cls:
                
                mock_settings.OLLAMA_URL = "http://mock-ollama"
                
                # Mock response
                mock_session = AsyncMock()
                mock_response = AsyncMock()
                mock_response.status = 200
                mock_response.json.return_value = {"response": "This is the summary."}
                mock_response.__aenter__.return_value = mock_response
                
                mock_session.post.return_value = mock_response
                mock_session.__aenter__.return_value = mock_session
                mock_session_cls.return_value = mock_session

                summary = await generate_summary("Transcript text", user_id="user123")
                
                print("Generated Summary:")
                print(summary)
                
                assert "This is the summary." in summary
                assert "**Summary Details:**" in summary
                assert "- Model:" in summary
                assert "- Template: Test Template (en)" in summary

    async def main():
        await test_get_template_builtin()
        await test_get_template_custom()
        await test_generate_summary_metadata()

    if __name__ == "__main__":
        asyncio.run(main())
