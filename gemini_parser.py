import os
import json
import datetime
from openai import OpenAI

api_key = os.environ.get("GOOGLE_GEMINI_KEY")

if api_key:
    credentials_set = True
else:
    print("GOOGLE_GEMINI_KEY environment variable not found.")
    credentials_set = False

def parse_data_with_gemini(text, data_type):
    """Parses data using Gemini API."""
    if not credentials_set:
        print("API key not set, cannot use Gemini API.")
        return None

    try:
        client = OpenAI(
            api_key=api_key,
            base_url="https://generativelanguage.googleapis.com/v1beta/openai/"
        )

        prompt = f"""
        Extract the following information from the {data_type} text and return it as a JSON object:
        Customer Name, Previous bill, Payment, Balance forward, New charges, Total amount due, Due date (YYYY-MM-DD), Received date (YYYY-MM-DD).

        {data_type} Text:
        {text}

        JSON:
        """

        response = client.chat.completions.create(
            model="gemini-2.0-flash",
            n=1,
            messages=[
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user", "content": prompt}
            ]
        )

        if not response.choices or not response.choices[0].message.content:
            print("DEBUG: Gemini returned an empty response.")
            return None

        cleaned_response = response.choices[0].message.content.strip()

        if cleaned_response.startswith('```json'):
            cleaned_response = cleaned_response[7:]
        if cleaned_response.endswith('```'):
            cleaned_response = cleaned_response[:-3]

        try:
            response_json = json.loads(cleaned_response)
            # Convert keys to lowercase with underscores
            converted_json = {}
            for key, value in response_json.items():
                converted_key = key.lower().replace(" ", "_")
                converted_json[converted_key] = value

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

            return converted_json
        except json.JSONDecodeError as e:
            print(f"DEBUG: Gemini Response: {response.choices[0].message.content}")
            print(f"DEBUG: JSONDecodeError: {e}")
            return None
    except FileNotFoundError:
        print("APS_bill.md file not found in sample_files directory. os.cwd: ", os.getcwd())
        return None
    except Exception as e:
        print(f"Error using Gemini API: {e}")
        return None

if credentials_set:
    print("Gemini API Ready")
    if __name__ == "__main__":
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