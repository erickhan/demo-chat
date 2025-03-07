import uuid
import os
import csv
from datetime import datetime

class BillPaymentSystem:
    def __init__(self, company_name):
        self.company_name = company_name
        self.bills = []
        self._load_data_from_csv()  # Load data from CSV on initialization

    def set_current_user(self, user_id, user_role):
        self.current_user = {"user_id": user_id, "user_role": user_role}

    def enter_bill(self, customer_name, previous_bill, payment_amount, balance_forward, amount_due, due_date, received_date, new_charges, note):
        bill_id = f"{customer_name}_{due_date}_{len(self.bills)}"
        bill = {
            "bill_id": bill_id,
            "customer_name": customer_name,
            "previous_bill": previous_bill,
            "payment_amount": payment_amount,
            "balance_forward": balance_forward,
            "amount_due": amount_due,
            "due_date": due_date,
            "received_date": received_date,
            "new_charges": new_charges,
            "note": note,  # Include the note
            "state": "ENTERED",
            "created_by": "{'user_id': 'demo', 'user_role': 'AP Clerk'}",
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat(),
            "verified_by": "",
            "payment_scheduled_by": "",
            "paid_by": ""
        }
        self.bills.append(bill)
        print(f"DEBUG: Entering bill with data: {bill}")
        self._save_bill_to_csv(bill)
        return bill_id

    def verify_bill(self, bill_id):
        for bill in self.bills:
            if bill["bill_id"] == bill_id:
                bill["state"] = "VERIFIED"
                bill["updated_at"] = datetime.now().isoformat()
                bill["verified_by"] = "{'user_id': 'demo', 'user_role': 'AP Clerk'}"
                self._save_bill_to_csv(bill)
                print(f"DEBUG: Verifying bill {bill_id}")
                return
        print(f"Error: Bill {bill_id} not found in bills list")

    def schedule_payment(self, bill_id):
        for bill in self.bills:
            if bill["bill_id"] == bill_id:
                bill["state"] = "PAYMENT_SCHEDULED"
                bill["updated_at"] = datetime.now().isoformat()
                bill["payment_scheduled_by"] = "{'user_id': 'demo', 'user_role': 'AP Clerk'}"
                self._save_bill_to_csv(bill)
                print(f"DEBUG: Scheduling payment for bill {bill_id}")
                return
        print(f"Error: Bill {bill_id} not found in bills list")

    def pay_bill(self, bill_id):
        print(f"DEBUG: Paying bill {bill_id}")
        return self._transition_state(bill_id, "PAID")

    def _transition_state(self, bill_id, new_state):
        #check if a user is logged in.
        if self.current_user is None:
            print("Error: No user logged in")
            return False
        
        #check that the bill exists
        if bill_id not in self.bills:
            print(f"Error: Bill {bill_id} not found in bills list")
            return False

        current_state = self.bills[bill_id]["state"]

        if new_state == "VERIFIED" and current_state == "ENTERED":
            print(f"DEBUG: Transitioning bill {bill_id} from {current_state} to {new_state}")
            self.bills[bill_id]["state"] = new_state
            self.bills[bill_id]["updated_at"] = datetime.now()
            self.bills[bill_id]["verified_by"] = self.current_user
            print(f"Bill {bill_id} moved from {current_state} to {new_state}")
            self._update_csv(bill_id)
            return True

        elif new_state == "PAYMENT_SCHEDULED" and current_state == "VERIFIED":
            print(f"DEBUG: Transitioning bill {bill_id} from {current_state} to {new_state}")
            self.bills[bill_id]["state"] = new_state
            self.bills[bill_id]["updated_at"] = datetime.now()
            self.bills[bill_id]["payment_scheduled_by"] = self.current_user
            print(f"Bill {bill_id} moved from {current_state} to {new_state}")
            self._update_csv(bill_id)
            return True

        elif new_state == "PAID" and current_state == "PAYMENT_SCHEDULED":
            print(f"DEBUG: Transitioning bill {bill_id} from {current_state} to {new_state}")
            self.bills[bill_id]["state"] = new_state
            self.bills[bill_id]["updated_at"] = datetime.now()
            self.bills[bill_id]["paid_by"] = self.current_user
            print(f"Bill {bill_id} moved from {current_state} to {new_state}")
            self._update_csv(bill_id)
            return True
        else:
            print(f"Error: Invalid state transition from {current_state} to {new_state}")
            return False

    def add_note(self, bill_id, note):
        """Adds or updates a note for a specific bill."""
        if bill_id in self.bills:
            self.bills[bill_id]["note"] = note
            self._update_csv(bill_id)
            return True
        else:
            return False

    def get_note(self, bill_id):
        """Retrieves the note for a specific bill."""
        if bill_id in self.bills:
            return self.bills[bill_id]["note"]
        else:
            return None

    def _update_csv(self, bill_id):
        """Updates the CSV file with the bill data."""
        #first, we create a list with all rows, and save it as a csv.
        
        file_exists = os.path.isfile(self.csv_filename)
        all_rows = []
        for id, bill in self.bills.items():
            row = {"bill_id": id}
            row.update(bill)
            all_rows.append(row)

        with open(self.csv_filename, "w", newline="") as csvfile:
            fieldnames = [
                "bill_id", "customer_name", "previous_bill", "payment_amount",
                "balance_forward", "amount_due", "due_date", "received_date",
                "new_charges", "state", "created_by", "created_at", "updated_at", "verified_by", "payment_scheduled_by", "paid_by", "note"
            ]
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)

            writer.writeheader()  # Write the header row

            for row in all_rows:
                writer.writerow(row)

        print(f"CSV file '{self.csv_filename}' updated successfully.")

    def _save_bill_to_csv(self, bill):
        try:
            with open('bills.csv', mode='a', newline='') as file:  # Use the correct file name
                writer = csv.DictWriter(file, fieldnames=bill.keys())
                if file.tell() == 0:
                    writer.writeheader()  # Write header if file is empty
                writer.writerow(bill)
        except Exception as e:
            print(f"Error saving bill to CSV: {e}")

    def _load_data_from_csv(self):
        """Loads data from the CSV file into the bills dictionary."""
        try:
            with open('bills.csv', mode='r') as file:  # Use the correct file name
                csv_reader = csv.DictReader(file)
                for row in csv_reader:
                    bill = {
                        "bill_id": row["bill_id"],
                        "customer_name": row["customer_name"],
                        "previous_bill": row["previous_bill"],
                        "payment_amount": row["payment_amount"],  # Correct column name
                        "balance_forward": row["balance_forward"],
                        "amount_due": row["amount_due"],
                        "due_date": row["due_date"],
                        "received_date": row["received_date"],
                        "new_charges": row["new_charges"],
                        "note": row.get("note", ""),  # Use .get() to handle missing key
                        "state": row["state"],
                        "created_by": row["created_by"],
                        "created_at": row["created_at"],
                        "updated_at": row["updated_at"],
                        "verified_by": row["verified_by"],
                        "payment_scheduled_by": row["payment_scheduled_by"],
                        "paid_by": row["paid_by"]
                    }
                    self.bills.append(bill)
        except Exception as e:
            print(f"Error loading data from CSV: {e}")
