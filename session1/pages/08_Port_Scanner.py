import streamlit as st
import socket
import concurrent.futures
import re
import time
import pandas as pd
import ipaddress

# Set page configuration
st.set_page_config(
    page_title="Network Port Scanner",
    page_icon="🔍",
    layout="wide"
)

st.title("🔍 Network Port Scanner")
st.markdown("Scan for open ports on IPv4/IPv6 addresses or domain names")

# Initialize session state variables
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

# Function to validate IPv4 address
def is_valid_ipv4(ip):
    try:
        ipaddress.IPv4Address(ip)
        return True
    except ValueError:
        return False

# Function to validate IPv6 address
def is_valid_ipv6(ip):
    try:
        ipaddress.IPv6Address(ip)
        return True
    except ValueError:
        return False

# Function to validate domain name
def is_valid_domain(domain):
    if len(domain) > 255:
        return False
    domain_pattern = re.compile(
        r"^(?:[a-zA-Z0-9](?:[a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?\.)+[a-zA-Z]{2,}$"
    )
    return bool(domain_pattern.match(domain))

# Function to validate target input
def validate_target(target):
    if is_valid_ipv4(target):
        return "IPv4"
    elif is_valid_ipv6(target):
        return "IPv6"
    elif is_valid_domain(target):
        return "Domain"
    else:
        return False

# Function to scan a single port
def scan_port(target, port, timeout=1):
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
            except socket.error:
                continue
        return False
    except socket.gaierror:
        st.error(f"Could not resolve hostname: {target}")
        return None
    except Exception as e:
        st.error(f"Error scanning {target}:{port} - {str(e)}")
        return None

# Function to perform scan of multiple ports with progress tracking
def perform_scan(target, start_port, end_port, max_workers=50, timeout=1):
    st.session_state.scan_results = []
    st.session_state.scanning = True
    st.session_state.total_ports = end_port - start_port + 1
    st.session_state.scanned_ports = 0
    
    ports_to_scan = range(start_port, end_port + 1)
    
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
            except Exception as e:
                st.session_state.scan_results.append({
                    "Port": port,
                    "Status": f"Error: {str(e)}",
                    "Service": "N/A"
                })
            
            # Update progress
            st.session_state.scanned_ports += 1
            st.session_state.progress = st.session_state.scanned_ports / st.session_state.total_ports
            st.session_state.progress_text = f"Scanning port {port}... ({st.session_state.scanned_ports}/{st.session_state.total_ports})"
    
    # Sort results by port number
    st.session_state.scan_results = sorted(st.session_state.scan_results, key=lambda x: x["Port"])
    st.session_state.scanning = False

# Function to scan specific ports (for preset options)
def scan_specific_ports(target, ports_list, timeout=1):
    st.session_state.scan_results = []
    st.session_state.scanning = True
    st.session_state.total_ports = len(ports_list)
    st.session_state.scanned_ports = 0
    
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
            except Exception as e:
                st.session_state.scan_results.append({
                    "Port": port,
                    "Status": f"Error: {str(e)}",
                    "Service": "N/A"
                })
            
            # Update progress
            st.session_state.scanned_ports += 1
            st.session_state.progress = st.session_state.scanned_ports / st.session_state.total_ports
            st.session_state.progress_text = f"Scanning port {port}... ({st.session_state.scanned_ports}/{st.session_state.total_ports})"
    
    # Sort results by port number
    st.session_state.scan_results = sorted(st.session_state.scan_results, key=lambda x: x["Port"])
    st.session_state.scanning = False

# Callback functions for preset buttons
def set_well_known_ports():
    st.session_state.selected_port_range = "well_known"
    
def set_registered_ports():
    st.session_state.selected_port_range = "registered"
    
def set_common_web_ports():
    st.session_state.selected_port_range = "common_web"

# UI layout
col1, col2 = st.columns([2, 1])

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

# Set default port values based on selected range
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

with col1:
    start_port = st.number_input("Start Port", min_value=1, max_value=65535, value=default_start)

with col2:
    end_port = st.number_input("End Port", min_value=1, max_value=65535, value=default_end)

with col3:
    scan_options = st.expander("Scan Options")
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

# Common web ports list
common_web_ports = [80, 443, 8080, 8443, 3000, 5000, 8000, 8888]

# Scan button
if st.button("Scan", type="primary", disabled=not target or not target_type):
    if end_port < start_port:
        st.error("End port must be greater than or equal to start port")
    else:
        # Handle special case for common web ports
        if st.session_state.selected_port_range == "common_web":
            with st.spinner(f"Scanning common web ports on {target}..."):
                scan_specific_ports(target, common_web_ports, timeout)
        else:
            # Normal port range scan
            with st.spinner(f"Scanning ports {start_port}-{end_port} on {target}..."):
                perform_scan(target, start_port, end_port, max_workers, timeout)

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
                    file_name=f"port_scan_{target}_{int(time.time())}.csv",
                    mime="text/csv",
                )
            else:
                st.download_button(
                    label="Download JSON",
                    data=df.to_json(orient="records"),
                    file_name=f"port_scan_{target}_{int(time.time())}.json",
                    mime="application/json",
                )
    else:
        st.info("No open ports found with current filter settings.")

# Footer with warnings
st.markdown("---")
st.warning("""
**Disclaimer:** Only scan networks and systems you have permission to scan.
Unauthorized port scanning may be illegal in some jurisdictions and against the policies of some network providers.
""")
