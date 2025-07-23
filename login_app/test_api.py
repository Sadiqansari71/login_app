import requests
import json
import time

class APITester:
    def __init__(self):
        self.base_url = "http://127.0.0.1:5000/api"
        self.test_email = "testuser@example.com"
        self.token = None
    
    def print_response(self, title, response):
        """Pretty print API response"""
        print(f"\n{title}")
        print("-" * len(title))
        print(f"Status Code: {response.status_code}")
        try:
            print(f"Response: {json.dumps(response.json(), indent=2)}")
        except:
            print(f"Response: {response.text}")
    
    def test_registration(self):
        """Test user registration"""
        print("TESTING USER REGISTRATION")
        response = requests.post(
            f"{self.base_url}/register",
            json={"email": self.test_email}
        )
        self.print_response("Registration Result", response)
        return response.status_code == 201
    
    def test_otp_request(self):
        """Test OTP request"""
        print("\nTESTING OTP REQUEST")
        response = requests.post(
            f"{self.base_url}/request-otp",
            json={"email": self.test_email}
        )
        self.print_response("OTP Request Result", response)
        return response.status_code == 200
    
    def test_otp_verification(self, otp_code):
        """Test OTP verification"""
        print("\nTESTING OTP VERIFICATION")
        response = requests.post(
            f"{self.base_url}/verify-otp",
            json={"email": self.test_email, "otp": otp_code}
        )
        self.print_response("OTP Verification Result", response)
        
        if response.status_code == 200:
            self.token = response.json().get('token')
        
        return response.status_code == 200
    
    def test_profile_access(self):
        """Test protected profile endpoint"""
        print("\nTESTING PROFILE ACCESS")
        if not self.token:
            print("ERROR: No token available for testing")
            return False
        
        headers = {"Authorization": f"Bearer {self.token}"}
        response = requests.get(f"{self.base_url}/profile", headers=headers)
        self.print_response("Profile Access Result", response)
        return response.status_code == 200
    
    def run_complete_test(self):
        """Run complete API test flow"""
        print("STARTING COMPLETE API TEST")
        print("=" * 50)
        
        # Test registration
        if not self.test_registration():
            print("ERROR: Registration failed, stopping test")
            return
        
        # Test OTP request
        if not self.test_otp_request():
            print("ERROR: OTP request failed, stopping test")
            return
        
        # Get OTP from user
        print("\nCHECK YOUR FLASK APP TERMINAL FOR THE OTP CODE")
        otp_code = input("Enter the 6-digit OTP code: ").strip()
        
        # Test OTP verification
        if not self.test_otp_verification(otp_code):
            print("ERROR: OTP verification failed, stopping test")
            return
        
        # Test profile access
        if not self.test_profile_access():
            print("ERROR: Profile access failed")
            return
        
        print("\nSUCCESS: ALL TESTS PASSED SUCCESSFULLY!")
        print("Your API is working perfectly!")

if __name__ == "__main__":
    tester = APITester()
    tester.run_complete_test()
