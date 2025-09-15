import requests
import sys
import json
import os
from datetime import datetime
from pathlib import Path

class AIBotAPITester:
    def __init__(self, base_url="https://pdf-data-vault.preview.emergentagent.com"):
        self.base_url = base_url
        self.api_url = f"{base_url}/api"
        self.test_user_id = None
        self.tests_run = 0
        self.tests_passed = 0
        self.test_results = []

    def log_test(self, name, success, details=""):
        """Log test results"""
        self.tests_run += 1
        if success:
            self.tests_passed += 1
            print(f"✅ {name} - PASSED")
        else:
            print(f"❌ {name} - FAILED: {details}")
        
        self.test_results.append({
            "name": name,
            "success": success,
            "details": details
        })

    def test_health_check(self):
        """Test basic health endpoint"""
        try:
            response = requests.get(f"{self.api_url}/health", timeout=10)
            success = response.status_code == 200
            details = f"Status: {response.status_code}"
            if success:
                data = response.json()
                details += f", Response: {data}"
            self.log_test("Health Check", success, details)
            return success
        except Exception as e:
            self.log_test("Health Check", False, str(e))
            return False

    def test_root_endpoint(self):
        """Test root API endpoint"""
        try:
            response = requests.get(f"{self.api_url}/", timeout=10)
            success = response.status_code == 200
            details = f"Status: {response.status_code}"
            if success:
                data = response.json()
                details += f", Message: {data.get('message', 'No message')}"
            self.log_test("Root Endpoint", success, details)
            return success
        except Exception as e:
            self.log_test("Root Endpoint", False, str(e))
            return False

    def test_user_registration(self):
        """Test user registration"""
        try:
            test_data = {
                "first_name": f"TestUser_{datetime.now().strftime('%H%M%S')}",
                "username": "test_user",
                "phone": "+1234567890"
            }
            
            response = requests.post(f"{self.api_url}/users", json=test_data, timeout=15)
            success = response.status_code == 200
            
            if success:
                user_data = response.json()
                self.test_user_id = user_data.get('id')
                details = f"User created with ID: {self.test_user_id}"
            else:
                details = f"Status: {response.status_code}, Response: {response.text}"
            
            self.log_test("User Registration", success, details)
            return success, self.test_user_id
        except Exception as e:
            self.log_test("User Registration", False, str(e))
            return False, None

    def test_get_user(self, user_id):
        """Test getting user by ID"""
        if not user_id:
            self.log_test("Get User", False, "No user ID provided")
            return False
            
        try:
            response = requests.get(f"{self.api_url}/users/{user_id}", timeout=10)
            success = response.status_code == 200
            
            if success:
                user_data = response.json()
                details = f"Retrieved user: {user_data.get('first_name', 'Unknown')}"
            else:
                details = f"Status: {response.status_code}, Response: {response.text}"
            
            self.log_test("Get User", success, details)
            return success
        except Exception as e:
            self.log_test("Get User", False, str(e))
            return False

    def test_chat_functionality(self, user_id):
        """Test AI chat functionality"""
        if not user_id:
            self.log_test("Chat Functionality", False, "No user ID provided")
            return False
            
        try:
            chat_data = {
                "user_id": user_id,
                "message": "Hello, this is a test message. Please respond briefly."
            }
            
            print("🔄 Sending chat message (this may take a few seconds for AI response)...")
            response = requests.post(f"{self.api_url}/chat", json=chat_data, timeout=30)
            success = response.status_code == 200
            
            if success:
                chat_response = response.json()
                ai_response = chat_response.get('response', '')
                details = f"AI responded with {len(ai_response)} characters"
                if len(ai_response) > 100:
                    details += f": {ai_response[:100]}..."
                else:
                    details += f": {ai_response}"
            else:
                details = f"Status: {response.status_code}, Response: {response.text}"
            
            self.log_test("Chat Functionality", success, details)
            return success
        except Exception as e:
            self.log_test("Chat Functionality", False, str(e))
            return False

    def test_get_chat_history(self, user_id):
        """Test getting chat history"""
        if not user_id:
            self.log_test("Get Chat History", False, "No user ID provided")
            return False
            
        try:
            response = requests.get(f"{self.api_url}/chat/{user_id}", timeout=10)
            success = response.status_code == 200
            
            if success:
                chat_history = response.json()
                details = f"Retrieved {len(chat_history)} chat messages"
            else:
                details = f"Status: {response.status_code}, Response: {response.text}"
            
            self.log_test("Get Chat History", success, details)
            return success
        except Exception as e:
            self.log_test("Get Chat History", False, str(e))
            return False

    def test_file_upload(self, user_id):
        """Test file upload functionality"""
        if not user_id:
            self.log_test("File Upload", False, "No user ID provided")
            return False
            
        try:
            # Create a simple test image file
            test_content = b"Test image content for API testing"
            
            files = {
                'file': ('test_image.jpg', test_content, 'image/jpeg')
            }
            data = {
                'user_id': user_id
            }
            
            print("🔄 Uploading test file (this may take a few seconds for AI analysis)...")
            response = requests.post(f"{self.api_url}/upload", files=files, data=data, timeout=45)
            success = response.status_code == 200
            
            if success:
                file_data = response.json()
                details = f"File uploaded: {file_data.get('filename', 'Unknown')}"
                description = file_data.get('description', '')
                if description:
                    details += f", Analysis: {description[:100]}..."
            else:
                details = f"Status: {response.status_code}, Response: {response.text}"
            
            self.log_test("File Upload", success, details)
            return success
        except Exception as e:
            self.log_test("File Upload", False, str(e))
            return False

    def test_get_user_files(self, user_id):
        """Test getting user files"""
        if not user_id:
            self.log_test("Get User Files", False, "No user ID provided")
            return False
            
        try:
            response = requests.get(f"{self.api_url}/files/{user_id}", timeout=10)
            success = response.status_code == 200
            
            if success:
                files = response.json()
                details = f"Retrieved {len(files)} files"
            else:
                details = f"Status: {response.status_code}, Response: {response.text}"
            
            self.log_test("Get User Files", success, details)
            return success
        except Exception as e:
            self.log_test("Get User Files", False, str(e))
            return False

    def test_web_search(self, user_id):
        """Test web search functionality"""
        if not user_id:
            self.log_test("Web Search", False, "No user ID provided")
            return False
            
        try:
            search_data = {
                "user_id": user_id,
                "query": "What is artificial intelligence?"
            }
            
            print("🔄 Performing web search (this may take a few seconds for AI processing)...")
            response = requests.post(f"{self.api_url}/websearch", json=search_data, timeout=30)
            success = response.status_code == 200
            
            if success:
                search_result = response.json()
                summary = search_result.get('summary', '')
                details = f"Search completed, summary length: {len(summary)} characters"
                if len(summary) > 100:
                    details += f": {summary[:100]}..."
            else:
                details = f"Status: {response.status_code}, Response: {response.text}"
            
            self.log_test("Web Search", success, details)
            return success
        except Exception as e:
            self.log_test("Web Search", False, str(e))
            return False

    def test_get_search_history(self, user_id):
        """Test getting search history"""
        if not user_id:
            self.log_test("Get Search History", False, "No user ID provided")
            return False
            
        try:
            response = requests.get(f"{self.api_url}/search/{user_id}", timeout=10)
            success = response.status_code == 200
            
            if success:
                search_history = response.json()
                details = f"Retrieved {len(search_history)} search results"
            else:
                details = f"Status: {response.status_code}, Response: {response.text}"
            
            self.log_test("Get Search History", success, details)
            return success
        except Exception as e:
            self.log_test("Get Search History", False, str(e))
            return False

    def run_all_tests(self):
        """Run all API tests"""
        print("🚀 Starting AI Chatbot API Tests")
        print(f"🌐 Testing against: {self.base_url}")
        print("=" * 60)
        
        # Basic connectivity tests
        if not self.test_health_check():
            print("❌ Health check failed - stopping tests")
            return False
            
        self.test_root_endpoint()
        
        # User management tests
        success, user_id = self.test_user_registration()
        if not success or not user_id:
            print("❌ User registration failed - stopping user-dependent tests")
            self.print_summary()
            return False
            
        self.test_get_user(user_id)
        
        # Feature tests (these may take longer due to AI processing)
        print("\n🤖 Testing AI-powered features (may take longer)...")
        self.test_chat_functionality(user_id)
        self.test_get_chat_history(user_id)
        self.test_file_upload(user_id)
        self.test_get_user_files(user_id)
        self.test_web_search(user_id)
        self.test_get_search_history(user_id)
        
        self.print_summary()
        return self.tests_passed == self.tests_run

    def print_summary(self):
        """Print test summary"""
        print("\n" + "=" * 60)
        print("📊 TEST SUMMARY")
        print("=" * 60)
        print(f"Total Tests: {self.tests_run}")
        print(f"Passed: {self.tests_passed}")
        print(f"Failed: {self.tests_run - self.tests_passed}")
        print(f"Success Rate: {(self.tests_passed/self.tests_run*100):.1f}%" if self.tests_run > 0 else "0%")
        
        # Show failed tests
        failed_tests = [test for test in self.test_results if not test['success']]
        if failed_tests:
            print("\n❌ FAILED TESTS:")
            for test in failed_tests:
                print(f"  • {test['name']}: {test['details']}")
        
        print("=" * 60)

def main():
    tester = AIBotAPITester()
    success = tester.run_all_tests()
    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main())