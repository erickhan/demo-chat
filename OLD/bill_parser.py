import re
import datetime

def extract_number(text):
    """Extracts a number from a string, handling dollar signs and commas."""
    text = text.replace('$', '').replace(',', '').strip()
    try:
        return float(text)
    except ValueError:
        return None

def parse_markdown_bill_data(markdown_text):
    """Parses bill data from markdown text."""
    customer_name = None  # Changed to match the case in the Markdown
    previous_bill = None
    payment = None
    balance_forward = None
    new_charges = None
    total_amount_due = None
    due_date = None
    received_date = None

    def convert_date(date_str):
        """Converts a date string to %Y-%m-%d format."""
        try:
            date_obj = datetime.datetime.strptime(date_str, "%b %d, %Y")  # Matches "Oct 1, 2025"
            return date_obj.strftime("%Y-%m-%d")
        except ValueError:
            try:
                date_obj = datetime.datetime.strptime(date_str, "%Y-%m-%d")
                return date_obj.strftime("%Y-%m-%d")
            except ValueError:
                try:
                    date_obj = datetime.datetime.strptime(date_str, "%d/%m/%Y")
                    return date_obj.strftime("%Y-%m-%d")
                except ValueError:
                    try:
                        date_obj = datetime.datetime.strptime(date_str, "%d-%b-%Y")
                        return date_obj.strftime("%Y-%m-%d")
                    except ValueError:
                        return None  # Return None if no date format is matched.
 
    customer_name = "Unknown Customer"  # Initialize with a default value
    lines = markdown_text.split('\n')
    for line in lines:
        line = line.strip()

        if "* **Customer Name:**" in line: 
            try:
                customer_name = line.split("**Customer Name:**")[1].strip()
            except IndexError:
                print(f"DEBUG: IndexError on Customer Name line: {line}")
                customer_name = "Unknown Customer"
        elif "* **Previous bill:**" in line:
            previous_bill = extract_number(line.split("**Previous bill:**")[1].strip())
        elif "* **Payment:**" in line:
            payment = extract_number(line.split("**Payment:**")[1].strip())
        elif "* **Balance forward:**" in line:
            balance_forward = extract_number(line.split("**Balance forward:**")[1].strip())
        elif "* **New charges:**" in line:
            new_charges = extract_number(line.split("**New charges:**")[1].strip())
        elif "* **Total amount due:**" in line:
            total_amount_due = extract_number(line.split("**Total amount due:**")[1].strip())
        elif "* **Due date:**" in line:
            due_date = line.split("**Due date:**")[1].strip()
            due_date = convert_date(due_date)  # Convert the date
        elif "* **Received date:**" in line:
            received_date = line.split("**Received date:**")[1].strip()
            received_date = convert_date(received_date)  # Convert the date

    result = {
        "customer_name": customer_name,
        "previous_bill": previous_bill,
        "payment": payment,
        "balance_forward": balance_forward,
        "new_charges": new_charges,
        "total_amount_due": total_amount_due,
        "due_date": due_date,
        "received_date": received_date,
    }
    print(f"DEBUG: parse_markdown_bill_data returning: {result}") #added print statement
    return result
def parse_bill_data(pdf_text):
    customer_name = "Unknown Customer"  # Initialize 
    """Parses bill data from extracted PDF text using more robust logic."""
    bill_data = {
        "customer_name": None,
        "previous_bill": None,
        "payment": None,
        "balance_forward": None,
        "new_charges": None,
        "total_amount_due": None,
        "due_date": None,
        "received_date": None,
    }

    def convert_date(date_str):
        """Converts a date string to %Y-%m-%d format."""
        date_formats = [
            "%b %d, %Y",  # Oct 1, 2025
            "%Y-%m-%d",  # 2025-10-01
            "%d/%m/%Y",  # 01/10/2025
            "%d-%b-%Y",  # 01-Oct-2025
        ]
        for fmt in date_formats:
            try:
                date_obj = datetime.datetime.strptime(date_str, fmt)
                return date_obj.strftime("%Y-%m-%d")
            except ValueError:
                continue
        return None

    # Customer Name
    customer_name_match = re.search(r"Customer Name:\s*(.+)", pdf_text, re.IGNORECASE)
    if customer_name_match:
        bill_data["customer_name"] = customer_name_match.group(1).strip()
    else:
        print("Warning: customer_name not found in PDF.")

    # Previous Bill
    previous_bill_match = re.search(r"Previous Bill:\s*([$,\d.]+)", pdf_text, re.IGNORECASE)
    if previous_bill_match:
        bill_data["previous_bill"] = extract_number(previous_bill_match.group(1))

    # Payment
    payment_match = re.search(r"Payment:\s*([$,\d.]+)", pdf_text, re.IGNORECASE)
    if payment_match:
        bill_data["payment"] = extract_number(payment_match.group(1))

    # Balance Forward
    balance_forward_match = re.search(r"Balance Forward:\s*([$,\d.]+)", pdf_text, re.IGNORECASE)
    if balance_forward_match:
        bill_data["balance_forward"] = extract_number(balance_forward_match.group(1))

    # New Charges
    new_charges_match = re.search(r"New Charges:\s*([$,\d.]+)", pdf_text, re.IGNORECASE)
    if new_charges_match:
        bill_data["new_charges"] = extract_number(new_charges_match.group(1))

    # Total Amount Due
    total_amount_due_match = re.search(r"Total Amount Due:\s*([$,\d.]+)", pdf_text, re.IGNORECASE)
    if total_amount_due_match:
        bill_data["total_amount_due"] = extract_number(total_amount_due_match.group(1))

    # Due Date
    due_date_match = re.search(r"Due Date:\s*(\w{3}\s\d{1,2},\s\d{4}|\d{4}-\d{2}-\d{2}|\d{2}/\d{2}/\d{4}|\d{2}-\w{3}-\d{4})", pdf_text, re.IGNORECASE)
    if due_date_match:
        bill_data["due_date"] = convert_date(due_date_match.group(1))

    # Received Date
    received_date_match = re.search(r"Received Date:\s*(\w{3}\s\d{1,2},\s\d{4}|\d{4}-\d{2}-\d{2}|\d{2}/\d{2}/\d{4}|\d{2}-\w{3}-\d{4})", pdf_text, re.IGNORECASE)
    if received_date_match:
        bill_data["received_date"] = convert_date(received_date_match.group(1))

    return bill_data