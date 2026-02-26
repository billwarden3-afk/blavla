import streamlit as st
from playwright.sync_api import sync_playwright
import re
import time
import os

# --- SILENT BROWSER INSTALLATION ---
@st.cache_resource
def install_browser():
    os.system("playwright install chromium")

install_browser()

st.title("🔗 LinkedIn Promo Extractor")

# --- THE SECURITY WALL ---
secret_pin = st.text_input("Enter Access PIN", type="password")
if secret_pin != "9999":  
    st.warning("Enter the correct PIN to unlock the extractor.")
    st.stop() 
# -------------------------

st.write("Enter the Outlook credentials below to extract the Premium link.")

email = st.text_input("Outlook Email")
password = st.text_input("Password", type="password")

if st.button("Extract Link"):
    if not email or not password:
        st.warning("Please enter both email and password.")
    else:
        with st.spinner("⏳ Firing up cloud browser and logging in..."):
            try:
                with sync_playwright() as p:
                    browser = p.chromium.launch(headless=True)
                    page = browser.new_page()
                    
                    page.goto("https://login.live.com/")
                    time.sleep(3) # Let the page fully load its security scripts
                    
                    # 1. Enter Email using Microsoft's internal 'name' attribute
                    page.wait_for_selector("input[name='loginfmt']", timeout=15000)
                    page.fill("input[name='loginfmt']", email)
                    page.click("#idSIButton9") 
                    time.sleep(3) 
                    
                    # 2. Enter Password
                    page.wait_for_selector("input[name='passwd']", timeout=15000)
                    page.fill("input[name='passwd']", password)
                    page.click("#idSIButton9") 
                    time.sleep(4) 
                    
                    # 3. Bypass "Stay signed in?" screen
                    if page.locator("#idSIButton9").is_visible():
                        page.click("#idSIButton9")
                        time.sleep(3)

                    # 4. Search for the LinkedIn email
                    search_url = "https://outlook.live.com/mail/0/inbox/search/subject:Claim%20your%20LinkedIn%20Premium"
                    page.goto(search_url)
                    time.sleep(6) 
                    
                    page.click("div[aria-label='Message list'] div[role='option']:first-child") 
                    time.sleep(4)

                    body_text = page.inner_text("div[aria-label='Reading Pane']")
                    
                    match = re.search(r'(https://www\.linkedin\.com/premium/redeem\S+)', body_text)
                    if match:
                        clean_link = match.group(1).rstrip('"> \n')
                        st.success("✅ Link Extracted Successfully!")
                        st.code(clean_link)
                    else:
                        st.error("⚠️ Logged in, but couldn't find the link in the top email.")
                        
                    browser.close()
            except Exception as e:
                st.error(f"❌ Automation Error: {str(e)}")
                # --- THE X-RAY SCREENSHOT ---
                page.screenshot(path="crash_screenshot.png")
                st.image("crash_screenshot.png", caption="What the bot saw right before it crashed.")
                browser.close()
