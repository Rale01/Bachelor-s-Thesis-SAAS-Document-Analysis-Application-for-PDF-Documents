import streamlit as st
from dotenv import load_dotenv
from PyPDF2 import PdfReader
from langchain.text_splitter import CharacterTextSplitter
from langchain.embeddings import HuggingFaceInstructEmbeddings
from langchain.vectorstores import FAISS

from langchain.memory import ConversationBufferMemory
from langchain.chains import ConversationalRetrievalChain
from htmlTemplates import  bot_template, man_template, woman_template, anonymous_template
from langchain.llms import HuggingFaceHub

import firebase_admin
from firebase_admin import credentials, firestore
from firebase_admin import auth
import time

import json
import requests
import streamlit.runtime.legacy_caching

def load_lottiefile(filepath: str):
    with open(filepath, "r") as f:
        return json.load(f)


lottie_loading_animation = load_lottiefile("animations/animation1.json")



def initialize_firebase():
    if not firebase_admin._apps:
        cred = credentials.Certificate('pdfinquistor-firebase-credentials.json')
        firebase_admin.initialize_app(cred)

initialize_firebase()

db = firestore.client()

def login(email):
    try:
        user = auth.get_user_by_email(email)
        success_message = st.empty()
        success_message = st.success('Login successful!', icon="✅")
        

        # Set a session state variable to indicate the user is logged in
        st.session_state.is_logged_in = True
        st.session_state.user_email = email

        user_ref = db.collection("payment_plans").document(user.uid)
        user_data = user_ref.get().to_dict()
        if user_data:
            user_gender = user_data.get("gender")
            st.session_state.user_gender = user_gender 

        with st.spinner("Logging In..."):
            st.markdown(
                f"""
                <style>
                    .stSpinner div {{
                        display: flex;
                        justify-content: center;
                        align-items: center;
                        height: 100%;
                        width: 100%;
                    }}
                </style>
                """,
                unsafe_allow_html=True
            )
            # Display the Lottie animation
            st.lottie(lottie_loading_animation, width=500, height=500)
        time.sleep(3)  # Adjust the sleep duration as needed
        success_message.empty()
        

    except Exception as e:
        st.warning(f"Login failed: {e}")


header_html = '<span style="font-size: 40px; font-weight: bold; color:white;">Login into PDFInqusitor</span> <img src="https://i.ibb.co/4mKV5jQ/PDFInquisitor-logo.png" alt="Custom Icon" style="vertical-align:middle" width="135" height="100">'


def loginAndSignUp():
    st.set_page_config(page_title="PDFInqusitor",
                                page_icon="images/PDF Analyzer logo.png")
    st.markdown(header_html, unsafe_allow_html=True)
    

    choice = st.selectbox('Login/Signup', ['Login', "Sign Up"])
    if choice == 'Login':
        st.markdown(page_bg_img, unsafe_allow_html=True)
        email = st.text_input('Email Address')
        password = st.text_input('Password', type = 'password')

        st.button('Login', on_click=lambda:login(email))

    else:
        st.markdown(page_bg_img, unsafe_allow_html=True)
        email = st.text_input('Email Address')
        password = st.text_input('Password', type = 'password')
        payment_plan = st.selectbox('Payment plan: ', ['20$ one month🔥', '50$ six months💣', '100$ a year💯'])
        gender = st.radio("Select your gender", ["Male ♂️ ", "Female ♀️ ", "Other ⚧️ "])

        if st.button('Create my account'):
            user = auth.create_user(email = email , password = password)
            
            payment_plan_data = {
            "email": email,
            "payment_plan": payment_plan,
            "gender": gender
            }
            db.collection("payment_plans").document(user.uid).set(payment_plan_data)
        

            st.success("Account created successfully!")
            st.markdown("Please Login using your email and password")
            st.balloons()


def get_pdf_text(pdf_docs):
    text = ""
    for pdf in pdf_docs:
        pdf_reader = PdfReader(pdf)
        for page in pdf_reader.pages:
            text += page.extract_text()
    return text


def get_text_chunks(text):
    text_splitter = CharacterTextSplitter(
        separator="\n",
        chunk_size=1000,
        chunk_overlap=200,
        length_function=len
    )
    chunks = text_splitter.split_text(text)
    return chunks


def get_vectorstore(text_chunks):
    #embeddings = OpenAIEmbeddings()
    embeddings = HuggingFaceInstructEmbeddings(model_name="intfloat/e5-large-v2")
    vectorstore = FAISS.from_texts(texts=text_chunks, embedding=embeddings)
    return vectorstore


def get_conversation_chain(vectorstore):
    #llm = ChatOpenAI()
    llm = HuggingFaceHub(repo_id="google/flan-t5-xxl", model_kwargs={"temperature":0.5, "max_length":1000})

    memory = ConversationBufferMemory(
        memory_key='chat_history', return_messages=True)
    conversation_chain = ConversationalRetrievalChain.from_llm(
        llm=llm,
        retriever=vectorstore.as_retriever(),
        memory=memory
    )
    return conversation_chain


def handle_userinput(user_question):
    response = st.session_state.conversation({'question': user_question})
    st.session_state.chat_history = response['chat_history']
    for i, message in enumerate(st.session_state.chat_history):
        if i % 2 == 0:
            if st.session_state.user_gender == "Male ♂️ ":
                st.write(man_template.replace(
                    "{{MSG}}", message.content), unsafe_allow_html=True)
            elif st.session_state.user_gender == "Female ♀️ ":
                 st.write(woman_template.replace(
                    "{{MSG}}", message.content), unsafe_allow_html=True)
            else:
                 st.write(anonymous_template.replace(
                    "{{MSG}}", message.content), unsafe_allow_html=True)
        else:
            st.write(bot_template.replace(
                "{{MSG}}", message.content), unsafe_allow_html=True)



header_html = '<span style="font-size: 40px; font-weight: bold; color:white;">Welcome to PDFInqusitor</span> <img src="https://i.ibb.co/4mKV5jQ/PDFInquisitor-logo.png" alt="Custom Icon" style="vertical-align:middle" width="135" height="100">'
question_html = '<p style="font-size: 14px; font-weight: bold; color:white; margin-bottom: -450px;">Ask a question related the content of the PDFs you have provided: </p>'
instruction_html = '<p style="font-size: 15px; font-weight: bold; color:white; margin-bottom: -450px;"> Upload your PDFs here and click on &apos;Process&apos; </p>'

html_sider = '<span style="font-size: 23px; font-weight: bold; color: white">Your PDF documents</span> <img src="https://i.ibb.co/LpqGMR5/features-3-Photo-Room-png-Photo-Room.png" alt="Custom Icon" style="vertical-align:middle" width="90" height="60">'

page_bg_img = """
<style>
[data-testid = "stAppViewContainer"]{
background-image:url("https://wallpapers.com/images/hd/3d-red-and-black-polygon-w0xm5hsgnjeajcnr.webp");
background-size:cover;
}

[data-testid = "stHeader"]{
background-color: rgba(0, 0, 0, 0);
}

[data-testid = "stToolbar"]{
right: 2rem;
}

[data-testid = "stSidebar"]{
background-image:url("https://e0.pxfuel.com/wallpapers/590/133/desktop-wallpaper-futuristic-black-720x1440-thumbnail.jpg");
background-size:cover;
}

[data-testid = "baseButton-header"]{
color:white;
}

[data-testid = "baseButton-headerNoPadding"]{
color:white;
}

[data-testid = "stMarkdownContainer"]{
color:#DFDFDE;
}

[data-testid="baseButton-secondary"]:hover {
    color: white;
}

.css-145e98g{
color: #931818;
}

[data-testid="stRadio"]{
    background-color: rgb(16, 12, 8);
    border-radius: 20px;
    padding: 10px;
}

#MainMenu {visibility: hidden;}
footer {visibility: hidden;}

iframe {
  margin: 0;
  padding: 0;
  visibility: hidden;
  display:none;
}

.st-b3 st-b8 st-d8 st-b1 st-bq st-ae st-af st-ag st-ah st-ai st-aj st-br st-bw{
 display:none;
}
</style>
"""

a_underline = """
<style>
    .css-oyvdv1 a{
        color: white;
    }
    a {
    color: white;
    text-decoration: none;

    }
</style>
"""



def main():
        email = None
        if "is_logged_in" not in st.session_state:
                st.session_state.is_logged_in = False
        if "user_email" not in st.session_state:
                st.session_state.user_email = None
        

            # If the user is not logged in, show the login/signup page
        if not st.session_state.is_logged_in:
                email = loginAndSignUp()
        else:
                load_dotenv()
                st.set_page_config(page_title="PDFInqusitor",
                                page_icon="images/PDF Analyzer logo.png")
                st.markdown(page_bg_img, unsafe_allow_html=True)
                
                if "conversation" not in st.session_state:
                    st.session_state.conversation = None
                if "chat_history" not in st.session_state:
                    st.session_state.chat_history = None

              

                st.markdown(header_html, unsafe_allow_html=True)
                st.markdown(question_html, unsafe_allow_html=True)
                user_question = st.text_input("")
                if user_question:
                    handle_userinput(user_question)

                with st.sidebar:

                    user_email = st.session_state.user_email
                    html_man = f'<span style="background-color: rgb(16, 12, 8); border-radius: 20px; border: 1px solid white; padding: 30px;"> <span style="font-size: 18px; font-weight: bold; color: white">Hello <span style="text-decoration: none; color: white !important;">{user_email}</span>! </span> <img src="https://i.ibb.co/PhRgRGg/man.jpg" alt="Custom Icon" style="vertical-align:middle; max-height: 60px; max-width: 60px; border-radius: 50%; object-fit: cover; margin-left: 10px; border: 1px solid white;"> </span>'
                    html_woman = f'<span style="background-color: rgb(16, 12, 8); border-radius: 20px; border: 1px solid white; padding: 30px;"><span style="font-size: 18px; font-weight: bold; color: white">Hello <span style="text-decoration: none; color: white !important;">{user_email}</span>! </span> <img src="https://i.ibb.co/K0GxZ1K/woman.jpg" alt="Custom Icon" style="vertical-align:middle; max-height: 60px; max-width: 60px; border-radius: 50%; object-fit: cover; margin-left: 10px; border: 1px solid white;"> </span>'
                    html_anonymous = f'<span style="background-color: rgb(16, 12, 8); border-radius: 20px; border: 1px solid white; padding: 30px;"><span style="font-size: 18px; font-weight: bold; color: white">Hello <span style="text-decoration: none; color: white !important;">{user_email}</span>! </span> <img src="https://i.ibb.co/TP65G0P/anonymous.jpg" alt="Custom Icon" style="vertical-align:middle; max-height: 60px; max-width: 80px; border-radius: 50%; object-fit: cover; margin-left: 10px; border: 1px solid white;"> </span>'

                    if st.session_state.user_gender == "Male ♂️ ":
                       st.markdown(html_man, unsafe_allow_html=True)
                       st.markdown(a_underline, unsafe_allow_html=True)
                       
                    elif st.session_state.user_gender == "Female ♀️ ":
                       st.markdown(html_woman, unsafe_allow_html=True)
                       st.markdown(a_underline, unsafe_allow_html=True)
                       
                    else:
                       st.markdown(html_anonymous, unsafe_allow_html=True)
                       st.markdown(a_underline, unsafe_allow_html=True)
                       

                    if st.session_state.is_logged_in:
                        if st.button("Logout"):
                            # Clear the session state to log the user out
                            st.session_state.is_logged_in = False
                            st.session_state.user_email = None
                            st.session_state.user_gender = None

                            # Refresh the page
                            streamlit.runtime.legacy_caching.clear_cache()
                            st.experimental_rerun()

                    st.markdown(html_sider, unsafe_allow_html=True)
                    st.markdown(instruction_html, unsafe_allow_html=True)
                    pdf_docs = st.file_uploader(
                        "", accept_multiple_files=True)
                    
            
                    
                    if st.button("Process⚙️"):
                        with st.spinner("Processing..."):
                            # get pdf text
                            raw_text = get_pdf_text(pdf_docs)

                            # get the text chunks
                            text_chunks = get_text_chunks(raw_text)

                            # create vector store
                            vectorstore = get_vectorstore(text_chunks)

                            # create conversation chain
                            st.session_state.conversation = get_conversation_chain(
                                vectorstore)


if __name__ == '__main__':
    main()
