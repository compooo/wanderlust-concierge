"""Firestore catalog tools for Wanderlust Concierge."""

import logging
from typing import Any, Optional
from google.cloud import firestore
from google.adk.tools import ToolContext

# IMPORTANT: Hardcoded project ID as required for Firestore client on Agent Platform
FIRESTORE_PROJECT_ID = "qwiklabs-gcp-01-099df5840de9"
COLLECTION_NAME = "destinations"

_db_client: Optional[firestore.Client] = None


def get_db_client() -> firestore.Client:
    global _db_client
    if _db_client is None:
        _db_client = firestore.Client(project=FIRESTORE_PROJECT_ID)
    return _db_client


def list_destinations(category: Optional[str] = None) -> list[dict[str, Any]]:
    """List travel destinations from the Firestore catalog, optionally filtered by category.

    Args:
        category: Optional category filter (e.g. 'Culture & History', 'Beach & Coastal', 'Urban & Culinary', 'Nature & Adventure', 'Mountain & Outdoor').

    Returns:
        List of destination dictionaries containing name, country, category, daily budget, and highlights.
    """
    db = get_db_client()
    collection_ref = db.collection(COLLECTION_NAME)

    if category:
        docs = collection_ref.where("category", "==", category).stream()
    else:
        docs = collection_ref.stream()

    results = []
    for doc in docs:
        data = doc.to_dict()
        data["id"] = doc.id
        results.append(data)
    return results


def get_destination_details(destination_id: str) -> dict[str, Any]:
    """Get full details for a specific travel destination from Firestore by its ID.

    Args:
        destination_id: The unique ID of the destination (e.g. 'kyoto-japan', 'paris-france', 'santorini-greece').

    Returns:
        Dictionary containing destination details, or an error message if not found.
    """
    db = get_db_client()
    doc_ref = db.collection(COLLECTION_NAME).document(destination_id)
    doc = doc_ref.get()

    if not doc.exists:
        return {"error": f"Destination '{destination_id}' not found in catalog."}

    data = doc.to_dict()
    data["id"] = doc.id
    return data


def add_destination(
    destination_id: str,
    name: str,
    country: str,
    category: str,
    description: str,
    avg_daily_budget_usd: float,
    highlights: list[str],
) -> dict[str, Any]:
    """Add or update a travel destination in the Firestore catalog.

    Args:
        destination_id: Unique ID/slug for the destination (e.g., 'rome-italy').
        name: Name of the destination city or region.
        country: Country name.
        category: Category (e.g. 'Culture & History', 'Beach & Coastal', 'Urban & Culinary', 'Nature & Adventure').
        description: Description of the destination.
        avg_daily_budget_usd: Estimated average daily budget in USD.
        highlights: List of key highlights or attractions.

    Returns:
        Dictionary confirming successful addition.
    """
    db = get_db_client()
    doc_ref = db.collection(COLLECTION_NAME).document(destination_id)
    item_data = {
        "name": name,
        "country": country,
        "category": category,
        "description": description,
        "avg_daily_budget_usd": avg_daily_budget_usd,
        "highlights": highlights,
    }
    doc_ref.set(item_data)
    item_data["id"] = destination_id
    return {
        "status": "success",
        "message": f"Successfully added '{name}' ({country}) to the destination catalog.",
        "destination": item_data,
    }


def calculate_trip_budget(
    avg_daily_budget_usd: float,
    num_days: int,
    num_travelers: int = 1,
    target_currency: str = "USD",
    currency_rate_to_usd: float = 1.0,
) -> dict[str, Any]:
    """Calculate an itemized trip budget breakdown for accommodations, dining, activities, and contingency.

    Args:
        avg_daily_budget_usd: Average daily budget per person in USD (from destination catalog).
        num_days: Total number of days for the trip.
        num_travelers: Total number of travelers (default: 1).
        target_currency: Target currency code (e.g. 'USD', 'EUR', 'JPY', 'GBP').
        currency_rate_to_usd: Exchange rate of target currency per 1 USD (default: 1.0).

    Returns:
        Dictionary containing total cost, breakdown by category (lodging, food, activities, buffer), and currency details.
    """
    if num_days <= 0 or num_travelers <= 0 or avg_daily_budget_usd <= 0:
        return {"error": "num_days, num_travelers, and avg_daily_budget_usd must be greater than 0."}

    total_usd = avg_daily_budget_usd * num_days * num_travelers
    lodging_usd = total_usd * 0.40
    food_usd = total_usd * 0.30
    activities_usd = total_usd * 0.20
    contingency_usd = total_usd * 0.10

    total_converted = total_usd * currency_rate_to_usd

    return {
        "num_days": num_days,
        "num_travelers": num_travelers,
        "avg_daily_per_person_usd": avg_daily_budget_usd,
        "total_budget_usd": round(total_usd, 2),
        "target_currency": target_currency.upper(),
        "total_budget_target_currency": round(total_converted, 2),
        "breakdown_usd": {
            "accommodations": round(lodging_usd, 2),
            "dining_and_food": round(food_usd, 2),
            "activities_and_tours": round(activities_usd, 2),
            "emergency_buffer": round(contingency_usd, 2),
        },
    }


def get_destination_weather(destination_name: str) -> dict[str, Any]:
    """Fetch live real-time weather data and forecast for a travel destination using Open-Meteo public API.

    Args:
        destination_name: Name of the city or destination (e.g. 'Kyoto', 'Paris', 'Santorini', 'Banff', 'Rome').

    Returns:
        Dictionary with location details, current temperature (°C and °F), wind speed, weather condition, and timezone.
    """
    import json
    import urllib.parse
    import urllib.request

    try:
        encoded_name = urllib.parse.quote(destination_name)
        geo_url = f"https://geocoding-api.open-meteo.com/v1/search?name={encoded_name}&count=1"

        req = urllib.request.Request(geo_url, headers={"User-Agent": "WanderlustConcierge/1.0"})
        with urllib.request.urlopen(req, timeout=5) as response:
            geo_data = json.loads(response.read().decode())

        results = geo_data.get("results")
        if not results:
            return {"error": f"Could not find coordinates for destination '{destination_name}'."}

        loc = results[0]
        lat, lon = loc["latitude"], loc["longitude"]
        city = loc.get("name", destination_name)
        country = loc.get("country", "")
        timezone = loc.get("timezone", "UTC")

        weather_url = f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}&current_weather=true"
        req_w = urllib.request.Request(weather_url, headers={"User-Agent": "WanderlustConcierge/1.0"})
        with urllib.request.urlopen(req_w, timeout=5) as resp_w:
            weather_data = json.loads(resp_w.read().decode())

        current = weather_data.get("current_weather", {})
        temp_c = current.get("temperature")
        temp_f = round((temp_c * 9 / 5) + 32, 1) if temp_c is not None else None
        windspeed = current.get("windspeed")

        w_code = current.get("weathercode", 0)
        code_descriptions = {
            0: "Clear sky",
            1: "Mainly clear",
            2: "Partly cloudy",
            3: "Overcast",
            45: "Foggy",
            48: "Depositing rime fog",
            51: "Light drizzle",
            53: "Moderate drizzle",
            55: "Dense drizzle",
            61: "Slight rain",
            63: "Moderate rain",
            65: "Heavy rain",
            71: "Slight snow",
            73: "Moderate snow",
            75: "Heavy snow",
            80: "Slight rain showers",
            81: "Moderate rain showers",
            82: "Violent rain showers",
            95: "Thunderstorm",
        }
        condition = code_descriptions.get(w_code, f"Weather code {w_code}")

        return {
            "destination": city,
            "country": country,
            "latitude": lat,
            "longitude": lon,
            "timezone": timezone,
            "temperature_celsius": temp_c,
            "temperature_fahrenheit": temp_f,
            "windspeed_kmh": windspeed,
            "condition": condition,
        }
    except Exception as e:
        return {"error": f"Failed to fetch weather for '{destination_name}': {str(e)}"}


def geocode_address(address: str) -> dict[str, Any]:
    """Convert an address or place name into geographic coordinates using Google Maps Geocoding API.

    Args:
        address: The address or place name to geocode (e.g. 'Kyoto Station', 'Eiffel Tower', 'Colosseum Rome').

    Returns:
        Dictionary containing formatted address, latitude, longitude, and place_id.
    """
    import json
    import os
    import urllib.parse
    import urllib.request
    from dotenv import load_dotenv

    load_dotenv()
    api_key = os.getenv("GOOGLE_MAPS_API_KEY")
    if not api_key:
        return {"error": "GOOGLE_MAPS_API_KEY environment variable is not set."}

    try:
        encoded_address = urllib.parse.quote(address)
        url = f"https://maps.googleapis.com/maps/api/geocode/json?address={encoded_address}&key={api_key}"
        req = urllib.request.Request(url, headers={"User-Agent": "WanderlustConcierge/1.0"})
        with urllib.request.urlopen(req, timeout=5) as response:
            data = json.loads(response.read().decode())

        results = data.get("results")
        if not results:
            return {"error": f"No geocoding results found for address '{address}'."}

        first_res = results[0]
        location = first_res.get("geometry", {}).get("location", {})
        return {
            "address": address,
            "formatted_address": first_res.get("formatted_address"),
            "location": {
                "latitude": location.get("lat"),
                "longitude": location.get("lng"),
            },
            "place_id": first_res.get("place_id"),
        }
    except Exception as e:
        return {"error": f"Geocoding API call failed for '{address}': {str(e)}"}


def find_nearby_places(
    latitude: float,
    longitude: float,
    place_type: str = "restaurant",
    radius_meters: float = 1000.0,
) -> list[dict[str, Any]]:
    """Find nearby places of a given type around a coordinate location using Google Places API (New).

    Args:
        latitude: Center latitude coordinate.
        longitude: Center longitude coordinate.
        place_type: Type of place to search for (e.g. 'restaurant', 'tourist_attraction', 'cafe', 'museum', 'lodging').
        radius_meters: Search radius in meters (default: 1000.0).

    Returns:
        List of nearby place dictionaries containing name, address, location (lat/lng), and rating.
    """
    import json
    import os
    import urllib.request
    from dotenv import load_dotenv

    load_dotenv()
    api_key = os.getenv("GOOGLE_MAPS_API_KEY")
    if not api_key:
        return [{"error": "GOOGLE_MAPS_API_KEY environment variable is not set."}]

    try:
        url = "https://places.googleapis.com/v1/places:searchNearby"
        headers = {
            "Content-Type": "application/json",
            "X-Goog-Api-Key": api_key,
            "X-Goog-FieldMask": "places.displayName,places.formattedAddress,places.location,places.rating",
            "User-Agent": "WanderlustConcierge/1.0",
        }
        payload = json.dumps(
            {
                "includedTypes": [place_type],
                "maxResultCount": 5,
                "locationRestriction": {
                    "circle": {
                        "center": {
                            "latitude": latitude,
                            "longitude": longitude,
                        },
                        "radius": radius_meters,
                    }
                },
            }
        ).encode("utf-8")

        req = urllib.request.Request(url, data=payload, headers=headers, method="POST")
        with urllib.request.urlopen(req, timeout=5) as response:
            data = json.loads(response.read().decode())

        places = data.get("places", [])
        results = []
        for p in places:
            display_name = p.get("displayName", {}).get("text", "")
            address = p.get("formattedAddress", "")
            loc = p.get("location", {})
            rating = p.get("rating")
            results.append(
                {
                    "name": display_name,
                    "address": address,
                    "location": {
                        "latitude": loc.get("latitude"),
                        "longitude": loc.get("longitude"),
                    },
                    "rating": rating,
                }
            )
        return results
    except Exception as e:
        return [{"error": f"Places API (New) call failed: {str(e)}"}]


def generate_destination_image(
    prompt: str,
    tool_context: ToolContext,
) -> dict[str, Any]:
    """Generate a scenic travel or destination image using gemini-3.1-flash-lite-image in the global region,
    save it with tool_context.save_artifact for Playground Artifacts, and upload it to the public Cloud Storage bucket.

    Args:
        prompt: Detailed description of the travel image to generate (e.g. 'A scenic view of Kyoto cherry blossoms at sunset').
        tool_context: ADK ToolContext automatically injected by framework.

    Returns:
        Dictionary containing image generation status and the public Cloud Storage https URL (https://storage.googleapis.com/<bucket>/<filename>).
    """
    import uuid
    from google import genai
    from google.genai import types
    from google.cloud import storage

    BUCKET_NAME = "wanderlust-concierge-media-099df584"
    PROJECT_ID = "qwiklabs-gcp-01-099df5840de9"

    try:
        # Step 1: Initialize GenAI Client with Vertex AI in global location
        client = genai.Client(vertexai=True, project=PROJECT_ID, location="global")

        # Step 2: Generate content with gemini-3.1-flash-lite-image
        response = client.models.generate_content(
            model="gemini-3.1-flash-lite-image",
            contents=prompt,
        )

        image_bytes = None
        mime_type = "image/jpeg"
        if response.candidates and response.candidates[0].content and response.candidates[0].content.parts:
            for part in response.candidates[0].content.parts:
                if part.inline_data:
                    image_bytes = part.inline_data.data
                    mime_type = part.inline_data.mime_type or mime_type
                    break

        if not image_bytes:
            return {"error": "Failed to extract image bytes from generated response."}

        # Step 3: Save as ADK session artifact for Playground Artifacts panel
        unique_id = uuid.uuid4().hex[:8]
        filename = f"destination_{unique_id}.jpg"
        artifact_part = types.Part.from_bytes(data=image_bytes, mime_type=mime_type)
        tool_context.save_artifact(filename=filename, artifact=artifact_part)

        # Step 4: Upload image bytes directly to public GCS bucket
        storage_client = storage.Client(project=PROJECT_ID)
        bucket = storage_client.bucket(BUCKET_NAME)
        blob = bucket.blob(filename)
        blob.upload_from_string(image_bytes, content_type=mime_type)

        public_url = f"https://storage.googleapis.com/{BUCKET_NAME}/{filename}"

        return {
            "status": "success",
            "prompt": prompt,
            "filename": filename,
            "public_url": public_url,
        }
    except Exception as e:
        return {"error": f"Image generation failed: {str(e)}"}


def generate_destination_video(
    prompt: str,
    tool_context: ToolContext,
) -> dict[str, Any]:
    """Generate a short scenic video for a travel destination using Google's Omni model (gemini-omni-flash-preview) in the global region,
    save it with tool_context.save_artifact for Playground Artifacts, and upload it to the public Cloud Storage bucket.

    Args:
        prompt: Detailed description of the travel destination video to generate (e.g. 'A scenic drone video of Amalfi Coast cliffs and turquoise ocean waves').
        tool_context: ADK ToolContext automatically injected by framework.

    Returns:
        Dictionary containing video generation status and the public Cloud Storage https URL (https://storage.googleapis.com/<bucket>/<filename>).
    """
    import base64
    import uuid
    from google import genai
    from google.genai import types
    from google.cloud import storage

    BUCKET_NAME = "wanderlust-concierge-media-099df584"
    PROJECT_ID = "qwiklabs-gcp-01-099df5840de9"

    try:
        # Step 1: Initialize GenAI Client with Vertex AI in global location
        client = genai.Client(vertexai=True, project=PROJECT_ID, location="global")

        # Step 2: Generate video with gemini-omni-flash-preview via Interactions API
        interaction = client.interactions.create(
            model="gemini-omni-flash-preview",
            input=prompt,
        )

        video_data = None
        if hasattr(interaction, "output_video") and interaction.output_video:
            video_data = getattr(interaction.output_video, "data", None)
        if not video_data and hasattr(interaction, "model_dump"):
            video_data = interaction.model_dump().get("output_video", {}).get("data")

        video_bytes = None
        mime_type = "video/mp4"

        if isinstance(video_data, str):
            video_bytes = base64.b64decode(video_data)
        elif isinstance(video_data, bytes):
            video_bytes = video_data

        if not video_bytes:
            return {"error": "Failed to extract video bytes from generated response."}

        # Step 3: Save as ADK session artifact for Playground Artifacts panel
        unique_id = uuid.uuid4().hex[:8]
        filename = f"destination_video_{unique_id}.mp4"
        artifact_part = types.Part.from_bytes(data=video_bytes, mime_type=mime_type)
        tool_context.save_artifact(filename=filename, artifact=artifact_part)

        # Step 4: Upload video bytes directly to public GCS bucket (no local file)
        storage_client = storage.Client(project=PROJECT_ID)
        bucket = storage_client.bucket(BUCKET_NAME)
        blob = bucket.blob(filename)
        blob.upload_from_string(video_bytes, content_type=mime_type)

        public_url = f"https://storage.googleapis.com/{BUCKET_NAME}/{filename}"

        return {
            "status": "success",
            "prompt": prompt,
            "filename": filename,
            "public_url": public_url,
        }
    except Exception as e:
        return {"error": f"Video generation failed: {str(e)}"}




