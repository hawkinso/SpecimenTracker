
# 🧪 SpecimenTracker

A Streamlit app for tracking specimen inventory through staining and imaging workflows. Track specimens through stages like Formalin, Ethanol step up, Sudan black, Destain, Glycerol, Imaging, and storage.

# Specimen tracker

A simple Streamlit app that allows for inventory and management of specimens for clearing and staining!

- Open the app locally at: [http://localhost:8501](http://localhost:8501)
- In GitHub Codespaces, open forwarded port `8501` or use the browser preview for the forwarded port.

### How to run it on your own machine

1. Install the requirements

   ```
   pip install -r requirements.txt
   ```

2. Run the app

   ```
   streamlit run streamlit_app.py
   ```

### Deploy a shareable public app (no Python required for viewers)

1. Push this repository to GitHub (if not already hosted).
2. Use Streamlit Community Cloud: https://share.streamlit.io to deploy the app from your GitHub repo. Choose the repository and branch, and set the main file to `streamlit_app.py`.
3. After deployment, Streamlit will provide a public URL you can share with collaborators — they can open the app in their browser without installing Python.

Notes:
- The app stores data in `data/specimens.json` inside the repository workspace when run; when deployed on Streamlit Cloud, data will be written to the deployment instance storage and persists for the session/instance. For long-term shared persistence, connect an external database or storage service and update `streamlit_app.py` accordingly.
