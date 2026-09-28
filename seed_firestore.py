"""Script to seed initial travel destinations into Firestore."""

import logging
from google.cloud import firestore

# IMPORTANT: Hardcode project ID as string
FIRESTORE_PROJECT_ID = "qwiklabs-gcp-01-099df5840de9"
COLLECTION_NAME = "destinations"

INITIAL_DESTINATIONS = [
    {
        "id": "kyoto-japan",
        "name": "Kyoto",
        "country": "Japan",
        "category": "Culture & History",
        "description": "Historical heart of Japan with thousands of classical Buddhist temples, gardens, imperial palaces, and traditional wooden houses.",
        "best_season": "Spring / Autumn",
        "avg_daily_budget_usd": 180.0,
        "highlights": ["Fushimi Inari Shrine", "Arashiyama Bamboo Grove", "Gion District", "Kinkaku-ji"],
        "rating": 4.9,
    },
    {
        "id": "santorini-greece",
        "name": "Santorini",
        "country": "Greece",
        "category": "Beach & Coastal",
        "description": "Iconic Aegean island known for white-washed cubiform houses, blue-domed churches, dramatic volcanic caldera views, and stunning sunsets.",
        "best_season": "Late Spring / Early Autumn",
        "avg_daily_budget_usd": 250.0,
        "highlights": ["Oia Sunset Viewpoint", "Red Beach", "Akrotiri Archaeological Site", "Wine Tasting in Pyrgos"],
        "rating": 4.8,
    },
    {
        "id": "paris-france",
        "name": "Paris",
        "country": "France",
        "category": "Urban & Culinary",
        "description": "A global center for art, fashion, gastronomy, and culture with iconic landmarks, world-class museums, and charming cafe culture.",
        "best_season": "Spring / Fall",
        "avg_daily_budget_usd": 220.0,
        "highlights": ["Eiffel Tower", "Louvre Museum", "Montmartre & Sacré-Cœur", "Seine River Cruise"],
        "rating": 4.7,
    },
    {
        "id": "costa-rica",
        "name": "Costa Rica",
        "country": "Costa Rica",
        "category": "Nature & Adventure",
        "description": "Rugged, rainforested Central American country with coastlines on the Caribbean and Pacific, famous for biodiversity and eco-tourism.",
        "best_season": "December to April",
        "avg_daily_budget_usd": 150.0,
        "highlights": ["Arenal Volcano", "Manuel Antonio National Park", "Monteverde Cloud Forest", "Ziplining & Zip Canopy Tours"],
        "rating": 4.9,
    },
    {
        "id": "banff-canada",
        "name": "Banff National Park",
        "country": "Canada",
        "category": "Mountain & Outdoor",
        "description": "Canada's oldest national park in the heart of the Rocky Mountains, featuring turquoise glacial lakes, dramatic peaks, and abundant wildlife.",
        "best_season": "June to September / December to March",
        "avg_daily_budget_usd": 200.0,
        "highlights": ["Lake Louise", "Moraine Lake", "Banff Gondola", "Icefields Parkway"],
        "rating": 4.9,
    },
]


def seed_database():
    print(f"Connecting to Firestore with project ID: '{FIRESTORE_PROJECT_ID}'...")
    db = firestore.Client(project=FIRESTORE_PROJECT_ID)
    collection_ref = db.collection(COLLECTION_NAME)

    for item in INITIAL_DESTINATIONS:
        doc_id = item["id"]
        data = {k: v for k, v in item.items() if k != "id"}
        collection_ref.document(doc_id).set(data)
        print(f"  ✓ Seeded destination: {doc_id} ({item['name']}, {item['country']})")

    print(f"\nSuccessfully seeded {len(INITIAL_DESTINATIONS)} destinations into '{COLLECTION_NAME}' collection!")


if __name__ == "__main__":
    seed_database()
