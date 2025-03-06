import uuid
import os
import csv
from datetime import datetime

class BillPaymentSystem:
    def __init__(self, company_name="My Company"):
        self.company_name = company_name
        self.bills = {}  # {bill_id: bill_data}
        self.current_user = None

    def set_current_user(self, user_id, user_role):
        self.current_user = {"user_id": user_id, "user_role": user_role}

    def enter_bill(self, customer_name, previous_bill, payment_amount, balance_forward, amount_due, due_date, received_date, new_charges):
        bill_id = f"{customer_name}_{due_date.replace('-', '')}"
        # check if bill exists, then modify, otherwise, add new.
        if bill_id not in self.bills:
            bill_id = f"{customer_name}_{due_date.replace('-', '')}_{len(self.bills)}" #add a count to the end of the duplicate id
        bill_data = {
            "customer_name": customer_name,
            "previous_bill": previous_bill,
            "payment_amount": payment_amount,
            "balance_forward": balance_forward,
            "amount_due": amount_due,
            "due_date": due_date,
            "received_date": received_date,
            "new_charges": new_charges,
            "state": "ENTERED",
            "created_by": self.current_user,
            "created_at": datetime.now(),
            "updated_at": datetime.now(),
        }
        self.bills[bill_id] = bill_data
        print(f"DEBUG: Entering bill with data: customer_name='{customer_name}', previous_bill='{previous_bill}', payment_amount='{payment_amount}', balance_forward='{balance_forward}', amount_due='{amount_due}', due_date='{due_date}', received_date='{received_date}', new_charges='{new_charges}'")
        print(f"Attachment saved as /workspaces/demo-chat/data/attachments/{bill_id}_aps_bill_scan.pdf")
        print(f"Bill {bill_id} entered successfully")
        # code for making the csv file starts here.
        csv_filename = "processed_bills.csv"
        file_exists = os.path.isfile(csv_filename)

        with open(csv_filename, "a", newline="") as csvfile:
            fieldnames = [
                "bill_id", "customer_name", "previous_bill", "payment_amount",
                "balance_forward", "amount_due", "due_date", "received_date",
                "new_charges", "state", "created_by", "created_at", "updated_at", "verified_by", "payment_scheduled_by", "paid_by"
            ]
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)

            if not file_exists:
                writer.writeheader()  # Write the header row only if the file is newly created

            row = {"bill_id": bill_id}
            row.update(bill_data)
            writer.writerow(row)

        print(f"CSV file '{csv_filename}' updated successfully.")

        return bill_id

    def verify_bill(self, bill_id):
        print(f"DEBUG: Verifying bill {bill_id}")
        return self._transition_state(bill_id, "VERIFIED")

    def schedule_payment(self, bill_id):
        print(f"DEBUG: Scheduling payment for bill {bill_id}")
        return self._transition_state(bill_id, "PAYMENT_SCHEDULED")

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
            return True

        elif new_state == "PAYMENT_SCHEDULED" and current_state == "VERIFIED":
            print(f"DEBUG: Transitioning bill {bill_id} from {current_state} to {new_state}")
            self.bills[bill_id]["state"] = new_state
            self.bills[bill_id]["updated_at"] = datetime.now()
            self.bills[bill_id]["payment_scheduled_by"] = self.current_user
            print(f"Bill {bill_id} moved from {current_state} to {new_state}")
            return True

        elif new_state == "PAID" and current_state == "PAYMENT_SCHEDULED":
            print(f"DEBUG: Transitioning bill {bill_id} from {current_state} to {new_state}")
            self.bills[bill_id]["state"] = new_state
            self.bills[bill_id]["updated_at"] = datetime.now()
            self.bills[bill_id]["paid_by"] = self.current_user
            print(f"Bill {bill_id} moved from {current_state} to {new_state}")
            return True
        else:
            print(f"Error: Invalid state transition from {current_state} to {new_state}")
            return False
