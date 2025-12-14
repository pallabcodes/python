#!/usr/bin/env python3
"""
DocuMind Complete Demo

This script demonstrates DocuMind's capabilities:
1. Repository initialization
2. Code analysis and documentation generation
3. Documentation search and management
4. Export functionality

Usage: python demo.py
"""

import asyncio
import os
import tempfile
from pathlib import Path

# Demo repository content
DEMO_CODE = '''
# example_functions.py
"""
Example functions for DocuMind demonstration.
"""

def calculate_fibonacci(n: int) -> int:
    """
    Calculate the nth Fibonacci number.

    Args:
        n: The position in the Fibonacci sequence (0-indexed)

    Returns:
        The nth Fibonacci number

    Raises:
        ValueError: If n is negative
    """
    if n < 0:
        raise ValueError("n must be non-negative")

    if n == 0:
        return 0
    elif n == 1:
        return 1

    a, b = 0, 1
    for _ in range(2, n + 1):
        a, b = b, a + b
    return b


class DataProcessor:
    """A class for processing data with various operations."""

    def __init__(self, data: list):
        """
        Initialize the DataProcessor.

        Args:
            data: List of data items to process
        """
        self.data = data
        self.processed_count = 0

    def process_items(self, operation: str) -> list:
        """
        Process all items with the specified operation.

        Args:
            operation: The operation to apply ('uppercase', 'lowercase', 'reverse')

        Returns:
            List of processed items
        """
        results = []

        for item in self.data:
            if operation == 'uppercase':
                result = str(item).upper()
            elif operation == 'lowercase':
                result = str(item).lower()
            elif operation == 'reverse':
                result = str(item)[::-1]
            else:
                result = item

            results.append(result)
            self.processed_count += 1

        return results

    def get_statistics(self) -> dict:
        """
        Get processing statistics.

        Returns:
            Dictionary with processing statistics
        """
        return {
            'total_items': len(self.data),
            'processed_count': self.processed_count,
            'remaining_count': len(self.data) - self.processed_count
        }


# JavaScript example
// example.js
/**
 * Calculate factorial of a number
 * @param {number} n - The number to calculate factorial for
 * @returns {number} The factorial result
 */
function factorial(n) {
    if (n < 0) {
        throw new Error("n must be non-negative");
    }

    if (n === 0 || n === 1) {
        return 1;
    }

    let result = 1;
    for (let i = 2; i <= n; i++) {
        result *= i;
    }
    return result;
}

/**
 * User class for managing user data
 */
class User {
    /**
     * Create a new user
     * @param {string} name - User name
     * @param {string} email - User email
     */
    constructor(name, email) {
        this.name = name;
        this.email = email;
    }

    /**
     * Get user display name
     * @returns {string} Formatted display name
     */
    getDisplayName() {
        return `${this.name} <${this.email}>`;
    }
}
'''


async def create_demo_repository():
    """Create a temporary demo repository."""
    # Create temporary directory
    temp_dir = tempfile.mkdtemp(prefix="documind_demo_")

    # Create Python file
    py_file = Path(temp_dir) / "example_functions.py"
    with open(py_file, 'w') as f:
        f.write(DEMO_CODE.split('// JavaScript example')[0].strip())

    # Create JavaScript file
    js_file = Path(temp_dir) / "example.js"
    with open(js_file, 'w') as f:
        f.write("// JavaScript example\n" + DEMO_CODE.split('// JavaScript example')[1].strip())

    # Create README
    readme_file = Path(temp_dir) / "README.md"
    with open(readme_file, 'w') as f:
        f.write("# Demo Repository\n\nExample code for DocuMind demonstration.\n")

    return temp_dir


async def run_demo():
    """Run the complete DocuMind demonstration."""
    print("🚀 DocuMind Complete Demonstration")
    print("=" * 50)

    # Check if we're in development mode
    if not os.getenv("DOCUMIND_DEMO"):
        print("⚠️  This demo requires database access.")
        print("   Make sure DocuMind is properly configured and run:")
        print("   export DOCUMIND_DEMO=1 && python demo.py")
        return

    try:
        # Import after environment check
        from app.db.session import get_db
        from app.services.repository_service import RepositoryService
        from app.services.analysis_service import AnalysisService
        from app.services.documentation_service import DocumentationService

        async for db in get_db():
            repo_service = RepositoryService(db)
            analysis_service = AnalysisService(db)
            doc_service = DocumentationService(db)

            print("\n📁 Step 1: Creating Demo Repository")
            print("-" * 40)

            # Create demo repository
            repo_path = await create_demo_repository()
            print(f"✅ Created demo repository at: {repo_path}")

            # Initialize repository in DocuMind
            repo_data = {
                "name": "documind-demo",
                "full_name": "demo/documind-demo",
                "url": f"file://{repo_path}",
                "clone_url": f"file://{repo_path}",
                "platform": "local",
                "language": "python",
                "is_active": True,
                "analysis_enabled": True,
            }

            repository = await repo_service.create_repository(repo_data)
            repo_id = repository.id
            print(f"✅ Initialized repository in DocuMind (ID: {repo_id})")

            print("\n🔍 Step 2: Analyzing Repository")
            print("-" * 40)

            # Run analysis
            analysis_result = await analysis_service.analyze_repository(repo_id, repo_path)

            print("✅ Analysis completed!")
            print(f"   • Files processed: {analysis_result['files_processed']}")
            print(f"   • Entities found: {analysis_result['entities_found']}")
            print(f"   • Documentation generated: {analysis_result['docs_generated']}")
            print(f"   • Languages detected: {', '.join(analysis_result['languages'])}")

            print("\n📚 Step 3: Exploring Generated Documentation")
            print("-" * 40)

            # Get documentation list
            docs = await doc_service.list_repository_documentation(repo_id, limit=10)

            if docs:
                print(f"✅ Found {len(docs)} documentation entries:")

                for i, doc in enumerate(docs[:5], 1):  # Show first 5
                    print(f"\n{i}. {doc.title}")
                    print(f"   Type: {doc.doc_type} | Status: {doc.status}")
                    print(f"   Quality Score: {doc.quality_score:.2f}" if doc.quality_score else "   Quality Score: N/A")
                    if doc.summary:
                        summary = doc.summary[:80] + "..." if len(doc.summary) > 80 else doc.summary
                        print(f"   Summary: {summary}")
            else:
                print("⚠️  No documentation found")

            print("\n🔎 Step 4: Searching Documentation")
            print("-" * 40)

            # Search for specific terms
            search_terms = ["fibonacci", "process", "calculate"]

            for term in search_terms:
                results = await doc_service.search_documentation(repo_id, term, limit=3)
                if results:
                    print(f"✅ Search '{term}': Found {len(results)} results")
                    for result in results:
                        print(f"   • {result.title}")
                else:
                    print(f"⚠️  Search '{term}': No results found")

            print("\n📊 Step 5: Documentation Statistics")
            print("-" * 40)

            # Get documentation stats
            stats = await doc_service.get_documentation_stats(repo_id)

            print("✅ Documentation Statistics:"            print(f"   • Total documentation: {stats['total_documentations']}")
            print(f"   • Documentation by type: {stats['by_type']}")
            print(f"   • Documentation by status: {stats['by_status']}")
            print(f"   • Average quality: {stats['quality_metrics']['average_quality']:.2f}")

            print("\n📤 Step 6: Exporting Documentation")
            print("-" * 40)

            # Export documentation
            export_result = await doc_service.export_documentation(repo_id, format="markdown")
            export_file = f"documind_demo_export_{repo_id}.md"

            with open(export_file, 'w') as f:
                f.write(export_result['data'])

            print(f"✅ Exported {export_result['total_docs']} documents to {export_file}")

            print("\n🧹 Step 7: Cleanup")
            print("-" * 40)

            # Clean up demo repository
            import shutil
            shutil.rmtree(repo_path)
            print("✅ Cleaned up demo repository")

            if os.path.exists(export_file):
                print(f"✅ Demo export saved as: {export_file}")

    except Exception as e:
        print(f"❌ Demo failed: {e}")
        import traceback
        traceback.print_exc()

    print("\n🎉 DocuMind Demo Complete!")
    print("\nTo use DocuMind with your own repositories:")
    print("1. documind init /path/to/your/repo")
    print("2. documind analyze <repo_id>")
    print("3. documind docs <repo_id>")
    print("4. documind search <repo_id> 'your query'")
    print("\nFor web interface: documind server")


if __name__ == "__main__":
    print("🤖 DocuMind: AI-Powered Documentation Assistant")
    print("   Making documentation effortless and always current")
    print()

    asyncio.run(run_demo())
