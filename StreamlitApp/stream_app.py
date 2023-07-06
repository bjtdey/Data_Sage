import streamlit as st
from databricks_api import DatabricksAPI
import requests
import json
import tempfile
import os
import time

# getting environment variables
from dotenv import load_dotenv

load_dotenv()

st.set_page_config(layout="wide")
st.markdown("""
    <div style='text-align: center;'>
        <h2 style='font-size: 70px; font-family: Arial, sans-serif; 
                   letter-spacing: 2px; text-decoration: none;'>
            <a href='https://affine.ai/' target='_blank' rel='noopener noreferrer'
               style='background: linear-gradient(45deg, #00ff00, #ff8c00);
                      -webkit-background-clip: text;
                      -webkit-text-fill-color: transparent;
                      text-shadow: none; text-decoration: none;'>
                DocuMind
            </a>
        </h2>
    </div>
""", unsafe_allow_html=True)

col1, _, col2 = st.columns([1, 0.5, 2])

DATABRICKS_HOST = os.getenv("DATABRICKS_HOST")
DATABRICKS_TOKEN = os.getenv("DATABRICKS_TOKEN")
API_endpoint = os.getenv("API_endpoint")
# print(DATABRICKS_HOST)
# print(DATABRICKS_TOKEN)
# print(API_endpoint)


db = DatabricksAPI(host=DATABRICKS_HOST, token=DATABRICKS_TOKEN)


def res(query=str):
    response = requests.request(method='POST',
                                headers={
                                    'Authorization': f'Bearer {DATABRICKS_TOKEN}'},
                                url=API_endpoint,
                                data=query)
    return response.content


def main():
    col1.header("Upload your File ")
    col2.header("Ask your File 💬")

    # , type=["pdf,mp3,mpeg"])
    file = col1.file_uploader("Supports PDF, MP3, WAV, MP4")

    if file is not None:
        if col1.button(f"Upload"):
            file_details = {"FileName": file.name, "FileType": file.type}
            # st.write(file_details)

            with tempfile.NamedTemporaryFile(delete=False) as temp_file:
                temp_file.write(file.read())
                file_path = temp_file.name

            # st.write("File Path:", file_path)

            progress_text = col1.empty()
            progress_text.text("File is being uploaded...")
            db.dbfs.put(path=f"dbfs:/data/{file.name}",
                        src_path=file_path,
                        overwrite=True)
            progress_text.text("File is being indexed...")
            os.remove(file_path)
            progress_text.empty()
            prog_text = col1.empty()
            # progress_text.text("Indexing in progress...")
            # print(file.type)
            if file.type != "application/pdf":
                for _ in range(30):
                    time.sleep(0.5)
                    progress_text.text("Indexing in progress" + "." * (_ % 4))
            prog_text.text(f"{file.name} \n Indexed Successfully")

    user_question = col2.text_input(
        "Ask a question based on the content of your file:")
    # if col2.button(f"Submit_{hash('query')}"):
    if col2.button(f"Submit query"):
        if user_question:
            response = res(user_question)
            try:
                generated_text = json.loads(response)
                output_text = generated_text["output_text"]
                similar_docs = generated_text["similar_docs"]

                # Display output_text
                col2.subheader("Answer:")
                col2.write(output_text)

                # Display similar_docs
                col2.subheader("Context from the uploaded file:")
                for doc in similar_docs:
                    col2.write(f"Page: {doc['metadata']['page']}")
                    col2.write(doc['page_content'])
                    col2.write("---")

            except ValueError:
                col2.write("Error: Invalid response format.")
            except KeyError:
                col2.write("Error: Missing required fields in the response.")


if __name__ == '__main__':
    main()
