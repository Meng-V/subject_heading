"""Test script for the V2 workflow with multi-image and 65X support."""
import asyncio
import httpx
import json
from pathlib import Path


BASE_URL = "http://localhost:8000/v2"


async def test_v2_workflow():
    """Test the complete V2 workflow."""
    async with httpx.AsyncClient(timeout=60.0) as client:
        print("🧪 Testing AI Subject Heading Assistant V2 Workflow\n")
        print("=" * 70)
        
        # 1. Health Check
        print("\n1️⃣  Health Check...")
        response = await client.get(f"{BASE_URL}/api/health")
        print(f"   Status: {response.json()}\n")
        
        # 2. Check Authority Stats
        print("2️⃣  Authority Statistics...")
        response = await client.get(f"{BASE_URL}/api/authority-stats")
        result = response.json()
        if result.get("success"):
            print(f"   Stats: {json.dumps(result['stats'], indent=4)}\n")
        
        # 3. Test Topic Generation with Types
        print("3️⃣  Testing Topic Generation (with types)...")
        metadata = {
            "title": "The Art and History of Chinese Calligraphy",
            "author": "Wang Wei and Zhang Li",
            "publisher": "Beijing Cultural Press",
            "pub_place": "Beijing",
            "pub_year": "2023",
            "summary": "A comprehensive exploration of Chinese calligraphy from ancient times to the present day. This volume examines the philosophical foundations, technical mastery, and cultural significance of this revered art form. Special focus on the Ming and Qing dynasties.",
            "table_of_contents": [
                "Introduction to Chinese Calligraphy",
                "Historical Development and Evolution",
                "The Four Treasures of Study: Brush, Ink, Paper, Inkstone",
                "Major Script Styles: Seal, Clerical, Regular, Running, Cursive",
                "Ming Dynasty Masters and Innovations",
                "Qing Dynasty Traditions and Reforms",
                "Calligraphy and Chinese Philosophy",
                "Contemporary Practice and Preservation",
                "Appendix: Chronology of Chinese Dynasties"
            ],
            "preface_snippets": [
                "This book represents a synthesis of traditional scholarship and modern research into the art of Chinese calligraphy.",
                "We hope this volume will serve both scholars and practitioners interested in this ancient art form."
            ],
            "raw_pages": []
        }
        
        response = await client.post(
            f"{BASE_URL}/api/generate-topics",
            json={"metadata": metadata}
        )
        topics_result = response.json()
        print(f"   Generated Topics:\n")
        for topic in topics_result.get("topics", []):
            print(f"      • {topic['topic']}")
            print(f"        Type: {topic['type']}")
        print()
        
        if not topics_result.get("success"):
            print("❌ Topic generation failed")
            return
        
        # 4. Test Multi-Vocabulary Authority Matching
        print("4️⃣  Testing Multi-Vocabulary Authority Matching...")
        topics_data = topics_result["topics"]
        
        response = await client.post(
            f"{BASE_URL}/api/authority-match-typed",
            json={
                "topics": topics_data,
                "vocabularies": ["lcsh", "fast"]
            }
        )
        authority_result = response.json()
        
        print(f"   Authority Matches:\n")
        for match in authority_result.get("matches", []):
            print(f"      Topic: \"{match['topic']}\" [{match['topic_type']}]")
            for candidate in match.get("authority_candidates", [])[:3]:
                print(f"         → {candidate['label']}")
                print(f"           Vocab: {candidate['vocabulary'].upper()}, Score: {candidate['score']:.3f}")
                print(f"           URI: {candidate['uri']}")
            print()
        
        if not authority_result.get("success"):
            print("❌ Authority matching failed")
            return
        
        # 5. Test 65X MARC Generation
        print("5️⃣  Testing MARC 65X Generation...")
        
        response = await client.post(
            f"{BASE_URL}/api/build-65x",
            json={"topics_with_candidates": authority_result["matches"]}
        )
        marc_result = response.json()
        
        if marc_result.get("success"):
            print(f"   📝 Generated {len(marc_result['subjects_65x'])} MARC 65X Fields:\n")
            for field in marc_result["subjects_65x"]:
                # Build MARC string
                marc_str = f"{field['tag']} {field['ind1']}{field['ind2']}"
                for sf in field['subfields']:
                    marc_str += f" ${sf['code']} {sf['value']}"
                
                print(f"      {marc_str}.")
                print(f"      └─ Vocabulary: {field['vocabulary'].upper()}")
                if field.get('explanation'):
                    print(f"      └─ {field['explanation']}")
                print()
        
        # 6. Test Final Submission
        print("6️⃣  Testing Final Submission...")
        final_data = {
            "metadata": metadata,
            "ai_topics": topics_result["topics"],
            "lcsh_matches": authority_result.get("matches", []),
            "librarian_selected": [],
            "marc_fields": [],
            "marc_65x_fields": marc_result.get("subjects_65x", [])
        }
        
        response = await client.post(
            f"{BASE_URL}/api/submit-final",
            json=final_data
        )
        final_result = response.json()
        print(f"   Final Submission: {json.dumps(final_result, indent=2)}\n")
        
        print("=" * 70)
        print("✅ V2 Workflow test completed successfully!\n")
        print("📊 Summary:")
        print(f"   - Topics generated: {len(topics_result.get('topics', []))}")
        print(f"   - Authority matches: {len(authority_result.get('matches', []))}")
        print(f"   - MARC 65X fields: {len(marc_result.get('subjects_65x', []))}")
        print(f"   - Record UUID: {final_result.get('uuid', 'N/A')}")


async def initialize_v2_data():
    """Initialize authority schemas and sample data for V2."""
    async with httpx.AsyncClient(timeout=30.0) as client:
        print("🔧 Initializing V2 authority schemas...")
        response = await client.post(f"{BASE_URL}/api/initialize-authorities")
        print(f"   {response.json()}\n")
        
        print("📚 Indexing sample authority data (LCSH + FAST)...")
        response = await client.post(f"{BASE_URL}/api/index-sample-authorities")
        print(f"   {response.json()}\n")


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "init":
        print("Initializing V2 data...")
        asyncio.run(initialize_v2_data())
    else:
        print("Running V2 workflow test...")
        asyncio.run(test_v2_workflow())
        print("\n💡 To initialize V2 data, run: python test_workflow_v2.py init")
