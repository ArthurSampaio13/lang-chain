import asyncio
import random

import streamlit as st
from dotenv import load_dotenv

from utils.chain import ask_question, create_chain
from utils.config import Config
from utils.ingestor import Ingestor
from utils.model import create_llm
from utils.retriever import create_retriever
from utils.uploader import upload_files

load_dotenv()

LOADING_MESSAGES = [
    "Calculando sua resposta através do multiverso...",
    "Ajustando o entrelaçamento quântico...",
    "Invocando a sabedoria das estrelas... quase lá!",
    "Consultando o gato de Schrödinger...",
    "Distorcendo o espaço-tempo para sua resposta...",
    "Equilibrando equações de estrelas de nêutrons...",
    "Analisando matéria escura... por favor, aguarde...",
    "Ativando o hiperespaço... a caminho!",
    "Coletando fótons de uma galáxia...",
    "Transmitindo dados de Andrômeda... aguarde!",
]


@st.cache_resource(show_spinner=False)
def build_qa_chain(files):
    file_paths = upload_files(files)
    vector_store = Ingestor().ingest(file_paths)
    llm = create_llm()
    retriever = create_retriever(llm, vector_store=vector_store)
    return create_chain(llm, retriever)


async def ask_chain(question: str, chain):
    full_response = ""
    assistant = st.chat_message(
        "assistant", avatar=str(Config.Path.IMAGES_DIR / "assistant-avatar.png")
    )
    with assistant:
        message_placeholder = st.empty()
        message_placeholder.status(random.choice(LOADING_MESSAGES), state="running")
        documents = []
        async for event in ask_question(chain, question, session_id="session-id-42"):
            if type(event) is str:
                full_response += event
                message_placeholder.markdown(full_response)
            if type(event) is list:
                documents.extend(event)
        for i, doc in enumerate(documents):
            with st.expander(f"Fonte #{i+1}"):
                st.write(doc.page_content)

    st.session_state.messages.append({"role": "assistant", "content": full_response})


def show_upload_documents():
    holder = st.empty()
    with holder.container():
        st.header("ChatPDF")
        st.subheader("Consiga respostas dos seus PDFs")
        uploaded_files = st.file_uploader(
            label="Upload PDF", type=["pdf"], accept_multiple_files=True
        )
    if not uploaded_files:
        st.warning("É necessário fazer o upload de um PDF para continuar!")
        st.stop()

    with st.spinner("Lendo o arquivo..."):
        holder.empty()
        return build_qa_chain(uploaded_files)


def show_message_history():
    for message in st.session_state.messages:
        role = message["role"]
        avatar_path = (
            Config.Path.IMAGES_DIR / "assistant-avatar.png"
            if role == "assistant"
            else Config.Path.IMAGES_DIR / "user-avatar.png"
        )
        with st.chat_message(role, avatar=str(avatar_path)):
            st.markdown(message["content"])


def show_chat_input(chain):
    if prompt := st.chat_input("Faça sua pergunta"):
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message(
            "user",
            avatar=str(Config.Path.IMAGES_DIR / "user-avatar.png"),
        ):
            st.markdown(prompt)
        asyncio.run(ask_chain(prompt, chain))


st.set_page_config(page_title="ChatPDF", page_icon="📖")

st.html(
    """
<style>
    .st-emotion-cache-p4micv {
        width: 2.75rem;
        height: 2.75rem;
    }
</style>
"""
)

if "messages" not in st.session_state:
    st.session_state.messages = [
        {
            "role": "assistant",
            "content": "Olá, tudo bem? O que você gostaria de saber dos seus arquivos?",
        }
    ]

if Config.CONVERSATION_MESSAGES_LIMIT > 0 and Config.CONVERSATION_MESSAGES_LIMIT <= len(
    st.session_state.messages
):
    st.warning(
        "Você atingiu o limite de mensagens. Recarregue a página, por favor."
    )
    st.stop()

chain = show_upload_documents()
show_message_history()
show_chat_input(chain)
