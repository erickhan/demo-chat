import os
import streamlit as st
from streamlit import session_state as ss
from streamlit_pdf_viewer import pdf_viewer
from billpay import BillPaymentSystem
import io
import pypdf
from gemini_parser import parse_data_with_gemini  # Import Gemini parser

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
    ss.bill_system = BillPaymentSystem("ACME Corporation") #initialize the bill_system here.

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
        guidance_file = st.file_uploader("Instructions file", type=('pdf'), key='pdf_guidance')
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
        st.success(f"📂 Demo File Loaded: bill_example_APS.pdf")
        # Explicitly decode the bill data in demo mode
        text = ss.pdf_ref_toProcess.decode("utf-8")
        bill_data = parse_data_with_gemini(text, "markdown")
        if bill_data is None:
            st.error(f"Error parsing demo bill data with Gemini API.")
            st.stop()
    else:
        toProcess_file = st.file_uploader("Bill to Process file (PDF or MD)", type=['pdf', 'md'], key='pdf_toProcess')
        if toProcess_file is not None:
            ss.pdf_ref_toProcess = toProcess_file.read()
            ss.toProcess_file = toProcess_file  # Store in session state
        else:
            toProcess_file = None  # initialize toProcess_file to none.

    with st.expander("File Preview"):
        if ss.pdf_ref_toProcess is not None:
            if ss.demo_mode:
                st.write("Bill: APS_bill.md")
                st.write(f"  File size: {len(ss.pdf_ref_toProcess)} bytes")
                try:
                    st.markdown(ss.pdf_ref_toProcess.decode("utf-8", errors="ignore"))
                except Exception as e:
                    st.error(f"Failed to load Markdown: {e}")
            else:
                st.write("Bill: Uploaded File")
                st.write("  File size:", len(ss.pdf_ref_toProcess), "bytes")
                try:
                    if toProcess_file is not None and toProcess_file.type == 'application/pdf':
                        pdf_viewer(input=ss.pdf_ref_toProcess, width=700)
                    elif toProcess_file is not None:  # Assume markdown
                        st.markdown(ss.pdf_ref_toProcess.decode("utf-8", errors="ignore"))
                except Exception as e:
                    st.error(f"Failed to load file: {e}")
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
            print("--- Process Button Clicked ---")  # Indicate that the process started

            try:
                if ss.demo_mode:
                    print("--- Demo Mode Activated ---")
                    print("\n--- Demo Mode Bill Data (Parsed by Gemini) ---")
                    print(bill_data)
                    print("-----------------------------------------------\n")
                    
                    # **THIS LINE IS MOVED UP**: Set the current user *before* doing anything else.
                    ss.bill_system.set_current_user("demo", "AP Clerk")
                    
                    bill_id = ss.bill_system.enter_bill(
                        customer_name = bill_data.get("customer_name"),
                        previous_bill= bill_data.get("previous_bill"),
                        payment_amount= bill_data.get("payment"),
                        balance_forward= bill_data.get("balance_forward"),
                        amount_due=bill_data.get("total_amount_due"),
                        due_date= bill_data.get("due_date"),
                        received_date= bill_data.get("received_date"),
                        new_charges = bill_data.get("new_charges"),
                    )

                    
                    # now that the user is set, the bill can be verified and scheduled.
                    ss.bill_system.verify_bill(bill_id)
                    ss.bill_system.schedule_payment(bill_id)
                    print(f"Bill {bill_id} data added and processed (Demo Mode).\n")

                else:
                    print("--- Standard Mode Activated (File Processing) ---")
                    # **THIS LINE IS MOVED UP:** Set the current user *before* doing anything else.
                    ss.bill_system.set_current_user("appUser", "AP Clerk")
                    
                    text = ss.pdf_ref_toProcess.decode("utf-8")
                    data_type = "markdown"  # Default to markdown

                    if ss.toProcess_file is not None and ss.toProcess_file.type == 'application/pdf':  # Use the session state variable
                        pdf_text = extract_text_from_pdf(ss.pdf_ref_toProcess)
                        if pdf_text:
                            text = pdf_text
                            data_type = "PDF"  # Set data_type to PDF
                        else:
                            st.error("Error: PDF extraction failed.")
                            st.stop()

                    bill_data = parse_data_with_gemini(text, data_type)  # Use gemini parser
                    if bill_data is None:
                        st.error(f"Error parsing data with Gemini API. Data type: {data_type}")
                        st.stop()

                    print("\n--- Parsed Bill Data (Gemini API) ---")
                    print(bill_data)
                    print("--------------------------------------\n")

                    bill_id = ss.bill_system.enter_bill(
                        customer_name=bill_data.get("customer_name"),
                        previous_bill=bill_data.get("previous_bill"),
                        payment_amount=bill_data.get("payment"),
                        balance_forward=bill_data.get("balance_forward"),
                        amount_due=bill_data.get("total_amount_due"),
                        due_date=bill_data.get("due_date"),
                        received_date=bill_data.get("received_date"),
                        new_charges=bill_data.get("new_charges"),
                    )

                    
                    ss.bill_system.verify_bill(bill_id)
                    ss.bill_system.schedule_payment(bill_id)
                    print(f"Bill {bill_id} data added and processed.\n")

            except Exception as e:
                print(f"--- Error During Processing ---")
                print(f"Error: {e}")
                st.error(f"Error processing data: {e}")

    st.divider()
