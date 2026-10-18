"""
ListingCraft AI - AI-Powered Product Listing & SEO Tags Generator
Powered by open-weight Vision Language Models (VLMs) on Groq.

Installation Instructions:
pip install streamlit groq pillow

Run the app:
streamlit run app.py
"""

import base64
import io
import json
import os
import re
from PIL import Image
import streamlit as st
from groq import Groq

# ---------------------------------------------------------
# Page Configuration
# ---------------------------------------------------------
st.set_page_config(
    page_title="ListingCraft AI",
    page_icon="📦",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ---------------------------------------------------------
# Custom Styling (CSS)
# ---------------------------------------------------------
st.markdown(
    """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800&display=swap');

    html, body, [class*="css"] {
        font-family: 'Plus Jakarta Sans', sans-serif;
    }

    .main-title {
        font-size: 2.4rem;
        font-weight: 800;
        background: linear-gradient(135deg, #FF6B35 0%, #F7931E 50%, #7B2CBF 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-bottom: 0.2rem;
        display: flex;
        align-items: center;
        gap: 0.5rem;
    }

    .sub-title {
        font-size: 1.05rem;
        color: #64748B;
        margin-bottom: 1.5rem;
        font-weight: 500;
    }

    .tag-pill {
        display: inline-block;
        background: linear-gradient(135deg, rgba(255, 107, 53, 0.12), rgba(123, 44, 191, 0.12));
        border: 1px solid rgba(255, 107, 53, 0.35);
        color: #E65100;
        padding: 6px 14px;
        margin: 4px;
        border-radius: 9999px;
        font-size: 0.88rem;
        font-weight: 600;
        letter-spacing: 0.2px;
        transition: all 0.2s ease-in-out;
    }
    .tag-pill:hover {
        transform: translateY(-1px);
        box-shadow: 0 4px 10px rgba(255, 107, 53, 0.2);
    }

    .marketplace-badge {
        display: inline-block;
        padding: 3px 10px;
        border-radius: 6px;
        font-size: 0.78rem;
        font-weight: 700;
        text-transform: uppercase;
        margin-left: 8px;
        background-color: #EEF2F6;
        color: #334155;
    }

    .preview-box {
        border-radius: 12px;
        padding: 1rem;
        background: #F8FAFC;
        border: 1px solid #E2E8F0;
        margin-bottom: 1rem;
    }

    .stButton>button {
        width: 100%;
        border-radius: 10px;
        font-weight: 700;
        padding: 0.65rem 1.25rem;
        background: linear-gradient(135deg, #FF6B35 0%, #E65100 100%);
        color: white;
        border: none;
        box-shadow: 0 4px 14px rgba(230, 81, 0, 0.3);
        transition: all 0.2s ease;
    }
    .stButton>button:hover {
        background: linear-gradient(135deg, #F7931E 0%, #FF6B35 100%);
        box-shadow: 0 6px 18px rgba(230, 81, 0, 0.4);
        transform: translateY(-1px);
        color: white;
    }

    .char-count {
        font-size: 0.8rem;
        color: #94A3B8;
        float: right;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

# ---------------------------------------------------------
# Helper Functions
# ---------------------------------------------------------
def process_and_encode_image(uploaded_file, max_dimension=1024, quality=85):
    """
    Load an uploaded image file, convert to RGB, resize within bounds,
    and return as a Base64 Data URI string.
    """
    image = Image.open(uploaded_file)
    
    # Handle orientation metadata if present and convert to RGB
    if image.mode != "RGB":
        image = image.convert("RGB")
    
    # Resize preserving aspect ratio if dimension exceeds max_dimension
    width, height = image.size
    if width > max_dimension or height > max_dimension:
        image.thumbnail((max_dimension, max_dimension), Image.Resampling.LANCZOS)
    
    # Save to buffer
    buffered = io.BytesIO()
    image.save(buffered, format="JPEG", quality=quality, optimize=True)
    base64_str = base64.b64encode(buffered.getvalue()).decode("utf-8")
    
    return f"data:image/jpeg;base64,{base64_str}"


def extract_json_from_response(raw_text: str):
    """
    Safely extract and parse JSON object from text that might include
    markdown code fences or leading/trailing commentary.
    """
    cleaned = raw_text.strip()
    
    # Check for markdown code fences
    fence_match = re.search(r"```(?:json)?\s*([\s\S]*?)\s*```", cleaned)
    if fence_match:
        cleaned = fence_match.group(1).strip()
    
    # Attempt direct JSON parsing
    try:
        return json.loads(cleaned)
    except json.JSONDecodeError:
        # Fallback: extract substring between first { and last }
        first_brace = cleaned.find("{")
        last_brace = cleaned.rfind("}")
        if first_brace != -1 and last_brace != -1 and last_brace > first_brace:
            sub = cleaned[first_brace : last_brace + 1]
            return json.loads(sub)
        raise


# ---------------------------------------------------------
# Sidebar Configuration
# ---------------------------------------------------------
with st.sidebar:
    st.header("⚙️ Listing Preferences")
    
    target_marketplace = st.selectbox(
        "Target Marketplace",
        options=["Etsy", "eBay", "Shopify", "Instagram / Social Shop"],
        index=0,
        help="Tailors title length, description structure, and tag strategy.",
    )
    
    tone_of_voice = st.selectbox(
        "Tone of Voice",
        options=[
            "Casual & Trendy",
            "Professional & Clean",
            "Vintage & Antique",
            "Luxury & Elegant",
            "Persuasive & High Energy",
        ],
        index=0,
        help="Influences storytelling, emotion, and phrasing.",
    )
    
    vision_model = st.selectbox(
        "Vision Model Selection",
        options=["qwen/qwen3.8-27b"],
        index=0,
        help="Select the Groq-hosted open-weight Vision Language Model.",
    )
    
    st.markdown("---")
    st.markdown(
        """
        <div style="font-size: 0.8rem; color: #64748B; line-height: 1.4;">
            <strong>Pro Tip:</strong> For Etsy listings, 13 exact search tags and a keyword-dense 140-char title maximize discovery algorithm placement.
        </div>
        """,
        unsafe_allow_html=True,
    )


# ---------------------------------------------------------
# Main Page Header
# ---------------------------------------------------------
st.markdown('<div class="main-title">📦 ListingCraft AI</div>', unsafe_allow_html=True)
st.markdown(
    '<div class="sub-title">Turn product photos into high-converting descriptions & SEO tags using hosted open-weight vision models.</div>',
    unsafe_allow_html=True,
)

# ---------------------------------------------------------
# Inputs Section
# ---------------------------------------------------------
col_left, col_right = st.columns([1.1, 0.9], gap="large")

with col_left:
    st.subheader("1. Upload Product Photos")
    uploaded_files = st.file_uploader(
        "Upload up to 3 product photos",
        type=["jpg", "jpeg", "png"],
        accept_multiple_files=True,
        help="Add clear images highlighting front, details, labels, or textures.",
    )

    if uploaded_files:
        if len(uploaded_files) > 3:
            st.warning("⚠️ Only the first 3 images will be processed.")
            active_files = uploaded_files[:3]
        else:
            active_files = uploaded_files

        thumb_cols = st.columns(len(active_files))
        for idx, file in enumerate(active_files):
            with thumb_cols[idx]:
                st.image(file, use_container_width=True, caption=f"Photo #{idx + 1}")
    else:
        active_files = []

with col_right:
    st.subheader("2. Product Context (Optional)")
    brand_name = st.text_input(
        "Brand / Manufacturer Name",
        placeholder="e.g., Handmade, Nike, Vintage Levi's, Artisan Studio...",
        help="Add brand or maker name if applicable.",
    )

    context_notes = st.text_area(
        "Additional Context / Flaws / Sizing Notes",
        placeholder="e.g., Minor patina on brass buckle, 100% genuine full-grain leather, Size M (chest 38-40 in), handcrafted in Portland...",
        height=120,
        help="Specify dimensions, materials, flaws, or unique selling points.",
    )

st.markdown("<br>", unsafe_allow_html=True)
generate_btn = st.button("⚡ Generate Product Listing", use_container_width=True)

# Initialize session state for holding results
if "listing_result" not in st.session_state:
    st.session_state.listing_result = None

# ---------------------------------------------------------
# Backend Execution & Groq API Integration
# ---------------------------------------------------------
if generate_btn:
    # 1. Retrieve API key securely from server secrets or environment
    groq_api_key = ""
    try:
        if "GROQ_API_KEY" in st.secrets:
            groq_api_key = st.secrets["GROQ_API_KEY"]
    except Exception:
        pass
    if not groq_api_key:
        groq_api_key = os.environ.get("GROQ_API_KEY", "")

    if not groq_api_key or not groq_api_key.strip():
        st.error("Server API key not configured. Please ensure GROQ_API_KEY is configured in secrets or environment.")
        st.stop()

    # 2. Validate at least one image uploaded
    if not active_files:
        st.error("Please upload at least one product photo before generating.")
        st.stop()

    with st.spinner(f"Analyzing product photos with {vision_model}..."):
        try:
            # 3. Convert images to Base64 Data URIs
            image_data_uris = []
            for file in active_files:
                uri = process_and_encode_image(file)
                image_data_uris.append(uri)

            # 4. Initialize Groq Client
            client = Groq(api_key=groq_api_key.strip())

            # 5. Build prompt and marketplace guidelines
            marketplace_guidelines = {
                "Etsy": "Strict character limit under 140 characters for title. Rich searchable tags. Highlight handcrafted, vintage, aesthetic, or unique gift appeal.",
                "eBay": "Include brand, model, size, key specs, condition in title. Clear bullet points for item specifics and dimensions.",
                "Shopify": "Catchy branded title, benefit-driven product description, scannable bullet points, and social proof angles.",
                "Instagram / Social Shop": "Engaging hook, emoji-rich friendly description, visual aesthetics, and viral/niche tags.",
            }

            system_instruction = (
                "You are an expert e-commerce copywriter, marketplace SEO specialist, and visual appraiser. "
                "Analyze the provided product image(s) with high precision (identifying materials, colors, textures, craftsmanship, "
                "aesthetic style, and visible flaws or markings). "
                "You must return ONLY a valid, strict JSON object with NO preamble or conversational text outside the JSON. "
                "The JSON must have the following exact schema:\n"
                "{\n"
                '  "title": "string under 140 characters, keyword-rich and optimized for marketplace search",\n'
                '  "description": "structured, compelling copy with visual details, bulleted features, specs, and suggested uses",\n'
                '  "tags": ["13 high-traffic SEO search tags/keywords as strings"]\n'
                "}\n"
                f"Target Marketplace: {target_marketplace} ({marketplace_guidelines.get(target_marketplace, '')})\n"
                f"Tone of Voice: {tone_of_voice}."
            )

            # Prepare user content message payload
            user_content = []

            # Add each image to payload
            for uri in image_data_uris:
                user_content.append({
                    "type": "image_url",
                    "image_url": {
                        "url": uri
                    }
                })

            # Add text instructions
            text_prompt = (
                f"Analyze these product images carefully.\n"
                f"Marketplace: {target_marketplace}\n"
                f"Tone: {tone_of_voice}\n"
            )
            if brand_name:
                text_prompt += f"Brand / Maker: {brand_name}\n"
            if context_notes:
                text_prompt += f"Seller Notes / Flaws / Sizing: {context_notes}\n"

            text_prompt += (
                "\nProvide a strict JSON response containing:\n"
                "1. 'title': Catchy, keyword-optimized title under 140 characters.\n"
                "2. 'description': Complete high-converting product description with bullet points.\n"
                "3. 'tags': A list of exactly 13 search tags tailored for discovery on this marketplace."
            )

            user_content.append({
                "type": "text",
                "text": text_prompt
            })

            # Create chat completion
            chat_completion = client.chat.completions.create(
                model=vision_model,
                messages=[
                    {"role": "system", "content": system_instruction},
                    {"role": "user", "content": user_content},
                ],
                response_format={"type": "json_object"},
                temperature=0.3,
                max_tokens=1500,
            )

            raw_response = chat_completion.choices[0].message.content
            parsed_data = extract_json_from_response(raw_response)

            # Ensure all keys exist
            if "title" not in parsed_data:
                parsed_data["title"] = "Custom Crafted Product Listing"
            if "description" not in parsed_data:
                parsed_data["description"] = "No description generated."
            if "tags" not in parsed_data or not isinstance(parsed_data["tags"], list):
                parsed_data["tags"] = []

            # Trim tags to 13 if more, or keep whatever returned
            parsed_data["marketplace"] = target_marketplace
            parsed_data["tone"] = tone_of_voice
            parsed_data["model"] = vision_model

            st.session_state.listing_result = parsed_data
            st.success("✨ Product listing generated successfully!")

        except Exception as e:
            st.error(f"Error communicating with Groq API: {str(e)}")


# ---------------------------------------------------------
# Output Display & Features
# ---------------------------------------------------------
if st.session_state.listing_result:
    result = st.session_state.listing_result
    st.markdown("---")
    st.subheader("📋 Generated Product Listing")

    tab_copy, tab_tags, tab_export = st.tabs(["📝 Listing Copy", "🏷️ SEO Tags", "💾 Export & Raw Output"])

    # --- TAB 1: Listing Copy ---
    with tab_copy:
        st.markdown("#### Product Title")
        title_val = result.get("title", "")
        char_count = len(title_val)
        status_color = "#10B981" if char_count <= 140 else "#EF4444"

        st.markdown(
            f'<div class="char-count" style="color: {status_color}; font-weight: 600;">{char_count} / 140 characters</div>',
            unsafe_allow_html=True,
        )
        edited_title = st.text_input(
            "Editable Title (Optimized for Search)",
            value=title_val,
            label_visibility="collapsed",
        )

        st.markdown("#### Product Description")
        desc_val = result.get("description", "")
        
        # Display formatted markdown inside preview container
        st.markdown(f'<div class="preview-box">{desc_val}</div>', unsafe_allow_html=True)
        
        with st.expander("✏️ Edit Description Text"):
            edited_desc = st.text_area("Description Source", value=desc_val, height=220)

    # --- TAB 2: SEO Tags ---
    with tab_tags:
        tags_list = result.get("tags", [])
        st.markdown(f"#### SEO Search Tags ({len(tags_list)} Generated)")
        
        # Display as pill badges
        if tags_list:
            pill_html = '<div style="margin-bottom: 1.25rem;">'
            for tag in tags_list:
                clean_tag = str(tag).strip()
                pill_html += f'<span class="tag-pill">#{clean_tag}</span>'
            pill_html += '</div>'
            st.markdown(pill_html, unsafe_allow_html=True)

            st.markdown("#### 1-Click Copy-Paste Tag String")
            st.caption("Copy this comma-separated string directly into Etsy, eBay, or Shopify tag fields:")
            comma_tags = ", ".join([str(t).strip() for t in tags_list])
            st.code(comma_tags, language=None)
        else:
            st.info("No tags were generated in the response.")

    # --- TAB 3: Export & Raw Output ---
    with tab_export:
        st.markdown("#### Export Listing")
        
        # Format markdown output
        current_title = edited_title if 'edited_title' in locals() else result.get("title", "")
        current_desc = edited_desc if 'edited_desc' in locals() else result.get("description", "")
        tags_str = ", ".join([str(t).strip() for t in result.get("tags", [])])

        export_content = (
            f"# {current_title}\n\n"
            f"**Marketplace:** {result.get('marketplace', target_marketplace)}\n"
            f"**Tone:** {result.get('tone', tone_of_voice)}\n"
            f"**Model:** {result.get('model', vision_model)}\n\n"
            f"## Product Description\n\n"
            f"{current_desc}\n\n"
            f"## SEO Tags\n\n"
            f"{tags_str}\n"
        )

        st.download_button(
            label="📥 Download Listing (.md)",
            data=export_content,
            file_name="listingcraft_product.md",
            mime="text/markdown",
            use_container_width=True,
        )

        st.markdown("<br>", unsafe_allow_html=True)
        st.download_button(
            label="📄 Download Listing (.txt)",
            data=export_content,
            file_name="listingcraft_product.txt",
            mime="text/plain",
            use_container_width=True,
        )

        with st.expander("🔍 View Raw JSON Output"):
            st.json(result)
