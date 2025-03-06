import os
import streamlit as st
from streamlit import session_state as ss
from streamlit_pdf_viewer import pdf_viewer
from billpay import BillPaymentSystem
from openai import OpenAI
import io
import pypdf
import re

# Set up header with a title on the left and a demo button on the right.
col1, col2 = st.columns([0.8, 0.2])
with col1:
    st.title("✉️ Send to Accounting-AI")
    st.write("Email simulate orchestrating an AI AccountsPayable Agent.")
with col2:
    ss.demo_mode = st.toggle("Demo Mode", value=False)

# Ensure session state keys exist
if "pdf_ref_guidance" not in ss:
    ss.pdf_ref_guidance = None
if "pdf_ref_toProcess" not in ss:
    ss.pdf_ref_toProcess = None
if "demo_mode" not in ss:
    ss.demo_mode = False

# If Demo Mode is enabled, pre-load files from the local working directory
if ss.demo_mode:
    current_working_dir = os.getcwd()
    demo_guidance_path = os.path.join(current_working_dir, "requirements.txt")
    demo_bill_path = os.path.join(current_working_dir, "bill_example_APS.pdf")

    # Read files as bytes
    with open(demo_guidance_path, "rb") as f:
        ss.pdf_ref_guidance = f.read()
    with open(demo_bill_path, "rb") as f:
        ss.pdf_ref_toProcess = f.read()

# File for Guidance
with st.container():
    st.subheader("📘 Guidance File")
    if ss.demo_mode:
        st.success(f"📂 Demo File Loaded: requirements.txt")
    else:
        guidance_file = st.file_uploader("Instructions file", type=('pdf'), key='pdf_guidance')
        if guidance_file is not None:
            ss.pdf_ref_guidance = guidance_file.getvalue() #store the bytes

    with st.expander("File Preview"):
        if ss.pdf_ref_guidance is not None:
            if ss.demo_mode:
                st.write("Guidance: requirements.txt")
                st.write(f"  File size: {len(ss.pdf_ref_guidance)} bytes")
                st.text(ss.pdf_ref_guidance.decode("utf-8", errors="ignore"))
            else:
                st.write("Guidance: Uploaded PDF")
                st.write("  File size:", len(ss.pdf_ref_guidance), "bytes")
                try:
                    pdf_viewer(input=ss.pdf_ref_guidance, width=700)
                except Exception as e:
                    st.error(f"Failed to load PDF: {e}")
                    st.info("Attempting to display as plain text.")
                    try:
                        st.text(ss.pdf_ref_guidance.decode("utf-8", errors="ignore"))
                    except:
                        st.error("Could not decode as text.")

st.divider()

# File for Processing
with st.container():
    st.subheader("📑 Bill to Process")
    if ss.demo_mode:
        st.success(f"📂 Demo File Loaded: APS_sample_bill.pdf")
    else:
        toProcess_file = st.file_uploader("Bill to Process PDF file", type=('pdf'), key='pdf_toProcess')
        if toProcess_file is not None:
            ss.pdf_ref_toProcess = toProcess_file.read()  # Read as bytes

with st.expander("File Preview"):
    if ss.pdf_ref_toProcess is not None:
        if ss.demo_mode:
            st.write("Bill: APS_sample_bill.pdf")
            st.write(f"  File size: {len(ss.pdf_ref_toProcess)} bytes")
            try:
                pdf_viewer(input=ss.pdf_ref_toProcess, width=700)
            except Exception as e:
                st.error(f"Failed to load PDF: {e}")
                st.info("Attempting to display as plain text.")
                try:
                    st.text(ss.pdf_ref_toProcess.decode("utf-8", errors="ignore"))
                except Exception as decode_error:
                    st.error(f"Could not decode as text: {decode_error}")

        else:
            st.write("Bill: Uploaded PDF")
            st.write("  File size:", len(ss.pdf_ref_toProcess), "bytes")
            try:
                pdf_viewer(input=ss.pdf_ref_toProcess, width=700)
            except Exception as e:
                st.error(f"Failed to load PDF: {e}")
                st.info("Attempting to display as plain text.")
                try:
                    st.text(ss.pdf_ref_toProcess.decode("utf-8", errors="ignore"))
                except Exception as decode_error:
                    st.error(f"Could not decode as text: {decode_error}")

st.divider()

# Show box if both files are available
if ss.pdf_ref_guidance is not None and ss.pdf_ref_toProcess is not None:
    with st.container():
        st.markdown("### ✅ Ready to Send")
        st.info("Both files are available. Click **Process** to extract data and proceed.")
        if st.button("Process"):
            try:
                pdf_file = io.BytesIO(ss.pdf_ref_toProcess)
                pdf_reader = pypdf.PdfReader(pdf_file)
                text = ""
                for page in pdf_reader.pages:
                    text += page.extract_text() or ""

                # Text Preprocessing: Remove extra whitespace
                text = re.sub(r'\s+', ' ', text).strip()  # Replace multiple spaces with single space

                # Parsing logic for APS bill using refined regular expressions
                payee = None
                previous_bill = None
                payment = None
                balance_forward = None
                new_charges = None
                total_amount_due = None
                due_date = None
                received_date = None

                lines = text.split('\n')
                for line in lines:
                    line = line.strip() #remove leading/trailing whitespace.
                    print(f"Processing Line: {line}") #Debug line.

                    if "Payee:" in line:
                        payee = line.split(":")[1].strip()
                    elif "Previous bill:" in line:
                        match = re.search(r'Previous bill:\s*\$?([\d.]+)', line)
                        if match:
                            previous_bill = float(match.group(1))
                    elif "Payment:" in line:
                        match = re.search(r'Payment:\s*-?\s*\$?([\d.]+)', line) #added optional space
                        if match:
                            payment = -float(match.group(1))
                    elif "Balance forward:" in line:
                        match = re.search(r'Balance forward:\s*\$?([\d.]+)', line)
                        if match:
                            balance_forward = float(match.group(1))
                    elif "New charges:" in line:
                        match = re.search(r'New charges:\s*\$?([\d.]+)', line)
                        if match:
                            new_charges = float(match.group(1))
                    elif "Total amount due:" in line:
                        match = re.search(r'Total amount due:\s*\$?([\d.]+)', line)
                        if match:
                            total_amount_due = float(match.group(1))
                    elif "Due date:" in line:
                        match = re.search(r'Due date:\s*(.+)', line)
                        if match:
                            due_date = match.group(1).strip()
                    elif "Received date:" in line:
                        match = re.search(r'Received date:\s*(.+)', line)
                        if match:
                            received_date = match.group(1).strip()

                # Detailed error checking
                errors = []
                if not payee:
                    errors.append("Payee not found.")
                if previous_bill is None:
                    errors.append("Previous bill not found or could not be parsed.")
                if payment is None:
                    errors.append("Payment not found or could not be parsed.")
                if balance_forward is None:
                    errors.append("Balance forward not found or could not be parsed.")
                if new_charges is None:
                    errors.append("New charges not found or could not be parsed.")
                if total_amount_due is None:
                    errors.append("Total amount due not found or could not be parsed.")
                if not due_date:
                    errors.append("Due date not found.")
                if not received_date:
                    errors.append("Received date not found.")

                if errors:
                    for error in errors:
                        st.error(error)
                    st.stop()  # Stop execution if any errors were found

                # Initialize the system
                aps_bills = BillPaymentSystem("My Company")
                # Log in as the accountant
                aps_bills.set_current_user("jane.accountant", "AP Clerk")

                # Enter the APS bill information
                bill_id = aps_bills.enter_bill(
                    customer_name=payee,
                    previous_balance=previous_bill,
                    payment_amount=payment,
                    balance_forward=balance_forward,
                    amount_due=total_amount_due,
                    due_date=due_date,
                    received_date=received_date,
                    new_charges=new_charges,
                    attachment_path="aps_bill_scan.pdf"
                )

                # Verify the bill information
                aps_bills.verify_bill(bill_id, "Verified all information against original bill")
                # Schedule payment 90 days after due date
                aps_bills.schedule_payment(bill_id)
                # Submit for approval
                aps_bills.submit_for_approval(bill_id)

                # Display Status
                bill_info = aps_bills.get_bill(bill_id)
                if bill_info:
                    st.write(f"Bill **{bill_id}** entered and scheduled for payment.")
                    st.write(f"Current status: **{bill_info['current_state']}**")
                    st.write(f"Scheduled payment date: **{bill_info['scheduled_payment_date']}**")
                else:
                    st.warning("No data to process.")

            except Exception as e:
                st.error(f"Error processing PDF: {e}")
st.divider()

# Initialize the system
aps_bills = BillPaymentSystem("My Company")
# Log in as the accountant
aps_bills.set_current_user("jane.accountant", "AP Clerk")

# Enter the APS bill information
bill_id = aps_bills.enter_bill(
    account_number="0123456789",
    customer_name="John Doe",
    service_address="123 Main St",
    billing_period="January 1 - January 31, 2023",
    due_date="2023-02-15",
    amount_due=142.75,
    bill_type="Utility - Electric",
    attachment_path="aps_bill_scan.pdf"
)

# Verify the bill information
aps_bills.verify_bill(bill_id, "Verified all information against original bill")
# Schedule payment 90 days after due date
aps_bills.schedule_payment(bill_id)
# Submit for approval
aps_bills.submit_for_approval(bill_id)

# Display Status
bill_info = aps_bills.get_bill(bill_id)
if bill_info:
    st.write(f"Bill **{bill_id}** entered and scheduled for payment.")
    st.write(f"Current status: **{bill_info['current_state']}**")
    st.write(f"Scheduled payment date: **{bill_info['scheduled_payment_date']}**")
else:
    st.warning("No data to process.")

###### End Accountant

# Ask user for their OpenAI API key via `st.text_input`.
openai_api_key = st.text_input("OpenAI API Key", type="password")
if not openai_api_key:
    st.info("Please add your OpenAI API key to continue.", icon="🗝️")
else:
    client = OpenAI(api_key=openai_api_key)
    if "messages" not in st.session_state:
        st.session_state.messages = []
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])
    if prompt := st.chat_input("What is up?"):
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)
        stream = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[{"role": m["role"], "content": m["content"]} for m in st.session_state.messages],
            stream=True,
        )
        full_response = ""
        with st.chat_message("assistant"):
            message_placeholder = st.empty()
            for chunk in stream:
                if chunk.choices[0].delta.content is not None:
                    full_response += chunk.choices[0].delta.content