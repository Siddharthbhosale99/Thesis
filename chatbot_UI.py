import streamlit as st
import sqlite3
import os
import importlib
import pandas as pd
from datetime import date, datetime

# --- Load your chatbot backend
import chatbot_backend1
importlib.reload(chatbot_backend1)
from chatbot_backend1 import dynamic_category_response

# --- Theme config
os.makedirs(".streamlit", exist_ok=True)
with open(".streamlit/config.toml", "w") as f:
    f.write(
        """
[theme]
base="light"
primaryColor="#FFA500"
backgroundColor="#FFFFFF"
secondaryBackgroundColor="#FFF7E8"
textColor="#000000"
font="sans serif"
        """
    )

# --- Optional CSS
st.markdown(
    """
    <style>
    .css-18e3th9 { background-color: #FFFFFF !important; }
    .css-12oz5g7 { color: #000000 !important; }
    </style>
    """,
    unsafe_allow_html=True
)

# --- Lists
categories = [
    "billing", "shipping", "cancellation", "subscription", "order_status",
    "payment_issue", "general_query", "refund", "technical_support", "feedback"
]
product_list = ["Laptop", "Mobile Phone", "TV", "Headphones", "Smart Watch" , "Ott subscribtion " , "Others" ]

def clean_response(response: str) -> str:
    """Remove 'Bot:' prefix if present."""
    if "Bot:" in response:
        return response.split("Bot:")[-1].strip()
    return response.strip()

# --- Page navigation
if "page" not in st.session_state:
    st.session_state.page = "welcome"

# --- SQLite setup
conn = sqlite3.connect("user_data.db")
cursor = conn.cursor()
cursor.execute(
    """
    CREATE TABLE IF NOT EXISTS user_records(
        record_id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT,
        email TEXT,
        product_name TEXT,
        order_date TEXT,
        delivery_date TEXT,
        category TEXT,
        issue_detail TEXT,
        chosen_response TEXT,
        rating INTEGER,
        feedback TEXT,
        created_at TEXT
    )
    """
)
conn.commit()

def add_back_button(prev_page):
    """Reusable back button helper."""
    if st.button("Back"):
        st.session_state.page = prev_page
        st.experimental_rerun()

# ------------------ PAGE 1: WELCOME ------------------
if st.session_state.page == "welcome":
    st.title("Welcome to Customer Support")
    st.write("We're here to help you with your product and order-related issues.")
    if st.button("Start"):
        st.session_state.page = "get_details"
        st.experimental_rerun()
    st.stop()

# ------------------ PAGE 2: GET USER DETAILS ------------------
if st.session_state.page == "get_details":
    st.title("Enter Your Details")
    name = st.text_input("Name:")
    email = st.text_input("Email:")
    product_choice = st.selectbox("Product:", product_list)
    order_dt = st.date_input("Order Date:", value=date.today())
    delivery_dt = st.date_input("Delivery Date:", value=date.today())
    not_delivered = st.checkbox("Not yet delivered?")
    delivery = "Not yet delivered" if not_delivered else delivery_dt.isoformat()

    col1, col2 = st.columns(2)
    with col1:
        if st.button("Back"):
            st.session_state.page = "welcome"
            st.experimental_rerun()
    with col2:
        if st.button("Continue"):
            st.session_state.user_name = name
            st.session_state.email = email
            st.session_state.product_choice = product_choice
            st.session_state.order_date = order_dt
            st.session_state.delivery_date = delivery
            st.session_state.page = "greeting"
            st.experimental_rerun()
    st.stop()

# ------------------ PAGE 3: GREETING ------------------
if st.session_state.page == "greeting":
    st.title(f"Hello, {st.session_state.get('user_name', 'Customer')}!")
    greeting = st.radio("Select your greeting:", ["Good morning", "Good afternoon", "Good evening"])
    st.write(f"{greeting}, how can I help you today?")

    col1, col2 = st.columns(2)
    with col1:
        add_back_button("get_details")
    with col2:
        if st.button("Proceed to Issue Selection"):
            st.session_state.page = "select_category"
            st.experimental_rerun()
    st.stop()

# ------------------ PAGE 4: ISSUE CATEGORY ------------------
if st.session_state.page == "select_category":
    st.title("Select an Issue Category")
    selected_category = st.selectbox("Choose a category:", categories)

    col1, col2 = st.columns(2)
    with col1:
        add_back_button("greeting")
    with col2:
        if st.button("Next"):
            st.session_state.selected_category = selected_category
            st.session_state.page = "get_issue"
            st.experimental_rerun()
    st.stop()

# ------------------ PAGE 5: GET ISSUE DETAILS ------------------
if st.session_state.page == "get_issue":
    st.title("Describe Your Issue")
    issue_detail = st.text_input("What problem are you facing?")

    col1, col2 = st.columns(2)
    with col1:
        add_back_button("select_category")
    with col2:
        if st.button("Generate Responses"):
            st.session_state.issue_detail = issue_detail
            st.session_state.page = "responses_and_feedback"
            # Clear old responses
            st.session_state.pop("response_candidates", None)
            st.experimental_rerun()
    st.stop()

# ------------------ PAGE 6: RESPONSES + FEEDBACK ------------------
if st.session_state.page == "responses_and_feedback":
    st.title("Select or Customize a Response")

    # 1. Generate or retrieve candidate responses
    if "response_candidates" not in st.session_state:
        category = st.session_state.get("selected_category", "")
        issue_detail = st.session_state.get("issue_detail", "")
        context = {"user_name": st.session_state.get("user_name", "Customer")}

        # Generate 3 random or AI-based responses
        candidates = []
        for _ in range(3):
            resp = dynamic_category_response(category, issue_detail, context)
            candidates.append(clean_response(resp))

        # Remove duplicates, then add "Custom Response"
        unique_candidates = list(dict.fromkeys(candidates))
        unique_candidates.append("Custom Response")

        st.session_state.response_candidates = unique_candidates

    # 2. The radio widget
    chosen_option = st.radio(
        "Pick a response:",
        st.session_state.response_candidates,
        index=0,  
        key="chosen_option"
    )

    # 3. If user picks "Custom Response," show a text area for custom text
    if chosen_option == "Custom Response":
       
        custom_text = st.text_area(
            "Type your custom response here:",
            key="custom_response_text"  
        )
        final_response = custom_text  
    else:
        # If a canned response was chosen
        final_response = chosen_option

    # 4. Rating slider
    rating = st.slider(
        "Rate Your Experience:",
        min_value=1,
        max_value=5,
        value=3,   
        key="rating"  
    )

    # 5. Feedback text area
    feedback_text = st.text_area(
        "Additional feedback (optional):",
        key="feedback_text"  # The widget manages st.session_state["feedback_text"]
    )

    # 6. Buttons
    col1, col2 = st.columns(2)
    with col1:
        add_back_button("get_issue")
    with col2:
        if st.button("Finish & Save"):
            # If user picked "Custom Response" but typed nothing, warn
            if chosen_option == "Custom Response" and not final_response.strip():
                st.warning("Please enter a custom response before submitting.")
                st.stop()

            # Insert into DB
            now_str = datetime.now().isoformat(sep=" ", timespec="seconds")
            name = st.session_state.get("user_name", "")
            email = st.session_state.get("email", "")
            product_choice = st.session_state.get("product_choice", "")
            order_dt = st.session_state.get("order_date", date.today())
            delivery = st.session_state.get("delivery_date", "")
            category = st.session_state.get("selected_category", "")
            issue_detail = st.session_state.get("issue_detail", "")

            cursor.execute(
                """
                INSERT INTO user_records (
                    name, email, product_name, order_date,
                    delivery_date, category, issue_detail,
                    chosen_response, rating, feedback, created_at
                ) VALUES (?,?,?,?,?,?,?,?,?,?,?)
                """,
                (
                    name,
                    email,
                    product_choice,
                    order_dt.isoformat(),
                    delivery,
                    category,
                    issue_detail,
                    final_response,
                    st.session_state.rating,       
                    st.session_state.feedback_text, 
                    now_str
                )
            )
            conn.commit()

            # Also save to Excel
            try:
                existing_df = pd.read_excel("user_data.xlsx")
            except FileNotFoundError:
                existing_df = pd.DataFrame()

            new_df = pd.DataFrame([{
                "name": name,
                "email": email,
                "product_name": product_choice,
                "order_date": order_dt.isoformat(),
                "delivery_date": delivery,
                "category": category,
                "issue_detail": issue_detail,
                "chosen_response": final_response,
                "rating": st.session_state.rating,
                "feedback": st.session_state.feedback_text,
                "created_at": now_str
            }])
            final_df = pd.concat([existing_df, new_df], ignore_index=True)
            final_df.to_excel("user_data.xlsx", index=False)

            st.success("Record saved to user_data.db and user_data.xlsx.")
            st.session_state.page = "done"
            st.experimental_rerun()

    st.stop()

# ------------------ PAGE 7: DONE ------------------
if st.session_state.page == "done":
    st.title("Thank You!")
    st.write("Your record was saved. Have a great day!")
    if st.button("Restart"):
        st.session_state.clear()
    st.stop()
