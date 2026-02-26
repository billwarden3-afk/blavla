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
    try:
        # 100 seconds total wait time for OTP
        for _ in range(10): 
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
        page.goto("https://login.live.com/", wait_until="networkidle")
        
        # 1. Email Phase (Increased Timeout to 30s)
        page.wait_for_selector("input[type='email']", timeout=30000)
        page.fill("input[type='email']", email)
        page.keyboard.press("Enter")
        
        # Wait for page to react after Enter
        time.sleep(5) 
        page.wait_for_load_state("networkidle")
        
        # 2. Password Phase (Increased Timeout to 30s)
        try:
            page.wait_for_selector("input[type='password']", timeout=30000)
            page.fill("input[type='password']", password)
            page.keyboard.press("Enter")
        except Exception:
            # Screenshot if password field doesn't show up
            page.screenshot(path="login_fail.png")
            st.image("login_fail.png", caption="Stuck at this screen")
            return "Error: Password field not found (Timeout)"
            
        time.sleep(6)
        page.wait_for_load_state("networkidle")
        
        # 3. 2FA Bypass
        if "identity/confirm" in page.url or page.locator("text=Verify your identity").is_visible():
            st.info(f"🛡️ 2FA detected for {email}...")
            email_opt = page.locator("div[role='option']", has_text="Email")
            if email_opt.is_visible():
                email_opt.click()
                if page.locator("input[name='ProofConfirmation']").is_visible():
                    page.fill("input[name='ProofConfirmation']", MASTER_EMAIL)
                    page.keyboard.press("Enter")
                
                code = fetch_otp_from_master()
                if code:
                    page.fill("input[name='otc']", code)
                    page.keyboard.press("Enter")
                    time.sleep(6)
                else:
                    return "Error: OTP Timeout"

        # 4. Final Extraction
        search_url = "https://outlook.live.com/mail/0/inbox/search/subject:Claim%20your%20LinkedIn%20Premium"
        page.goto(search_url, wait_until="networkidle")
        time.sleep(10)
        
        try:
            page.click("div[aria-label='Message list'] div[role='option']:first-child", timeout=20000)
            time.sleep(5)
            body = page.inner_text("div[aria-label='Reading Pane']")
            match = re.search(r'(https://www\.linkedin\.com/premium/redeem\S+)', body)
            return match.group(1).rstrip('"> \n') if match else "Link Not Found"
        except:
            return "Email/Link Not Found"
            
    except Exception as e:
        return f"Process Failed: {str(e)}"

# --- UI INTERFACE ---
st.set_page_config(page_title="Bulk Extractor Pro", layout="wide")
st.title("🚀 LinkedIn 2FA Bulk Automation")

if st.text_input("Security PIN", type="password") != PIN_CODE:
    st.stop()

t1, t2 = st.tabs(["👤 Single Account", "📂 Bulk CSV/Excel"])

with t1:
    usr = st.text_input("Outlook Email")
    pwd = st.text_input("Password", type="password")
    if st.button("Extract Now"):
        with st.spinner("Bypassing security..."):
            with sync_playwright() as pw:
                browser = pw.chromium.launch(headless=True)
                res = extraction_engine(usr, pwd, browser.new_page())
                st.code(res)
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
        st.download_button("📥 Download Result", df.to_csv(index=False), "results.csv")    pwd = st.text_input("Password", type="password")
    if st.button("Extract Now"):
        with st.spinner("Bypassing security..."):
            with sync_playwright() as pw:
                browser = pw.chromium.launch(headless=True)
                res = extraction_engine(usr, pwd, browser.new_page())
                st.code(res)
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
        st.download_button("📥 Download Final Report", df.to_csv(index=False), "extracted_data.csv")
