import os
import json
from google.cloud import aiplatform
import datetime
import pypdf
import io

project_id = "leafy-racer-452822-c3"
location = "us-west1"
api_key = os.environ.get("GOOGLE_GEMINI_KEY")

if not api_key:
    print("GOOGLE_GEMINI_KEY environment variable not found.")
    credentials_set = False
else:
    genai.configure(api_key=api_key)
    credentials_set = True


def parse_data_with_gemini(text, data_type):
    """Parses data using Gemini API."""
    if not credentials_set:
        print("API key not set, cannot use Gemini API.")
        return None

    try:
        model = genai.GenerativeModel('gemini-pro')  # Or 'gemini-pro-vision' if you need image inputs

        prompt = f"""
        Extract the following information from the {data_type} text and return it as a JSON object:
        Customer Name, Previous bill, Payment, Balance forward, New charges, Total amount due, Due date (YYYY-MM-DD), Received date (YYYY-MM-DD).

        {data_type} Text:
        {text}

        JSON:
        """

        response = model.generate_content(prompt)

        try:
            response_json = json.loads(response.text)

            # Convert dates to ISO 8601 format if they are not already.
            if "Due date" in response_json and response_json["Due date"]:
                try:
                    datetime.datetime.strptime(response_json["Due date"], "%Y-%m-%d")
                except ValueError:
                    try:
                        date_obj = datetime.datetime.strptime(response_json["Due date"], "%b %d, %Y")
                        response_json["Due date"] = date_obj.strftime("%Y-%m-%d")
                    except ValueError:
                        response_json["Due date"] = None

            if "Received date" in response_json and response_json["Received date"]:
                try:
                    datetime.datetime.strptime(response_json["Received date"], "%Y-%m-%d")
                except ValueError:
                    try:
                        date_obj = datetime.datetime.strptime(response_json["Received date"], "%b %d, %Y")
                        response_json["Received date"] = date_obj.strftime("%Y-%m-%d")
                    except ValueError:
                        response_json["Received date"] = None

            return response_json
        except (json.JSONDecodeError, IndexError, KeyError, TypeError) as e:
            print(f"Error parsing Gemini response: {e}")
            return None

    except Exception as e:
        print(f"Error using Gemini API: {e}")
        return None

if credentials_set:
    print("Gemini API Ready")

    # Example usage with the APS_bill.md file from sample_files subdirectory:
    try:
        file_path = os.path.join("sample_files", "APS_bill.md")
        with open(file_path, "r") as f:
            markdown_text = f.read()

        result = parse_data_with_gemini(markdown_text, "markdown")
        if result:
            print(result)
        else:
            print("Failed to parse bill data using Gemini API.")
    except FileNotFoundError:
        print("APS_bill.md file not found in sample_files directory. os.cwd: ", os.getcwd())
    except Exception as e:
        print(f"Error reading or processing APS_bill.md: {e}")

else:
    print("Gemini API initialization skipped due to missing API key.")