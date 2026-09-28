# ruff: noqa
import datetime
import json
from pathlib import Path
from zoneinfo import ZoneInfo

from a2ui.basic_catalog.provider import BasicCatalog
from a2ui.schema.manager import A2uiSchemaManager
from google.adk.agents import Agent
from google.adk.agents.callback_context import CallbackContext
from google.adk.apps import App
from google.adk.code_executors import AgentEngineSandboxCodeExecutor
from google.adk.memory import VertexAiMemoryBankService
from google.adk.models import Gemini
from google.adk.tools.preload_memory_tool import PreloadMemoryTool
from google.genai import types

from app.a2ui_utils import a2ui_callback
from app.tools import (
    list_destinations,
    get_destination_details,
    add_destination,
    calculate_trip_budget,
    get_destination_weather,
    geocode_address,
    find_nearby_places,
    generate_destination_image,
    generate_destination_video,
)

PROJECT_ID = "qwiklabs-gcp-01-099df5840de9"
LOCATION = "us-east1"


def _get_agent_engine_id() -> str | None:
    metadata_path = Path(__file__).parent.parent / "deployment_metadata.json"
    if metadata_path.exists():
        try:
            with open(metadata_path) as f:
                meta = json.load(f)
                runtime_id = meta.get("remote_agent_runtime_id", "")
                return runtime_id.split("/")[-1] if runtime_id else None
        except Exception:
            pass
    return None


ENGINE_ID = _get_agent_engine_id() or "4462352548166107136"

memory_service = VertexAiMemoryBankService(
    project=PROJECT_ID,
    location=LOCATION,
    agent_engine_id=ENGINE_ID,
)


def _get_sandbox_code_executor() -> AgentEngineSandboxCodeExecutor:
    metadata_path = Path(__file__).parent.parent / "deployment_metadata.json"
    agent_engine_id = None
    if metadata_path.exists():
        try:
            with open(metadata_path) as f:
                meta = json.load(f)
                agent_engine_id = meta.get("remote_agent_runtime_id")
        except Exception:
            pass
    return AgentEngineSandboxCodeExecutor(agent_engine_resource_name=agent_engine_id)


async def auto_save_memory_callback(callback_context: CallbackContext):
    """Sends the session's events to Memory Bank for memory generation."""
    try:
        await callback_context.add_session_to_memory()
    except Exception as e:
        print(f"Memory save callback status: {e}")
    return None


def get_current_time(query: str) -> str:
    """Simulates getting the current time for a city.

    Args:
        query: The name of the city to get the current time for.

    Returns:
        A string with the current time information.
    """
    if "sf" in query.lower() or "san francisco" in query.lower():
        tz_identifier = "America/Los_Angeles"
    else:
        return f"Sorry, I don't have timezone information for query: {query}."

    tz = ZoneInfo(tz_identifier)
    now = datetime.datetime.now(tz)
    return f"The current time for query {query} is {now.strftime('%Y-%m-%d %H:%M:%S %Z%z')}"


schema_manager = A2uiSchemaManager(
    version="0.8",
    catalogs=[BasicCatalog.get_config("0.8")],
)

instruction = schema_manager.generate_system_prompt(
    role_description=(
        "You are Wanderlust Concierge, an expert travel assistant. "
        "Pay special attention to and remember all user dietary restrictions and allergies "
        "(such as peanuts, gluten, shellfish, dairy, nuts, or eggs) mentioned in conversations. "
        "Always account for these allergies when recommending travel destinations, dining options, or itineraries. "
        "Use your tools to list or search travel destinations in your catalog, fetch destination details, "
        "add new destinations, calculate estimated trip budgets, check real live weather forecasts, "
        "geocode addresses into coordinates, find nearby points of interest, generate scenic travel images, "
        "generate scenic travel videos using gemini-omni-flash-preview, execute Python code calculations in a secure sandbox, or access recalled user memories."
    ),
    workflow_description="Analyze the request and return structured UI when appropriate.",
    ui_description=(
        "Keep every surface tiny and flat: ONE Card > ONE Column > a few Text rows. "
        "Never nest a Card inside a Card. "
        "Use ONLY these components: Card, Column, Row, Text, and Image. Do not use "
        "Table or Heading (unsupported), or Buttons, actions, or forms (they do "
        "nothing in adk web). "
        "You may include one Image component, but only when you have a public https "
        "URL for the image (for example the URL an image tool returns after uploading "
        "to a public bucket). Set the Image url to that exact https link, for example "
        "{\"Image\": {\"url\": {\"literalString\": \"https://...\"}}}. Never point an "
        "Image at a bare filename, an artifact name, or a non-http(s) path. If you do "
        "not have a public URL, add a short Text line noting the image instead. "
        "No markdown in text; use the usageHint property ('h1', 'h2', 'body') for "
        "headings and emphasis. "
        "Output ONLY the raw A2UI JSON array — no prose, and never wrap it in "
        "<a2a_datapart_json> tags or 'kind'/'data'/'metadata' objects."
    ),
    include_schema=True,
    include_examples=True,
)


root_agent = Agent(
    name="root_agent",
    model=Gemini(
        model="gemini-flash-latest",
        retry_options=types.HttpRetryOptions(attempts=3),
    ),
    code_executor=_get_sandbox_code_executor(),
    instruction=instruction,
    after_model_callback=a2ui_callback,
    after_agent_callback=auto_save_memory_callback,
    tools=[
        PreloadMemoryTool(),
        list_destinations,
        get_destination_details,
        add_destination,
        calculate_trip_budget,
        get_destination_weather,
        geocode_address,
        find_nearby_places,
        generate_destination_image,
        generate_destination_video,
        get_current_time,
    ],
)

app = App(
    root_agent=root_agent,
    name="app",
)
