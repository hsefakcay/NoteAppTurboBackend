import argparse
import os
from datetime import datetime, timezone
from google.cloud import firestore
from google.oauth2 import service_account
from dotenv import load_dotenv

# .env dosyasını yükle
load_dotenv()

parser = argparse.ArgumentParser(description="Seed Firestore with sample notes")
parser.add_argument("--user", required=True, help="Firebase uid")
parser.add_argument("--count", type=int, default=3, help="Number of notes to create")

if __name__ == "__main__":
    args = parser.parse_args()
    project_id = os.getenv("FIREBASE_PROJECT_ID")
    cred_path = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")
    
    # Credentials'ı ayarla
    credentials = None
    if cred_path and os.path.exists(cred_path):
        credentials = service_account.Credentials.from_service_account_file(cred_path)
    
    client = firestore.Client(project=project_id, credentials=credentials)
    col = client.collection("notes")
    for i in range(args.count):
        doc = col.document()
        doc.set({
            "title": f"Deneme {i+1}",
            "content": f"İçerik {i+1}",
            "pinned": (i % 2 == 0),
            "updated_at": datetime.now(timezone.utc),
            "owner_id": args.user,
        })
    print(f"Seed tamamlandı: {args.count} not eklendi (owner={args.user}).")
