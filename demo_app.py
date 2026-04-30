"""Streamlit dashboard for Sheng-Native API demo.

This provides a real-time interface for testing the Sheng-Native API
with visual feedback on sentiment and logistics intent detection.
"""

import streamlit as st
import requests
import json
from typing import Dict, Any


def analyze_text(text: str, api_url: str = "http://localhost:8000") -> Dict[str, Any]:
    """Send text to the API for analysis.
    
    Args:
        text: Sheng text to analyze
        api_url: Base URL of the API
        
    Returns:
        Analysis response as dictionary
    """
    endpoint = f"{api_url}/v1/analyze"
    payload = {
        "text": text,
        "include_logistics": True,
        "include_code_switches": True
    }
    
    try:
        response = requests.post(endpoint, json=payload, timeout=10)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        st.error(f"API Error: {e}")
        return None


def main():
    """Main Streamlit application."""
    st.set_page_config(
        page_title="Sheng-Native API Dashboard",
        page_icon="🇰🇪",
        layout="wide"
    )
    
    # Header
    st.title("🇰🇪 Sheng-Native API Dashboard")
    st.markdown("Real-time sentiment analysis and logistics intent detection for Kenyan Sheng")
    
    # Sidebar for API configuration
    with st.sidebar:
        st.header("API Configuration")
        api_url = st.text_input("API URL", value="http://localhost:8000")
        
        st.header("Test Cases")
        test_cases = {
            "General/Negative": "Buda niko sapa, nisaidie chapaa",
            "Logistics/Traffic": "Jam imekali CBD, tumetuma saa tatu",
            "Logistics/Police": "Karao wako Westlands, wanawakamata",
            "General/Positive": "Hii mbogi ni fiti sana",
            "Logistics/Obstacle": "Mreki imetoka Thika Road, mat imejaa"
        }
        
        selected_test = st.selectbox("Select Test Case", list(test_cases.keys()))
        if st.button("Load Test Case"):
            st.session_state.test_text = test_cases[selected_test]
    
    # Main content area
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.header("Input Text")
        
        # Text input
        default_text = st.session_state.get("test_text", "")
        user_input = st.text_area(
            "Enter Sheng text to analyze:",
            value=default_text,
            height=100,
            placeholder="Type Sheng text here..."
        )
        
        # Analyze button
        if st.button("Analyze", type="primary"):
            if user_input.strip():
                with st.spinner("Analyzing..."):
                    result = analyze_text(user_input, api_url)
                    st.session_state.last_result = result
            else:
                st.warning("Please enter some text to analyze")
    
    with col2:
        st.header("Quick Stats")
        
        # Display last result stats if available
        if "last_result" in st.session_state and st.session_state.last_result:
            result = st.session_state.last_result
            
            st.metric("Sentiment", result.get("sentiment_label", "N/A"))
            st.metric("Confidence", f"{result.get('confidence', 0):.2%}")
            st.metric("Is Logistics", "Yes" if result.get("is_logistics") else "No")
            
            if result.get("logistics_intent"):
                li = result["logistics_intent"]
                st.metric("Intent", li.get("intent", "N/A"))
    
    # Results section
    if "last_result" in st.session_state and st.session_state.last_result:
        result = st.session_state.last_result
        
        st.header("Analysis Results")
        
        # Create columns for different result sections
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.subheader("Sentiment Analysis")
            
            # Sentiment score gauge
            sentiment_score = result.get("sentiment_score", 0)
            st.progress((sentiment_score + 1) / 2)  # Convert -1 to 1 range to 0 to 1
            
            st.metric("Score", f"{sentiment_score:.2f}")
            st.metric("Label", result.get("sentiment_label", "N/A"))
            
            # Refinement info
            if result.get("metadata", {}).get("refinement_applied"):
                st.info("Logic refinements applied")
                with st.expander("Refinement Details"):
                    st.text(result.get("metadata", {}).get("refinement_reasoning", ""))
        
        with col2:
            st.subheader("Logistics Intent")
            
            if result.get("is_logistics"):
                li = result["logistics_intent"]
                st.success(f"Intent: {li.get('intent', 'N/A')}")
                st.info(f"Severity: {li.get('severity', 'N/A')}")
                st.text(li.get("description", ""))
            else:
                st.info("No logistics intent detected")
        
        with col3:
            st.subheader("Language Analysis")
            
            # Slang terms
            slang_terms = result.get("slang_terms", [])
            if slang_terms:
                st.write("**Slang Terms:**")
                for term in slang_terms:
                    st.success(f"• {term}")
            else:
                st.info("No slang terms detected")
            
            # Code switches
            code_switches = result.get("code_switches", [])
            if code_switches:
                st.write("**Code Switches:**")
                for cs in code_switches:
                    st.info(f"• {cs}")
        
        # Detailed breakdown
        with st.expander("Detailed Breakdown"):
            col1, col2 = st.columns(2)
            
            with col1:
                st.write("**Original Text:**")
                st.text(result.get("original_text", ""))
                
                st.write("**Normalized Text:**")
                st.text(result.get("normalized_text", ""))
            
            with col2:
                st.write("**Tokens:**")
                tokens = result.get("tokens", [])
                if tokens:
                    st.write(", ".join(tokens))
                else:
                    st.info("No tokens")
                
                st.write("**Metadata:**")
                metadata = result.get("metadata", {})
                if metadata:
                    st.json(metadata)
    
    # Footer
    st.markdown("---")
    st.markdown("**Sheng-Native API Dashboard** | Built for Nairobi's informal economy")


if __name__ == "__main__":
    main()
