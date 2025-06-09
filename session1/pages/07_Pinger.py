
"""
Network Ping Monitor - A Streamlit application to monitor network connectivity.

This application provides a simple interface to ping IP addresses or domain names
and monitor the results in real-time. It supports IPv4, IPv6, and domain names.
"""

import streamlit as st
import subprocess
import time
import re
import threading
import platform
import queue
import socket
import logging
from typing import List, Optional, Tuple, Union
import utils.authenticate as authenticate
import utils.common as common

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("network_ping_monitor")


def initialize_session_state() -> None:
    """
    Initialize session state variables if they don't exist.
    """
    if 'ping_process' not in st.session_state:
        st.session_state.ping_process = None
    if 'is_pinging' not in st.session_state:
        st.session_state.is_pinging = False
    if 'ping_queue' not in st.session_state:
        st.session_state.ping_queue = queue.Queue()
    if 'ping_results' not in st.session_state:
        st.session_state.ping_results = []


def is_valid_ipv4(ip: str) -> bool:
    """
    Validate if the input string is a valid IPv4 address.
    
    Args:
        ip: String to validate as IPv4 address
        
    Returns:
        bool: True if valid IPv4 address, False otherwise
    """
    try:
        socket.inet_pton(socket.AF_INET, ip)
        return True
    except socket.error:
        return False


def is_valid_ipv6(ip: str) -> bool:
    """
    Validate if the input string is a valid IPv6 address.
    
    Args:
        ip: String to validate as IPv6 address
        
    Returns:
        bool: True if valid IPv6 address, False otherwise
    """
    try:
        socket.inet_pton(socket.AF_INET6, ip)
        return True
    except socket.error:
        return False


def is_valid_domain(domain: str) -> bool:
    """
    Validate if the input string is a valid domain name.
    
    Args:
        domain: String to validate as domain name
        
    Returns:
        bool: True if valid domain name, False otherwise
    """
    if len(domain) > 255:
        return False
    domain_pattern = re.compile(
        r"^(?:[a-zA-Z0-9](?:[a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?\.)+[a-zA-Z]{2,}$"
    )
    return bool(domain_pattern.match(domain))


def validate_target(target: str) -> Union[str, bool]:
    """
    Validate if the input string is a valid IP address or domain name.
    
    Args:
        target: String to validate
        
    Returns:
        str or bool: "IPv4", "IPv6", "Domain" if valid, False otherwise
    """
    if is_valid_ipv4(target):
        return "IPv4"
    elif is_valid_ipv6(target):
        return "IPv6"
    elif is_valid_domain(target):
        return "Domain"
    else:
        return False


def read_ping_output(process: subprocess.Popen, queue_obj: queue.Queue) -> None:
    """
    Read output from the ping process and put it into the queue.
    
    Args:
        process: Subprocess running ping command
        queue_obj: Queue to store ping results
    """
    try:
        for line in iter(process.stdout.readline, b''):
            if process.poll() is not None:
                break
            decoded_line = line.decode('utf-8', errors='replace').strip()
            if decoded_line:
                queue_obj.put(decoded_line)
        process.stdout.close()
    except Exception as e:
        logger.error(f"Error reading ping output: {str(e)}")


def get_ping_command(target: str, target_type: str) -> List[str]:
    """
    Build ping command based on target type and operating system.
    
    Args:
        target: IP address or domain name to ping
        target_type: Type of target ("IPv4", "IPv6", or "Domain")
        
    Returns:
        list: Command to execute as a list of strings
    """
    os_name = platform.system().lower()
    
    if os_name == "windows":
        if target_type == "IPv6":
            cmd = ["ping", "-6", "-t", target]
        else:
            cmd = ["ping", "-t", target]
    else:  # Linux, MacOS, etc.
        if target_type == "IPv6":
            # On Linux/MacOS ping6 or ping -6 depending on the system
            try:
                subprocess.check_output(["ping6", "-c", "1", "::1"], stderr=subprocess.STDOUT)
                cmd = ["ping6", target]
            except (subprocess.SubprocessError, FileNotFoundError):
                cmd = ["ping", "-6", target]
        else:
            cmd = ["ping", target]
    
    logger.info(f"Ping command: {' '.join(cmd)}")
    return cmd


def start_ping() -> None:
    """
    Start pinging the target specified in session state.
    """
    target = st.session_state.target.strip()
    if not target:
        st.error("Please enter an IP address or domain name.")
        return
    
    target_type = validate_target(target)
    if not target_type:
        st.error("Please enter a valid IP address or domain name.")
        return
    
    # Clear previous results
    st.session_state.ping_results = []
    
    try:
        # Create appropriate ping command based on target type and OS
        cmd = get_ping_command(target, target_type)
        
        # Start ping process
        process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=False,
            bufsize=1
        )
        
        st.session_state.ping_process = process
        st.session_state.is_pinging = True
        logger.info(f"Started pinging {target} ({target_type})")
        
        # Start thread to read output
        thread = threading.Thread(
            target=read_ping_output, 
            args=(process, st.session_state.ping_queue),
            daemon=True
        )
        thread.start()
        
    except Exception as e:
        error_msg = f"Error starting ping: {str(e)}"
        logger.error(error_msg)
        st.error(error_msg)
        st.session_state.is_pinging = False


def stop_ping() -> None:
    """
    Stop the current ping process.
    """
    try:
        if st.session_state.ping_process:
            # Terminate the ping process
            if platform.system().lower() == "windows":
                subprocess.call(['taskkill', '/F', '/T', '/PID', str(st.session_state.ping_process.pid)])
            else:
                st.session_state.ping_process.terminate()
            logger.info("Ping process stopped")
            st.session_state.ping_process = None
        st.session_state.is_pinging = False
    except Exception as e:
        error_msg = f"Error stopping ping process: {str(e)}"
        logger.error(error_msg)
        st.error(error_msg)


def render_sidebar() -> None:
    """
    Render the sidebar with about information.
    """
    with st.sidebar:

        common.render_sidebar()

        with st.expander("About this Application", expanded=False):
            st.write("""
            # Network Ping Monitor
            
            This application allows you to monitor network connectivity by pinging 
            IP addresses or domain names in real-time. It supports:
            
            - IPv4 addresses
            - IPv6 addresses
            - Domain names
            
            The application shows ping responses as they come in, allowing you to 
            monitor network latency and packet loss without leaving your browser.
            """)


def render_footer() -> None:
    """
    Render the footer with copyright information.
    """
    st.markdown(
        """
        <div style="position: fixed; bottom: 0; width: 100%; text-align: center; padding: 10px; background-color: white;">
        © 2025, Amazon Web Services, Inc. or its affiliates. All rights reserved.
        </div>
        """,
        unsafe_allow_html=True
    )


def render_ui() -> None:
    """
    Render the main user interface.
    """
    st.title("Network Ping Monitor")
    
    with st.container(border=True):
        st.session_state.target = st.text_input(
            "Enter IP Address or Domain Name", 
            help="Enter a valid IPv4/IPv6 address (e.g., 192.168.1.1, 2001:db8::1) or domain name (e.g., example.com)"
        )

        if st.session_state.is_pinging:
            if st.button("Stop Ping", key="stop", type="primary"):
                stop_ping()
        else:
            if st.button("Start Ping", key="start", type="primary"):
                start_ping()

        # Show info about the target type if entered
        if st.session_state.target:
            target_type = validate_target(st.session_state.target.strip())
            if target_type:
                st.info(f"Target type detected: {target_type}")

    # Create a container for ping results
    results_container = st.container()

    # Show results placeholder
    with results_container:
        st.subheader("Ping Results")
        ping_text = st.empty()

    # Update ping results in real-time
    if st.session_state.is_pinging:
        # Process any new ping results in the queue
        max_displayed_lines = 20
        
        while not st.session_state.ping_queue.empty():
            try:
                line = st.session_state.ping_queue.get()
                st.session_state.ping_results.append(line)
                # Keep only the most recent results
                if len(st.session_state.ping_results) > max_displayed_lines:
                    st.session_state.ping_results.pop(0)
            except Exception as e:
                logger.error(f"Error processing ping results: {str(e)}")
        
        # Display ping results
        ping_text.code('\n'.join(st.session_state.ping_results))

    # Run this in an infinite loop to update the UI
    if st.session_state.is_pinging:
        time.sleep(0.1)
        st.rerun()


def main() -> None:
    """
    Main function to set up and run the application.
    """
    
    # Initialize session state
    initialize_session_state()
    
    # Render sidebar with about information
    render_sidebar()
    
    # Render main UI
    render_ui()
    
    # Render footer
    render_footer()


# Main execution flow
if __name__ == "__main__":
    # Set page title and configure layout
    st.set_page_config(page_title="Network Ping Monitor", layout="wide")
    try:
        # First check authentication
        is_authenticated = authenticate.login()
        
        # If authenticated, show the main app content
        if is_authenticated:
            main()
    except Exception as e:
        logger.exception(f"Unhandled exception in application: {str(e)}")
        st.error(f"An unexpected error occurred: {str(e)}")
