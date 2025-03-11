import uuid
import os
import csv
from datetime import datetime

class BillPaymentSystem:
    def __init__(self, company_name):
        self.company_name = company_name
        self.bills = []
        self.csv_filename = 'bills.csv'
        self._load_data_from_csv()
        self.current_user = None

    def set_current_user(self, username, role):
        self.current_user = {"username": username, "role": role}

    def enter_bill(self, customer_name, payee, previous_bill, payment_amount, balance_forward, amount_due, due_date, received_date, new_charges, note):
        bill_id = f"bill_{len(self.bills) + 1}"
        bill = {
            "bill_id": bill_id,
            "payee": payee,
            "customer_name": customer_name,
            "previous_bill": previous_bill,
            "payment_amount": payment_amount,
            "balance_forward": balance_forward,
            "amount_due": amount_due,
            "due_date": due_date,
            "received_date": received_date,
            "new_charges": new_charges,
            "note": note,
            "state": "ENTERED",
            "created_by": self.current_user["username"] if self.current_user else "system",
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat(),
            "verified_by": None,
            "payment_scheduled_by": None,
            "paid_by": None
        }
        self.bills.append(bill)
        return bill_id

    def verify_bill(self, bill_id):
        return self._transition_state(bill_id, "VERIFIED")

    def schedule_payment(self, bill_id):
        return self._transition_state(bill_id, "PAYMENT_SCHEDULED")

    def pay_bill(self, bill_id):
        print(f"DEBUG: Paying bill {bill_id}")
        return self._transition_state(bill_id, "PAID")

    def _transition_state(self, bill_id, new_state):
        if self.current_user is None:
            print("Error: No user logged in")
            return False

        found_bill = None
        for bill in self.bills:
            if bill["bill_id"] == bill_id:
                found_bill = bill
                break
        if found_bill is None:
            print(f"Error: Bill {bill_id} not found in bills list")
            return False

        current_state = found_bill["state"]

        if new_state == "VERIFIED" and current_state == "ENTERED":
            print(f"DEBUG: Transitioning bill {bill_id} from {current_state} to {new_state}")
            found_bill["state"] = new_state
            found_bill["updated_at"] = datetime.now().isoformat()
            found_bill["verified_by"] = self.current_user["username"] if self.current_user else None
            print(f"Bill {bill_id} moved from {current_state} to {new_state}")
            self._update_csv()
            return True

        elif new_state == "PAYMENT_SCHEDULED" and current_state == "VERIFIED":
            print(f"DEBUG: Transitioning bill {bill_id} from {current_state} to {new_state}")
            found_bill["state"] = new_state
            found_bill["updated_at"] = datetime.now().isoformat()
            found_bill["payment_scheduled_by"] = self.current_user["username"] if self.current_user else None
            print(f"Bill {bill_id} moved from {current_state} to {new_state}")
            self._update_csv()
            return True

        elif new_state == "PAID" and current_state == "PAYMENT_SCHEDULED":
            print(f"DEBUG: Transitioning bill {bill_id} from {current_state} to {new_state}")
            found_bill["state"] = new_state
            found_bill["updated_at"] = datetime.now().isoformat()
            found_bill["paid_by"] = self.current_user["username"] if self.current_user else None
            print(f"Bill {bill_id} moved from {current_state} to {new_state}")
            self._update_csv()
            return True
        else:
            print(f"Invalid state transition from {current_state} to {new_state}")
            return False

    def add_note(self, bill_id, note):
        for bill in self.bills:
             if bill["bill_id"] == bill_id:
                bill["note"] = note
                self._update_csv()
                return True 
        return False

    def get_note(self, bill_id):
        for bill in self.bills:
              if bill["bill_id"] == bill_id:
                return bill["note"]
        return None

    def _update_csv(self):
        with open(self.csv_filename, "w", newline="") as csvfile:
            fieldnames = [
                "bill_id", "payee", "customer_name", "previous_bill", "payment_amount",
                "balance_forward", "amount_due", "due_date", "received_date",
                "new_charges", "state", "created_by", "created_at", "updated_at", "verified_by", "payment_scheduled_by", "paid_by", "note"
            ]
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(self.bills)
        print(f"CSV file '{self.csv_filename}' updated successfully.")

    def _save_bill_to_csv(self, bill):
        try:
            with open(self.csv_filename, mode='a', newline='') as file:
                writer = csv.DictWriter(file, fieldnames=bill.keys())
                if file.tell() == 0:
                    writer.writeheader()
                writer.writerow(bill)
        except Exception as e:
            print(f"Error saving bill to CSV: {e}")

    def _load_data_from_csv(self):
        try:
            with open(self.csv_filename, mode='r') as file:
                csv_reader = csv.DictReader(file)
                for row in csv_reader:
                    self.bills.append(row)
        except FileNotFoundError:
            with open(self.csv_filename, mode='w', newline='') as file:
                writer = csv.DictWriter(file, fieldnames=[
                    "bill_id", "payee", "customer_name", "previous_bill", "payment_amount",
                    "balance_forward", "amount_due", "due_date", "received_date",
                    "new_charges", "state", "created_by", "created_at", "updated_at",
                    "verified_by", "payment_scheduled_by", "paid_by", "note"
                ])
                writer.writeheader()
            print("CSV file not found. Created a new one.")
        except Exception as e:
            print(f"Error loading data from CSV: {e}")
