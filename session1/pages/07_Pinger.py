
import streamlit as st
import subprocess
import time
import re
import threading
import platform
import queue
import socket

# Set page title and configure layout
st.set_page_config(page_title="Network Ping Monitor", layout="wide")
st.title("Network Ping Monitor")

# Initialize session state variables if they don't exist
if 'ping_process' not in st.session_state:
    st.session_state.ping_process = None
if 'is_pinging' not in st.session_state:
    st.session_state.is_pinging = False
if 'ping_queue' not in st.session_state:
    st.session_state.ping_queue = queue.Queue()
if 'ping_results' not in st.session_state:
    st.session_state.ping_results = []

# Function to validate IPv4 address
def is_valid_ipv4(ip):
    try:
        socket.inet_pton(socket.AF_INET, ip)
        return True
    except socket.error:
        return False

# Function to validate IPv6 address
def is_valid_ipv6(ip):
    try:
        socket.inet_pton(socket.AF_INET6, ip)
        return True
    except socket.error:
        return False

# Function to validate domain name
def is_valid_domain(domain):
    # Simple check for domain format
    if len(domain) > 255:
        return False
    domain_pattern = re.compile(
        r"^(?:[a-zA-Z0-9](?:[a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?\.)+[a-zA-Z]{2,}$"
    )
    return bool(domain_pattern.match(domain))

# Function to validate input (IP or domain)
def validate_target(target):
    if is_valid_ipv4(target):
        return "IPv4"
    elif is_valid_ipv6(target):
        return "IPv6"
    elif is_valid_domain(target):
        return "Domain"
    else:
        return False

# Function to read output from ping process
def read_ping_output(process, queue_obj):
    for line in iter(process.stdout.readline, b''):
        if process.poll() is not None:
            break
        decoded_line = line.decode('utf-8', errors='replace').strip()
        if decoded_line:
            queue_obj.put(decoded_line)
    process.stdout.close()

# Function to build ping command based on target type and OS
def get_ping_command(target, target_type):
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
    
    return cmd

# Function to start pinging
def start_ping():
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
    
    # Create appropriate ping command based on target type and OS
    cmd = get_ping_command(target, target_type)
    
    try:
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
        
        # Start thread to read output
        thread = threading.Thread(
            target=read_ping_output, 
            args=(process, st.session_state.ping_queue),
            daemon=True
        )
        thread.start()
        
    except Exception as e:
        st.error(f"Error starting ping: {str(e)}")
        st.session_state.is_pinging = False

# Function to stop pinging
def stop_ping():
    if st.session_state.ping_process:
        # Terminate the ping process
        if platform.system().lower() == "windows":
            subprocess.call(['taskkill', '/F', '/T', '/PID', str(st.session_state.ping_process.pid)])
        else:
            st.session_state.ping_process.terminate()
        st.session_state.ping_process = None
    st.session_state.is_pinging = False

# UI Layout
col1, col2 = st.columns([3, 1])

with col1:
    st.session_state.target = st.text_input(
        "Enter IP Address or Domain Name", 
        help="Enter a valid IPv4/IPv6 address (e.g., 192.168.1.1, 2001:db8::1) or domain name (e.g., example.com)"
    )

with col2:
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
        line = st.session_state.ping_queue.get()
        st.session_state.ping_results.append(line)
        # Keep only the most recent results
        if len(st.session_state.ping_results) > max_displayed_lines:
            st.session_state.ping_results.pop(0)
    
    # Display ping results
    ping_text.code('\n'.join(st.session_state.ping_results))

# Run this in an infinite loop to update the UI
if st.session_state.is_pinging:
    time.sleep(0.1)
    st.rerun()
