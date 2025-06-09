
"""
Coffee shop sales data generator and sender.

This Streamlit application generates random coffee shop transaction data
and sends it to a REST endpoint. It simulates a point-of-sale system 
generating sales records in real-time.
"""

import json
import logging
import queue
import random
import threading
import time
import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

import requests
import streamlit as st
from faker import Faker

import utils.authenticate as authenticate
import utils.common as common

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

# Thread-safe queues for communication between threads
log_queue = queue.Queue()
sample_data_queue = queue.Queue(maxsize=1)  # Hold the current sample data

# ----------------------
# Setup Functions
# ----------------------

def setup_logging() -> logging.Logger:
    """
    Configure the logging system.
    
    Returns:
        logging.Logger: Configured logger instance
    """
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )
    return logging.getLogger('coffee_sales_generator')

def initialize_session_state() -> None:
    """Initialize all required session state variables."""
    session_vars = {
        'running': False,
        'logs': [],
        'endpoint_url': DEFAULT_ENDPOINT_URL,
        'delay': DEFAULT_DELAY,
        'auto_refresh': True,
        'stop_flag': False,
        'last_sample_time': time.time()
    }
    
    # Initialize variables if they don't exist
    for var, default in session_vars.items():
        if var not in st.session_state:
            st.session_state[var] = default
    
    # Initialize sample_data separately as it requires generation
    if 'sample_data' not in st.session_state:
        fake = Faker()
        st.session_state['sample_data'] = generate_sale_record(fake)

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
    # Remove metadata before sending
    data = {k: v for k, v in record.items() if k != '_meta'}
    
    try:
        headers = {'Content-Type': 'application/json'}
        response = requests.post(
            endpoint_url, 
            data=json.dumps(data), 
            headers=headers, 
            timeout=5
        )
        response.raise_for_status()
        return True, response.status_code
    except requests.exceptions.ConnectionError as e:
        logger.error(f"Connection error: {str(e)}")
        return False, f"Connection error: {str(e)}"
    except requests.exceptions.Timeout as e:
        logger.error(f"Request timed out: {str(e)}")
        return False, f"Request timed out: {str(e)}"
    except requests.exceptions.HTTPError as e:
        logger.error(f"HTTP error: {str(e)}")
        return False, f"HTTP error: {str(e)}"
    except requests.exceptions.RequestException as e:
        logger.error(f"Request error: {str(e)}")
        return False, f"Request error: {str(e)}"
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}")
        return False, f"Unexpected error: {str(e)}"

# ----------------------
# Threading Functions
# ----------------------

def add_to_log_queue(message: str, level: str = "INFO") -> None:
    """
    Add a log message to the log queue for processing in the main thread.
    
    Args:
        message: The log message
        level: The log level (INFO, ERROR, etc.)
    """
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    formatted_log = f"[{timestamp}] [{level}] {message}"
    
    # Add to queue for the main thread to process
    log_queue.put(formatted_log)

def process_log_queue() -> bool:
    """
    Process any logs in the queue and add them to session state logs.
    
    Returns:
        bool: True if logs were updated, False otherwise
    """
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

def update_sample_data() -> bool:
    """
    Update sample data at the same rate as the delay timer.
    
    Returns:
        bool: True if sample data was updated, False otherwise
    """
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

def data_generation_worker(
    delay: float, 
    endpoint_url: str, 
    logger: logging.Logger, 
    stop_flag_event: threading.Event
) -> None:
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

def handle_start_button() -> None:
    """Handle the Start button click."""
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

def handle_stop_button() -> None:
    """Handle the Stop button click."""
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

def handle_clear_logs() -> None:
    """Handle the Clear Logs button click."""
    st.session_state['logs'] = []
    log_message = "Logs cleared"
    st.session_state['logs'].append(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] [INFO] {log_message}")

# ----------------------
# UI Rendering Functions
# ----------------------

def render_page_config() -> None:
    """Configure the Streamlit page settings."""
    st.set_page_config(
        page_title="Coffee Sales Generator",
        page_icon="☕",
        layout="wide"
    )

def render_config_section() -> None:
    """Render the configuration section of the application."""
    st.header("Configuration")
    
    st.text_input(
        "API Endpoint URL", 
        value=st.session_state['endpoint_url'],
        key="config_endpoint_url",
        on_change=lambda: setattr(st.session_state, 'endpoint_url', st.session_state.config_endpoint_url)
    )
    
    st.slider(
        "Delay between records (seconds)", 
        min_value=0.5, 
        max_value=10.0, 
        value=st.session_state['delay'], 
        step=0.5,
        key="config_delay",
        on_change=lambda: setattr(st.session_state, 'delay', st.session_state.config_delay)
    )
    
    col1, col2 = st.columns(2)
    with col1:
        if not st.session_state['running']:
            st.button("▶️ Start", on_click=handle_start_button, use_container_width=True)
        else:
            st.button("⏹️ Stop", on_click=handle_stop_button, use_container_width=True)
    with col2:
        st.button("🗑️ Clear Logs", on_click=handle_clear_logs, use_container_width=True)
    
    # Auto-refresh control
    st.checkbox(
        "Auto-refresh logs",
        value=st.session_state['auto_refresh'],
        key="config_auto_refresh",
        on_change=lambda: setattr(st.session_state, 'auto_refresh', st.session_state.config_auto_refresh)
    )

def render_about_section() -> None:
    """Render the about section of the application."""
    with st.expander("About this Application", expanded=False):
        st.markdown("""
        ## Coffee Shop Sales Data Generator
        
        This application simulates a point-of-sale system generating coffee shop sales records in real-time. 
        It creates random transaction data based on realistic coffee orders and sends them to a configurable 
        API endpoint.
        
        ### Features:
        - Customizable sending rate (delay between records)
        - Real-time log display
        - Sample data preview
        - Configurable API endpoint
        
        This tool is useful for testing data pipeline integrations, streaming analytics, 
        and demonstrating real-time data processing capabilities.
        """)

def render_sample_data() -> None:
    """Render the sample data preview."""
    with st.expander("Sample Data Preview", expanded=True):
        # This will show the current sample data that updates at the same rate as the delay
        st.json(st.session_state['sample_data'])

def render_log_display() -> None:
    """Render the log display section."""
    st.header("Activity Logs")
    
    if st.session_state['logs']:
        for log in reversed(st.session_state['logs'][-MAX_LOGS_DISPLAY:]):
            st.text(log)
        
        st.text(f"Total log entries: {len(st.session_state['logs'])}")
    else:
        st.info("No logs yet. Start the generator to see activity.")

def render_footer() -> None:
    """Render the application footer."""
    st.markdown("---")
    st.markdown("© 2025, Amazon Web Services, Inc. or its affiliates. All rights reserved.")

def render_main_content() -> None:
    """Render the main content area with a 50/50 layout."""
    st.title("☕ Coffee Shop Sales Generator")
    
    # Split the screen into two columns for 50/50 layout
    col1, col2 = st.columns(2)
    
    with col1:
        # Left side - Configuration and about sections
        render_config_section()
        st.markdown("---")
        render_sample_data()
        st.markdown("---")
        render_about_section()
    
    with col2:
        # Right side - Status indicator and log display
        if st.session_state['running']:
            st.success("✅ Generator is running")
        else:
            st.warning("⏸️ Generator is stopped")
        
        # Log display
        render_log_display()
    
    # Footer spans the full width
    render_footer()

# ----------------------
# Main Application Logic
# ----------------------

def main() -> None:
    """Main application entry point."""
    # Setup

    logger = setup_logging()
    initialize_session_state()
    
    with st.sidebar:
    # Render the sidebar
        common.render_sidebar()
        
    # Process any queued logs from the worker thread
    logs_updated = process_log_queue()
    
    # Update sample data at the same rate as the delay timer
    sample_updated = update_sample_data()
    
    # Render UI components
    render_main_content()
    
    # Handle auto-refresh if needed
    if st.session_state['auto_refresh'] and (st.session_state['running'] or logs_updated or sample_updated):
        time.sleep(AUTO_REFRESH_RATE)  # Slightly faster refresh for better real-time feeling
        st.rerun()

if __name__ == "__main__":
    render_page_config()
    try:
        # First check authentication
        is_authenticated = authenticate.login()
        
        # If authenticated, show the main app content
        if is_authenticated:
            main()
    except Exception as e:
        # Log and display any uncaught exceptions
        logger = logging.getLogger('coffee_sales_generator')
        logger.exception(f"Uncaught application error: {str(e)}")
        st.error(f"An unexpected error occurred: {str(e)}")
        st.exception(e)
