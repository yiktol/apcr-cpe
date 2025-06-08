"""
Coffee shop sales data generator and sender.

This Streamlit application generates random coffee shop transaction data
and sends it to a REST endpoint. It simulates a point-of-sale system 
generating sales records in real-time.
"""

import streamlit as st
import json
import random
import time
import uuid
import logging
from typing import Dict, Any, List, Tuple
import requests
import threading
from faker import Faker
import queue
from datetime import datetime

# ----------------------
# Configuration Constants
# ----------------------

COFFEE_TYPES = ["Flat White", "Americano", "Macchiato", "Cappuccino", "Latte", "Mocha", "Cold Brew"]
MILK_TYPES = ["Full Cream", "Skinny", "Soy", "Almond", "Oat"]
SIZES = ["Small", "Regular", "Large"]
QUANTITIES = [1, 1, 2, 2, 3, 4]  # Weighted towards 1-2
DEFAULT_ENDPOINT_URL = 'https://serverless.aws.yikyakyuk.com/cashier'
DEFAULT_DELAY = 1.0  # seconds
AUTO_REFRESH_RATE = 0.5  # seconds - faster refresh for better real-time feeling
MAX_LOGS_DISPLAY = 1000  # Maximum number of logs to display

# Thread-safe queue for communication between threads
log_queue = queue.Queue()
sample_data_queue = queue.Queue(maxsize=1)  # Hold the current sample data

# ----------------------
# Setup Functions
# ----------------------

def setup_logging():
    """Configure the logging system"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )
    return logging.getLogger('coffee_sales_generator')

def initialize_session_state():
    """Initialize all required session state variables"""
    if 'running' not in st.session_state:
        st.session_state['running'] = False
    if 'logs' not in st.session_state:
        st.session_state['logs'] = []
    if 'endpoint_url' not in st.session_state:
        st.session_state['endpoint_url'] = DEFAULT_ENDPOINT_URL
    if 'delay' not in st.session_state:
        st.session_state['delay'] = DEFAULT_DELAY
    if 'auto_refresh' not in st.session_state:
        st.session_state['auto_refresh'] = True
    if 'stop_flag' not in st.session_state:
        st.session_state['stop_flag'] = False
    if 'sample_data' not in st.session_state:
        fake = Faker()
        st.session_state['sample_data'] = generate_sale_record(fake)
    if 'last_sample_time' not in st.session_state:
        st.session_state['last_sample_time'] = time.time()

# ----------------------
# Data Generation Functions
# ----------------------

def generate_sale_record(faker: Faker) -> Dict[str, Any]:
    """
    Generate a random coffee sale transaction record.
    
    Args:
        faker: Faker instance for generating customer names
    
    Returns:
        Dict[str, Any]: A dictionary containing details of the coffee sale
    """
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    customer_name = faker.first_name()
    sale_id = str(uuid.uuid4())[24:]  # Using last part of UUID
    coffee = random.choice(COFFEE_TYPES)
    milk = random.choice(MILK_TYPES)
    size = random.choice(SIZES)
    qty = random.choice(QUANTITIES)
    
    return {
        "customer": customer_name,
        "saleid": sale_id,
        "timestamp": timestamp,
        "coffee": coffee,
        "milk": milk,
        "size": size,
        "qty": qty,
        # Include metadata for easier log formatting
        "_meta": {
            "log_description": f"ID: {sale_id}, Time: {timestamp}, Customer: {customer_name}, "
                              f"Order: {size} {coffee} with {milk} milk, Quantity: {qty}"
        }
    }
    

def send_message(record: Dict[str, Any], endpoint_url: str, logger: logging.Logger) -> Tuple[bool, Any]:
    """
    Send a coffee sale record to the endpoint.
    
    Args:
        record: The coffee sale record to send
        endpoint_url: The URL to send data to
        logger: Logger instance
        
    Returns:
        Tuple[bool, Any]: (Success status, Response or error message)
    """
    data = json.dumps({k: v for k, v in record.items() if k != '_meta'})
    headers = {'Content-Type': 'application/json'}
    
    try:
        response = requests.post(endpoint_url, data=data, headers=headers, timeout=5)
        response.raise_for_status()
        return True, response.status_code
    except requests.exceptions.RequestException as e:
        return False, str(e)

# ----------------------
# Threading Functions
# ----------------------

def add_to_log_queue(message: str, level: str = "INFO"):
    """
    Add a log message to the log queue for processing in the main thread
    
    Args:
        message: The log message
        level: The log level (INFO, ERROR, etc.)
    """
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    formatted_log = f"[{timestamp}] [{level}] {message}"
    
    # Add to queue for the main thread to process
    log_queue.put(formatted_log)

def process_log_queue():
    """Process any logs in the queue and add them to session state logs"""
    updated = False
    while not log_queue.empty():
        try:
            log_message = log_queue.get_nowait()
            st.session_state['logs'].append(log_message)
            updated = True
            
            # Keep logs within max length
            if len(st.session_state['logs']) > MAX_LOGS_DISPLAY:
                st.session_state['logs'] = st.session_state['logs'][-MAX_LOGS_DISPLAY:]
        except queue.Empty:
            break
    return updated

def update_sample_data():
    """Update sample data at the same rate as the delay timer"""
    now = time.time()
    elapsed = now - st.session_state['last_sample_time']
    
    # Check if it's time to update based on the delay setting
    if elapsed >= st.session_state['delay']:
        # Try to get new sample data if available
        try:
            if not sample_data_queue.empty():
                st.session_state['sample_data'] = sample_data_queue.get_nowait()
            # If queue is empty but enough time has passed, generate a new one
            else:
                fake = Faker()
                st.session_state['sample_data'] = generate_sale_record(fake)
            
            st.session_state['last_sample_time'] = now
            return True
        except queue.Empty:
            pass
    
    return False

def data_generation_worker(delay: float, endpoint_url: str, logger: logging.Logger, stop_flag_event: threading.Event):
    """
    Worker function to generate and send data at regular intervals.
    
    Args:
        delay: Seconds to wait between sending records
        endpoint_url: The URL to send data to
        logger: Logger instance
        stop_flag_event: Event to signal when to stop
    """
    fake = Faker()
    add_to_log_queue(f"Data generation thread started with {delay}s delay to {endpoint_url}")
    logger.info(f"Data generation thread started with {delay}s delay to {endpoint_url}")
    
    try:
        while not stop_flag_event.is_set():
            # Generate a record
            record = generate_sale_record(fake)
            
            # Update the sample data queue (non-blocking)
            try:
                # Clear the queue if it has old data
                while not sample_data_queue.empty():
                    sample_data_queue.get_nowait()
                
                # Add the new data
                sample_data_queue.put_nowait(record)
            except queue.Full:
                pass  # If queue is full, just skip updating sample data
            
            # Log the generated sale with _meta information
            sale_log = record['_meta']['log_description']
            logger.info(sale_log)
            add_to_log_queue(sale_log)
                
            # Send the record
            success, result = send_message(record, endpoint_url, logger)

            if success:
                send_log = f"Message sent successfully. Status code: {result}"
                logger.info(send_log)
                add_to_log_queue(send_log)
            else:
                error_log = f"Failed to send message: {result}"
                logger.error(error_log)
                add_to_log_queue(error_log, "ERROR")
            
            # Wait before next iteration with periodic checks for stop signal
            for _ in range(int(delay * 10)):  # Check stop flag more frequently
                if stop_flag_event.is_set():
                    break
                time.sleep(0.1)
    except Exception as e:
        error_msg = f"Unexpected error in data generation thread: {str(e)}"
        logger.exception(error_msg)
        add_to_log_queue(error_msg, "ERROR")
    finally:
        add_to_log_queue("Data generation thread stopped")
        logger.info("Data generation thread stopped")

# ----------------------
# UI Action Handlers
# ----------------------

def handle_start_button():
    """Handle the Start button click"""
    if st.session_state['running']:
        return
    
    st.session_state['running'] = True
    st.session_state['stop_flag'] = False
    
    delay = st.session_state['delay']
    endpoint_url = st.session_state['endpoint_url']
    
    logger = logging.getLogger('coffee_sales_generator')
    
    # Create an event for thread communication
    stop_flag_event = threading.Event()
    
    # Store the event in session state
    st.session_state['stop_flag_event'] = stop_flag_event
    
    # Create and start thread
    thread = threading.Thread(
        target=data_generation_worker,
        args=(delay, endpoint_url, logger, stop_flag_event),
        daemon=True
    )
    thread.start()
    
    # Store thread for potential cleanup
    st.session_state['generator_thread'] = thread
    
    log_message = f"Started data generation with {delay}s delay to {endpoint_url}"
    logger.info(log_message)
    st.session_state['logs'].append(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] [INFO] {log_message}")

def handle_stop_button():
    """Handle the Stop button click"""
    if not st.session_state['running']:
        return
    
    # Signal the thread to stop
    if 'stop_flag_event' in st.session_state:
        st.session_state['stop_flag_event'].set()
    
    st.session_state['running'] = False
    st.session_state['stop_flag'] = True
    
    log_message = "Stopping data generation..."
    logger = logging.getLogger('coffee_sales_generator')
    logger.info(log_message)
    st.session_state['logs'].append(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] [INFO] {log_message}")

def handle_clear_logs():
    """Handle the Clear Logs button click"""
    st.session_state['logs'] = []
    log_message = "Logs cleared"
    st.session_state['logs'].append(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] [INFO] {log_message}")

# ----------------------
# UI Rendering Functions
# ----------------------

def render_page_config():
    """Configure the Streamlit page settings"""
    st.set_page_config(
        page_title="Coffee Sales Generator",
        page_icon="☕",
        layout="wide"
    )

def render_sidebar():
    """Render the sidebar configuration elements"""
    with st.sidebar:
        st.header("Configuration")
        
        endpoint_url = st.text_input(
            "API Endpoint URL", 
            value=st.session_state['endpoint_url']
        )
        if endpoint_url != st.session_state['endpoint_url']:
            st.session_state['endpoint_url'] = endpoint_url
        
        delay = st.slider(
            "Delay between records (seconds)", 
            min_value=0.5, 
            max_value=10.0, 
            value=st.session_state['delay'], 
            step=0.5
        )
        if delay != st.session_state['delay']:
            st.session_state['delay'] = delay
        
        col1, col2 = st.columns(2)
        with col1:
            if not st.session_state['running']:
                st.button("▶️ Start", on_click=handle_start_button, use_container_width=True)
            else:
                st.button("⏹️ Stop", on_click=handle_stop_button, use_container_width=True)
        with col2:
            st.button("🗑️ Clear Logs", on_click=handle_clear_logs, use_container_width=True)
        
        # Auto-refresh control
        auto_refresh = st.checkbox(
            "Auto-refresh logs", 
            value=st.session_state['auto_refresh']
        )
        if auto_refresh != st.session_state['auto_refresh']:
            st.session_state['auto_refresh'] = auto_refresh
        
        with st.expander("Sample Data Preview", expanded=True):
            # This will show the current sample data that updates at the same rate as the delay
            st.json(st.session_state['sample_data'])

def render_main_content():
    """Render the main content area"""
    st.title("☕ Coffee Shop Sales Generator")
    
    # Status indicator
    status = st.empty()
    if st.session_state['running']:
        status.success("✅ Generator is running")
    else:
        status.warning("⏸️ Generator is stopped")
    
    # Log display
    st.subheader("Activity Logs")
    log_container = st.container()
    
    with log_container:
        if st.session_state['logs']:
            for log in reversed(st.session_state['logs'][-MAX_LOGS_DISPLAY:]):
                st.text(log)
        else:
            st.info("No logs yet. Start the generator to see activity.")
    
    # Display total records count
    if st.session_state['logs']:
        st.text(f"Total log entries: {len(st.session_state['logs'])}")

# ----------------------
# Main Application Logic
# ----------------------

def main():
    
    """Main application entry point"""
    # Setup
    render_page_config()

    logger = setup_logging()
    initialize_session_state()
    
    # Process any queued logs from the worker thread
    logs_updated = process_log_queue()
    
    # Update sample data at the same rate as the delay timer
    sample_updated = update_sample_data()
    
    # Render UI components
    render_sidebar()
    render_main_content()
    
    # Handle auto-refresh if needed
    if st.session_state['auto_refresh'] and (st.session_state['running'] or logs_updated or sample_updated):
        time.sleep(AUTO_REFRESH_RATE)  # Slightly faster refresh for better real-time feeling
        st.rerun()

if __name__ == "__main__":
    main()
