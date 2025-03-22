import streamlit as st
import importlib
import re

# Force a reload of your backend module to use the latest version.
import chatbot_backend1
importlib.reload(chatbot_backend1)
from chatbot_backend1 import dynamic_category_response

# List of possible issue categories.
categories = [
    "billing", "shipping", "cancellation", "subscription",
    "order_status", "payment_issue", "general_query",
    "refund", "technical_support", "feedback"
]

# Function to clean the generated response.
def clean_response(response):
    # If "Bot:" exists in the response, extract text after it.
    if "Bot:" in response:
        return response.split("Bot:")[-1].strip()
    return response.strip()

# Initialize session state for multi-page navigation.
if "page" not in st.session_state:
    st.session_state["page"] = "welcome"

# Page 1: Welcome Page
if st.session_state["page"] == "welcome":
    st.title("Welcome to Customer Support")
    st.write("Welcome to Customer Support!")
    if st.button("Start"):
        st.session_state["page"] = "get_name"
    st.stop()

# Page 2: Get User Name
if st.session_state["page"] == "get_name":
    st.title("Enter Your Name")
    name = st.text_input("Please enter your name:", key="name_input")
    if name:
        st.session_state["user_name"] = name
        if st.button("Continue"):
            st.session_state["page"] = "greeting"
    st.stop()

# Page 3: Greeting and Greeting Selection
if st.session_state["page"] == "greeting":
    name = st.session_state.get("user_name", "Customer")
    st.title(f"Hello {name}!")
    st.write(f"Hi {name}!")
    # Provide radio buttons for selecting a greeting.
    greeting = st.radio("Select your greeting:", ["Good morning", "Good afternoon", "Good evening"])
    st.write(f"{greeting}, How can I help you today?")
    if st.button("Proceed to Issue Selection"):
        st.session_state["greeting"] = greeting
        st.session_state["page"] = "select_category"
    st.stop()

# Page 4: Issue Category Selection
if st.session_state["page"] == "select_category":
    st.title("Select an Issue Category")
    selected_category = st.selectbox("Choose a category", categories)
    if st.button("Next"):
        st.session_state["selected_category"] = selected_category
        st.session_state["page"] = "get_responses"
    st.stop()

# Page 5: Display Candidate Responses for the Selected Category
if st.session_state["page"] == "get_responses":
    st.title("Candidate Responses")
    selected_category = st.session_state.get("selected_category", "billing")
    
    # Let the user input issue details with no default text, removing "optional" mention.
    issue_detail = st.text_input("Enter your issue details:", value="")
    
    # Generate candidate responses.
    candidates = []
    context = {"user_name": st.session_state.get("user_name", "Customer")}
    for i in range(3):
        response = dynamic_category_response(selected_category, issue_detail, context)
        cleaned = clean_response(response)
        candidates.append(cleaned)
    
    # Remove duplicate responses while preserving order.
    unique_candidates = list(dict.fromkeys(candidates))
    
    st.write("Select the response you want to send:")
    # Add an extra option for a custom response.
    unique_candidates.append("Custom Response")
    chosen_option = st.radio("Candidate Responses:", unique_candidates, key="response_radio")
    
    # If custom response is selected, display a text input box.
    if chosen_option == "Custom Response":
        custom_response = st.text_area("Type your custom response here:")
        final_response = custom_response
    else:
        final_response = chosen_option
        
    if st.button("Submit Response"):
        st.session_state["chosen_response"] = final_response
        st.session_state["page"] = "display_response"
    st.stop()

# Page 6: Display the Chosen Response and Feedback
if st.session_state["page"] == "display_response":
    st.title("Response Chosen")
    chosen_response = st.session_state.get("chosen_response", "")
    st.write("The chosen response is:")
    st.write(chosen_response)
    st.markdown("---")
    st.write("**Thank you for contacting Customer Support!**")
    st.write("If you would like to start a new conversation, please click the restart button below.")
    st.markdown("### Please provide your feedback:")
    
    # Feedback: rating and comments.
    rating = st.slider("Rate your experience:", 1, 5, 3)
    comments = st.text_area("Additional comments (optional):")
    if st.button("Submit Feedback"):
        # Here you might save feedback to a database or file.
        st.success("Thank you for your feedback!")
    
    # Only here is the "Restart Conversation" button present.
    if st.button("Restart Conversation"):
        st.session_state.clear()
        st.experimental_rerun()
