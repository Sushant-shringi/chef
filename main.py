import streamlit as st
import os
from google import genai
from typing import List
import re
from dotenv import load_dotenv

# Load environment variables from .env if present
load_dotenv()

# ==========================
# ⚡ Gemini API Key Configuration
# ==========================
api_key = os.getenv("GEMINI_API_KEY") or (st.secrets.get("GEMINI_API_KEY") if hasattr(st, "secrets") and "GEMINI_API_KEY" in st.secrets else None)

# ==========================
# Utility Functions
# ==========================

def clean_ingredients(raw: str) -> List[str]:
    """Parse comma-separated ingredients into a clean, unique list."""
    if not raw:
        raise ValueError("No ingredients provided.")
    items = [i.strip().lower() for i in raw.split(",")]
    items = [re.sub(r"[^a-z0-9\s]", "", i) for i in items]
    items = [i for i in items if i]
    if not items:
        raise ValueError("Ingredients list is malformed.")
    return sorted(list(set(items)))

def validate_diet(diet: str) -> str:
    """Validate dietary restriction selection."""
    allowed = {"none", "vegan", "keto", "vegetarian", "gluten-free"}
    diet_norm = diet.strip().lower()
    if diet_norm not in allowed:
        raise ValueError(f"Diet '{diet}' not supported.")
    return diet_norm

# ==========================
# Chef Persona & Few-Shot Examples
# ==========================

CHEF_PERSONA = """
You are Chef Remy, a master of resourceful cooking.
Your goal is to create delicious, frugal recipes while reducing food waste.
Do NOT add any ingredients not listed except salt, pepper, olive oil, or water.
Follow dietary restrictions exactly. Tone: enthusiastic and waste-conscious.
"""

FEW_SHOT_EXAMPLES = """
Example 1:
Ingredients: Tomato, Egg, Stale Bread
Diet: Keto
Recipe:
Title: Keto Egg & Tomato Toast
Prep Time: 15 mins
Ingredients Used: Tomato, Egg, Stale Bread, Salt, Pepper, Olive Oil
Instructions:
1. Toast the stale bread.
2. Sauté tomatoes in olive oil with salt & pepper.
3. Fry the egg and assemble.

Example 2:
Ingredients: Chickpeas, Spinach, Garlic
Diet: Vegan
Recipe:
Title: Garlicky Chickpea Spinach Sauté
Prep Time: 20 mins
Ingredients Used: Chickpeas, Spinach, Garlic, Salt, Olive Oil
Instructions:
1. Heat olive oil and sauté garlic.
2. Add chickpeas and wilt spinach.
3. Season with salt.
"""

# ==========================
# Recipe Generator
# ==========================

def generate_recipe(ingredients: List[str], diet: str, active_api_key: str) -> str:
    if not active_api_key:
        raise ValueError("Google Gemini API Key is missing. Please provide it in the sidebar or in your .env file.")
    
    client = genai.Client(api_key=active_api_key)
    ingredient_list = ", ".join(ingredients)
    
    user_block = f"""
User Ingredients: {ingredient_list}
Dietary Restriction: {diet}

Generate a structured recipe using ONLY the listed ingredients.
Output format MUST be:

Title
Prep Time
Ingredients Used
Instructions
"""
    full_prompt = CHEF_PERSONA + FEW_SHOT_EXAMPLES + user_block

    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=[{"text": full_prompt}]
    )

    text = getattr(response, "text", None)
    if not text:
        raise RuntimeError("No output received from Gemini model.")
    return text.strip()

# ==========================
# Streamlit UI
# ==========================

st.set_page_config(page_title="ChefRemy AI — Generative AI Meal Planner", page_icon="🍳", layout="wide")

# Sidebar for settings & API key
with st.sidebar:
    st.header("⚙️ Configuration")
    if not api_key:
        user_key = st.text_input("Gemini API Key:", type="password", placeholder="Enter your Gemini API key")
        if user_key:
            active_key = user_key
        else:
            active_key = None
            st.warning("⚠️ Enter a Gemini API Key to enable recipe generation.")
    else:
        active_key = api_key
        st.success("✅ Gemini API Key detected")
        
    st.markdown("---")
    st.markdown("### 🧠 Model Info")
    st.write("**Engine:** `gemini-2.5-flash`")
    st.write("**SDK:** `google-genai`")
    st.write("**Strategy:** Few-Shot In-Context Learning & Persona Prompting")

st.title("🍳 ChefRemy AI — Personal Chef & Meal Planner")
st.caption("Powered by **Google Gemini 2.5 Flash** • Zero-Waste Recipe Synthesis • Strict Dietary Guardrails")

col1, col2 = st.columns([2, 1])

with col1:
    ingredients_input = st.text_input(
        "Enter available ingredients (comma-separated):",
        placeholder="e.g. eggs, tomatoes, spinach, garlic, onion"
    )

with col2:
    diet_input = st.selectbox(
        "Dietary restriction:", 
        ["None", "Vegan", "Keto", "Vegetarian", "Gluten-Free"]
    )

if st.button("🍳 Generate Recipe", type="primary"):
    try:
        ingredients = clean_ingredients(ingredients_input)
        diet = validate_diet(diet_input)
        with st.spinner("Chef Remy is synthesizing your recipe... 🍲"):
            recipe = generate_recipe(ingredients, diet, active_key)
        st.success("✨ Recipe generated successfully!")
        st.text_area("Your Structured Recipe:", recipe, height=350)
    except Exception as e:
        st.error(f"❌ Error: {str(e)}")
