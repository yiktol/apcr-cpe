import streamlit as st
import boto3
import json
import time
import logging
from datetime import datetime
import utils.authenticate as authenticate
import utils.common as common

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def send_stress_command(target_tag_name, target_tag_value, stress_duration):
    """
    Send stress-ng command to EC2 instances with specified tag.
    
    Args:
        target_tag_name (str): The name of the EC2 tag to target
        target_tag_value (str): The value of the tag to match
        stress_duration (int): Duration in minutes for the stress test
    
    Returns:
        tuple: (bool, str) - Success status and command ID or error message
    """
    try:
        # Initialize AWS SSM client
        ssm_client = boto3.client('ssm')
        
        # Format the stress command with the specified duration
        stress_command = f"stress-ng --matrix 0 -t {stress_duration}m"
        logger.info(f"Preparing stress command: {stress_command}")
        
        # Prepare command document
        command_params = {
            "Targets": [
                {
                    "Key": f"tag:{target_tag_name}",
                    "Values": [target_tag_value]
                }
            ],
            "DocumentName": "AWS-RunShellScript",
            "Comment": "ALB-Target Stress Test",
            "Parameters": {
                "commands": [stress_command]
            }
        }
        
        # Send the command
        response = ssm_client.send_command(**command_params)
        command_id = response['Command']['CommandId']
        logger.info(f"Successfully sent stress command with ID: {command_id}")
        return True, command_id
    except Exception as e:
        logger.error(f"Error sending stress command: {str(e)}")
        return False, str(e)

def stop_stress_command(target_tag_name, target_tag_value):
    """
    Send command to stop stress-ng processes on EC2 instances with specified tag.
    
    Args:
        target_tag_name (str): The name of the EC2 tag to target
        target_tag_value (str): The value of the tag to match
    
    Returns:
        tuple: (bool, str) - Success status and command ID or error message
    """
    try:
        # Initialize AWS SSM client
        ssm_client = boto3.client('ssm')
        
        # Command to kill stress-ng processes
        stop_command = "pkill stress-ng"
        logger.info("Preparing stop stress command")
        
        # Prepare command document
        command_params = {
            "Targets": [
                {
                    "Key": f"tag:{target_tag_name}",
                    "Values": [target_tag_value]
                }
            ],
            "DocumentName": "AWS-RunShellScript",
            "Comment": "Stop ALB-Target Stress Test",
            "Parameters": {
                "commands": [stop_command]
            }
        }
        
        # Send the command
        response = ssm_client.send_command(**command_params)
        command_id = response['Command']['CommandId']
        logger.info(f"Successfully sent stop stress command with ID: {command_id}")
        return True, command_id
    except Exception as e:
        logger.error(f"Error sending stop stress command: {str(e)}")
        return False, str(e)

def get_command_status(command_id):
    """
    Get the status of a command execution.
    
    Args:
        command_id (str): The SSM command ID to check
        
    Returns:
        dict or str: Command status information or error message
    """
    try:
        ssm_client = boto3.client('ssm')
        response = ssm_client.list_command_invocations(
            CommandId=command_id,
            Details=True
        )
        logger.info(f"Successfully retrieved status for command ID: {command_id}")
        return response
    except Exception as e:
        logger.error(f"Error retrieving command status: {str(e)}")
        return str(e)

def display_command_status(command_id, command_time_label):
    """
    Display the status of a command execution.
    
    Args:
        command_id (str): The SSM command ID to check
        command_time_label (str): Label for the command time to display
    """
    with st.spinner("Fetching command status..."):
        status_response = get_command_status(command_id)
        
        if isinstance(status_response, dict):
            st.write(f"Command ID: {command_id}")
            st.write(f"Command sent at: {command_time_label}")
            
            # Create a table to display instance status
            if 'CommandInvocations' in status_response and status_response['CommandInvocations']:
                st.subheader("Target Instances")
                
                for invocation in status_response['CommandInvocations']:
                    st.write(f"**Instance ID**: {invocation['InstanceId']}")
                    st.write(f"**Status**: {invocation['Status']}")
                    
                    if 'CommandPlugins' in invocation:
                        for plugin in invocation['CommandPlugins']:
                            output = plugin.get('Output', 'No output available')
                            st.write(f"**Output**: {output[:500]}")
                            if len(output) > 500:
                                st.write("(Output truncated...)")
            else:
                st.warning("No instances have executed the command yet.")
        else:
            st.error(f"Failed to fetch status: {status_response}")

def init_session_state():
    """Initialize session state variables with default values if they don't exist."""
    if 'tag_name' not in st.session_state:
        st.session_state.tag_name = "Name"
    if 'tag_value' not in st.session_state:
        st.session_state.tag_value = "EC2-AutoScale"
    if 'stress_active' not in st.session_state:
        st.session_state.stress_active = False

def render_about_section():
    """Render the About section in the sidebar."""
    with st.sidebar.expander("About this Application", expanded=False):
        st.write("""
        This application uses AWS Systems Manager (SSM) to send stress test commands to EC2 instances.
        
        You can target instances by tag and apply CPU stress using the stress-ng tool to simulate 
        high load scenarios. This helps test auto-scaling policies, monitor system performance,
        and validate application behavior under load.
        """)

def render_stress_test_form():
    """Render the stress test parameters form."""
    with st.form("stress_test_form"):
        st.header("Stress Test Parameters")
        
        col1, col2 = st.columns(2)
        with col1:
            tag_name = st.text_input("Tag Name", value=st.session_state.tag_name)
        with col2:
            tag_value = st.text_input("Tag Value", value=st.session_state.tag_value)
        
        stress_duration = st.slider("Stress Test Duration (minutes)", 1, 60, 30)
        
        submit_button = st.form_submit_button("Send Stress Test Command")
        
        if submit_button:
            # Update session state with current values
            st.session_state.tag_name = tag_name
            st.session_state.tag_value = tag_value
            
            with st.spinner("Sending command..."):
                success, command_result = send_stress_command(tag_name, tag_value, stress_duration)
                
                if success:
                    st.success(f"Command sent successfully! Command ID: {command_result}")
                    st.session_state.command_id = command_result
                    st.session_state.command_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    st.session_state.stress_active = True
                else:
                    st.error(f"Failed to send command: {command_result}")

def render_stop_button():
    """Render the button to stop active stress test."""
    if st.session_state.stress_active:
        st.markdown("---")
        st.subheader("Stop Stress Test")
        
        if st.button("Stop Stress Test Command", type="primary", use_container_width=True):
            with st.spinner("Stopping stress test..."):
                success, command_result = stop_stress_command(
                    st.session_state.tag_name, 
                    st.session_state.tag_value
                )
                
                if success:
                    st.success(f"Stop command sent successfully! Command ID: {command_result}")
                    st.session_state.stop_command_id = command_result
                    st.session_state.stop_command_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    st.session_state.stress_active = False
                else:
                    st.error(f"Failed to send stop command: {command_result}")

def render_command_monitoring():
    """Render the command monitoring section."""
    st.markdown("---")
    st.header("Command Monitoring")

    # Two columns for checking different commands
    col1, col2 = st.columns(2)

    with col1:
        if st.button("Check Status of Last Start Command"):
            if 'command_id' in st.session_state:
                display_command_status(st.session_state.command_id, st.session_state.command_time)
            else:
                st.warning("No start commands have been sent yet.")

    with col2:
        if st.button("Check Status of Last Stop Command"):
            if 'stop_command_id' in st.session_state:
                display_command_status(st.session_state.stop_command_id, st.session_state.stop_command_time)
            else:
                st.warning("No stop commands have been sent yet.")

def render_help_section():
    """Render the help information section."""
    with st.expander("Usage Instructions"):
        st.write("""
        This application uses AWS Systems Manager (SSM) to send stress test commands to EC2 instances.
        
        The stress test uses the `stress-ng` tool with the `--matrix` parameter which performs 
        matrix operations to stress the CPU.
        
        You can stop the stress test at any time using the "Stop Stress Test Command" button,
        which will kill all stress-ng processes on the target instances.
        
        Make sure the target EC2 instances:
        1. Have the SSM agent installed and running
        2. Have the proper IAM permissions for SSM
        3. Have the stress-ng tool installed
        
        To install stress-ng on Amazon Linux:
        ```
        sudo amazon-linux-extras install epel -y
        sudo yum install stress-ng -y
        ```
        
        To install on Ubuntu:
        ```
        sudo apt update
        sudo apt install -y stress-ng
        ```
        """)

def render_sidebar():
    """Render the sidebar elements."""
    common.render_sidebar()
    
    # Add about section to sidebar
    render_about_section()
    
    # Display stress test status
    st.sidebar.markdown("---")
    st.sidebar.subheader("Stress Test Status")
    if st.session_state.stress_active:
        st.sidebar.error("⚠️ Stress Test ACTIVE")
    else:
        st.sidebar.success("✅ No Active Stress Test")
    
    # Add footer
    st.sidebar.markdown("---")
    st.sidebar.caption("© 2025, Amazon Web Services, Inc. or its affiliates. All rights reserved.")

def render_region_selector():
    """Render the AWS region selector."""
    aws_regions = [
        "us-east-1", "us-east-2", "us-west-1", "us-west-2",
        "eu-west-1", "eu-west-2", "eu-west-3", "eu-central-1",
        "ap-northeast-1", "ap-northeast-2", "ap-southeast-1", "ap-southeast-2",
        "sa-east-1", "ca-central-1"
    ]
    selected_region = st.selectbox("Select AWS Region", aws_regions)
    
    # Create session with selected region
    try:
        st.session_state.boto3_session = boto3.Session(region_name=selected_region)
        logger.info(f"Successfully created boto3 session for region: {selected_region}")
    except Exception as e:
        logger.error(f"Error creating boto3 session: {str(e)}")
        st.error(f"Error setting AWS region: {str(e)}")

def main():
    """Main application function."""
    try:
        # Apply CSS Style
        common.apply_styles()
        
        # Set up page title and description
        st.title("EC2 Stress Test Tool")
        st.write("This application sends stress test commands to EC2 instances with specified tags.")
        
        # Initialize session state
        init_session_state()
        
        # Render the region selector
        render_region_selector()
        
        # Render the main interface sections
        render_stress_test_form()
        render_stop_button()
        render_command_monitoring()
        render_help_section()
        
        # Render the sidebar
        render_sidebar()
        
        # Add footer
        st.caption("© 2025, Amazon Web Services, Inc. or its affiliates. All rights reserved.")
        
    except Exception as e:
        logger.error(f"Unexpected error in main application: {str(e)}", exc_info=True)
        st.error(f"An unexpected error occurred: {str(e)}")

# Main execution flow
if __name__ == "__main__":
    # First check authentication
    is_authenticated = authenticate.login()
    
    # If authenticated, show the main app content
    if is_authenticated:
        main()

