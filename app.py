import streamlit as st
from playwright.sync_api import sync_playwright
import re
import time
import os

# This silently installs the browser on the server once, avoiding Docker entirely
@st.cache_resource
def install_browser():
    os.system("playwright install chromium")
    os.system("playwright install-deps chromium")

install_browser()

st.title("🔗 LinkedIn Promo Extractor")
st.write("Enter the Outlook credentials below to extract the Premium link.")

# The input fields on your private website
email = st.text_input("Outlook Email")
password = st.text_input("Password", type="password")

if st.button("Extract Link"):
    if not email or not password:
        st.warning("Please enter both email and password.")
    else:
        with st.spinner("⏳ Firing up cloud browser and logging in..."):
            with sync_playwright() as p:
                browser = p.chromium.launch(headless=True)
                page = browser.new_page()
                try:
                    page.goto("https://login.live.com/")
                    page.fill("input[type='email']", email)
                    page.click("input[type='submit']")
                    time.sleep(2) 
                    
                    page.fill("input[type='password']", password)
                    page.click("input[type='submit']")
                    time.sleep(3) 
                    
                    if page.locator("text=Yes").is_visible():
                        page.click("text=Yes")
                        time.sleep(3)

                    search_url = f"https://outlook.live.com/mail/0/inbox/search/subject:Claim%20your%20LinkedIn%20Premium"
                    page.goto(search_url)
                    time.sleep(5) 
                    
                    page.click("div[aria-label='Message list'] div[role='option']:first-child") 
                    time.sleep(3)

                    body_text = page.inner_text("div[aria-label='Reading Pane']")
                    
                    match = re.search(r'(https://www\.linkedin\.com/premium/redeem\S+)', body_text)
                    if match:
                        clean_link = match.group(1).rstrip('"> \n')
                        st.success("✅ Link Extracted Successfully!")
                        st.code(clean_link)
                    else:
                        st.error("⚠️ Logged in, but couldn't find the link in the top email.")
                        
                except Exception as e:
                    st.error(f"❌ Automation Error: {str(e)}")
                finally:
                    browser.close()
                  
