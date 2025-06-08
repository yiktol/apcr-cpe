
import streamlit as st
import boto3
import json
import time
from datetime import datetime

def send_stress_command(target_tag_name, target_tag_value, stress_duration):
    """
    Send stress-ng command to EC2 instances with specified tag
    """
    # Initialize AWS SSM client
    ssm_client = boto3.client('ssm')
    
    # Format the stress command with the specified duration
    stress_command = f"stress-ng --matrix 0 -t {stress_duration}m"
    
    # Prepare command document
    command_params = {
        "Targets": [
            {
                "Key": f"tag:{target_tag_name}",
                "Values": [
                    target_tag_value
                ]
            }
        ],
        "DocumentName": "AWS-RunShellScript",
        "Comment": "ALB-Target Stress Test",
        "Parameters": {
            "commands": [
                stress_command
            ]
        }
    }
    
    # Send the command
    try:
        response = ssm_client.send_command(**command_params)
        command_id = response['Command']['CommandId']
        return True, command_id
    except Exception as e:
        return False, str(e)

def stop_stress_command(target_tag_name, target_tag_value):
    """
    Send command to stop stress-ng processes on EC2 instances with specified tag
    """
    # Initialize AWS SSM client
    ssm_client = boto3.client('ssm')
    
    # Command to kill stress-ng processes
    stop_command = "pkill stress-ng"
    
    # Prepare command document
    command_params = {
        "Targets": [
            {
                "Key": f"tag:{target_tag_name}",
                "Values": [
                    target_tag_value
                ]
            }
        ],
        "DocumentName": "AWS-RunShellScript",
        "Comment": "Stop ALB-Target Stress Test",
        "Parameters": {
            "commands": [
                stop_command
            ]
        }
    }
    
    # Send the command
    try:
        response = ssm_client.send_command(**command_params)
        command_id = response['Command']['CommandId']
        return True, command_id
    except Exception as e:
        return False, str(e)

def get_command_status(command_id):
    """
    Get the status of a command execution
    """
    ssm_client = boto3.client('ssm')
    try:
        response = ssm_client.list_command_invocations(
            CommandId=command_id,
            Details=True
        )
        return response
    except Exception as e:
        return str(e)

# Streamlit Application
st.title("EC2 Stress Test Tool")
st.write("This application sends stress test commands to EC2 instances with specified tags.")

# AWS Region selector
aws_regions = [
    "us-east-1", "us-east-2", "us-west-1", "us-west-2",
    "eu-west-1", "eu-west-2", "eu-west-3", "eu-central-1",
    "ap-northeast-1", "ap-northeast-2", "ap-southeast-1", "ap-southeast-2",
    "sa-east-1", "ca-central-1"
]
selected_region = st.selectbox("Select AWS Region", aws_regions)

# Create session with selected region
st.session_state.boto3_session = boto3.Session(region_name=selected_region)

# Store tag parameters in session state for reuse
if 'tag_name' not in st.session_state:
    st.session_state.tag_name = "Name"
if 'tag_value' not in st.session_state:
    st.session_state.tag_value = "EC2-AutoScale"
if 'stress_active' not in st.session_state:
    st.session_state.stress_active = False

# Form for stress test parameters
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

# Stop stress test button
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

# Command monitoring section
st.markdown("---")
st.header("Command Monitoring")

# Two columns for checking different commands
col1, col2 = st.columns(2)

with col1:
    if st.button("Check Status of Last Start Command"):
        if 'command_id' in st.session_state:
            with st.spinner("Fetching command status..."):
                status_response = get_command_status(st.session_state.command_id)
                
                if isinstance(status_response, dict):
                    st.write(f"Command ID: {st.session_state.command_id}")
                    st.write(f"Command sent at: {st.session_state.command_time}")
                    
                    # Create a table to display instance status
                    if 'CommandInvocations' in status_response and status_response['CommandInvocations']:
                        st.subheader("Target Instances")
                        
                        for invocation in status_response['CommandInvocations']:
                            st.write(f"**Instance ID**: {invocation['InstanceId']}")
                            st.write(f"**Status**: {invocation['Status']}")
                            
                            if 'CommandPlugins' in invocation:
                                for plugin in invocation['CommandPlugins']:
                                    st.write(f"**Output**: {plugin.get('Output', 'No output available')[:500]}")
                                    if len(plugin.get('Output', '')) > 500:
                                        st.write("(Output truncated...)")
                    else:
                        st.warning("No instances have executed the command yet.")
                else:
                    st.error(f"Failed to fetch status: {status_response}")
        else:
            st.warning("No start commands have been sent yet.")

with col2:
    if st.button("Check Status of Last Stop Command"):
        if 'stop_command_id' in st.session_state:
            with st.spinner("Fetching stop command status..."):
                status_response = get_command_status(st.session_state.stop_command_id)
                
                if isinstance(status_response, dict):
                    st.write(f"Stop Command ID: {st.session_state.stop_command_id}")
                    st.write(f"Stop Command sent at: {st.session_state.stop_command_time}")
                    
                    # Create a table to display instance status
                    if 'CommandInvocations' in status_response and status_response['CommandInvocations']:
                        st.subheader("Target Instances")
                        
                        for invocation in status_response['CommandInvocations']:
                            st.write(f"**Instance ID**: {invocation['InstanceId']}")
                            st.write(f"**Status**: {invocation['Status']}")
                            
                            if 'CommandPlugins' in invocation:
                                for plugin in invocation['CommandPlugins']:
                                    st.write(f"**Output**: {plugin.get('Output', 'No output available')[:500]}")
                                    if len(plugin.get('Output', '')) > 500:
                                        st.write("(Output truncated...)")
                    else:
                        st.warning("No instances have executed the stop command yet.")
                else:
                    st.error(f"Failed to fetch status: {status_response}")
        else:
            st.warning("No stop commands have been sent yet.")

# Additional information
with st.expander("About this application"):
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

st.sidebar.header("Configuration")
with st.sidebar.expander("AWS Credentials"):
    st.write("""
    This application uses the default AWS credentials configured on your system.
    Make sure you have configured AWS credentials with appropriate permissions.
    
    Required permissions:
    - ssm:SendCommand
    - ssm:ListCommandInvocations
    """)

# Display stress test status
st.sidebar.markdown("---")
st.sidebar.subheader("Stress Test Status")
if st.session_state.stress_active:
    st.sidebar.error("⚠️ Stress Test ACTIVE")
else:
    st.sidebar.success("✅ No Active Stress Test")
