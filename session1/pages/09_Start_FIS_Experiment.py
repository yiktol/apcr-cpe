"""
AWS Fault Injection Service (FIS) Experiment Manager.

This Streamlit application allows users to start, monitor, and manage AWS FIS experiments.
"""

import logging
import time
from datetime import datetime

import boto3
import pandas as pd
import plotly.express as px
import streamlit as st

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Set page configuration
st.set_page_config(
    page_title="AWS FIS Experiment Manager",
    page_icon="🧪",
    layout="wide",
    initial_sidebar_state="expanded"
)

def initialize_session_state():
    """Initialize session state variables if they don't exist."""
    if 'experiments' not in st.session_state:
        st.session_state.experiments = []
    if 'auto_refresh' not in st.session_state:
        st.session_state.auto_refresh = False
    if 'refresh_interval' not in st.session_state:
        st.session_state.refresh_interval = 10

def reset_session():
    """Reset the session state to defaults."""
    st.session_state.experiments = []
    st.session_state.auto_refresh = False
    st.session_state.refresh_interval = 10
    logger.info("Session reset successfully")

def safe_timestamp_to_datetime(timestamp):
    """
    Convert various timestamp formats to datetime safely.
    
    Args:
        timestamp: Input timestamp value (datetime, int, float)
        
    Returns:
        datetime object or None if conversion fails
    """
    try:
        if isinstance(timestamp, datetime):
            return timestamp
        elif isinstance(timestamp, (int, float)):
            return datetime.fromtimestamp(timestamp)
        else:
            return None
    except Exception as e:
        logger.error(f"Failed to convert timestamp {timestamp}: {e}")
        return None

def start_experiment(template_id):
    """
    Start a new AWS FIS experiment.
    
    Args:
        template_id: AWS FIS experiment template ID
        
    Returns:
        experiment data dictionary or None if error occurs
    """
    try:
        client = boto3.client('fis')
        response = client.start_experiment(experimentTemplateId=template_id)
        experiment = response['experiment']
        experiment['_startRequestTime'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        st.session_state.experiments.append(experiment)
        logger.info(f"Started experiment with ID: {experiment['id']}")
        return experiment
    except Exception as e:
        logger.error(f"Error starting experiment: {str(e)}")
        return None

def get_experiment_status(experiment_id):
    """
    Get the current status of an experiment.
    
    Args:
        experiment_id: AWS FIS experiment ID
        
    Returns:
        experiment data dictionary or None if error occurs
    """
    try:
        client = boto3.client('fis')
        response = client.get_experiment(id=experiment_id)
        return response['experiment']
    except Exception as e:
        logger.error(f"Error fetching experiment status: {str(e)}")
        return None

def refresh_experiments():
    """Refresh the status of all tracked experiments."""
    if not st.session_state.experiments:
        return
        
    updated_experiments = []
    for experiment in st.session_state.experiments:
        updated_exp = get_experiment_status(experiment['id'])
        if updated_exp:
            # Preserve our custom fields
            if '_startRequestTime' in experiment:
                updated_exp['_startRequestTime'] = experiment['_startRequestTime']
            updated_experiments.append(updated_exp)
        else:
            updated_experiments.append(experiment)  # Keep original if refresh failed
    st.session_state.experiments = updated_experiments
    logger.info(f"Refreshed status of {len(updated_experiments)} experiments")

def format_status_with_duration(experiment):
    """
    Format the experiment status with duration information.
    
    Args:
        experiment: Experiment data dictionary
        
    Returns:
        Formatted status string
    """
    status = experiment.get('state', {}).get('status', 'unknown')
    start_time = experiment.get('_startRequestTime', 'Unknown')
    
    duration = ""
    if experiment.get('startTime') and status != 'completed':
        start = safe_timestamp_to_datetime(experiment['startTime'])
        if start:
            now = datetime.now()
            duration = f" (Running: {(now - start).seconds // 60}m {(now - start).seconds % 60}s)"
    elif experiment.get('startTime') and experiment.get('endTime'):
        start = safe_timestamp_to_datetime(experiment['startTime'])
        end = safe_timestamp_to_datetime(experiment['endTime'])
        if start and end:
            duration = f" (Took: {(end - start).seconds // 60}m {(end - start).seconds % 60}s)"
        
    return f"{status.upper()}{duration}"

def stop_experiment(experiment_id):
    """
    Stop an in-progress experiment.
    
    Args:
        experiment_id: AWS FIS experiment ID
        
    Returns:
        True if successful, False otherwise
    """
    try:
        client = boto3.client('fis')
        client.stop_experiment(id=experiment_id)
        logger.info(f"Stop request sent for experiment {experiment_id}")
        return True
    except Exception as e:
        logger.error(f"Error stopping experiment: {str(e)}")
        return False

def display_sidebar():
    """Display and handle sidebar UI elements."""
    with st.sidebar:
        st.title("Experiment Controls")
        
        # Experiment starters
        st.header("Start New Experiment")
        template_id = st.text_input("Experiment Template ID", "ABCDE1fgHIJkLmNop")
        

        if st.button("Start Experiment", use_container_width=True):
            with st.spinner("Starting experiment..."):
                experiment = start_experiment(template_id)
                if experiment:
                    st.success(f"Started experiment: {experiment['id'][:8]}...")
        
        st.divider()
        
        # Monitoring controls
        st.subheader("Monitoring Controls")
        auto_refresh = st.checkbox("Auto-refresh", st.session_state.auto_refresh)
        if auto_refresh:
            refresh_interval = st.slider(
                "Refresh Interval (seconds)", 
                min_value=5, 
                max_value=60, 
                value=st.session_state.refresh_interval
            )
            st.session_state.refresh_interval = refresh_interval
        
        st.session_state.auto_refresh = auto_refresh
        

        if st.button("Refresh Now", use_container_width=True):
            with st.spinner("Refreshing..."):
                refresh_experiments()
    

        if st.button("Reset Session", use_container_width=True):
            reset_session()
            st.success("Session reset")
            time.sleep(1)
            st.rerun()

def display_experiments():
    """Display experiment data in the main area."""
    st.header("Active Experiments", help="Displays all active and recent experiments")
    
    # Handle auto-refresh if enabled
    if st.session_state.auto_refresh:
        refresh_placeholder = st.empty()
        with refresh_placeholder.container():
            st.info(f"Auto-refreshing data every {st.session_state.refresh_interval} seconds...")
        refresh_experiments()
        time.sleep(0.5)
        refresh_placeholder.empty()
    
    # Display experiments
    if not st.session_state.experiments:
        st.info("No experiments started yet. Use the sidebar to start a new experiment.")
        return
    
    # Create DataFrame for overview
    experiment_data = []
    for exp in st.session_state.experiments:
        # Make sure status is accessible
        status = exp.get('state', {}).get('status', 'unknown')
        
        # Safely handle start time conversion
        start_time_display = "Pending"
        if exp.get('startTime'):
            start_dt = safe_timestamp_to_datetime(exp['startTime'])
            if start_dt:
                start_time_display = start_dt.strftime('%Y-%m-%d %H:%M:%S')
        
        experiment_data.append({
            "ID": exp['id'],
            "Template ID": exp['experimentTemplateId'],
            "Status": status.upper(),
            "Start Time": start_time_display,
            "Request Time": exp.get('_startRequestTime', 'Unknown')
        })
    
    # Display overview table with modern styling
    st.dataframe(
        pd.DataFrame(experiment_data),
        use_container_width=True,
        height=200,
        column_config={
            "ID": st.column_config.TextColumn("Experiment ID"),
            "Status": st.column_config.TextColumn(
                "Status",
                help="Current status of the experiment",
                width="medium",
            ),
        },
        hide_index=True,
    )
    
    # Create tabs for detailed experiment information
    tabs = st.tabs([f"Exp: {exp['id'][-8:]}" for exp in st.session_state.experiments])
    
    for i, tab in enumerate(tabs):
        with tab:
            display_experiment_details(st.session_state.experiments[i])

def display_experiment_details(exp):
    """
    Display detailed information about an experiment.
    
    Args:
        exp: Experiment data dictionary
    """
    # Create columns for key info and actions
    col1, col2, col3 = st.columns([2, 1, 1])
    
    with col1:
        st.subheader(f"Experiment: {exp['id']}")
        st.caption(f"Template: {exp['experimentTemplateId']}")
    
    with col2:
        # Ensure status is accessible
        status = exp.get('state', {}).get('status', 'unknown').upper()
        status_color = {
            'PENDING': 'blue',
            'INITIATING': 'blue',
            'RUNNING': 'orange',
            'COMPLETED': 'green',
            'STOPPING': 'yellow',
            'STOPPED': 'red',
            'FAILED': 'red'
        }.get(status, 'gray')
        
        st.markdown(f"<h3 style='color: {status_color};'>{status}</h3>", unsafe_allow_html=True)
        st.caption(f"Reason: {exp.get('state', {}).get('reason', 'N/A')}")
    
    with col3:
        # Only show stop button for running or initiating experiments
        if exp.get('state', {}).get('status') in ['running', 'initiating']:
            if st.button("⚠️ Stop Experiment", key=f"stop_{exp['id']}", type="primary"):
                with st.spinner("Stopping experiment..."):
                    if stop_experiment(exp['id']):
                        st.success("Stop request sent")
                        time.sleep(1)
                        refresh_experiments()
                    else:
                        st.error("Failed to stop experiment")
    
    # Create tabs for different sections of experiment details
    detail_tabs = st.tabs(["Status", "Actions & Targets", "Timeline", "Raw Data"])
    
    with detail_tabs[0]:
        st.json(exp.get('state', {}))
    
    with detail_tabs[1]:
        # Create columns for actions and targets
        action_col, target_col = st.columns(2)
        
        with action_col:
            st.subheader("Actions")
            if not exp.get('actions'):
                st.info("No action information available")
            else:
                for action_name, action_details in exp.get('actions', {}).items():
                    action_status = action_details.get('state', {}).get('status', 'unknown')
                    status_emoji = {
                        'pending': '⏳',
                        'initiating': '🔄',
                        'running': '🚀',
                        'completed': '✅',
                        'cancelled': '❌',
                        'failed': '💥',
                        'skipped': '⏭️'
                    }.get(action_status, '❓')
                    
                    st.markdown(f"**{status_emoji} {action_name}** - {action_status}")
                    st.caption(f"Action ID: {action_details.get('actionId', 'N/A')}")
                    if action_details.get('state', {}).get('reason'):
                        st.caption(f"Reason: {action_details['state']['reason']}")
        
        with target_col:
            st.subheader("Targets")
            if not exp.get('targets'):
                st.info("No target information available")
            else:
                for target_name, target_details in exp.get('targets', {}).items():
                    st.markdown(f"**{target_name}**")
                    st.caption(f"Type: {target_details.get('resourceType', 'N/A')}")
                    st.caption(f"Selection: {target_details.get('selectionMode', 'N/A')}")
                    if target_details.get('resourceArns'):
                        st.caption(f"Resources: {len(target_details['resourceArns'])} resource(s)")
                        with st.expander("View Resources"):
                            for arn in target_details['resourceArns']:
                                st.text(arn)
    
    with detail_tabs[2]:
        # Timeline visualization with safe type conversion
        if exp.get('startTime'):
            timeline_data = []
            
            # Safely convert timestamps
            start_dt = safe_timestamp_to_datetime(exp['startTime'])
            if start_dt:
                timeline_data.append({
                    'Event': 'Experiment',
                    'Status': 'Started',
                    'Time': start_dt
                })
            
            if exp.get('endTime'):
                end_dt = safe_timestamp_to_datetime(exp['endTime'])
                if end_dt:
                    timeline_data.append({
                        'Event': 'Experiment',
                        'Status': 'Ended',
                        'Time': end_dt
                    })
            
            # Add action points if available
            for action_name, action_details in exp.get('actions', {}).items():
                if action_details.get('startTime'):
                    start_dt = safe_timestamp_to_datetime(action_details['startTime'])
                    if start_dt:
                        timeline_data.append({
                            'Event': action_name,
                            'Status': 'Started',
                            'Time': start_dt
                        })
                if action_details.get('endTime'):
                    end_dt = safe_timestamp_to_datetime(action_details['endTime'])
                    if end_dt:
                        timeline_data.append({
                            'Event': action_name,
                            'Status': 'Ended',
                            'Time': end_dt
                        })
            
            # Create timeline if we have valid data
            if timeline_data:
                timeline_df = pd.DataFrame(timeline_data)
                fig = px.scatter(
                    timeline_df, 
                    x='Time', 
                    y='Event', 
                    color='Status',
                    title="Experiment Timeline", 
                    height=300
                )
                fig.update_layout(
                    xaxis_title="Time",
                    yaxis_title="Event",
                    legend_title="Status"
                )
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("No timeline data available")
        else:
            st.info("Experiment has not started yet - timeline will appear once it begins")
    
    with detail_tabs[3]:
        st.subheader("Raw JSON Data")
        st.json(exp)

def display_footer():
    """Display footer with AWS copyright information."""
    st.markdown("---")
    st.caption("© 2025, Amazon Web Services, Inc. or its affiliates. All rights reserved.")

def main():
    """Main application function."""
    try:
        # Apply custom CSS for better styling
        st.markdown("""
            <style>
            .main .block-container {
                padding-top: 2rem;
                padding-bottom: 2rem;
            }
            .st-emotion-cache-16txtl3 h1 {
                margin-bottom: 0.5rem;
            }
            .stTabs [data-baseweb="tab-list"] button [data-testid="stMarkdownContainer"] p {
                font-size: 1rem;
            }
            </style>
            """, unsafe_allow_html=True)
        
        # Initialize session state
        initialize_session_state()
        
        # App title
        st.title("🧪 AWS Fault Injection Service Experiment Manager")
        
        # Display sidebar content
        display_sidebar()
        
        # Main content area - Monitor experiments
        display_experiments()
        
        # Display footer
        display_footer()
        
        # Handle auto-refresh
        if st.session_state.auto_refresh:
            st.sidebar.caption(f"Auto-refreshing every {st.session_state.refresh_interval} seconds...")
            time.sleep(st.session_state.refresh_interval - 1)  # Sleep for interval minus processing time
            st.rerun()
            
    except Exception as e:
        logger.error(f"Application error: {e}")
        st.error(f"An unexpected error occurred: {str(e)}")
        st.info("Please try refreshing the page or resetting the session.")

if __name__ == "__main__":
    main()
