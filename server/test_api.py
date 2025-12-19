"""Simple test script to verify API endpoints"""

import asyncio

import httpx

BASE_URL = "http://localhost:8080"


async def test_health():
    """Test health endpoint"""
    async with httpx.AsyncClient() as client:
        response = await client.get(f"{BASE_URL}/health")
        print("🏥 Health Check:")
        print(f"   Status: {response.status_code}")
        print(f"   Response: {response.json()}\n")
        return response.status_code == 200


async def test_graph_overview():
    """Test graph overview endpoint"""
    async with httpx.AsyncClient() as client:
        response = await client.get(f"{BASE_URL}/api/graph/overview")
        print("🕸️  Graph Overview:")
        print(f"   Status: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"   Nodes: {len(data['nodes'])}")
            print(f"   Edges: {len(data['edges'])}")
            print(f"   Sample nodes: {[n['label'] for n in data['nodes'][:3]]}\n")
        else:
            print(f"   Error: {response.text}\n")
        return response.status_code == 200


async def test_search():
    """Test search endpoint"""
    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{BASE_URL}/api/graph/search",
            json={"query": "machine learning", "limit": 3},
        )
        print("🔍 Search Test:")
        print(f"   Status: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            results = data.get("results", [])
            print(f"   Results: {len(results)}")
            for item in results:
                node = item.get("node", {})
                score = item.get("score", 0.0)
                print(f"   - {node.get('label','unknown')} (score: {score:.3f})")
        else:
            print(f"   Error: {response.text}")
        print()
        return response.status_code == 200


async def test_node_detail():
    """Test node detail endpoint"""
    async with httpx.AsyncClient() as client:
        # First get overview to get a node ID
        overview = await client.get(f"{BASE_URL}/api/graph/overview")
        if overview.status_code != 200 or not overview.json()["nodes"]:
            print("⚠️  No nodes available for detail test\n")
            return False

        node_id = overview.json()["nodes"][0]["id"]

        response = await client.get(f"{BASE_URL}/api/graph/node/{node_id}")
        print(f"📄 Node Detail Test (ID: {node_id}):")
        print(f"   Status: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"   Node: {data['node']['label']}")
            print(f"   Recommendations: {len(data['recommendations'])}")
        else:
            print(f"   Error: {response.text}")
        print()
        return response.status_code == 200


async def test_upload_text():
    """Test text upload endpoint"""
    async with httpx.AsyncClient(timeout=60.0) as client:
        test_doc = {
            "title": "Test Document",
            "content": "This is a test document about artificial intelligence and neural networks.",
            "type": "text",
        }

        response = await client.post(f"{BASE_URL}/api/ingest/upload", data=test_doc)
        print("📤 Upload Text Test:")
        print(f"   Status: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"   Success: {data['success']}")
            print(f"   Doc ID: {data['doc_id']}")
        else:
            print(f"   Error: {response.text}")
        print()
        return response.status_code == 200


async def main():
    """Run all tests"""
    print("=" * 60)
    print("🧪 MarkMind API Test Suite")
    print("=" * 60)
    print()

    tests = [
        ("Health Check", test_health),
        ("Graph Overview", test_graph_overview),
        ("Search", test_search),
        ("Node Detail", test_node_detail),
        # ("Upload Text", test_upload_text),  # Comment out to avoid creating test data
    ]

    results = []
    for name, test_func in tests:
        try:
            success = await test_func()
            results.append((name, success))
        except Exception as e:
            print(f"❌ {name} failed with exception: {e}\n")
            results.append((name, False))

    print("=" * 60)
    print("📊 Test Results Summary")
    print("=" * 60)
    passed = sum(1 for _, success in results if success)
    total = len(results)

    for name, success in results:
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status} - {name}")

    print()
    print(f"Total: {passed}/{total} tests passed")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
