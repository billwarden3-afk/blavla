import streamlit as st
from playwright.sync_api import sync_playwright
import re
import time
import os
import pandas as pd
from imap_tools import MailBox, AND

# --- BROWSER SETUP ---
@st.cache_resource
def install_browser():
    os.system("playwright install chromium")

install_browser()

# ########################################################
# #### CONFIGURATION: PRE-FILLED FOR VAIBHAVSINGH #######
# ########################################################
MASTER_EMAIL = "mychali1hyskd@hotmail.com" 
MASTER_PASS = "jcylavuqyzkqjzog" # Using your 16-digit App Password
IMAP_SERVER = "outlook.office365.com" 
PIN_CODE = "9999" 
# ########################################################

def fetch_otp_from_master():
    """Master email se latest Microsoft security code nikalna"""
    try:
        # 120 seconds wait time for security codes
        for _ in range(12): 
            time.sleep(10)
            with MailBox(IMAP_SERVER).login(MASTER_EMAIL, MASTER_PASS) as mailbox:
                for msg in mailbox.fetch(AND(from_='account-security-noreply@accountprotection.microsoft.com'), limit=1, reverse=True):
                    otp = re.search(r'\b\d{6,7}\b', msg.subject + msg.text)
                    if otp:
                        return otp.group(0)
    except Exception as e:
        st.error(f"IMAP Error: {e}")
    return None

def extraction_engine(email, password, page):
    try:
        # Step 1: Initialize Login
        page.goto("https://login.live.com/", wait_until="domcontentloaded", timeout=60000)
        
        # Email Phase
        page.wait_for_selector("input[type='email']", timeout=30000)
        page.fill("input[type='email']", email)
        page.keyboard.press("Enter")
        
        time.sleep(7) 
        
        # --- FIX: ACCOUNT SELECTION BYPASS ---
        # If Microsoft shows "Pick an account", we force click it
        account_selector = page.locator(f"text={email}")
        if account_selector.is_visible():
            account_selector.click(force=True) # Force click bypasses intercepting elements
            time.sleep(5)

        # Step 2: Password Phase
        try:
            page.wait_for_selector("input[type='password']", timeout=30000)
            page.fill("input[type='password']", password)
            page.keyboard.press("Enter")
        except Exception:
            page.screenshot(path="login_error.png")
            st.image("login_error.png", caption=f"Login failed at {email}")
            return "Error: Password field blocked or hidden"
            
        time.sleep(8)
        
        # Step 3: 2FA / Identity Verification
        if "identity/confirm" in page.url or page.locator("text=Verify your identity").is_visible():
            st.info(f"🛡️ 2FA detected for {email}. Fetching code...")
            
            # Click the email verification option
            email_opt = page.locator("div[role='option']", has_text="Email")
            if email_opt.is_visible():
                email_opt.click(force=True)
                
                # Confirm Master Email if Microsoft asks
                confirm_box = page.locator("input[name='ProofConfirmation']")
                if confirm_box.is_visible():
                    confirm_box.fill(MASTER_EMAIL)
                    page.keyboard.press("Enter")
                
                code = fetch_otp_from_master()
                if code:
                    st.success(f"✅ Code: {code}")
                    page.fill("input[name='otc']", code)
                    page.keyboard.press("Enter")
                    time.sleep(8)
                else:
                    return "Error: OTP Timeout"

        # Step 4: Promo Link Extraction
        # Navigating directly to search for better speed
        search_url = "https://outlook.live.com/mail/0/inbox/search/subject:Claim%20your%20LinkedIn%20Premium"
        page.goto(search_url, wait_until="networkidle", timeout=60000)
        time.sleep(12)
        
        try:
            # Select first email from search results
            page.wait_for_selector("div[aria-label='Message list']", timeout=25000)
            page.click("div[aria-label='Message list'] div[role='option']:first-child", force=True)
            time.sleep(6)
            
            body = page.inner_text("div[aria-label='Reading Pane']")
            match = re.search(r'(https://www\.linkedin\.com/premium/redeem\S+)', body)
            return match.group(1).rstrip('"> \n') if match else "Link Not Found"
        except Exception:
            return "Email/Link Not Found in Inbox"
            
    except Exception as e:
        return f"Process Failed: {str(e)}"

# --- UI INTERFACE ---
st.set_page_config(page_title="Bulk Extractor Pro", layout="wide")
st.title("🚀 LinkedIn 2FA Bulk Automation")

security_pin = st.text_input("Security PIN", type="password")
if security_pin != PIN_CODE:
    st.stop()

t1, t2 = st.tabs(["👤 Single Account", "📂 Bulk CSV/Excel"])

with t1:
    usr = st.text_input("Outlook Email")
    pwd = st.text_input("Password", type="password")
    if st.button("Extract Now"):
        with st.spinner("Executing extraction..."):
            with sync_playwright() as pw:
                browser = pw.chromium.launch(headless=True)
                res = extraction_engine(usr, pwd, browser.new_page())
                st.success(f"Result: {res}")
                browser.close()

with t2:
    st.write("Upload file with 'email' and 'password' columns.")
    file = st.file_uploader("Select File", type=['csv', 'xlsx'])
    if file and st.button("Execute Bulk Run"):
        df = pd.read_csv(file) if file.name.endswith('.csv') else pd.read_excel(file)
        results = []
        with sync_playwright() as pw:
            browser = pw.chromium.launch(headless=True)
            for _, row in df.iterrows():
                st.write(f"⚙️ Cracking: {row['email']}")
                results.append(extraction_engine(row['email'], row['password'], browser.new_page()))
            browser.close()
        df['LinkedIn_Link'] = results
        st.success("All Done!")
        st.dataframe(df)
        csv_data = df.to_csv(index=False).encode('utf-8')
        st.download_button(
            label="📥 Download Result",
            data=csv_data,
            file_name="results.csv",
            mime="text/csv"
                                        )
