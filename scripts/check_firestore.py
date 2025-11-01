"""
Firestore'da notların olup olmadığını kontrol eden script
"""
import os
from google.cloud import firestore
from google.oauth2 import service_account
from dotenv import load_dotenv

# .env dosyasını yükle
load_dotenv()

def main():
    project_id = os.getenv("FIREBASE_PROJECT_ID")
    cred_path = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")
    
    print(f"Firebase Project ID: {project_id}")
    print(f"Credentials Path: {cred_path}")
    print("-" * 50)
    
    # Credentials'ı ayarla
    credentials = None
    if cred_path and os.path.exists(cred_path):
        print(f"Service account dosyası bulundu: {cred_path}")
        credentials = service_account.Credentials.from_service_account_file(cred_path)
    else:
        print("Service account dosyası bulunamadı, Application Default Credentials kullanılıyor.")
    
    try:
        client = firestore.Client(project=project_id, credentials=credentials)
        col = client.collection("notes")
        
        print(f"\nFirestore Collection: 'notes'")
        print("=" * 50)
        
        # Tüm notları getir
        docs = list(col.stream())
        total_count = len(docs)
        
        print(f"\nToplam Not Sayısı: {total_count}")
        
        if total_count == 0:
            print("\n⚠️  Hiç not bulunamadı!")
            print("\nOlası nedenler:")
            print("1. Backend henüz hiç not oluşturmadı")
            print("2. Farklı bir Firebase projesine bağlanılıyor")
            print("3. Farklı bir collection adı kullanılıyor")
            print("4. Firestore Security Rules verileri gizliyor")
        else:
            print(f"\n{'ID':<30} {'Owner ID':<30} {'Title':<20} {'Updated At'}")
            print("-" * 100)
            
            # İlk 20 notu göster
            for i, doc in enumerate(docs[:20]):
                data = doc.to_dict() or {}
                owner_id = data.get("owner_id", "N/A")
                title = data.get("title", "N/A")[:18]
                updated_at = data.get("updated_at", "N/A")
                print(f"{doc.id:<30} {owner_id:<30} {title:<20} {updated_at}")
            
            if total_count > 20:
                print(f"\n... ve {total_count - 20} not daha")
            
            # Owner ID'lere göre grupla
            owner_counts = {}
            for doc in docs:
                data = doc.to_dict() or {}
                owner_id = data.get("owner_id", "unknown")
                owner_counts[owner_id] = owner_counts.get(owner_id, 0) + 1
            
            print(f"\n{'Owner ID':<40} {'Not Sayısı'}")
            print("-" * 60)
            for owner_id, count in sorted(owner_counts.items(), key=lambda x: x[1], reverse=True):
                print(f"{owner_id:<40} {count}")
        
        print("\n" + "=" * 50)
        print("Firebase Console'da kontrol için:")
        print(f"1. Proje: {project_id}")
        print("2. Firestore Database -> 'notes' collection")
        print("3. Eğer boşsa, backend'in doğru projeye bağlandığından emin olun")
        
    except Exception as e:
        print(f"\n❌ Hata oluştu: {e}")
        print("\nKontrol edilecekler:")
        print("1. FIREBASE_PROJECT_ID doğru mu?")
        print("2. GOOGLE_APPLICATION_CREDENTIALS dosyası doğru yolda mı?")
        print("3. Service account'un Firestore'a erişim izni var mı?")

if __name__ == "__main__":
    main()

