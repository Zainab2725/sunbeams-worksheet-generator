"""
colab_setup.py

Run this INSIDE a Google Colab notebook cell-by-cell (copy each function
call into its own cell, or run the whole thing as one cell to start).
Colab can't render Streamlit directly in the browser tab, so we launch
Streamlit as a background process and expose it through a tunnel
(pyngrok) so you get a clickable public URL.

TYPICAL COLAB CELL SEQUENCE:

# Cell 1 -- install dependencies
!pip install -q -r requirements.txt

# Cell 2 -- mount Drive (if your dataset-sunbeams folder lives in Drive)
from google.colab import drive
drive.mount('/content/drive')

# Cell 3 -- set your API key securely (Colab Secrets, not hardcoded)
# Get a free Groq key (no credit card needed) at https://console.groq.com/keys
from google.colab import userdata
import os
os.environ["GROQ_API_KEY"] = userdata.get("GROQ_API_KEY")
os.environ["DATASET_ROOT"] = "/content/drive/MyDrive/dataset-sunbeams"  # adjust path

# Cell 4 -- launch Streamlit + ngrok tunnel
from colab_setup import launch_app
launch_app()
"""

import os
import subprocess
import time


def launch_app(port: int = 8501, ngrok_authtoken: str = None):
    """
    Starts `streamlit run app.py` as a background process, then opens
    a pyngrok tunnel to it and prints the public URL.
    """
    from pyngrok import ngrok

    if ngrok_authtoken:
        ngrok.set_auth_token(ngrok_authtoken)

    # Kill any previous streamlit process on this port (re-running the cell)
    subprocess.run(["pkill", "-f", "streamlit run"], check=False)
    time.sleep(1)

    # Launch Streamlit in the background, headless (no local browser to open in Colab)
    subprocess.Popen(
        [
            "streamlit", "run", "app.py",
            "--server.port", str(port),
            "--server.headless", "true",
        ]
    )
    time.sleep(4)  # give Streamlit a moment to boot

    public_url = ngrok.connect(port)
    print(f"✅ Streamlit app is live at: {public_url}")
    print("   (Keep this Colab cell running -- closing it stops the app.)")
    return public_url


if __name__ == "__main__":
    launch_app()
