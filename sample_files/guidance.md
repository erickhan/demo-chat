# APS Bill Payment Processing Workflow

## Overview

This document outlines our standard procedure for processing Arizona Public Service (APS) utility bills, recording them in our system, and scheduling payments for 90 days after the due date.

## Process Steps

1.  **Bill Receipt**

    * When we receive a utility bill from APS (either paper or electronic), the AI orchestrator (person) will email the “Accounts Payable” AI-agent clerk.
    * Upon which, the AI agent will:
        * Watermark the bill electronically with the receipt date
        * Store the bill in our record system [insert name]

2.  **Bill Entry**

    * [This may be API automated and below is meant to illustrate the outcome]
    * The Accounts Payable (AI-Agent) clerk will:
        * Log into our Bill Processing System in [insert name]
        * Select "Add New Bill" from the dashboard
        * Enter the following key information from the bill:
            * Account Number (found in the Account Information section)
            * Customer Name (found at the top of the bill)
            * Service Address (found in the Account Information section)
            * Billing Period (found in the Amount of Electricity Used section)
            * Due Date (found in the Summary section)
            * Total Amount Due (found in the Summary section)
            * Bill Type (select "Utility - Electric")

3.  **Bill Verification**

    * The Accounts Payable (AI-Agent) clerk will:
        * Review all entered information for accuracy
        * Flag any issues for human review and feedback
        * Attach a scan or photo of the original bill document to this system
        * Report verified to this system, which will mark the bill as "VERIFIED"

4.  **Payment Scheduling**

    * The system will automatically calculate a payment date of 90 days after the due date
    * Review the calculated payment date (e.g. for balances going negative in the account and potential holiday/known scheduling issues)
    * Confirm the payment source (e.g., Operating Account)
    * Click "Schedule Payment" to schedule the future payment
    * The system will mark the bill as "PAYMENT_SCHEDULED"

5.  **Approval Process**

    * The bill is automatically routed to the appropriate level based on amount via email:
        * Under $1,000: Department Manager or email with “Department Manager level”
        * $1,000-$5,000: Finance Director or email with “Finance Director level”
        * Over $5,000: CFO or email with “CFO level”
    * The approver (person) reviews the bill details and scheduled payment
    * The approver (person) either approves or rejects the payment by responding to the email with “APPROVED” or “REJECTED” in the email body and can write comments.
    * If approved, the system marks the bill as "APPROVED"
    * If rejected, the system marks the bill as "REJECTED" and returns it to Accounts Payable for correction

6.  **Payment Processing**

    * On the scheduled payment date, the system will:
        * Change the bill status to "PAYMENT_PENDING"
        * Generate a payment through our [insert name] banking system
        * Update the bill status to "PAID" once confirmation is received
        * Store payment confirmation details

7.  **Record Keeping**

    * All processed bills are archived in this system for 7 years
    * Monthly reconciliation reports are generated for all utility payments
    * Any payment issues or exceptions are flagged for manual review

## Important Notes

* From AI orchestrator (person) to the AI agents:
    * Never schedule a payment without proper verification
    * If a bill seems unusual (significantly higher or lower than normal), flag it for review
    * All rejected bills must be resolved within 3 business days, which should be flagged in our audit systems and alerting systems.
    * For urgent bills that cannot wait 90 days, use the "Override Payment Schedule" option (requires Director approval)