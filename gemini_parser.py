import os
import json
import datetime
import pandas as pd
from openai import OpenAI

api_key = os.environ.get("GOOGLE_GEMINI_KEY")

if api_key:
    credentials_set = True
    client = OpenAI(
        api_key=api_key,
        base_url="https://generativelanguage.googleapis.com/v1beta/openai/"
    )
else:
    print("GOOGLE_GEMINI_KEY environment variable not found.")
    credentials_set = False

def parse_data_with_gemini(text, data_type):
    """Parses data using Gemini API."""
    if not credentials_set:
        print("API key not set, cannot use Gemini API.")
        return None

    try:
        prompt = f"""
        Extract the following information from the provided bill text:
        - Customer Name
        - Previous mortgage payment
        - Payment
        - Balance forward
        - New charges
        - Total amount due (treat "Total 2025 Property Taxes" the same as "Total amount due")
        - Due date
        - Received date
        - Principal balance
        - Interest rate
        - Loan term
        - Payment schedule
        - Payment due date
        - Principal payment
        - Interest payment
        - Property taxes (monthly)
        - Homeowners Insurance (monthly)
        - Escrow (monthly)
        - Late fee
        - Subtotal
        - State property tax assessment
        - County property tax assessment
        - City property tax assessment
        - Franchise fee
        - Payee

        Here is the {data_type} text:
        {text}

        Return the extracted data as a JSON object. If a field is not found, return null for that field.
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

            # Clean payee
            if "payee" in converted_json and converted_json["payee"] is not None and isinstance(converted_json["payee"], str):
                converted_json["payee"] = converted_json["payee"].lstrip("#").strip()
            else:
                converted_json["payee"] = "Unknown Payee"

            if "due_date" in converted_json and converted_json["due_date"]:
                try:
                    datetime.datetime.strptime(converted_json["due_date"], "%Y-%m-%d")
                except ValueError:
                    try:
                        date_obj = datetime.datetime.strptime(converted_json["due_date"], "%b %d, %Y")
                        converted_json["due_date"] = date_obj.strftime("%Y-%m-%d")
                    except ValueError:
                        converted_json["due_date"] = None

            if "received_date" in converted_json and converted_json["received_date"]:
                try:
                    datetime.datetime.strptime(converted_json["received_date"], "%Y-%m-%d")
                except ValueError:
                    try:
                        date_obj = datetime.datetime.strptime(converted_json["received_date"], "%b %d, %Y")
                        converted_json["received_date"] = date_obj.strftime("%Y-%m-%d")
                    except ValueError:
                        converted_json["received_date"] = None

            return converted_json
        except json.JSONDecodeError as e:
            print(f"DEBUG: Gemini Response: {response.choices[0].message.content}")
            print(f"DEBUG: JSONDecodeError: {e}")
            return None
    except Exception as e:
        print(f"Error using Gemini API: {e}")
        return None

def generate_chat_response(processed_text, prompt):
    """Generates a chat response using the same Gemini API client."""
    if not credentials_set or client is None:
        return "API key not set or client not initialized, cannot use Gemini API."

    try:
        response = client.chat.completions.create(
            model="gemini-2.0-flash",
            n=1,
            messages=[
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user", "content": f"{processed_text}\n\nQuestion: {prompt}"}
            ]
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        return f"Error generating response: {e}"

if credentials_set:
    print("Gemini API Ready")
else:
    print("Gemini API initialization skipped due to missing API key.")

def update_csv(bill_data, file_path='bills.csv'):
    """Updates the CSV file with the new bill data."""
    try:
        df = pd.read_csv(file_path)
    except FileNotFoundError:
        df = pd.DataFrame(columns=bill_data.keys())
    
    new_row = pd.DataFrame([bill_data])
    df = pd.concat([df, new_row], ignore_index=True)
    df.to_csv(file_path, index=False)