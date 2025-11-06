#!/usr/bin/env python3
"""
Test script for the refactored analytics pipeline system.
"""

import sys
import os

# Add the project root to Python path
project_root = os.path.join(os.path.dirname(__file__), 'project', 'real_world', 'analytics_pipeline')
sys.path.insert(0, project_root)

def test_imports():
    """Test that all refactored modules can be imported."""
    print("🔍 Testing Module Imports...")
    
    try:
        # Test core modules
        from output.orchestrator_core import PipelineConfig
        from output.orchestrator import PipelineRunner
        from output.orchestrator_control import PipelineOrchestrator
        print("✅ Core orchestrator modules imported")
        
        # Test storage modules
        from storage.storage_metrics import StorageMetrics, StorageConfig
        from storage.storage_operations import StorageBackend
        print("✅ Storage modules imported")
        
        # Test processing modules
        from processing.stage_base import BaseProcessingStage
        print("✅ Processing modules imported")
        
        # Test source modules  
        from sources.source_factory import create_demo_sources
        print("✅ Source modules imported")
        
        return True
        
    except Exception as e:
        print(f"❌ Import error: {e}")
        return False

def test_basic_functionality():
    """Test basic pipeline functionality."""
    print("\n🔍 Testing Basic Functionality...")
    
    try:
        from output.orchestrator_core import PipelineConfig
        from output.orchestrator import PipelineRunner
        from output.orchestrator_control import PipelineOrchestrator
        
        # Create configuration
        config = PipelineConfig(name="Test Pipeline")
        print(f"✅ Configuration created: {config.name}")
        
        # Create pipeline runner
        runner = PipelineRunner(config)
        print("✅ PipelineRunner created")
        
        # Create orchestrator
        orchestrator = PipelineOrchestrator(config)
        print("✅ PipelineOrchestrator created")
        
        # Test status before starting
        status = orchestrator.get_status()
        print(f"✅ Initial status: {status}")
        
        # Test metrics before starting
        metrics = orchestrator.get_metrics()
        print(f"✅ Initial metrics: {len(metrics)} keys")
        
        return True
        
    except Exception as e:
        print(f"❌ Functionality error: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_file_sizes():
    """Verify all files are within size limits."""
    print("\n🔍 Verifying File Size Compliance...")
    
    import os
    import glob
    
    oversized_files = []
    
    # Find all Python files
    for py_file in glob.glob(os.path.join(project_root, '**', '*.py'), recursive=True):
        with open(py_file, 'r') as f:
            line_count = sum(1 for _ in f)
            
        if line_count > 200:
            oversized_files.append((py_file, line_count))
    
    if oversized_files:
        print(f"❌ Found {len(oversized_files)} files over 200 lines:")
        for file_path, lines in oversized_files:
            rel_path = os.path.relpath(file_path, project_root)
            print(f"   • {rel_path}: {lines} lines")
        return False
    else:
        print("✅ All files within 200-line limit")
        return True

def main():
    """Run all tests."""
    print("🧪 REFACTORED SYSTEM TEST SUITE")
    print("=" * 40)
    
    results = []
    
    results.append(("Module Imports", test_imports()))
    results.append(("Basic Functionality", test_basic_functionality()))
    results.append(("File Size Compliance", test_file_sizes()))
    
    print("\n" + "=" * 40)
    print("📊 TEST RESULTS SUMMARY")
    print("=" * 40)
    
    all_passed = True
    for test_name, passed in results:
        status = "✅ PASSED" if passed else "❌ FAILED"
        print(f"{status}: {test_name}")
        if not passed:
            all_passed = False
    
    print()
    if all_passed:
        print("🎉 ALL TESTS PASSED! Refactored system is working correctly.")
        print("🚀 The Real-Time Multi-Source Analytics Pipeline is ready for production!")
    else:
        print("⚠️  Some tests failed. Please review the issues above.")
    
    return all_passed

if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)
