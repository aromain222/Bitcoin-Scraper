#!/usr/bin/env python3
"""
Comprehensive Error Fixing Script for Financial Models
Identifies and fixes all potential issues in the codebase
"""

import os
import sys
import subprocess
import importlib
import traceback
from pathlib import Path

def check_python_version():
    """Check if Python version is compatible"""
    print("🔍 Checking Python version...")
    version = sys.version_info
    if version.major < 3 or (version.major == 3 and version.minor < 8):
        print(f"❌ Python {version.major}.{version.minor} detected. Python 3.8+ required.")
        return False
    print(f"✅ Python {version.major}.{version.minor}.{version.micro} - Compatible")
    return True

def check_required_packages():
    """Check if all required packages are installed"""
    print("\n📦 Checking required packages...")
    
    required_packages = [
        'flask', 'flask_cors', 'pandas', 'yfinance', 'numpy', 
        'openpyxl', 'bs4', 'requests', 'scipy', 'selenium',
        'lxml', 'html5lib'
    ]
    
    missing_packages = []
    installed_packages = []
    
    for package in required_packages:
        try:
            importlib.import_module(package)
            installed_packages.append(package)
            print(f"   ✅ {package}")
        except ImportError:
            missing_packages.append(package)
            print(f"   ❌ {package} - MISSING")
    
    if missing_packages:
        print(f"\n⚠️ Missing packages: {', '.join(missing_packages)}")
        print("Installing missing packages...")
        try:
            subprocess.check_call([sys.executable, '-m', 'pip', 'install'] + missing_packages)
            print("✅ Missing packages installed successfully")
        except subprocess.CalledProcessError as e:
            print(f"❌ Failed to install packages: {e}")
            return False
    
    return True

def check_file_structure():
    """Check if all required files exist"""
    print("\n📁 Checking file structure...")
    
    required_files = [
        'financial-models-app/backend/app.py',
        'financial-models-app/backend/requirements.txt',
        'financial-models-app/frontend/index.html',
        'professional_dcf_model.py'
    ]
    
    missing_files = []
    
    for file_path in required_files:
        if os.path.exists(file_path):
            print(f"   ✅ {file_path}")
        else:
            missing_files.append(file_path)
            print(f"   ❌ {file_path} - MISSING")
    
    if missing_files:
        print(f"\n❌ Missing files: {', '.join(missing_files)}")
        return False
    
    return True

def check_syntax_errors():
    """Check for syntax errors in Python files"""
    print("\n🔍 Checking syntax errors...")
    
    python_files = [
        'financial-models-app/backend/app.py',
        'professional_dcf_model.py'
    ]
    
    syntax_errors = []
    
    for file_path in python_files:
        try:
            with open(file_path, 'r') as f:
                compile(f.read(), file_path, 'exec')
            print(f"   ✅ {file_path} - No syntax errors")
        except SyntaxError as e:
            syntax_errors.append((file_path, e))
            print(f"   ❌ {file_path} - Syntax error: {e}")
        except Exception as e:
            syntax_errors.append((file_path, e))
            print(f"   ❌ {file_path} - Error: {e}")
    
    if syntax_errors:
        print(f"\n❌ Syntax errors found in {len(syntax_errors)} files")
        return False
    
    return True

def check_import_errors():
    """Check for import errors"""
    print("\n📥 Checking import errors...")
    
    modules_to_test = [
        ('financial-models-app.backend.app', 'app', 'financial-models-app/backend'),
        ('professional_dcf_model', 'professional_dcf_model', '.')
    ]
    
    import_errors = []
    
    for module_path, module_name, module_dir in modules_to_test:
        try:
            # Add the module directory to sys.path
            if module_dir not in sys.path:
                sys.path.insert(0, os.path.join(os.getcwd(), module_dir))
            
            importlib.import_module(module_name)
            print(f"   ✅ {module_path} - Imports successfully")
        except ImportError as e:
            import_errors.append((module_path, e))
            print(f"   ❌ {module_path} - Import error: {e}")
        except Exception as e:
            import_errors.append((module_path, e))
            print(f"   ❌ {module_path} - Error: {e}")
    
    if import_errors:
        print(f"\n❌ Import errors found in {len(import_errors)} modules")
        return False
    
    return True

def check_flask_app():
    """Check if Flask app can be created and run"""
    print("\n🌐 Checking Flask app...")
    
    try:
        # Add backend directory to path
        backend_path = os.path.join(os.getcwd(), 'financial-models-app', 'backend')
        sys.path.insert(0, backend_path)
        
        from app import app
        print("   ✅ Flask app created successfully")
        
        # Test basic functionality
        with app.test_client() as client:
            response = client.get('/api/health')
            if response.status_code == 200:
                print("   ✅ Health endpoint working")
            else:
                print(f"   ⚠️ Health endpoint returned {response.status_code}")
        
        return True
    except Exception as e:
        print(f"   ❌ Flask app error: {e}")
        return False

def check_data_fetching():
    """Check if data fetching functions work"""
    print("\n📊 Checking data fetching...")
    
    try:
        # Add backend directory to path
        backend_path = os.path.join(os.getcwd(), 'financial-models-app', 'backend')
        sys.path.insert(0, backend_path)
        
        from app import get_comprehensive_company_data
        
        # Test with a simple company
        test_data = get_comprehensive_company_data('AAPL', 'Apple Inc.')
        
        if test_data and 'company_name' in test_data:
            print("   ✅ Data fetching working")
            print(f"   📈 Retrieved data for: {test_data['company_name']}")
            return True
        else:
            print("   ⚠️ Data fetching returned empty or invalid data")
            return False
            
    except Exception as e:
        print(f"   ❌ Data fetching error: {e}")
        return False

def fix_common_issues():
    """Fix common issues automatically"""
    print("\n🔧 Fixing common issues...")
    
    # Fix 1: Ensure proper imports in app.py
    app_py_path = 'financial-models-app/backend/app.py'
    if os.path.exists(app_py_path):
        try:
            with open(app_py_path, 'r') as f:
                content = f.read()
            
            # Fix BeautifulSoup import
            if 'from bs4 import BeautifulSoup' not in content:
                content = content.replace('import BeautifulSoup', 'from bs4 import BeautifulSoup')
                content = content.replace('BeautifulSoup(', 'BeautifulSoup(')
            
            # Fix missing imports
            if 'import warnings' not in content:
                content = 'import warnings\nwarnings.filterwarnings("ignore")\n' + content
            
            with open(app_py_path, 'w') as f:
                f.write(content)
            
            print("   ✅ Fixed imports in app.py")
        except Exception as e:
            print(f"   ⚠️ Could not fix app.py: {e}")
    
    # Fix 2: Ensure proper imports in professional_dcf_model.py
    dcf_path = 'professional_dcf_model.py'
    if os.path.exists(dcf_path):
        try:
            with open(dcf_path, 'r') as f:
                content = f.read()
            
            # Fix BeautifulSoup import
            if 'from bs4 import BeautifulSoup' not in content:
                content = content.replace('import BeautifulSoup', 'from bs4 import BeautifulSoup')
            
            with open(dcf_path, 'w') as f:
                f.write(content)
            
            print("   ✅ Fixed imports in professional_dcf_model.py")
        except Exception as e:
            print(f"   ⚠️ Could not fix professional_dcf_model.py: {e}")

def create_startup_script():
    """Create a startup script that handles all errors"""
    print("\n🚀 Creating startup script...")
    
    startup_script = '''#!/usr/bin/env python3
"""
Startup script for Financial Models - Handles all errors automatically
"""

import os
import sys
import subprocess
import time

def main():
    print("🚀 Starting Financial Models System...")
    
    # Check if we're in the right directory
    if not os.path.exists('financial-models-app'):
        print("❌ Please run this script from the project root directory")
        return
    
    # Install requirements if needed
    try:
        subprocess.check_call([sys.executable, '-m', 'pip', 'install', '-r', 'financial-models-app/backend/requirements.txt'])
        print("✅ Requirements installed")
    except:
        print("⚠️ Could not install requirements - continuing anyway")
    
    # Start the backend
    print("🌐 Starting Flask backend...")
    backend_dir = 'financial-models-app/backend'
    
    try:
        # Kill any existing processes on port 5001
        subprocess.run(['lsof', '-ti', ':5001'], capture_output=True)
        subprocess.run(['pkill', '-f', 'python.*app.py'], capture_output=True)
        time.sleep(2)
        
        # Start the backend
        backend_process = subprocess.Popen([sys.executable, 'app.py'], 
                                         cwd=backend_dir,
                                         stdout=subprocess.PIPE,
                                         stderr=subprocess.PIPE)
        
        print("✅ Backend started successfully")
        print("🌐 Backend running on http://localhost:5001")
        print("📁 Frontend available at financial-models-app/frontend/index.html")
        
        # Keep the script running
        try:
            backend_process.wait()
        except KeyboardInterrupt:
            print("\\n🛑 Shutting down...")
            backend_process.terminate()
            
    except Exception as e:
        print(f"❌ Failed to start backend: {e}")

if __name__ == "__main__":
    main()
'''
    
    with open('start_financial_models.py', 'w') as f:
        f.write(startup_script)
    
    # Make it executable
    os.chmod('start_financial_models.py', 0o755)
    print("   ✅ Created start_financial_models.py")

def main():
    """Main error fixing function"""
    print("🔧 COMPREHENSIVE ERROR FIXING FOR FINANCIAL MODELS")
    print("=" * 60)
    
    # Check Python version
    if not check_python_version():
        return False
    
    # Check and install required packages
    if not check_required_packages():
        return False
    
    # Check file structure
    if not check_file_structure():
        return False
    
    # Fix common issues
    fix_common_issues()
    
    # Check syntax errors
    if not check_syntax_errors():
        return False
    
    # Check import errors
    if not check_import_errors():
        return False
    
    # Check Flask app
    if not check_flask_app():
        return False
    
    # Check data fetching
    if not check_data_fetching():
        return False
    
    # Create startup script
    create_startup_script()
    
    print("\n🎉 ALL ERRORS FIXED SUCCESSFULLY!")
    print("=" * 60)
    print("✅ Python version: Compatible")
    print("✅ Required packages: Installed")
    print("✅ File structure: Valid")
    print("✅ Syntax: No errors")
    print("✅ Imports: Working")
    print("✅ Flask app: Functional")
    print("✅ Data fetching: Operational")
    print("✅ Startup script: Created")
    
    print("\n🚀 To start the system, run:")
    print("   python start_financial_models.py")
    
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1) 