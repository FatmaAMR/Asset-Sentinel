# import httpx
# import logging
# from config.settings import settings

# logger = logging.getLogger(__name__)

# class QueryingLogic:
#     def __init__(self):
#         self.master_url = settings.MASTER_LLM_SERVICE_URL

#     async def get_llm_response(self, system_instruction: str, user_input: str):
#         # Standardized Payload according to Master LLM Service contract
#         payload = {
#             "system_instruction": system_instruction,
#             "user_input": user_input,
#             "temperature": 0.1
#         }

#         try:
#             async with httpx.AsyncClient() as client:
#                 # Direct call to the master service predict endpoint
#                 response = await client.post(
#                     f"{self.master_url}/v1/predict",
#                     json=payload,
#                     timeout=60.0
#                 )
                
#                 response.raise_for_status()
#                 result = response.json()
                
#                 # Expecting 'generated_text' from the Master Service Response
#                 return result.get("generated_text")

#         except httpx.HTTPStatusError as e:
#             logger.error(f"Master Service Error: {e.response.status_code}")
#             return None
#         except Exception as e:
#             logger.error(f"Communication Failure: {str(e)}")
#             return None







import httpx
import logging
from config.settings import settings

# Configure logging to show in terminal
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class QueryingLogic:
    def __init__(self):
        self.master_url = settings.MASTER_LLM_SERVICE_URL

    async def get_llm_response(self, system_instruction: str, user_input: str):
        payload = {
            "system_instruction": system_instruction,
            "user_input": user_input,
            "temperature": 0.1
        }

        # STEP 1: LOGGING THE START
        print(f"\n[STEP 1] Starting LLM Request to: {self.master_url}/v1/predict")
        print(f"[DEBUG] Payload being sent: {user_input[:50]}...")

        try:
            async with httpx.AsyncClient() as client:
                # STEP 2: ATTEMPTING CONNECTION
                print(f"[STEP 2] Attempting to connect to Master Service...")
                
                response = await client.post(
                    f"{self.master_url}/v1/predict",
                    json=payload,
                    timeout=10.0 # Shortened timeout for faster debugging
                )
                
                # STEP 3: CHECKING RESPONSE STATUS
                print(f"[STEP 3] Received response with status code: {response.status_code}")
                response.raise_for_status()
                
                result = response.json()
                
                # STEP 4: EXTRACTING DATA
                generated_text = result.get("generated_text")
                if generated_text:
                    print(f"[STEP 4] Success! SQL generated: {generated_text[:50]}...")
                else:
                    print(f"[STEP 4] Warning: 'generated_text' not found in response keys: {list(result.keys())}")
                
                return generated_text

        except httpx.ConnectError:
            print(f"[ERROR] Connection Failed! Is the Master Service/Mock running at {self.master_url}?")
            return None
        except httpx.TimeoutException:
            print(f"[ERROR] Request Timed Out! The service at {self.master_url} is too slow.")
            return None
        except Exception as e:
            print(f"[ERROR] Unexpected Failure: {str(e)}")
            return None