import streamlit as st
from streamlit.components.v1 import html
import pandas as pd
import hashlib
import time
from io import BytesIO
import sqlite3
import plotly.express as px
import requests
import base64
import os



# OpenAI API Endpoint and API Key
OPENAI_API_URL = "https://api.openai.com/v1/chat/completions"
API_KEY ="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"  # Replace this with your actual API key

# Function to call OpenAI API
def get_openai_response(prompt):
    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json",
    }
    payload = {
        "model": "gpt-3.5-turbo",
        "messages": [
            {"role": "system", "content": "You are a helpful assistant for a dashboard analyzing economic data like GDP, youth unemployment, and sectoral contributions."},
            {"role": "user", "content": prompt},
        ],
    }
    try:
        response = requests.post(OPENAI_API_URL, headers=headers, json=payload)
        response.raise_for_status()  # Raise an error for bad HTTP responses
        result = response.json()
        return result["choices"][0]["message"]["content"]
    except requests.exceptions.RequestException as e:
        return f"Error: {e}"


# Database setup
def init_db():
    conn = sqlite3.connect('users.db')
    c = conn.cursor()
    # Create table if not exists
    c.execute('''
        CREATE TABLE IF NOT EXISTS users (
            email TEXT PRIMARY KEY,
            password TEXT NOT NULL,
            name TEXT NOT NULL
        )
    ''')
    conn.commit()
    conn.close()

# Initialize the database
init_db()

# Helper functions for password hashing
def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

def verify_password(password, hashed):
    return hash_password(password) == hashed

# Database operations
def add_user(email, password, name):
    conn = sqlite3.connect('users.db')
    c = conn.cursor()
    try:
        c.execute('INSERT INTO users (email, password, name) VALUES (?, ?, ?)', 
                  (email, hash_password(password), name))
        conn.commit()
        success = True
    except sqlite3.IntegrityError:
        success = False
    conn.close()
    return success

def get_user(email):
    conn = sqlite3.connect('users.db')
    c = conn.cursor()
    c.execute('SELECT * FROM users WHERE email = ?', (email,))
    user = c.fetchone()
    conn.close()
    return user

def update_password(email, new_password):
    conn = sqlite3.connect('users.db')
    c = conn.cursor()
    c.execute('UPDATE users SET password = ? WHERE email = ?', 
              (hash_password(new_password), email))
    conn.commit()
    conn.close()
def get_base64_image(image_path):
    with open(image_path, "rb") as img_file:
        return base64.b64encode(img_file.read()).decode()
def add_background_image(image_file):
    st.markdown(
        f"""
        <style>
        .stApp {{
            background: url(data:image/png;base64,{image_file});
            background-size: cover;
            
        }}
        </style>
        """,
        unsafe_allow_html=True
    )

# Replace 'background.jpg' with your image file path
image_path = "india.jpg"
if os.path.exists(image_path):
    image_base64 = get_base64_image(image_path)
    add_background_image(image_base64)
else:
    st.warning("Background image not found.")


# Initialize session state
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
if "user" not in st.session_state:
    st.session_state.user = None
if "reset_password_step" not in st.session_state:
    st.session_state.reset_password_step = None
if "email_to_reset" not in st.session_state:
    st.session_state.email_to_reset = None

# Authentication Functionality
def signup():
    st.title("🔒 Sign Up")
    email = st.text_input("Email")
    name = st.text_input("Name")
    password = st.text_input("Password", type="password")
    confirm_password = st.text_input("Confirm Password", type="password")

    if st.button("Sign Up"):
        if not email or not name or not password:
            st.error("Please fill in all fields.")
        elif get_user(email):
            st.error("Email already exists.")
        elif password != confirm_password:
            st.error("Passwords do not match.")
        else:
            success = add_user(email, password, name)
            if success:
                st.success("Sign up successful. Please log in.")
                time.sleep(1)
                st.experimental_rerun()
            else:
                st.error("Error signing up. Please try again.")

def login():
    st.title("🔒Login")
    email = st.text_input("Email")
    password = st.text_input("Password", type="password")

    if st.button("Login"):
        user = get_user(email)
        if user and verify_password(password, user[1]):
            st.session_state.logged_in = True
            st.session_state.user = user[2]
            st.success("Login successful🔓")
            time.sleep(1)
        else:
            st.error("Invalid email or password.")

    if st.button("Forgot Password"):
        st.session_state.reset_password_step = 1
        # st.experimental_rerun()

def reset_password():
    if st.session_state.reset_password_step == 1:
        st.title("Reset Password")
        email = st.text_input("Enter your registered Email")

        if st.button("Submit"):
            user = get_user(email)
            if user:
                st.session_state.email_to_reset = email
                st.session_state.reset_password_step = 2
                # st.experimental_rerun()
            else:
                st.error("Email not found. Please check and try again.")

    elif st.session_state.reset_password_step == 2:
        st.title("Set New Password")
        new_password = st.text_input("New Password", type="password")
        confirm_new_password = st.text_input("Confirm New Password", type="password")

        if st.button("Reset Password"):
            if not new_password:
                st.error("Password cannot be empty.")
            elif new_password != confirm_new_password:
                st.error("Passwords do not match.")
            else:
                update_password(st.session_state.email_to_reset, new_password)
                st.success("Password has been reset successfully.")
                time.sleep(1)
                st.session_state.reset_password_step = None
                st.session_state.email_to_reset = None
                # st.experimental_rerun()

def logout():
    st.session_state.logged_in = False
    st.session_state.user = None
    # st.experimental_rerun()

# Main App Description
def app_description():
    st.markdown("<h2 style='color: #1a3704;'>Indian GDP and Productivity </h1>", unsafe_allow_html=True)
    st.markdown("""
    <style>
        
        .custom-paragraph {
            font-size: 18px;
            color:#1a3704 ; 
            text-align: justify;
            line-height: 1.6;
        }
    </style>
    
    <div class="custom-paragraph">
        India is one of the fastest-growing economies in the world, with its cities playing a pivotal role in 
        contributing to the nation's GDP and overall productivity. The economic activities in these cities 
        span various sectors, including information technology, manufacturing, trade, and services.
                
    </div>
    """, unsafe_allow_html=True)
    st.markdown("""
    <style>
        .custom-text {
            font-size: 20px; /* Set font size */
            color: #1a3704; /* Set text color */
            text-align: left; /* Align text to the left */
            line-height: 1.8; /* Increase line spacing for readability */
            padding: 10px; /* Add padding around the text */
           
            
        }
    </style>
    <div class="custom-text">
        Understanding the GDP and productivity metrics of Indian cities is crucial for:
        <ul>
            <li>Identifying economic hubs.</li>
            <li>Planning investments and developmental initiatives.</li>
            <li>Analyzing sectoral growth and workforce contributions.</li>
            <li>This app is designed to provide you with valuable insights, gather feedback, and present data in an interactive dashboard.</>
        </ul>
    </div>
""", unsafe_allow_html=True)
    st.markdown("<h5 style='color:olive green;'>How to Navigate:</h5>", unsafe_allow_html=True)
    st.markdown("""
    <style>
        .custom-text {
            font-size: 20px; /* Set font size */
            color: #1a3704; /* Set text color */
            text-align: left; /* Align text to the left */
            line-height: 1.8; /* Increase line spacing for readability */
            padding: 10px; /* Add padding around the text */
           
            
        }
    </style>
    <div class="custom-text">
        <ul>
            <li>Dashboard: Explore the latest data trends and visualizations/</li>
            <li>Additional Insights: Dive deeper into specific areas for more information.</li>
            <li>About: see conclusion,Share your thoughts to help us improve and for any help contact us.</li>
        </ul>
    </div>
""", unsafe_allow_html=True)
    st.markdown("<h3 style='text-align: center; color: #1a3704;'>Click button to explore more!!!</h3>", unsafe_allow_html=True)
        

# Power BI Dashboard Integration
def dashboard():
    st.markdown("<h2 style='color:#1a3704;'>GDP and Productivity Dashboard</h2>", unsafe_allow_html=True)
    st.write("""GDP: Gross Domestic Product (GDP) is a widely used indicator of a country's economic performance and growth. It represents the total value of all final goods and services produced within a country's borders over a specific period, typically a year.
        """)
    
    st.write(""" Productivity: Productivity of a country refers to the efficiency with which a country uses its resources, such as labor, capital, and technology, to produce goods and services.
            """)

    st.write("This dashboard provides insights and visualizations of gdp and productivity metrices of differet indian cities.")
    st.write("Click the buttons in the dashboard to explore more insights")
    st.components.v1.iframe("https://app.powerbi.com/view?r=eyJrIjoiYjdjZWVlMjUtZGQyMC00MjI4LWEzMTUtM2QxNDA5Yjk3ZTQ4IiwidCI6IjQ3NjlkODk1LTEwODEtNGZiYS1hZjVmLTg5ZTdjOGQ0NzRhMiJ9", height=500)
    st.markdown("<h1 style='color: #1a3704;'>🎯 Conclusion</h1>", unsafe_allow_html=True)
    st.markdown("#### - Top GDP Performers:")

    st.write("Ahmedabad achieved the highest GDP at 294 biliion dollars then comes Mumbai with $294.1 billion, supported by a balanced distribution across tourism, SMEs, and ICT sectors.")

           
    st.markdown("#### - Economic Diversification:")

    st.write("Cities like Ahmedabad, Bengaluru, and Hyderabad show significant contributions from the ICT sector, indicating a tech-driven economy.Mumbai and Chennai have diversified economies with notable inputs from tourism, ICT, and SME sectors.")
                
    st.markdown("#### - Youth Unemployment Trends:")

    st.write("Cities like Pune (2023) and Surat (2023) exhibit the lowest youth unemployment rates (8.3% and 8.7%, respectively), suggesting robust job creation.Ranchi (2023) and Ahmedabad (2023) also recorded improved employment metrics, indicating a steady economic recovery post-2020.")
                
    st.markdown("#### - Sector-Specific Strengths:")

    st.write("Tourism: Kolkata and Hyderabad show consistently higher employment in the tourism sector.")
    st.write("ICT Sector: Bengaluru and Hyderabad lead in ICT employment, making them tech hubs of the country.")
    st.write("Agriculture: Vadodara and Ahmedabad still maintain a significant portion of their economy in agriculture, ensuring rural inclusion in economic growth.")
                
    st.markdown("#### - Overall Economic Productivity:")

    st.write("Ahmedabad, Mumbai, and Bengaluru emerge as the most economically productive cities, combining high GDP, diversified sectoral contributions, and improving employment metrics.Cities like Vadodara and Surat have demonstrated exceptional growth trajectories in GDP and sectoral performances, positioning them as rising economic hubs.")

def data_download():
    st.markdown("<h2 style='color:#1a3704;'>Sample dataset</h2>",unsafe_allow_html=True)
    df="Final_dataset.csv"
    try:
    # Load data
        data = pd.read_csv(df)
        # st.write(data.head())
        Year = st.multiselect("Filter by Year", options=data["Year"].unique())
        City = st.multiselect("Filter by City", options=data["City"].unique())

        filtered_data1 = data
        if Year:
             filtered_data1 = filtered_data1[filtered_data1["Year"].isin(Year)]
        if City:
            filtered_data1 = filtered_data1[filtered_data1["City"].isin(City)]
        st.write(filtered_data1)
        csv = filtered_data1.to_csv(index=False)
        st.download_button("Download Data", data=csv, file_name="filtered_data1.csv", mime="text/csv")

        
    except FileNotFoundError:
        st.error("Error loading data. Ensure the 'InfosysDataset.csv' file exists in the working directory.")
    except Exception as e:
        st.error(f"An unexpected error occurred: {e}")


    # Additional insights based on gdp trends
    st.markdown("<h2 style='color:#1a3704;'>GDP Trends</h2>", unsafe_allow_html=True)
    st.write("""GDP:Gross Domestic Product (GDP) measures a country's economic output.It calculates the total value of goods and services produced within a country's borders.GDP includes personal consumption, investment, government spending, and net exports.""")
    st.write("""Economic Growth Rate:Economic growth rate measures the percentage change in a country's GDP over time.It indicates the pace at which a country's economy is expanding or contracting.A high growth rate signals a strong economy, while a low rate may indicate stagnation.Economic growth rate is a key indicator of a country's economic health and development prospects.""")
    selected_year = st.selectbox("Select Year", options=data["Year"].unique())
    selected_cities = st.multiselect("Select Cities", options=data["City"].unique())

    # Filter data based on selections
    filtered_data = data[(data["Year"] == selected_year) & (data["City"].isin(selected_cities))]

    # Main section
    st.markdown("<h4 style='color:#1a3704;'>GDP and Economic growth ratew viewer</h4>", unsafe_allow_html=True)
    filtered_data = filtered_data[["City","GDP (in billion $)","Economic Growth Rate (%)"]].reset_index(drop=True)
    if not filtered_data.empty:
        st.write(filtered_data)
    # fig1 = px.bar(data, x='Year', y=gdp,title=f"{gdp}  Over Years", labels={'value': f'{gdp}'}, color_discrete_sequence=['#556B2F']) 
    # st.plotly_chart(fig1)
    st.write("""Understanding GDP and economic growth helps individuals and policymakers make informed decisions. It guides investment choices, strategic planning, and policy-making. GDP and economic growth data inform decisions on taxation, spending, and regulation. It also helps identify areas for economic development and improve standard of living. Overall, understanding GDP and economic growth promotes economic stability and sustainable development.""")

    st.write("--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------")


     # Additional insights based on  sector contribution
    st.markdown("<h2 style='color:#1a3704;'>Sector Contribution</h2>", unsafe_allow_html=True)
    sector=st.selectbox("Select to view contributing sectors",["Agriculture (%)","Industrial Sector Contribution (%)","Service Sector Contribution (%)"])
    if sector == "Agriculture (%)":
        st.write("""The agriculture sector's contribution to a country's economy is measured by its share of GDP.It provides employment opportunities, food security, and raw materials for industries.A strong agriculture sector can reduce poverty, increase exports, and improve overall economic growth.In many developing countries, agriculture remains a significant contributor to GDP, often ranging from 20-50% of total GDP.""")
    elif sector == "Industrial Sector Contribution (%)":
        st.write("""The industrial sector's contribution to a country's economy is measured by its share of GDP, typically ranging from 20-40%.This sector drives economic growth, generates employment, and produces goods for domestic consumption and exports.A strong industrial sector can transform a country's economy, increasing its competitiveness and prosperity.""")
    elif sector == "Service Sector Contribution (%)":
        st.write("""The service sector's contribution to a country's economy is measured by its share of GDP, often accounting for 50-70%  of total GDP.This sector drives economic growth, generates high-skilled employment, and produces intangible goods such as finance, tourism, and IT services.A strong service sector can increase a country's economic competitiveness, attract foreign investment, and improve living standards.""")
    
    fig2= px.bar(data, x='Year', y=sector,title=f"{sector} Over Years", labels={'value': f'{sector}'}, color_discrete_sequence=[' #36454F'] ) 
    st.plotly_chart(fig2)

    st.write("""Understanding the contribution of agriculture, industrial, and service sectors helps policymakers allocate resources effectively.It informs strategies for economic diversification, job creation, and poverty reduction.Analyzing sectoral contributions enables governments to identify areas of strength and weakness, and make data-driven decisions.This understanding promotes balanced economic growth, increased competitiveness, and improved living standards.""")
    
    st.write("--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------")

    # Additional insights based on  sector employment
    st.markdown("<h2 style='color:#1a3704;'>Employment Sectors</h2>", unsafe_allow_html=True)
    st.markdown("""
    <style>
        body {
            font-family: Arial, sans-serif;
        }
        .description {
            margin-bottom: 20px;
        }
        .description h2 {
            color:#1a3704;
        }
        .description p {
            color: #1a3704;
        }
    </style>
""", unsafe_allow_html=True)


    with st.container():
        st.markdown("""
            <div class="description">
                <h5>ICT Employment</h5>
                <p>ICT employment refers to jobs in the Information and Communication Technology sector, encompassing roles in software development, data analysis, cybersecurity, and more.</p>
            </div>
        """, unsafe_allow_html=True)

        st.markdown("""
            <div class="description">
                <h5>SME Employment</h5>
                <p>SME (Small and Medium-sized Enterprises) employment refers to jobs in smaller, privately-owned businesses that employ fewer than 500 people and have limited annual revenues.</p>
            </div>
        """, unsafe_allow_html=True)

        st.markdown("""
            <div class="description">
                <h5>Youth Unemployment</h5>
                <p>Youth unemployment refers to the share of young people (typically aged 15-24) who are actively seeking work but are unable to find employment.</p>
            </div>
        """, unsafe_allow_html=True)

        st.markdown("""
            <div class="description">
                <h5>Tourist Sector Employment</h5>
                <p>Tourist sector employment refers to jobs in industries that cater to tourists, such as hospitality, transportation, recreation, and food services, which support local economies.</p>
            </div>
        """, unsafe_allow_html=True)

    fig=px.bar(data,x="Year",y=["ICT Sector Employment (%)", "Tourism Sector Employment (%)","SME Employment (%)", "Youth Unemployment Rate (%)"], barmode="group",title="Employment of Sectors over Years",
    color_discrete_map={
        "ICT Sector Employment (%)": "#636EFA",  # Blue
        "Tourism Sector Employment (%)": "#EF553B",  # Red
        "SME Employment (%)": "#00CC96",  # Green
        "Youth Unemployment Rate (%)": "#AB63FA"  # Purple
    }
)

    st.plotly_chart(fig)    
    st.write("""Understanding sectoral productivity helps policymakers focus on areas of potential growth and improvement.For example, the ICT sector's rise has been driven by increasing internet penetration and tech innovations, while the decline in agriculture’s share of GDP signals the need for innovation in farming practices.""")
    
def data_about():
    st.markdown("<h2 style='color: #1a3704;'>🤖 Chatbot</h2>", unsafe_allow_html=True)
    st.markdown("#### Chat with Us")
    if "chat_history" not in st.session_state:
        st.session_state.chat_history = []

    # User Input
    user_input = st.text_input("Ask us anything about the data or dashboard:", key="user_input")
    if st.button("Send"):
        if user_input:
            # Append user's question to the chat history
            st.session_state.chat_history.append({"user": user_input})
            
            # Get chatbot response
            response = get_openai_response(user_input)
            st.session_state.chat_history.append({"bot": response})
        else:
            st.warning("Please enter a message.")

    # Display Chat History
    for chat in st.session_state.chat_history:
        if "user" in chat:
            st.markdown(f"You: {chat['user']}")
        if "bot" in chat:
            st.markdown(f"Bot: {chat['bot']}")

    st.markdown("<h2 style='color: #1a3704;'>💬 Feedback</h2>", unsafe_allow_html=True)
    with st.form(key="feedback_form"):
        st.text_area("Your Feedback", placeholder="Write your comments here...")
        rating = st.slider("Rate Us", 1, 5, 3)
        submitted = st.form_submit_button("Submit")
        if submitted:
            st.success("Thank you for your feedback!")
    st.markdown("<h2 style='color: #1a3704;'>❓ Need Help</h2>", unsafe_allow_html=True)
    st.info("For issues or support, contact the administrator at anushkapolley23@gmail.com")
    st.markdown("<h3 style='text-align: center; color: olive green;'>Thank you for visiting my web app! 🙏</h3>", unsafe_allow_html=True)
# Main Logic
def main():
    # st.set_page_config(page_title="Dashboard App", page_icon=":bar_chart:", layout="wide")

    # Custom CSS for Styling
    st.markdown(f"""
        <style>
        body {{ 
            background-color: #f6f6f2; 
            font-family: 'Arial', sans-serif; 
        }}
        h1, h2, h3, h4, h5, h6 {{
            color: #388087;
        }}
        .stButton>button {{
            background-color: #AFAFB7; 
            color: black; 
            border-radius: 8px; 
            padding: 10px;
        }}
        .stButton>button:hover {{
            background-color: #556B2F;
        }}
        .custom-heading {{
            font-size: 34px; /* Slightly larger font size */
            font-weight: bold;
            color: #388087;
            text-align: center;
            margin-bottom: 20px;
        }}
    .content-container {{
            padding: 20px;
            background-color: #6FB3BB; 
            border-radius: 10px;
        }}
        </style>
    """, unsafe_allow_html=True)
    if st.session_state.reset_password_step:
        reset_password()
    elif not st.session_state.get('logged_in', False):
        choice = st.sidebar.radio("Choose an option", ["Login", "Sign Up"])
        if choice == "Login":
            login()
        elif choice == "Sign Up":
            signup()
    else:
        st.markdown("<h1 style='color:#1a3704;'>A snapshot of GDP and Productivity of Indian Cities </h1>", unsafe_allow_html=True)
        st.sidebar.write(f"Welcome, {st.session_state.user}!")
        st.sidebar.button("Logout", on_click=logout)
        st.markdown("<div style='display: flex; justify-content: center; gap: 10px;'>", unsafe_allow_html=True)
        if "page" not in st.session_state:
            st.session_state.page = "Home"
        cols = st.columns(4)
        if cols[0].button("🏡 Home"):
            st.session_state.page = "Home"
        if cols[1].button("📊 Dashboard"):
            st.session_state.page = "Dashboard"
        if cols[2].button("💡Other Insights"):
            st.session_state.page = "Insights"
        if cols[3].button("🧑‍💻 Support Hub "):
            st.session_state.page = "About"
        st.markdown("</div>", unsafe_allow_html=True)
        if st.session_state.page == "Home":
            app_description()
        elif st.session_state.page == "Dashboard":
            dashboard()
        elif st.session_state.page == "Insights":
            data_download()
        elif st.session_state.page == "About":
            data_about()


if __name__ == "__main__":
    main()