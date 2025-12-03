"""Test script for the complete workflow."""
import asyncio
import httpx
import json
from pathlib import Path


BASE_URL = "http://localhost:8000"


async def test_workflow():
    """Test the complete workflow."""
    async with httpx.AsyncClient(timeout=30.0) as client:
        print("🧪 Testing AI Subject Heading Assistant Workflow\n")
        
        # 1. Health Check
        print("1️⃣  Health Check...")
        response = await client.get(f"{BASE_URL}/api/health")
        print(f"   Status: {response.json()}\n")
        
        # 2. Check LCSH Stats
        print("2️⃣  LCSH Statistics...")
        response = await client.get(f"{BASE_URL}/api/lcsh-stats")
        print(f"   Stats: {response.json()}\n")
        
        # 3. Test Topic Generation (without OCR for now)
        print("3️⃣  Testing Topic Generation...")
        metadata = {
            "title": "The Art of Chinese Calligraphy",
            "author": "Wang Wei",
            "publisher": "Beijing Press",
            "pub_year": "2023",
            "summary": "A comprehensive guide to the history and techniques of Chinese calligraphy, covering the evolution from ancient scripts to modern practice. Includes detailed analysis of brush techniques, ink selection, and the philosophical foundations of the art form.",
            "toc": [
                "Introduction to Chinese Calligraphy",
                "Historical Development",
                "The Four Treasures of Study",
                "Basic Strokes and Techniques",
                "Regular Script (Kaishu)",
                "Running Script (Xingshu)",
                "Cursive Script (Caoshu)",
                "Seal Script (Zhuanshu)",
                "Contemporary Practice"
            ]
        }
        
        response = await client.post(
            f"{BASE_URL}/api/generate-topics",
            json={"metadata": metadata}
        )
        topics_result = response.json()
        print(f"   Generated Topics: {json.dumps(topics_result, indent=2)}\n")
        
        if not topics_result.get("success"):
            print("❌ Topic generation failed")
            return
        
        # Extract topic strings
        topics = [t["topic"] for t in topics_result["topics"]]
        
        # 4. Test LCSH Matching
        print("4️⃣  Testing LCSH Matching...")
        response = await client.post(
            f"{BASE_URL}/api/lcsh-match",
            json={"topics": topics}
        )
        lcsh_result = response.json()
        print(f"   LCSH Matches: {json.dumps(lcsh_result, indent=2)}\n")
        
        if not lcsh_result.get("success"):
            print("❌ LCSH matching failed")
            return
        
        # 5. Test MARC 650 Generation
        print("5️⃣  Testing MARC 650 Generation...")
        
        # Select first match from each topic
        selections = []
        for match_result in lcsh_result["matches"]:
            if match_result["matches"]:
                selections.append(match_result["matches"][0])
        
        if selections:
            response = await client.post(
                f"{BASE_URL}/api/marc650",
                json={"lcsh_selections": selections}
            )
            marc_result = response.json()
            print(f"   MARC Fields: {json.dumps(marc_result, indent=2)}\n")
            
            # Print MARC in readable format
            if marc_result.get("success"):
                print("   📝 MARC 650 Fields (formatted):")
                for field in marc_result["marc_fields"]:
                    marc_string = f"{field['tag']} {field['ind1']}{field['ind2']}"
                    marc_string += f" $a {field['subfield_a']}"
                    if field.get('subfield_x'):
                        marc_string += f" $x {field['subfield_x']}"
                    if field.get('subfield_y'):
                        marc_string += f" $y {field['subfield_y']}"
                    if field.get('subfield_z'):
                        marc_string += f" $z {field['subfield_z']}"
                    if field.get('subfield_0'):
                        marc_string += f" $0 {field['subfield_0']}"
                    print(f"      {marc_string}.")
                print()
            
            # 6. Test Final Submission
            print("6️⃣  Testing Final Submission...")
            final_data = {
                "metadata": metadata,
                "ai_topics": topics_result["topics"],
                "lcsh_matches": lcsh_result["matches"],
                "librarian_selected": selections,
                "marc_fields": marc_result.get("marc_fields", [])
            }
            
            response = await client.post(
                f"{BASE_URL}/api/submit-final",
                json=final_data
            )
            final_result = response.json()
            print(f"   Final Submission: {json.dumps(final_result, indent=2)}\n")
        
        print("✅ Workflow test completed successfully!")


async def initialize_sample_data():
    """Initialize LCSH schema and sample data."""
    async with httpx.AsyncClient(timeout=30.0) as client:
        print("🔧 Initializing LCSH schema...")
        response = await client.post(f"{BASE_URL}/api/initialize-lcsh")
        print(f"   {response.json()}\n")
        
        print("📚 Indexing sample LCSH data...")
        response = await client.post(f"{BASE_URL}/api/index-lcsh-sample")
        print(f"   {response.json()}\n")


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "init":
        print("Initializing sample data...")
        asyncio.run(initialize_sample_data())
    else:
        print("Running workflow test...")
        asyncio.run(test_workflow())
        print("\n💡 To initialize sample data, run: python test_workflow.py init")
