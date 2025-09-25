#!/usr/bin/env python3
"""
Comprehensive Test Script for All Financial Models
Tests all model types and verifies functionality
"""

import os
import sys
import time
from datetime import datetime

def test_data_fetching():
    """Test data fetching functionality"""
    print("🔍 Testing Data Fetching...")
    
    try:
        import sys
        sys.path.append('financial-models-app/backend')
        from app import get_comprehensive_company_data
        
        # Test with Microsoft
        data = get_comprehensive_company_data('MSFT', 'Microsoft Corporation')
        
        if data and 'company_name' in data:
            print("   ✅ Data fetching working")
            print(f"   📊 Company: {data['company_name']}")
            print(f"   💰 Revenue: {data.get('revenue_formatted', 'N/A')}")
            print(f"   📈 EBITDA: {data.get('ebitda_formatted', 'N/A')}")
            print(f"   🏭 Industry: {data.get('industry', 'N/A')}")
            print(f"   🧠 AI Quality Score: {data.get('ai_quality_score', 0)*100:.1f}%")
            return True
        else:
            print("   ❌ Data fetching failed")
            return False
            
    except Exception as e:
        print(f"   ❌ Data fetching error: {e}")
        return False

def test_3_statement_model():
    """Test 3-Statement model"""
    print("\n📊 Testing 3-Statement Model...")
    
    try:
        import sys
        sys.path.append('financial-models-app/backend')
        from three_statement_model import create_three_statement_model
        
        output_file = create_three_statement_model('Microsoft Corporation', 'MSFT')
        
        if os.path.exists(output_file):
            print("   ✅ 3-Statement model created successfully")
            print(f"   📁 File: {output_file}")
            print(f"   📏 Size: {os.path.getsize(output_file):,} bytes")
            return True
        else:
            print("   ❌ 3-Statement model file not found")
            return False
            
    except Exception as e:
        print(f"   ❌ 3-Statement model error: {e}")
        return False

def test_dcf_model():
    """Test DCF model"""
    print("\n📈 Testing DCF Model...")
    
    try:
        import sys
        sys.path.append('financial-models-app/backend')
        from app import create_professional_excel_model, get_comprehensive_company_data
        
        # Get company data
        data = get_comprehensive_company_data('AAPL', 'Apple Inc.')
        
        # Create DCF model
        result = create_professional_excel_model(data, 'dcf')
        
        # Handle both tuple and string returns
        if isinstance(result, tuple):
            output_file = result[0]  # filepath
        else:
            output_file = result
        
        if os.path.exists(output_file):
            print("   ✅ DCF model created successfully")
            print(f"   📁 File: {output_file}")
            print(f"   📏 Size: {os.path.getsize(output_file):,} bytes")
            return True
        else:
            print("   ❌ DCF model file not found")
            return False
            
    except Exception as e:
        print(f"   ❌ DCF model error: {e}")
        return False

def test_ma_model():
    """Test M&A model"""
    print("\n🤝 Testing M&A Model...")
    
    try:
        import sys
        sys.path.append('financial-models-app/backend')
        from app import create_professional_excel_model, get_comprehensive_company_data
        
        # Get company data
        data = get_comprehensive_company_data('MSFT', 'Microsoft Corporation')
        
        # Create M&A model
        result = create_professional_excel_model(data, 'ma')
        
        # Handle both tuple and string returns
        if isinstance(result, tuple):
            output_file = result[0]  # filepath
        else:
            output_file = result
        
        if os.path.exists(output_file):
            print("   ✅ M&A model created successfully")
            print(f"   📁 File: {output_file}")
            print(f"   📏 Size: {os.path.getsize(output_file):,} bytes")
            return True
        else:
            print("   ❌ M&A model file not found")
            return False
            
    except Exception as e:
        print(f"   ❌ M&A model error: {e}")
        return False

def test_lbo_model():
    """Test LBO model"""
    print("\n💰 Testing LBO Model...")
    
    try:
        import sys
        sys.path.append('financial-models-app/backend')
        from app import create_professional_excel_model, get_comprehensive_company_data
        
        # Get company data
        data = get_comprehensive_company_data('TSLA', 'Tesla Inc.')
        
        # Create LBO model
        result = create_professional_excel_model(data, 'lbo')
        
        # Handle both tuple and string returns
        if isinstance(result, tuple):
            output_file = result[0]  # filepath
        else:
            output_file = result
        
        if os.path.exists(output_file):
            print("   ✅ LBO model created successfully")
            print(f"   📁 File: {output_file}")
            print(f"   📏 Size: {os.path.getsize(output_file):,} bytes")
            return True
        else:
            print("   ❌ LBO model file not found")
            return False
            
    except Exception as e:
        print(f"   ❌ LBO model error: {e}")
        return False

def test_comps_model():
    """Test Comps model"""
    print("\n📊 Testing Comps Model...")
    
    try:
        import sys
        sys.path.append('financial-models-app/backend')
        from app import create_professional_excel_model, get_comprehensive_company_data
        
        # Get company data
        data = get_comprehensive_company_data('GOOGL', 'Alphabet Inc.')
        
        # Create Comps model
        result = create_professional_excel_model(data, 'comps')
        
        # Handle both tuple and string returns
        if isinstance(result, tuple):
            output_file = result[0]  # filepath
        else:
            output_file = result
        
        if os.path.exists(output_file):
            print("   ✅ Comps model created successfully")
            print(f"   📁 File: {output_file}")
            print(f"   📏 Size: {os.path.getsize(output_file):,} bytes")
            return True
        else:
            print("   ❌ Comps model file not found")
            return False
            
    except Exception as e:
        print(f"   ❌ Comps model error: {e}")
        return False

def test_ipo_model():
    """Test IPO model"""
    print("\n🚀 Testing IPO Model...")
    
    try:
        import sys
        sys.path.append('financial-models-app/backend')
        from app import create_professional_excel_model, get_comprehensive_company_data
        
        # Get company data
        data = get_comprehensive_company_data('NVDA', 'NVIDIA Corporation')
        
        # Create IPO model
        result = create_professional_excel_model(data, 'ipo')
        
        # Handle both tuple and string returns
        if isinstance(result, tuple):
            output_file = result[0]  # filepath
        else:
            output_file = result
        
        if os.path.exists(output_file):
            print("   ✅ IPO model created successfully")
            print(f"   📁 File: {output_file}")
            print(f"   📏 Size: {os.path.getsize(output_file):,} bytes")
            return True
        else:
            print("   ❌ IPO model file not found")
            return False
            
    except Exception as e:
        print(f"   ❌ IPO model error: {e}")
        return False

def test_options_model():
    """Test Options model"""
    print("\n📉 Testing Options Model...")
    
    try:
        import sys
        sys.path.append('financial-models-app/backend')
        from app import create_professional_excel_model, get_comprehensive_company_data
        
        # Get company data
        data = get_comprehensive_company_data('AMZN', 'Amazon.com Inc.')
        
        # Create Options model
        result = create_professional_excel_model(data, 'options')
        
        # Handle both tuple and string returns
        if isinstance(result, tuple):
            output_file = result[0]  # filepath
        else:
            output_file = result
        
        if os.path.exists(output_file):
            print("   ✅ Options model created successfully")
            print(f"   📁 File: {output_file}")
            print(f"   📏 Size: {os.path.getsize(output_file):,} bytes")
            return True
        else:
            print("   ❌ Options model file not found")
            return False
            
    except Exception as e:
        print(f"   ❌ Options model error: {e}")
        return False

def test_ai_enhancement():
    """Test AI enhancement functionality"""
    print("\n🤖 Testing AI Enhancement...")
    
    try:
        import sys
        sys.path.append('financial-models-app/backend')
        from ai_assumptions_enhancer import enhance_company_data_with_ai
        
        # Test data
        test_data = {
            'company_name': 'Test Company',
            'ticker': 'TEST',
            'revenue': 1000000000,
            'ebitda': 200000000,
            'industry': 'Technology'
        }
        
        enhanced_data = enhance_company_data_with_ai('TEST', 'Test Company', test_data)
        
        if enhanced_data and 'ai_quality_score' in enhanced_data:
            print("   ✅ AI enhancement working")
            print(f"   🎯 Quality Score: {enhanced_data['ai_quality_score']*100:.1f}%")
            print(f"   🧠 Confidence: {enhanced_data.get('ai_confidence_level', 'Unknown')}")
            return True
        else:
            print("   ❌ AI enhancement failed")
            return False
            
    except Exception as e:
        print(f"   ❌ AI enhancement error: {e}")
        return False

def test_flask_app():
    """Test Flask app functionality"""
    print("\n🌐 Testing Flask App...")
    
    try:
        import sys
        sys.path.append('financial-models-app/backend')
        from app import app
        
        with app.test_client() as client:
            # Test health endpoint
            response = client.get('/api/health')
            if response.status_code == 200:
                print("   ✅ Health endpoint working")
                
                # Test model generation endpoint
                test_data = {
                    "company_name": "Test Company",
                    "ticker": "TEST",
                    "models": ["dcf"]
                }
                
                response = client.post('/api/generate', json=test_data)
                if response.status_code == 200:
                    print("   ✅ Model generation endpoint working")
                    return True
                else:
                    print(f"   ⚠️ Model generation returned {response.status_code}")
                    return False
            else:
                print(f"   ❌ Health endpoint returned {response.status_code}")
                return False
                
    except Exception as e:
        print(f"   ❌ Flask app error: {e}")
        return False

def cleanup_test_files():
    """Clean up test files"""
    print("\n🧹 Cleaning up test files...")
    
    test_files = [f for f in os.listdir('.') if f.endswith('.xlsx') and 'Test' in f]
    
    for file in test_files:
        try:
            os.remove(file)
            print(f"   🗑️ Removed: {file}")
        except Exception as e:
            print(f"   ⚠️ Could not remove {file}: {e}")

def main():
    """Main test function"""
    print("🧪 COMPREHENSIVE FINANCIAL MODELS TEST")
    print("=" * 60)
    print(f"🕐 Test started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Track test results
    test_results = {}
    
    # Run all tests
    test_results['data_fetching'] = test_data_fetching()
    test_results['ai_enhancement'] = test_ai_enhancement()
    test_results['3_statement'] = test_3_statement_model()
    test_results['dcf'] = test_dcf_model()
    test_results['ma'] = test_ma_model()
    test_results['lbo'] = test_lbo_model()
    test_results['comps'] = test_comps_model()
    test_results['ipo'] = test_ipo_model()
    test_results['options'] = test_options_model()
    test_results['flask_app'] = test_flask_app()
    
    # Summary
    print("\n" + "=" * 60)
    print("📊 TEST RESULTS SUMMARY")
    print("=" * 60)
    
    passed = sum(test_results.values())
    total = len(test_results)
    
    for test_name, result in test_results.items():
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"   {test_name.replace('_', ' ').title()}: {status}")
    
    print(f"\n🎯 Overall: {passed}/{total} tests passed ({passed/total*100:.1f}%)")
    
    if passed == total:
        print("🎉 ALL TESTS PASSED! System is fully functional.")
    else:
        print("⚠️ Some tests failed. Please check the errors above.")
    
    # Cleanup
    cleanup_test_files()
    
    return passed == total

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1) 