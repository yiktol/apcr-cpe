"""
AWS Cognito Authentication Module for Streamlit Applications

This module provides functions to handle authentication with AWS Cognito in a Streamlit application.
It manages the OAuth 2.0 flow, token management, and user session handling.

Functions:
    - initialize_session: Initialize Streamlit session state variables
    - authenticate_user: Main function to handle the full authentication process
    - get_auth_code: Extract authorization code from query parameters
    - exchange_code_for_tokens: Exchange authorization code for access and ID tokens
    - get_user_info: Retrieve user information using access token
    - decode_cognito_groups: Extract Cognito groups from ID token
    - render_login_button: Display AWS-styled login button
    - render_logout_button: Display AWS-styled logout button
"""

import streamlit as st
import requests
import base64
import json
import logging
from typing import Dict, List, Tuple, Optional, Any
from utils.cognito_credentials import get_cognito_credentials

# Configure logging
logging.basicConfig(level=logging.INFO, 
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# AWS color scheme
AWS_ORANGE = "#FF9900"
AWS_HOVER = "#EC7211"
AWS_ACTIVE = "#D05C17"
AWS_TEXT = "#FFFFFF"

def set_st_state_vars() -> None:
    """
    Initialize Streamlit session state variables for authentication flow.
    """
    if "auth_code" not in st.session_state:
        st.session_state["auth_code"] = ""
    if "authenticated" not in st.session_state:
        st.session_state["authenticated"] = False
    if "user_cognito_groups" not in st.session_state:
        st.session_state["user_cognito_groups"] = []
    if "user_info" not in st.session_state:
        st.session_state["user_info"] = {}

def load_cognito_config() -> Dict[str, str]:
    """
    Load Cognito configuration from secrets.
    
    Returns:
        Dict containing Cognito configuration parameters
    
    Raises:
        RuntimeError: If required Cognito credentials are missing
    """
    try:
        credentials = get_cognito_credentials()
        
        # Log successful credential retrieval with masked values
        logger.info("Successfully retrieved Cognito credentials")
        required_keys = ["COGNITO_DOMAIN", "COGNITO_APP_CLIENT_ID", 
                         "COGNITO_APP_CLIENT_SECRET","COGNITO_REDIRECT_URI_AIP_1"]
        
        # Check for required keys
        missing_keys = [key for key in required_keys if not credentials.get(key)]
        if missing_keys:
            raise RuntimeError(f"Missing required Cognito credentials: {', '.join(missing_keys)}")
            
        return {
            "domain": credentials.get("COGNITO_DOMAIN"),
            "client_id": credentials.get("COGNITO_APP_CLIENT_ID"),
            "client_secret": credentials.get("COGNITO_APP_CLIENT_SECRET"),
            "redirect_uri": credentials.get("COGNITO_REDIRECT_URI_AIP_1")
        }
    except Exception as e:
        logger.error(f"Failed to retrieve Cognito credentials: {str(e)}")
        raise RuntimeError(f"Authentication configuration error: {str(e)}")

def get_auth_code() -> str:
    """
    Extract authorization code from query parameters.
    
    Returns:
        Authorization code string or empty string if not found
    """
    try:
        auth_query_params = st.query_params
        return auth_query_params.get("code", "")
    except Exception as e:
        logger.error(f"Error extracting auth code: {str(e)}")
        return ""

def exchange_code_for_tokens(auth_code: str, config: Dict[str, str]) -> Tuple[str, str]:
    """
    Exchange authorization code for access and ID tokens.
    
    Args:
        auth_code: Authorization code from Cognito server
        config: Dictionary containing Cognito configuration
        
    Returns:
        Tuple containing access_token and id_token
    """
    if not auth_code:
        return "", ""
        
    token_url = f"{config['domain']}/oauth2/token"
    client_secret_string = f"{config['client_id']}:{config['client_secret']}"
    client_secret_encoded = str(
        base64.b64encode(client_secret_string.encode("utf-8")), "utf-8"
    )
    
    headers = {
        "Content-Type": "application/x-www-form-urlencoded",
        "Authorization": f"Basic {client_secret_encoded}",
    }
    
    body = {
        "grant_type": "authorization_code",
        "client_id": config['client_id'],
        "code": auth_code,
        "redirect_uri": config['redirect_uri'],
    }
    
    try:
        token_response = requests.post(token_url, headers=headers, data=body)
        token_response.raise_for_status()
        
        response_data = token_response.json()
        return response_data.get("access_token", ""), response_data.get("id_token", "")
    except requests.exceptions.RequestException as e:
        logger.error(f"Token exchange failed: {str(e)}")
        if hasattr(e, 'response') and e.response:
            logger.error(f"Response status: {e.response.status_code}")
            logger.error(f"Response body: {e.response.text}")
        return "", ""

def get_user_info(access_token: str, config: Dict[str, str]) -> Dict[str, Any]:
    """
    Retrieve user information from AWS Cognito.
    
    Args:
        access_token: Access token from successful authentication
        config: Dictionary containing Cognito configuration
        
    Returns:
        Dictionary containing user information
    """
    if not access_token:
        return {}
        
    userinfo_url = f"{config['domain']}/oauth2/userInfo"
    headers = {
        "Content-Type": "application/json;charset=UTF-8",
        "Authorization": f"Bearer {access_token}",
    }
    
    try:
        response = requests.get(userinfo_url, headers=headers)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        logger.error(f"Failed to get user info: {str(e)}")
        return {}

def decode_cognito_groups(id_token: str) -> List[str]:
    """
    Decode ID token to extract user's Cognito groups.
    
    Args:
        id_token: ID token from successful authentication
        
    Returns:
        List of Cognito groups the user belongs to
    """
    if not id_token:
        return []
    
    try:
        # Split the JWT token
        header, payload, signature = id_token.split(".")
        
        # Pad the base64 string if needed
        def pad_base64(data):
            missing_padding = len(data) % 4
            if missing_padding:
                data += "=" * (4 - missing_padding)
            return data
        
        # Decode the payload
        decoded_payload = base64.urlsafe_b64decode(pad_base64(payload))
        payload_dict = json.loads(decoded_payload)
        
        # Extract Cognito groups
        return payload_dict.get("cognito:groups", [])
    except Exception as e:
        logger.error(f"Failed to decode token: {str(e)}")
        return []

def render_login_button(login_url: str) -> None:
    """
    Render AWS-styled login button.
    
    Args:
        login_url: URL to initiate Cognito login flow
    """
    css = f"""
    <style>
    .aws-button {{
        background-color: {AWS_ORANGE};
        color: {AWS_TEXT} !important;
        padding: 0.75em 1.25em;
        font-weight: bold;
        border-radius: 4px;
        text-decoration: none;
        text-align: center;
        display: inline-block;
        border: none;
        font-family: "Amazon Ember", Arial, sans-serif;
        transition: background-color 0.3s;
    }}
    .aws-button:hover {{
        background-color: {AWS_HOVER};
        text-decoration: none;
    }}
    .aws-button:active {{
        background-color: {AWS_ACTIVE};
    }}
    </style>
    """
    html = css + f"<a href='{login_url}' class='aws-button' target='_self'>Sign In</a>"
    st.markdown(html, unsafe_allow_html=True)

def render_logout_button(logout_url: str) -> None:
    """
    Render AWS-styled logout button.
    
    Args:
        logout_url: URL to initiate Cognito logout
    """
    css = f"""
    <style>
    .aws-button {{
        background-color: {AWS_ORANGE};
        color: {AWS_TEXT} !important;
        padding: 0.75em 1.25em;
        font-weight: bold;
        border-radius: 4px;
        text-decoration: none;
        text-align: center;
        display: inline-block;
        border: none;
        font-family: "Amazon Ember", Arial, sans-serif;
        transition: background-color 0.3s;
    }}
    .aws-button:hover {{
        background-color: {AWS_HOVER};
        text-decoration: none;
    }}
    .aws-button:active {{
        background-color: {AWS_ACTIVE};
    }}
    </style>
    """
    html = css + f"<a href='{logout_url}' class='aws-button' target='_self'>Sign Out</a>"
    st.sidebar.markdown(html, unsafe_allow_html=True)

def login() -> bool:
    """
    Main authentication function to handle Cognito auth flow.
    
    Returns:
        Boolean indicating whether user is authenticated
        
    Raises:
        RuntimeError: If authentication configuration fails
    """
    # Initialize session state
    set_st_state_vars()
    
    try:
        # Load configuration
        config = load_cognito_config()
        
        # Set up login/logout URLs
        login_url = (
            f"{config['domain']}/login?client_id={config['client_id']}"
            f"&response_type=code&scope=email+openid&redirect_uri={config['redirect_uri']}"
        )
        logout_url = (
            f"{config['domain']}/logout?client_id={config['client_id']}"
            f"&logout_uri={config['redirect_uri']}"
        )
        
        # Check for authorization code in URL
        auth_code = get_auth_code()
        
        # If we have a new auth code, process it
        if auth_code and auth_code != st.session_state.get("auth_code", ""):
            access_token, id_token = exchange_code_for_tokens(auth_code, config)
            
            if access_token and id_token:
                user_info = get_user_info(access_token, config)
                cognito_groups = decode_cognito_groups(id_token)
                
                # Update session state
                st.session_state["auth_code"] = auth_code
                st.session_state["authenticated"] = True
                st.session_state["user_cognito_groups"] = cognito_groups
                st.session_state["user_info"] = user_info
                
                logger.info(f"User authenticated successfully. Groups: {cognito_groups}")
                
        # Render appropriate UI based on authentication state
        if st.session_state.get("authenticated", False):
            render_logout_button(logout_url)
            return True
        else:
            st.info("Please sign in to access this application.")
            render_login_button(login_url)
            return False
            
    except RuntimeError as e:
        st.error(f"Authentication error: {str(e)}")
        logger.error(f"Authentication error: {str(e)}")
        return False
