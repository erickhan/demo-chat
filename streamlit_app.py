import os
import streamlit as st
from streamlit import session_state as ss
from billpay import BillPaymentSystem
import io
import pypdf
import pandas as pd
from gemini_parser import parse_data_with_gemini, generate_chat_response  # Import chat function
import base64
import uuid

def extract_text_from_pdf(pdf_bytes):
    """Extracts text from a PDF file."""
    try:
        pdf_reader = pypdf.PdfReader(io.BytesIO(pdf_bytes))
        text = ""
        for page in pdf_reader.pages:
            text += page.extract_text()
        return text
    except Exception as e:
        st.error(f"Error extracting text from PDF: {e}")
        return None

def display_pdf(file_path):
    """Displays a PDF file in an iframe."""
    with open(file_path, "rb") as f:
        base64_pdf = base64.b64encode(f.read()).decode('utf-8')
    pdf_display = f'<iframe src="data:application/pdf;base64,{base64_pdf}" width="700" height="1000" type="application/pdf"></iframe>'
    st.markdown(pdf_display, unsafe_allow_html=True)

def load_csv(file_path):
    """Loads the CSV file into a DataFrame."""
    try:
        df = pd.read_csv(file_path)
        return df
    except Exception as e:
        st.error(f"Error loading CSV file: {e}")
        return None

def update_csv(bill_data, file_path='bills.csv'):
    """Updates the CSV file with the new bill data."""
    try:
        df = pd.read_csv(file_path)
    except FileNotFoundError:
        df = pd.DataFrame(columns=bill_data.keys())
    
    new_row = pd.DataFrame([bill_data])
    df = pd.concat([df, new_row], ignore_index=True)
    df.to_csv(file_path, index=False)

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
if "bill_system" not in ss:
    ss.bill_system = BillPaymentSystem("ACME Corporation")
if "processed_text" not in ss:
    ss.processed_text = None
if "chat_history" not in ss:
    ss.chat_history = []
if "bill_data" not in ss:
    ss.bill_data = None

# Load dataframe from session state if it exists, otherwise load from CSV
if "df" not in ss:
    ss.df = load_csv('bills.csv')

if "all_bill_data" not in ss:
    ss.all_bill_data = []  # Add a list to store all processed bills

# If Demo Mode is enabled, pre-load files from the local working directory
if ss.demo_mode:
    current_working_dir = os.getcwd()
    demo_guidance_path = os.path.join(current_working_dir, "sample_files", "guidance.md")
    demo_bill_path = os.path.join(current_working_dir, "sample_files", "APS_bill.md")

    # Read files as bytes
    with open(demo_guidance_path, "rb") as f:
        ss.pdf_ref_guidance = f.read()
    with open(demo_bill_path, "rb") as f:
        ss.pdf_ref_toProcess = f.read()

# File for Guidance
with st.container():
    st.subheader("📘 Guidance File")
    if ss.demo_mode:
        st.success(f"📂 Demo File Loaded: guidance.pdf")
    else:
        guidance_file = st.file_uploader("Instructions file", type=['pdf', 'md'], key='pdf_guidance')
        if guidance_file is not None:
            ss.pdf_ref_guidance = guidance_file.getvalue()

    with st.expander("File Preview"):
        if ss.pdf_ref_guidance is not None:
            if ss.demo_mode:
                st.write("Guidance: guidance.md")
                st.write(f"  File size: {len(ss.pdf_ref_guidance)} bytes")
                try:
                    st.markdown(ss.pdf_ref_guidance.decode("utf-8", errors="ignore"))
                except Exception as e:
                    st.error(f"Failed to load Markdown: {e}")
            else:
                st.write("Guidance: Uploaded PDF or MD")
                st.write("  File size:", len(ss.pdf_ref_guidance), "bytes")
                try:
                    if st.session_state.pdf_guidance.type == 'application/pdf':
                        # Save the PDF to a temporary file and display it
                        with open("temp_guidance.pdf", "wb") as f:
                            f.write(ss.pdf_ref_guidance)
                        display_pdf("temp_guidance.pdf")
                    else:
                        text = ss.pdf_ref_guidance.decode("utf-8", errors="ignore")
                        st.markdown(text)
                except Exception as e:
                    st.error(f"Error extracting text from PDF: {e}")

st.divider()

# File for Processing
with st.container():
    st.subheader("📑 Bill to Process")

    if ss.demo_mode:
        current_working_dir = os.getcwd()
        st.success(f"📂 Demo File Loaded: bill_example_APS.pdf")
        sample_files_dir = os.path.join(current_working_dir, "sample_files")

        # Load guidance file
        demo_guidance_path = os.path.join(sample_files_dir, "guidance.md")
        with open(demo_guidance_path, "rb") as f:
            ss.pdf_ref_guidance = f.read()

        # Load bill files and process them
        bill_files = [f for f in os.listdir(sample_files_dir) if f.endswith("_bill.md")]
        # Add a text input field for additional notes
        additional_note = st.text_input("Enter additional notes:")
        for bill_file in bill_files:
            demo_bill_path = os.path.join(sample_files_dir, bill_file)
            with open(demo_bill_path, "rb") as f:
                bill_content = f.read().decode("utf-8")  # Decode to string
                ss.edited_text = bill_content

                try:
                    bill_data = parse_data_with_gemini(bill_content, "markdown")
                    if bill_data is None:
                        st.error(f"Error parsing bill data from {bill_file} in demo mode.")
                        continue  # Move to the next file

                    # Generate a unique bill_id
                    bill_data["bill_id"] = str(uuid.uuid4())

                    ss.all_bill_data.append(bill_data)  # Add the parsed data to the list

                    # Process the bill data using your BillPaymentSystem
                    ss.bill_system.set_current_user("demo", "AP Clerk")
                    bill_id = ss.bill_system.enter_bill(
                        customer_name=bill_data.get("customer_name"),
                        payee=bill_data.get("payee"),  # No default value.
                        previous_bill=bill_data.get("previous_bill"),
                        payment_amount=bill_data.get("payment"),
                        balance_forward=bill_data.get("balance_forward"),
                        amount_due=bill_data.get("total_amount_due"),
                        due_date=bill_data.get("due_date"),
                        received_date=bill_data.get("received_date"),
                        new_charges=bill_data.get("new_charges"),
                        note=additional_note  # Pass the additional note
                    )

                    update_csv(bill_data)  # Update the CSV file with the new bill data

                except Exception as e:
                    st.error(f"Error processing {bill_file}: {e}")
        ss.bill_data = ss.all_bill_data[-1] if ss.all_bill_data else None  # Set ss.bill_data to the last processed bill, or None if there are no bills.

        with st.expander("File Preview"):
            if ss.pdf_ref_toProcess is not None:
                st.write("Bill: bill_example_APS.md")
                st.write(f"  File size: {len(ss.pdf_ref_toProcess)} bytes")
                try:
                    text = ss.pdf_ref_toProcess.decode("utf-8", errors="ignore")
                    st.markdown(text)
                except Exception as e:
                    st.error(f"Failed to load Markdown: {e}")

        with st.expander("Edit File (Optional)"):
            if ss.pdf_ref_toProcess is not None:
                try:
                    text = ss.pdf_ref_toProcess.decode("utf-8", errors="ignore")
                    edited_text = st.text_area("Edit Markdown", text, height=300, key="demo_edit")
                    ss.edited_text = edited_text
                except Exception as e:
                    st.error(f"Failed to load Markdown: {e}")

    else:
        toProcess_file = st.file_uploader("Bill to Process file (PDF or MD)", type=['pdf', 'md'], key='pdf_toProcess')
        if toProcess_file is not None:
            ss.pdf_ref_toProcess = toProcess_file.getvalue()

        with st.expander("File Preview"):
            if ss.pdf_ref_toProcess is not None:
                st.write("Bill: Uploaded PDF or MD")
                st.write("  File size:", len(ss.pdf_ref_toProcess), "bytes")
                try:
                    if toProcess_file.type == 'application/pdf':
                        # Save the PDF to a temporary file and display it
                        with open("temp.pdf", "wb") as f:
                            f.write(ss.pdf_ref_toProcess)
                        display_pdf("temp.pdf")
                    else:
                        text = ss.pdf_ref_toProcess.decode("utf-8", errors="ignore")
                        st.markdown(text)
                except Exception as e:
                    st.error(f"Error extracting text from PDF: {e}")

        with st.expander("Edit File (Optional)"):
            if ss.pdf_ref_toProcess is not None:
                try:
                    if toProcess_file.type == 'application/pdf':
                        text = extract_text_from_pdf(ss.pdf_ref_toProcess)
                    else:
                        text = ss.pdf_ref_toProcess.decode("utf-8", errors="ignore")
                    edited_text = st.text_area("Edit Markdown", text, height=300, key="standard_edit")
                    ss.edited_text = edited_text
                except Exception as e:
                    st.error(f"Error extracting text from PDF: {e}")

    if st.button("Process"):
        print("--- Process Button Clicked ---")  # Indicate that the process started

        try:
            if ss.demo_mode:
                print("--- Demo Mode Activated ---")
                if ss.bill_data is None:
                    st.error("Error parsing bill data in demo mode.")
                    st.stop()
                bill_data = ss.bill_data  # This line ensures we are using the pre-parsed data.
                 # Debugging: Inspect bill_data before entering the bill
                print("--- Bill Data Before Enter Bill ---")
                print(bill_data)
                print("-----------------------------------")

                if "payee" not in bill_data:
                    st.error("Error: Payee information not found in parsed data.")
                    st.stop()

                if ss.bill_data:
                    ss.processed_text = str(ss.bill_data)
                    print(f"ss.bill_data: {ss.bill_data}")
                    print(f"ss.processed_text: {ss.processed_text}")
                else:
                    ss.processed_text = None

                print("\n--- Demo Mode Bill Data (Parsed by Gemini) ---")
                print(bill_data)
                print("-----------------------------------------------\n")

                ss.bill_system.set_current_user("demo", "AP Clerk")

                bill_id = ss.bill_system.enter_bill(
                    customer_name=bill_data.get("customer_name"),
                    payee=bill_data.get("payee"),  # No default value.
                    previous_bill=bill_data.get("previous_bill"),
                    payment_amount=bill_data.get("payment"),
                    balance_forward=bill_data.get("balance_forward"),
                    amount_due=bill_data.get("total_amount_due"),
                    due_date=bill_data.get("due_date"),
                    received_date=bill_data.get("received_date"),
                    new_charges=bill_data.get("new_charges"),
                    note=additional_note  # Pass the additional note
                )

            else:
                print("--- Standard Mode Activated (File Processing) ---")
                ss.bill_system.set_current_user("appUser", "AP Clerk")
                text = ss.edited_text  # Use the edited text
                data_type = "markdown"  # Default to markdown

                bill_data = parse_data_with_gemini(text, data_type)  # Use gemini parser
                if bill_data is None:
                    st.error(f"Error parsing data with Gemini API. Data type: {data_type}")
                    st.stop()
                ss.bill_data = bill_data

                # Generate a unique bill_id
                bill_data["bill_id"] = str(uuid.uuid4())

                if ss.bill_data:
                    ss.processed_text = str(ss.bill_data)
                    print(f"ss.bill_data: {ss.bill_data}")
                    print(f"ss.processed_text: {ss.processed_text}")
                else:
                    ss.processed_text = None

                print("\n--- Parsed Bill Data (Gemini API) ---")
                print(bill_data)
                print("--------------------------------------\n")

                bill_id = ss.bill_system.enter_bill(
                    payee=bill_data.get("payee"),  # Payee is now reliable.
                    customer_name=bill_data.get("customer_name"),
                    previous_bill=bill_data.get("previous_bill"),
                    payment_amount=bill_data.get("payment"),
                    balance_forward=bill_data.get("balance_forward"),
                    amount_due=bill_data.get("total_amount_due"),
                    due_date=bill_data.get("due_date"),
                    received_date=bill_data.get("received_date"),
                    new_charges=bill_data.get("new_charges"),
                    note=additional_note  # Pass the additional note
                )

            update_csv(ss.bill_data)  # Update the CSV file with the new bill data
            # Load and display the updated CSV file
            df = load_csv('bills.csv')
            if df is not None:
                st.subheader("📊 Processed Bills")
                st.dataframe(df)
                ss.df = df  # store dataframe in session state
            else:
                ss.df = None  # if no dataframe store none

        except Exception as e:
            print("--- Error During Processing ---")
            print(f"Error: {e}")
            st.error(f"Error processing data: {e}")

st.divider()

# Chat interface
with st.container():  # Create a container for the chat interface
    if ss.df is not None and not ss.df.empty:  # Check if the dataframe exists and is not empty
        st.divider()
        st.subheader("Chat with Gemini about the Processed Bills")

        # Display the DataFrame
        st.subheader("📊 Processed Bills")
        st.dataframe(ss.df)

        # Concatenate the contents of all processed bills into a single context string
        context = "\n\n".join([str(bill) for bill in ss.all_bill_data])

        # Display chat history
        for message in ss.chat_history:
            with st.chat_message(message["role"]):
                st.markdown(message["content"])

        # User input
        if prompt := st.chat_input("Ask a question about the bills"):
            ss.chat_history.append({"role": "user", "content": prompt})
            with st.chat_message("user"):
                st.markdown(prompt)

            # Send prompt and context to Gemini
            try:
                answer = generate_chat_response(context, prompt)
                ss.chat_history.append({"role": "assistant", "content": answer})
                with st.chat_message("assistant"):
                    st.markdown(answer)

            except Exception as e:
                st.error(f"Error generating response: {e}")
    else:
        st.info("Please process a bill to begin chatting.")

st.divider()