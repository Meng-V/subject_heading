"""Test script for AI Subject Heading Assistant API."""
import httpx
import json

BASE_URL = "http://localhost:8000"

def test_health():
    """Test health endpoint."""
    print("\n1️⃣  Testing health check...")
    r = httpx.get(f"{BASE_URL}/api/health")
    print(f"   Status: {r.status_code}")
    print(f"   Response: {r.json()}")
    return r.status_code == 200

def test_initialize_authorities():
    """Initialize Weaviate schemas."""
    print("\n2️⃣  Initializing authority schemas...")
    r = httpx.post(f"{BASE_URL}/api/initialize-authorities")
    print(f"   Status: {r.status_code}")
    print(f"   Response: {r.json()}")
    return r.status_code == 200

def test_index_sample_authorities():
    """Index sample LCSH/FAST data."""
    print("\n3️⃣  Indexing sample authorities (this may take a minute)...")
    r = httpx.post(f"{BASE_URL}/api/index-sample-authorities", timeout=120.0)
    print(f"   Status: {r.status_code}")
    print(f"   Response: {r.json()}")
    return r.status_code == 200

def test_authority_stats():
    """Check authority index stats."""
    print("\n4️⃣  Checking authority stats...")
    r = httpx.get(f"{BASE_URL}/api/authority-stats")
    print(f"   Status: {r.status_code}")
    print(f"   Response: {json.dumps(r.json(), indent=2)}")
    return r.status_code == 200

def test_generate_topics():
    """Test topic generation with sample metadata."""
    print("\n5️⃣  Testing topic generation...")
    
    metadata = {
        "title": "中国书法艺术 - Chinese Calligraphy Art",
        "author": "Wang Wei",
        "publisher": "Beijing Art Press",
        "pub_place": "Beijing",
        "pub_year": "2023",
        "summary": "A comprehensive guide to Chinese calligraphy covering techniques from the Ming and Qing dynasties. Includes chapters on brush selection, ink preparation, and famous calligraphers.",
        "table_of_contents": [
            "Introduction to Chinese Calligraphy",
            "History of Calligraphy in China",
            "Ming Dynasty Masters",
            "Qing Dynasty Innovations",
            "Brush Techniques",
            "Contemporary Practice"
        ],
        "preface_snippets": [],
        "raw_pages": []
    }
    
    r = httpx.post(
        f"{BASE_URL}/api/generate-topics",
        json={"metadata": metadata},
        timeout=60.0
    )
    print(f"   Status: {r.status_code}")
    if r.status_code == 200:
        data = r.json()
        print(f"   Topics generated: {len(data.get('topics', []))}")
        for topic in data.get('topics', []):
            print(f"   - [{topic['type']}] {topic['topic']}")
        return data.get('topics', [])
    else:
        print(f"   Error: {r.text}")
        return []

def test_authority_match(topics):
    """Test authority matching."""
    print("\n6️⃣  Testing authority matching...")
    
    # API expects list of topic strings
    r = httpx.post(
        f"{BASE_URL}/api/authority-match",
        json={"topics": [t["topic"] for t in topics]},
        timeout=60.0
    )
    print(f"   Status: {r.status_code}")
    if r.status_code == 200:
        data = r.json()
        matches = data.get('matches', [])
        print(f"   Matches found: {len(matches)}")
        for match in matches[:3]:  # Show first 3
            print(f"   - Topic: {match['topic']}")
            for cand in match.get('authority_candidates', [])[:2]:
                print(f"     → [{cand['vocabulary']}] {cand['label']} (score: {cand['score']:.2f})")
        return matches
    else:
        print(f"   Error: {r.text}")
        return []

def test_build_65x(matches):
    """Test 65X MARC field generation."""
    print("\n7️⃣  Testing 65X MARC generation...")
    
    r = httpx.post(
        f"{BASE_URL}/api/build-65x",
        json={"topics_with_candidates": matches},
        timeout=60.0
    )
    print(f"   Status: {r.status_code}")
    if r.status_code == 200:
        data = r.json()
        subjects = data.get('subjects_65x', [])
        print(f"   65X fields generated: {len(subjects)}")
        for subj in subjects[:5]:  # Show first 5
            print(f"   - {subj['tag']} {subj['ind1']}{subj['ind2']} [{subj['vocabulary']}]")
            print(f"     {subj['heading_string']}")
        return subjects
    else:
        print(f"   Error: {r.text}")
        return []

def main():
    print("=" * 60)
    print("🧪 AI Subject Heading Assistant - API Test")
    print("=" * 60)
    
    # Basic tests
    if not test_health():
        print("❌ Health check failed!")
        return
    
    # Initialize and index
    test_initialize_authorities()
    test_index_sample_authorities()
    test_authority_stats()
    
    # Full workflow test
    topics = test_generate_topics()
    
    if topics:
        matches = test_authority_match(topics)
        
        if matches:
            subjects = test_build_65x(matches)
    
    print("\n" + "=" * 60)
    print("✅ Test complete!")
    print("=" * 60)

if __name__ == "__main__":
    main()
