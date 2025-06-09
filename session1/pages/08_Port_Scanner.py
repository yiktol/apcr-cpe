
"""
Network Port Scanner Application

This Streamlit application allows users to scan ports on IPv4/IPv6 addresses or domain names.
It provides features for scanning custom port ranges or using predefined port ranges, 
with concurrent scanning capabilities and result visualization.
"""

import concurrent.futures
import ipaddress
import logging
import re
import socket
import time
from typing import Dict, List, Optional, Tuple, Union

import pandas as pd
import streamlit as st

import utils.authenticate as authenticate
import utils.common as common

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Common port descriptions
COMMON_PORTS = {
    21: "FTP",
    22: "SSH",
    23: "Telnet",
    25: "SMTP",
    53: "DNS",
    80: "HTTP",
    110: "POP3",
    143: "IMAP",
    443: "HTTPS",
    465: "SMTPS",
    587: "SMTP (submission)",
    993: "IMAPS",
    995: "POP3S",
    1433: "Microsoft SQL Server",
    1521: "Oracle",
    3306: "MySQL",
    3389: "RDP",
    5432: "PostgreSQL",
    5900: "VNC",
    6379: "Redis",
    8080: "HTTP Alternate",
    8443: "HTTPS Alternate",
    27017: "MongoDB"
}

# List of common web ports
COMMON_WEB_PORTS = [80, 443, 8080, 8443, 3000, 5000, 8000, 8888]


def initialize_session_state() -> None:
    """Initialize session state variables."""
    if 'scan_results' not in st.session_state:
        st.session_state.scan_results = []
    if 'scanning' not in st.session_state:
        st.session_state.scanning = False
    if 'progress' not in st.session_state:
        st.session_state.progress = 0
    if 'progress_text' not in st.session_state:
        st.session_state.progress_text = ""
    if 'total_ports' not in st.session_state:
        st.session_state.total_ports = 0
    if 'scanned_ports' not in st.session_state:
        st.session_state.scanned_ports = 0
    if 'selected_port_range' not in st.session_state:
        st.session_state.selected_port_range = "custom"


def is_valid_ipv4(ip: str) -> bool:
    """
    Validate if the input string is a valid IPv4 address.
    
    Args:
        ip: String to validate as IPv4 address
        
    Returns:
        bool: True if valid IPv4 address, False otherwise
    """
    try:
        ipaddress.IPv4Address(ip)
        return True
    except ValueError:
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
        ipaddress.IPv6Address(ip)
        return True
    except ValueError:
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
    Validate the target input to determine if it's a valid IPv4, IPv6, or domain name.
    
    Args:
        target: String to validate
        
    Returns:
        str or bool: Returns "IPv4", "IPv6", "Domain" if valid, or False otherwise
    """
    if is_valid_ipv4(target):
        return "IPv4"
    elif is_valid_ipv6(target):
        return "IPv6"
    elif is_valid_domain(target):
        return "Domain"
    else:
        return False


def scan_port(target: str, port: int, timeout: float = 1) -> Optional[bool]:
    """
    Scan a single port on the target host.
    
    Args:
        target: IP address or domain name to scan
        port: Port number to scan
        timeout: Connection timeout in seconds
        
    Returns:
        bool or None: True if port is open, False if closed, None on error
    """
    try:
        # Get address info for both IPv4 and IPv6
        for res in socket.getaddrinfo(target, port, socket.AF_UNSPEC, socket.SOCK_STREAM):
            af, socktype, proto, canonname, sa = res
            try:
                s = socket.socket(af, socktype, proto)
                s.settimeout(timeout)
                result = s.connect_ex(sa)
                s.close()
                if result == 0:
                    return True
            except socket.error as e:
                logger.debug(f"Socket error scanning {target}:{port} - {str(e)}")
                continue
        return False
    except socket.gaierror as e:
        logger.error(f"Could not resolve hostname: {target} - {str(e)}")
        return None
    except Exception as e:
        logger.error(f"Error scanning {target}:{port} - {str(e)}")
        return None


def perform_scan(target: str, start_port: int, end_port: int, max_workers: int = 50, timeout: float = 1) -> None:
    """
    Perform a scan of multiple ports with progress tracking.
    
    Args:
        target: IP address or domain name to scan
        start_port: Beginning of port range to scan
        end_port: End of port range to scan
        max_workers: Maximum number of concurrent workers
        timeout: Connection timeout in seconds
    """
    try:
        st.session_state.scan_results = []
        st.session_state.scanning = True
        st.session_state.total_ports = end_port - start_port + 1
        st.session_state.scanned_ports = 0
        
        ports_to_scan = range(start_port, end_port + 1)
        
        logger.info(f"Starting scan on {target} ports {start_port}-{end_port} with {max_workers} workers")
        
        with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
            # Submit all scan tasks
            future_to_port = {
                executor.submit(scan_port, target, port, timeout): port
                for port in ports_to_scan
            }
            
            # Process results as they complete
            for future in concurrent.futures.as_completed(future_to_port):
                port = future_to_port[future]
                try:
                    is_open = future.result()
                    if is_open:
                        service = COMMON_PORTS.get(port, "Unknown")
                        st.session_state.scan_results.append({
                            "Port": port,
                            "Status": "Open",
                            "Service": service
                        })
                        logger.info(f"Found open port {port} on {target}")
                except Exception as e:
                    st.session_state.scan_results.append({
                        "Port": port,
                        "Status": f"Error: {str(e)}",
                        "Service": "N/A"
                    })
                    logger.error(f"Error processing port {port} on {target}: {str(e)}")
                
                # Update progress
                st.session_state.scanned_ports += 1
                st.session_state.progress = st.session_state.scanned_ports / st.session_state.total_ports
                st.session_state.progress_text = f"Scanning port {port}... ({st.session_state.scanned_ports}/{st.session_state.total_ports})"
        
        # Sort results by port number
        st.session_state.scan_results = sorted(st.session_state.scan_results, key=lambda x: x["Port"])
        logger.info(f"Scan completed for {target}. Found {len([r for r in st.session_state.scan_results if r['Status'] == 'Open'])} open ports")
    
    except Exception as e:
        logger.error(f"Error during port scanning: {str(e)}")
        st.error(f"An error occurred during scanning: {str(e)}")
    finally:
        st.session_state.scanning = False


def scan_specific_ports(target: str, ports_list: List[int], timeout: float = 1) -> None:
    """
    Scan specific ports on the target host.
    
    Args:
        target: IP address or domain name to scan
        ports_list: List of specific ports to scan
        timeout: Connection timeout in seconds
    """
    try:
        st.session_state.scan_results = []
        st.session_state.scanning = True
        st.session_state.total_ports = len(ports_list)
        st.session_state.scanned_ports = 0
        
        logger.info(f"Starting specific port scan on {target} for {len(ports_list)} ports")
        
        with concurrent.futures.ThreadPoolExecutor(max_workers=min(50, len(ports_list))) as executor:
            # Submit all scan tasks
            future_to_port = {
                executor.submit(scan_port, target, port, timeout): port
                for port in ports_list
            }
            
            # Process results as they complete
            for future in concurrent.futures.as_completed(future_to_port):
                port = future_to_port[future]
                try:
                    is_open = future.result()
                    if is_open:
                        service = COMMON_PORTS.get(port, "Unknown")
                        st.session_state.scan_results.append({
                            "Port": port,
                            "Status": "Open", 
                            "Service": service
                        })
                        logger.info(f"Found open port {port} on {target}")
                except Exception as e:
                    st.session_state.scan_results.append({
                        "Port": port,
                        "Status": f"Error: {str(e)}",
                        "Service": "N/A"
                    })
                    logger.error(f"Error processing port {port} on {target}: {str(e)}")
                
                # Update progress
                st.session_state.scanned_ports += 1
                st.session_state.progress = st.session_state.scanned_ports / st.session_state.total_ports
                st.session_state.progress_text = f"Scanning port {port}... ({st.session_state.scanned_ports}/{st.session_state.total_ports})"
        
        # Sort results by port number
        st.session_state.scan_results = sorted(st.session_state.scan_results, key=lambda x: x["Port"])
        logger.info(f"Specific port scan completed for {target}. Found {len([r for r in st.session_state.scan_results if r['Status'] == 'Open'])} open ports")
    
    except Exception as e:
        logger.error(f"Error during specific port scanning: {str(e)}")
        st.error(f"An error occurred during scanning: {str(e)}")
    finally:
        st.session_state.scanning = False


def set_well_known_ports() -> None:
    """Set port range to well-known ports (1-1023)."""
    st.session_state.selected_port_range = "well_known"
    
    
def set_registered_ports() -> None:
    """Set port range to registered ports (1024-49151)."""
    st.session_state.selected_port_range = "registered"
    
    
def set_common_web_ports() -> None:
    """Set port range to common web ports."""
    st.session_state.selected_port_range = "common_web"


def create_sidebar() -> None:
    """Create the application sidebar with about information."""
    with st.sidebar:

        common.render_sidebar()

        with st.expander("About this Application", expanded=False):
            st.markdown("""
            ## Network Port Scanner
            
            This application allows you to scan for open ports on IPv4/IPv6 addresses or domain names.
            
            **Features:**
            - Scan custom port ranges
            - Use predefined port ranges (well-known, registered, common web ports)
            - Concurrent scanning for faster results
            - Export results in CSV or JSON format
            
            **Note:** Always ensure you have permission to scan the target network or system.
            """)


def get_default_port_values() -> Tuple[int, int]:
    """
    Get default port values based on the selected port range.
    
    Returns:
        Tuple[int, int]: Default start and end port values
    """
    if st.session_state.selected_port_range == "well_known":
        default_start = 1
        default_end = 1023
    elif st.session_state.selected_port_range == "registered":
        default_start = 1024
        default_end = 49151
    elif st.session_state.selected_port_range == "common_web":
        default_start = 80
        default_end = 80  # Will be handled specially
    else:  # custom
        default_start = 1
        default_end = 1000
    
    return default_start, default_end


def render_ui() -> Dict:
    """
    Render the user interface components.
    
    Returns:
        Dict: Dictionary containing the UI input values
    """
    col1, col2, col3 = st.columns([2, 1, 1])

    with col1:
        target = st.text_input("Target IP/Domain",
                            help="Enter a valid IPv4/IPv6 address or domain name")

    with col2:
        target_type = ""
        if target:
            target_type = validate_target(target)
            if target_type:
                st.success(f"Valid {target_type}")
            else:
                st.error("Invalid target")

    # Port range selection
    col1, col2, col3 = st.columns([1, 1, 2])

    # Get default port values
    default_start, default_end = get_default_port_values()

    with col1:
        start_port = st.number_input("Start Port", min_value=1, max_value=65535, value=default_start)

    with col2:
        end_port = st.number_input("End Port", min_value=1, max_value=65535, value=default_end)

    col1, col2, col3 = st.columns([2, 1, 1])
    with col1:
        scan_options = st.expander("Scan Options", expanded=True)
        with scan_options:
            col_a, col_b = st.columns(2)
            with col_a:
                timeout = st.slider("Timeout (seconds)", min_value=0.1, max_value=5.0, value=1.0, step=0.1)
            with col_b:
                max_workers = st.slider("Concurrent Scans", min_value=10, max_value=100, value=50)
            
            st.text("Preset Port Ranges:")
            preset_col1, preset_col2, preset_col3, preset_col4 = st.columns(4)
            
            with preset_col1:
                if st.button("Well-known Ports (1-1023)", on_click=set_well_known_ports):
                    pass
                    
            with preset_col2:
                if st.button("Registered Ports (1024-49151)", on_click=set_registered_ports):
                    pass
                    
            with preset_col3:
                if st.button("Common Web Ports", on_click=set_common_web_ports):
                    pass

    # Scan button
    if st.button("Scan", type="primary", disabled=not target or not target_type):
        if end_port < start_port:
            st.error("End port must be greater than or equal to start port")
            return {"valid": False}
        else:
            return {
                "valid": True,
                "target": target,
                "target_type": target_type,
                "start_port": start_port,
                "end_port": end_port,
                "timeout": timeout,
                "max_workers": max_workers
            }
    return {"valid": False}


def show_progress_and_results() -> None:
    """Display scan progress and results."""
    # Show progress while scanning
    if st.session_state.scanning:
        st.progress(st.session_state.progress)
        st.text(st.session_state.progress_text)

    # Display results
    if st.session_state.scan_results:
        st.subheader("Scan Results")
        
        # Prepare DataFrame for display
        df = pd.DataFrame(st.session_state.scan_results)
        
        # Count open ports
        open_ports_count = sum(1 for result in st.session_state.scan_results if result["Status"] == "Open")
        
        # Display summary
        st.metric(label="Open Ports Found", value=open_ports_count)
        
        # Filter options
        show_only_open = st.checkbox("Show only open ports", value=True)
        
        # Apply filters
        if show_only_open:
            df = df[df["Status"] == "Open"]
        
        if not df.empty:
            st.dataframe(df, use_container_width=True)
            
            # Export options
            col1, col2 = st.columns([1, 4])
            with col1:
                export_format = st.selectbox("Export format", ["CSV", "JSON"])
            with col2:
                if export_format == "CSV":
                    st.download_button(
                        label="Download CSV",
                        data=df.to_csv(index=False),
                        file_name=f"port_scan_{st.session_state.get('target', 'unknown')}_{int(time.time())}.csv",
                        mime="text/csv",
                    )
                else:
                    st.download_button(
                        label="Download JSON",
                        data=df.to_json(orient="records"),
                        file_name=f"port_scan_{st.session_state.get('target', 'unknown')}_{int(time.time())}.json",
                        mime="application/json",
                    )
        else:
            st.info("No open ports found with current filter settings.")


def show_footer_and_disclaimer() -> None:
    """Display footer with disclaimer and copyright notice."""
    st.markdown("---")
    st.warning("""
    **Disclaimer:** Only scan networks and systems you have permission to scan.
    Unauthorized port scanning may be illegal in some jurisdictions and against the policies of some network providers.
    """)
    
    st.markdown("© 2025, Amazon Web Services, Inc. or its affiliates. All rights reserved.", help="Copyright notice")


def main() -> None:
    """Main application function."""
    try:

        # Initialize session state
        initialize_session_state()

        # Display sidebar
        create_sidebar()

        # Display main title
        st.title("🔍 Network Port Scanner")
        st.markdown("Scan for open ports on IPv4/IPv6 addresses or domain names")

        # Render UI and get input values
        inputs = render_ui()
        
        # Store target for filename use in exports
        if inputs.get("valid") and "target" in inputs:
            st.session_state.target = inputs["target"]

        # Perform scan if inputs are valid
        if inputs.get("valid"):
            # Handle special case for common web ports
            if st.session_state.selected_port_range == "common_web":
                with st.spinner(f"Scanning common web ports on {inputs['target']}..."):
                    scan_specific_ports(inputs['target'], COMMON_WEB_PORTS, inputs['timeout'])
            else:
                # Normal port range scan
                with st.spinner(f"Scanning ports {inputs['start_port']}-{inputs['end_port']} on {inputs['target']}..."):
                    perform_scan(inputs['target'], inputs['start_port'], inputs['end_port'], 
                                inputs['max_workers'], inputs['timeout'])

        # Show scan progress and results
        show_progress_and_results()
        
        # Show footer with disclaimer
        show_footer_and_disclaimer()
        
    except Exception as e:
        logger.exception(f"Unexpected error in main application: {str(e)}")
        st.error(f"An unexpected error occurred: {str(e)}")
        st.error("Please try refreshing the page or contact support if the issue persists.")


if __name__ == "__main__":
    # Set page configuration
    st.set_page_config(
        page_title="Network Port Scanner",
        page_icon="🔍",
        layout="wide"
    )
    try:
        # First check authentication
        is_authenticated = authenticate.login()
        
        # If authenticated, show the main app content
        if is_authenticated:
            main()
    except Exception as e:
        logger.exception(f"Critical application error: {str(e)}")
        st.error("A critical error occurred during application startup.")
        st.error(f"Error details: {str(e)}")
