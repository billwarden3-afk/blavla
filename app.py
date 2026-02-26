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
MASTER_PASS = "jcylavuqyzkqjzog" 
IMAP_SERVER = "outlook.office365.com" 
PIN_CODE = "9999" 
# ########################################################

def fetch_otp_from_master():
    """Master email se latest Microsoft security code nikalna"""
    try:
        # 120 seconds wait time for the code
        for _ in range(12): 
            time.sleep(10)
            try:
                with MailBox(IMAP_SERVER).login(MASTER_EMAIL, MASTER_PASS) as mailbox:
                    for msg in mailbox.fetch(AND(from_='account-security-noreply@accountprotection.microsoft.com'), limit=1, reverse=True):
                        otp = re.search(r'\b\d{6,7}\b', msg.subject + msg.text)
                        if otp:
                            return otp.group(0)
            except Exception as login_err:
                # Agar login fail ho, toh yahan error dikhayega
                st.warning(f"Retrying IMAP... (Check if IMAP is enabled in Outlook settings): {login_err}")
    except Exception as e:
        st.error(f"Critical IMAP Error: {e}")
    return None

def extraction_engine(email, password, page):
    try:
        page.goto("https://login.live.com/", wait_until="domcontentloaded", timeout=60000)
        
        # Step 1: Login Phase
        page.wait_for_selector("input[type='email']", timeout=30000)
        page.fill("input[type='email']", email)
        page.keyboard.press("Enter")
        time.sleep(7) 

        # Handle Account Selector
        account_selector = page.locator(f"text={email}")
        if account_selector.is_visible():
            account_selector.click(force=True)
            time.sleep(5)

        # Step 2: Password/Verify
        password_field = page.locator("input[type='password']")
        verify_field = page.locator("input[name='ProofConfirmation']")
        
        if password_field.is_visible(timeout=10000):
            password_field.fill(password)
            page.keyboard.press("Enter")
            time.sleep(8)
        
        # 2FA / Identity Check
        if "identity/confirm" in page.url or page.locator("text=Verify your email").is_visible() or verify_field.is_visible():
            st.info(f"🛡️ 2FA detected for {email}...")
            
            if verify_field.is_visible():
                verify_field.fill(MASTER_EMAIL)
                page.click("#idSIButton9", force=True)
                time.sleep(5)
            
            email_opt = page.locator("div[role='option']", has_text="Email")
            if email_opt.is_visible():
                email_opt.click(force=True)
                time.sleep(3)
                if page.locator("input[name='ProofConfirmation']").is_visible():
                    page.fill("input[name='ProofConfirmation']", MASTER_EMAIL)
                    page.keyboard.press("Enter")
            
            st.info("⏳ Waiting for OTP from Master Mail...")
            code = fetch_otp_from_master()
            if code:
                st.success(f"✅ OTP Received: {code}")
                page.wait_for_selector("input[name='otc']", timeout=20000)
                page.fill("input[name='otc']", code)
                page.keyboard.press("Enter")
                time.sleep(8)
            else:
                return "Error: OTP Timeout (Check Master Email Settings)"

        # Step 3: Extraction
        search_url = "https://outlook.live.com/mail/0/inbox/search/subject:Claim%20your%20LinkedIn%20Premium"
        page.goto(search_url, wait_until="networkidle", timeout=60000)
        time.sleep(12)
        
        try:
            page.wait_for_selector("div[aria-label='Message list']", timeout=25000)
            page.click("div[aria-label='Message list'] div[role='option']:first-child", force=True)
            time.sleep(6)
            
            body = page.inner_text("div[aria-label='Reading Pane']")
            match = re.search(r'(https://www\.linkedin\.com/premium/redeem\S+)', body)
            return match.group(1).rstrip('"> \n') if match else "Link Not Found"
        except Exception:
            return "Email/Link Not Found"
            
    except Exception as e:
        return f"Process Failed: {str(e)}"

# --- UI INTERFACE ---
st.set_page_config(page_title="Bulk Extractor Pro", layout="wide")
st.title("🚀 LinkedIn 2FA Bulk Automation")

security_pin = st.text_input("Security PIN", type="password")
if security_pin != PIN_CODE:
    st.stop()

t1, t2 = st.tabs(["👤 Single Account", "📂 Bulk Mode"])

with t1:
    usr = st.text_input("Outlook Email")
    pwd = st.text_input("Password", type="password")
    if st.button("Extract Now"):
        with st.spinner("Processing..."):
            with sync_playwright() as pw:
                browser = pw.chromium.launch(headless=True)
                res = extraction_engine(usr, pwd, browser.new_page())
                st.success(f"Result: {res}")
                browser.close()

with t2:
    file = st.file_uploader("Upload CSV/Excel", type=['csv', 'xlsx'])
    if file and st.button("Start Bulk"):
        df = pd.read_csv(file) if file.name.endswith('.csv') else pd.read_excel(file)
        results = []
        with sync_playwright() as pw:
            browser = pw.chromium.launch(headless=True)
            for _, row in df.iterrows():
                st.write(f"⚙️ Processing: {row['email']}")
                results.append(extraction_engine(row['email'], row['password'], browser.new_page()))
            browser.close()
        df['LinkedIn_Link'] = results
        st.dataframe(df)
        st.download_button("Download CSV", df.to_csv(index=False), "final.csv")
