import streamlit as st
from pymongo import MongoClient
from transformers import AutoTokenizer, AutoModelForSeq2SeqLM
from datetime import datetime

# Load tokenizer and model
@st.cache_resource
def load_model():
    tokenizer = AutoTokenizer.from_pretrained("facebook/nllb-200-distilled-600M")
    model = AutoModelForSeq2SeqLM.from_pretrained("facebook/nllb-200-distilled-600M")
    return tokenizer, model

tokenizer, model = load_model()

# MongoDB setup
client = MongoClient("mongodb+srv://manisalian:PqXNq8KvMLpXplxP@crud.jeyup.mongodb.net/NEWS?retryWrites=true&w=majority&appName=NEWS")
db = client["NEWS"]

# Language mappings
language_codes = [
    "asm_Beng", "awa_Deva", "ben_Beng", "bho_Deva", "hne_Deva",
    "guj_Gujr", "hin_Deva", "kan_Knda", "mag_Deva", "mai_Deva",
    "mal_Mlym", "mar_Deva", "mni_Beng", "lus_Latn", "tam_Taml",
    "tel_Telu", "urd_Arab"
]
language_names = [
    "Assamese", "Awadhi", "Bengali", "Bhojpuri", "Chhattisgarhi",
    "Gujarati", "Hindi", "Kannada", "Magahi", "Maithili",
    "Malayalam", "Marathi", "Meithei", "Mizo", "Tamil",
    "Telugu", "Urdu"
]
language_map = dict(zip(language_codes, language_names))

# Translation function
def translate_text(text, lang_code):
    inputs = tokenizer(text, return_tensors="pt")
    translated_tokens = model.generate(
        **inputs, forced_bos_token_id=tokenizer.convert_tokens_to_ids(lang_code)
    )
    return tokenizer.batch_decode(translated_tokens, skip_special_tokens=True)[0]

# Streamlit UI
st.set_page_config(page_title="Multilingual News Dashboard", layout="wide")

menu = st.sidebar.selectbox("Choose Action", ["Add News", "View News"])

if menu == "Add News":
    st.title("Add News in English and Translate to Indian Languages")

    img_url = st.text_input("Image URL")
    title = st.text_input("Title")
    author = st.text_input("Author")
    short_desc = st.text_area("Short Description")
    desc = st.text_area("Full Description")

    if st.button("Submit and Translate"):
        post_id = db["English"].count_documents({}) + 1
        created_on = datetime.now()

        english_data = {
            "post_id": post_id,
            "img_url": img_url,
            "title": title,
            "author": author,
            "short_desc": short_desc,
            "desc": desc,
            "created_on": created_on
        }

        db["English"].insert_one(english_data)
        st.success("Inserted into English collection")

        for code, name in zip(language_codes, language_names):
            translated_data = {
                "post_id": post_id,
                "img_url": img_url,
                "title": translate_text(title, code),
                "author": translate_text(author, code),
                "short_desc": translate_text(short_desc, code),
                "desc": translate_text(desc, code),
                "created_on": created_on
            }
            db[name].insert_one(translated_data)
            st.info(f"Inserted into {name} collection")

elif menu == "View News":
    st.title("View Translated News")
    selected_lang = st.selectbox("Select Language", ["English"] + language_names)
    news_items = db[selected_lang].find().sort("created_on", -1)

    for item in news_items:
        st.markdown(f"### {item['title']}")
        st.image(item["img_url"], width=400)
        st.markdown(f"**Author:** {item['author']}")
        st.markdown(f"**Short Description:** {item['short_desc']}")
        st.markdown(f"**Full Description:** {item['desc']}")
        st.markdown("---")
