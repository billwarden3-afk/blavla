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
MASTER_PASS = "jcylavuqyzkqjzog" #
# Trying the alternate server address
IMAP_SERVER = "imap-mail.outlook.com" 
PIN_CODE = "9999" 
# ########################################################

def fetch_otp_from_master():
    st.info("🔍 Diagnostic: Attempting IMAP Login...")
    try:
        # Quick test connection
        with MailBox(IMAP_SERVER).login(MASTER_EMAIL, MASTER_PASS) as mailbox:
            st.success("✅ IMAP Connection Successful!")
            for _ in range(10):
                time.sleep(10)
                for msg in mailbox.fetch(AND(from_='account-security-noreply@accountprotection.microsoft.com'), limit=1, reverse=True):
                    otp = re.search(r'\b\d{6,7}\b', msg.subject + msg.text)
                    if otp:
                        return otp.group(0)
                st.write("Checking for new mails...")
    except Exception as e:
        st.error(f"❌ Login Failed: {str(e)}")
        if "AUTHENTICATIONFAILED" in str(e).upper():
            st.warning("Tip: Check if 'Security Defaults' are blocking App Passwords in your Microsoft Account.")
    return None

def extraction_engine(email, password, page):
    try:
        page.goto("https://login.live.com/", wait_until="domcontentloaded", timeout=60000)
        
        # Phase 1: Email
        page.wait_for_selector("input[type='email']", timeout=30000)
        page.fill("input[type='email']", email)
        page.keyboard.press("Enter")
        time.sleep(7) 

        # Account Selector Bypass
        if page.locator(f"text={email}").is_visible():
            page.click(f"text={email}", force=True)
            time.sleep(5)

        # Phase 2: Password or Verification
        verify_field = page.locator("input[name='ProofConfirmation']")
        pass_field = page.locator("input[type='password']")
        
        if pass_field.is_visible(timeout=10000):
            pass_field.fill(password)
            page.keyboard.press("Enter")
            time.sleep(8)
        
        # 2FA Handling
        if "identity/confirm" in page.url or page.locator("text=Verify your email").is_visible() or verify_field.is_visible():
            st.info("🛡️ Security Verification Screen Detected.")
            
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
            
            otp = fetch_otp_from_master()
            if otp:
                page.fill("input[name='otc']", otp)
                page.keyboard.press("Enter")
                time.sleep(10)
            else:
                return "Error: Could not retrieve OTP from Master Mail."

        # Phase 3: Extraction
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
        except:
            return "Inbox Item Not Accessible"
            
    except Exception as e:
        return f"Automation Error: {str(e)}"

# --- UI ---
st.title("🚀 Pro Extractor (Diagnostic Mode)")
if st.text_input("PIN", type="password") != PIN_CODE: st.stop()

usr = st.text_input("Outlook Email")
pwd = st.text_input("Password", type="password")
if st.button("Start Extraction"):
    with sync_playwright() as pw:
        browser = pw.chromium.launch(headless=True)
        result = extraction_engine(usr, pwd, browser.new_page())
        st.success(f"Final Result: {result}")
        browser.close()
