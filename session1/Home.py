
# app.py
import streamlit as st
import pandas as pd
import plotly.express as px
import matplotlib.pyplot as plt
import uuid
from PIL import Image
import base64
import time
import random

# Set page configuration
st.set_page_config(
    page_title="AWS Cloud Practitioner - Session 1",
    page_icon="☁️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# AWS Color Scheme
AWS_COLORS = {
    "primary": "#232F3E",     # AWS Dark Blue
    "secondary": "#FF9900",   # AWS Orange
    "accent": "#0073BB",      # AWS Light Blue
    "light": "#FFFFFF",       # White
    "dark": "#161E2D"         # Darker Blue
}

# Apply custom styles
def apply_custom_styles():
    st.markdown("""
    <style>
    .main {
        background-color: #F8F8F8;
    }
    .stTabs [data-baseweb="tab-list"] {
        gap: 10px;
    }
    .stTabs [data-baseweb="tab"] {
        background-color: #FFFFFF;
        border-radius: 4px 4px 0px 0px;
        padding: 10px 16px;
        font-weight: 600;
    }
    .stTabs [aria-selected="true"] {
        background-color: #FF9900 !important;
        color: white !important;
    }
    h1, h2, h3 {
        color: #232F3E;
    }
    .highlight {
        background-color: #FF9900;
        padding: 5px 10px;
        border-radius: 4px;
        color: white;
    }
    .info-box {
        background-color: #E6F7FF;
        padding: 15px;
        border-left: 5px solid #0073BB;
        border-radius: 4px;
        margin: 10px 0;
    }
    .footer {
        position: fixed;
        left: 0;
        bottom: 0;
        width: 100%;
        background-color: #232F3E;
        color: white;
        text-align: center;
        padding: 10px;
        font-size: 14px;
    }
    </style>
    """, unsafe_allow_html=True)

# Initialize session state
def initialize_session():
    if 'session_id' not in st.session_state:
        st.session_state['session_id'] = str(uuid.uuid4())
    
    if 'knowledge_check_progress' not in st.session_state:
        st.session_state['knowledge_check_progress'] = 0
        
    if 'knowledge_check_answers' not in st.session_state:
        st.session_state['knowledge_check_answers'] = {}
    
    if 'knowledge_check_results' not in st.session_state:
        st.session_state['knowledge_check_results'] = False

# Reset session
def reset_session():
    for key in list(st.session_state.keys()):
        if key != 'session_id':
            del st.session_state[key]
    st.session_state['knowledge_check_progress'] = 0
    st.session_state['knowledge_check_answers'] = {}
    st.session_state['knowledge_check_results'] = False
    st.experimental_rerun()

# Home Page Content
def show_home():
    st.title("AWS Cloud Practitioner - Content Review Session 1")
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.markdown("### Welcome to the AWS Partner Certification Readiness - Cloud Practitioner!")
        st.markdown("This interactive e-learning application will guide you through the content covered in Session 1 of the AWS Cloud Practitioner certification preparation.")
        
        st.markdown("### Learning Outcomes")
        st.markdown("""
        - Understand the Cloud Value Proposition of AWS
        - Explore AWS Global Infrastructure
        - Introduction to AWS Services
        """)
        
        st.markdown("### Weekly Program Summary")
        program_data = {
            "Task": ["Attend Kickoff Session", "Complete AWS Cloud Practitioner Essentials", 
                    "Attend Study Session 1", "Attend Study Session 2", "Attend Study Session 3", "Schedule Exam"],
            "Description": ["You Are Here! We will cover program basics and summarize your next 4 weeks of learning.",
                          "Complete the Cloud Practitioner Essentials Learning Plan to develop a fundamental understanding of the AWS Cloud.",
                          "Review a range of AWS technologies, cloud concepts, security & compliance, and billing & pricing",
                          "Review the AWS Well-Architected Framework, exam strategy, best practices, and intro to CloudQuest",
                          "Apply knowledge and test concepts through a series of practice exam questions",
                          "It's a pleasure supporting you on your AWS Certification journey! Best of luck on your exam!"],
            "Duration": ["60 minutes", "~8 hours", "90 minutes", "90 minutes", "90 minutes", "Schedule Exam"]
        }
        
        df = pd.DataFrame(program_data)
        st.table(df)
    
    with col2:
        st.image("https://d1.awsstatic.com/training-and-certification/certification-badges/AWS-Certified-Cloud-Practitioner_badge.634f8a21af2e0e956ed8905a72366146ba22b74c.png", 
                 caption="AWS Cloud Practitioner", width=300)
        
        st.markdown("### Getting Started")
        st.markdown("""
        1. Navigate through topics using the tabs above
        2. Test your knowledge in the Knowledge Check section
        3. Take notes and engage with the interactive examples
        """)
        
        with st.expander("Additional Resources"):
            st.markdown("""
            - [AWS Skill Builder](https://explore.skillbuilder.aws/)
            - [AWS Cloud Quest](https://aws.amazon.com/training/digital/aws-cloud-quest/)
            - [AWS Certification Official Practice Exams](https://aws.amazon.com/certification/certification-prep/)
            """)

# AWS Value Proposition Content
def show_value_proposition():
    st.title("Value Proposition of AWS")
    st.markdown("### Major Advantages of Cloud over On-Premises")
    
    # Create tabs for different value propositions
    vp_tabs = st.tabs(["Trade Fixed for Variable Expense", "Economies of Scale", 
                       "Stop Guessing Capacity", "Increase Speed & Agility", 
                       "Stop Data Center Spend", "Go Global in Minutes"])
    
    with vp_tabs[0]:
        col1, col2 = st.columns([3, 2])
        
        with col1:
            st.markdown("### Trade Capital Expense for Variable Expense")
            st.markdown("""
            Instead of having to invest heavily in data centers and servers before you know how you're going to use them, 
            you can pay only when you consume computing resources, and pay only for how much you consume.
            """)
            
            st.markdown("#### Capital vs Variable Expenses")
            capex_opex = {
                "Capital Expense": ["Buildings", "Vehicles", "Equipment", "Office furniture", "Machinery", "Trademarks"],
                "Variable/Operating Expense": ["Electricity", "Software", "Rent", "Salaries", "Accounting fees", "Utilities"]
            }
            
            df = pd.DataFrame(capex_opex)
            st.table(df)
        
        with col2:
            # Create visualization
            fig, ax = plt.subplots(figsize=(8, 6))
            
            categories = ['Hardware', 'Facilities', 'Admin', 'Software']
            on_prem = [35, 25, 20, 20]
            cloud = [5, 0, 10, 15]
            
            x = range(len(categories))
            width = 0.35
            
            ax.bar([i - width/2 for i in x], on_prem, width, label='On-Premises', color='#232F3E')
            ax.bar([i + width/2 for i in x], cloud, width, label='Cloud', color='#FF9900')
            
            ax.set_xlabel('Cost Categories')
            ax.set_ylabel('Percentage of Total Cost')
            ax.set_title('On-Premises vs Cloud Cost Structure')
            ax.set_xticks(x)
            ax.set_xticklabels(categories)
            ax.legend()
            
            st.pyplot(fig)
            
            st.info("With AWS, you transform large upfront expenses into smaller, predictable operational costs.")
    
    with vp_tabs[1]:
        st.markdown("### Benefit from Massive Economies of Scale")
        st.markdown("""
        By using cloud computing, you can achieve a lower variable cost than you can get on your own. 
        Because usage from hundreds of thousands of customers is aggregated in the cloud, providers such as AWS 
        can achieve higher economies of scale, which translates into lower pay-as-you-go prices.
        """)
        
        # Create economy of scale visualization
        st.image("https://d2908q01vomqb2.cloudfront.net/fc074d501302eb2b93e2554793fcaf50b3bf7291/2021/07/15/Figure-1.-Cloud-operating-model-%E2%80%93-Economic-value-loop.png", 
                caption="AWS Economy of Scale Model")
        
        st.markdown("""
        #### AWS Economy of Scale Flywheel Effect
        1. More Customers → More AWS Usage
        2. More AWS Usage → More Infrastructure
        3. More Infrastructure → Lower Infrastructure Costs
        4. Lower Infrastructure Costs → Reduced Prices
        5. Reduced Prices → More Customers
        """)
        
        st.info("As AWS grows, the cost of running the infrastructure decreases, and these savings are passed back to customers.")
    
    with vp_tabs[2]:
        st.markdown("### Stop Guessing Capacity")
        st.markdown("""
        Eliminate guessing on your infrastructure capacity needs. When you make a capacity decision prior to deploying an application, 
        you often end up either sitting on expensive idle resources or dealing with limited capacity. 
        With cloud computing, these problems go away. You can access as much or as little capacity as you need, and scale up and down as required with only a few minutes' notice.
        """)
        
        col1, col2 = st.columns(2)
        
        with col1:
            # Create traditional provisioning graph
            months = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
            capacity = [35000] * 12
            actual_usage = [10000, 15000, 18000, 20000, 32000, 28000, 25000, 30000, 35000, 30000, 25000, 30000]
            
            fig = px.line(x=months, y=[capacity, actual_usage], 
                         labels={"x": "Month", "y": "Capacity/Usage", "value": "Value"},
                         title="Guesswork Provisioning vs. Actual Demand")
            
            fig.update_layout(legend_title_text='')
            fig.update_traces(name='Provisioned Capacity', selector=dict(name="wide_variable_0"))
            fig.update_traces(name='Actual Usage', selector=dict(name="wide_variable_1"))
            
            st.plotly_chart(fig)
            st.caption("Traditional On-premises: Overprovisioning leads to wasted resources")
        
        with col2:
            # Create dynamic provisioning graph
            dynamic_capacity = [11000, 16000, 19000, 21000, 33000, 29000, 26000, 31000, 36000, 31000, 26000, 31000]
            
            fig = px.line(x=months, y=[dynamic_capacity, actual_usage], 
                         labels={"x": "Month", "y": "Capacity/Usage", "value": "Value"},
                         title="Dynamic Provisioning for Actual Demand")
            
            fig.update_layout(legend_title_text='')
            fig.update_traces(name='Provisioned Capacity', selector=dict(name="wide_variable_0"))
            fig.update_traces(name='Actual Usage', selector=dict(name="wide_variable_1"))
            
            st.plotly_chart(fig)
            st.caption("AWS Cloud: Dynamic provisioning matches actual demand")
        
        st.success("AWS allows you to scale elastically - provision only what you need, when you need it.")
    
    with vp_tabs[3]:
        st.markdown("### Increase Speed and Agility")
        st.markdown("""
        In a cloud computing environment, new IT resources are only a click away, which means that you reduce the time to make those resources 
        available to your developers from weeks to just minutes. This results in a dramatic increase in agility for the organization, 
        since the cost and time it takes to experiment and develop is significantly lower.
        """)
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("#### Traditional IT Procurement Process")
            traditional_steps = [
                "1. Define Requirements (2-4 weeks)",
                "2. Secure Budget Approval (1-4 weeks)",
                "3. Vendor Selection & Negotiation (2-8 weeks)",
                "4. Delivery & Installation (2-6 weeks)",
                "5. Configuration & Testing (1-4 weeks)",
                "6. Production Deployment (1-2 weeks)"
            ]
            
            for step in traditional_steps:
                st.markdown(f"- {step}")
            
            st.markdown("**Total Time: 9-28 weeks**")
        
        with col2:
            st.markdown("#### AWS Provisioning Process")
            aws_steps = [
                "1. Define Requirements (1-5 days)",
                "2. AWS Console Configuration (minutes)",
                "3. Deployment & Testing (hours to days)",
                "4. Production Deployment (minutes)"
            ]
            
            for step in aws_steps:
                st.markdown(f"- {step}")
                
            st.markdown("**Total Time: Days rather than months**")
            
            st.success("Faster time to market means more opportunity to innovate!")
    
    with vp_tabs[4]:
        st.markdown("### Stop Data Center Spend")
        st.markdown("""
        Focus on projects that differentiate your business, not the infrastructure. Cloud computing lets you focus on your own customers, 
        rather than on the heavy lifting of racking, stacking, and powering servers.
        """)
        
        col1, col2 = st.columns(2)
        
        with col1:
            # Create data center cost breakdown
            labels = 'Real Estate', 'Hardware', 'Power & Cooling', 'Networking', 'Security', 'IT Staff'
            sizes = [15, 25, 20, 15, 10, 15]
            colors = ['#232F3E', '#FF9900', '#0073BB', '#527FFF', '#8C1D40', '#007078']
            
            fig, ax = plt.subplots()
            ax.pie(sizes, labels=labels, colors=colors, autopct='%1.1f%%', startangle=90)
            ax.axis('equal')
            plt.title('Data Center Cost Breakdown')
            
            st.pyplot(fig)
        
        with col2:
            st.markdown("#### Hidden Costs of Running Your Own Data Center:")
            dc_costs = [
                "Real Estate - Purchase/leasing, security, management",
                "Physical assets - Procurement, installation, maintenance",
                "Power & Cooling - Continuous operation and optimization",
                "Networking - Equipment, bandwidth contracts, management",
                "Security - Physical and digital protection systems",
                "Specialist staffing - 24/7 operations team, security personnel"
            ]
            
            for cost in dc_costs:
                st.markdown(f"- {cost}")
            
            st.info("None of these costs directly provide value to customers or add differentiation to your business.")
    
    with vp_tabs[5]:
        st.markdown("### Go Global in Minutes")
        st.markdown("""
        Easily deploy your application in multiple regions around the world with just a few clicks. 
        This means you can provide lower latency and a better experience for your customers at minimal cost.
        """)
        
        # Global deployment visualization
        col1, col2 = st.columns([3, 1])
        
        with col1:
            st.image("https://d1.awsstatic.com/about-aws/regions/Global%20Infrastructure%20Map_3-22-2022.3ffd139a7eac1655a72a0b19dc7e4501eaac8848.png",
                    caption="AWS Global Infrastructure")
            
            st.markdown("""
            Deploy your application globally with AWS:
            - 31 geographic regions
            - 99 availability zones
            - 550+ points of presence
            - Low-latency content delivery to end users
            """)
        
        with col2:
            st.markdown("#### Traditional Global Deployment")
            st.markdown("""
            - Build multiple data centers
            - Manage complex networking
            - Negotiate with ISPs in each region
            - Maintain international IT staff
            - Address compliance per region
            """)
            
            st.markdown("#### AWS Global Deployment")
            st.markdown("""
            - Select regions in AWS Console
            - Deploy with a few clicks
            - Consistent management interface
            - Built-in compliance frameworks
            - Global network backbone
            """)

# AWS Global Infrastructure Content
def show_global_infrastructure():
    st.title("AWS Global Infrastructure")
    
    # Create tabs for different infrastructure components
    infra_tabs = st.tabs(["Overview", "Regions", "Availability Zones", "Edge Locations"])
    
    with infra_tabs[0]:
        col1, col2 = st.columns([2, 1])
        
        with col1:
            st.markdown("""
            AWS has built the most robust and powerful global infrastructure in the world, with AWS Regions offering multiple physically 
            separated and isolated Availability Zones connected with low-latency, high-throughput, redundant networking.
            
            The AWS Global Infrastructure is designed to provide:
            - High Availability
            - Fault Tolerance
            - Scalability
            - Low Latency
            - Global Reach
            """)
            
            # Global infrastructure metrics
            metrics = {
                "Component": ["Regions", "Availability Zones", "Edge Locations", "Local Zones"],
                "Count": ["31+", "99+", "550+", "29+"]
            }
            
            df = pd.DataFrame(metrics)
            st.table(df)
        
        with col2:
            st.image("https://d1.awsstatic.com/global-infrastructure/infrastructure-tiers.8a0d4c57804a0c2e42f25159613404a5546afbdb.png",
                    caption="AWS Global Infrastructure Tiers")
    
    with infra_tabs[1]:
        st.markdown("### AWS Regions")
        st.markdown("""
        A Region is a physical location around the world where AWS clusters data centers. Each AWS Region consists of multiple, 
        isolated, and physically separate Availability Zones.
        
        AWS Regions are designed to be completely isolated from each other, which achieves the greatest possible fault tolerance and stability.
        """)
        
        col1, col2 = st.columns([3, 2])
        
        with col1:
            st.image("https://d1.awsstatic.com/global-infrastructure/maps/Global-Infrastructure-Map_3-1-23.c3867f3ed2a80e81bbc5fa91677b4a4b269c6423.png",
                    caption="AWS Regions Global Map")
        
        with col2:
            st.markdown("#### How to Choose a Region")
            st.markdown("""
            When selecting a Region for your applications and workloads, consider:
            
            1. **Data Compliance** - Legal/regulatory requirements for where data can be stored
            2. **Proximity** - Choose regions close to your customers to reduce latency
            3. **Feature Availability** - Some AWS services aren't available in all regions
            4. **Pricing** - Pricing varies by region due to local costs
            """)
            
            st.info("Example Region Name: us-east-1 (N. Virginia)")
    
    with infra_tabs[2]:
        st.markdown("### AWS Availability Zones")
        st.markdown("""
        An Availability Zone (AZ) is one or more discrete data centers with redundant power, networking, and connectivity in an AWS Region.
        
        AZs give customers the ability to operate production applications and databases that are more highly available, fault tolerant, 
        and scalable than would be possible from a single data center.
        """)
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.image("https://d1.awsstatic.com/Product-Page-Diagram_Amazon-Global-Locations.8a2592e10a19bffd2f2bf89c7fe3c551801bef5c.png",
                    caption="AWS Availability Zone Architecture")
            
        with col2:
            st.markdown("#### Key Points About Availability Zones")
            st.markdown("""
            - All AZs in an AWS Region are interconnected with high-bandwidth, low-latency networking
            - Each AZ is physically separated (typically tens of miles apart)
            - AZs are designed to be isolated from failures in other AZs
            - Enterprise-grade physical security and controlled access
            - Connected through low-latency private links (not public internet)
            """)
            
            st.success("""
            **Best Practice**: Deploy critical applications across multiple AZs to create high availability architecture.
            
            Example AZ Name: us-east-1a
            """)
    
    with infra_tabs[3]:
        st.markdown("### Edge Locations & CloudFront")
        st.markdown("""
        AWS Edge Locations are sites deployed in major cities and highly populated areas across the globe. AWS uses Edge Locations 
        to deliver content to end users with lower latency.
        
        Edge Locations are separate from Regions, and are primarily used by Amazon CloudFront (CDN) and Amazon Route 53 (DNS).
        """)
        
        col1, col2 = st.columns([3, 2])
        
        with col1:
            # CloudFront diagram
            st.image("https://d1.awsstatic.com/product-marketing/CloudFront/product-page-diagram_CloudFront_HIW.654ffe23bfbc37d65132995c983e47f9107ea970.png",
                    caption="How Amazon CloudFront Works")
        
        with col2:
            st.markdown("#### Services Using Edge Locations")
            st.markdown("""
            - **Amazon CloudFront** - Content Delivery Network (CDN)
            - **Amazon Route 53** - Domain Name System (DNS)
            - **AWS WAF** - Web Application Firewall
            - **AWS Shield** - DDoS protection
            - **Lambda@Edge** - Run code closer to users
            """)
            
            st.info("""
            Edge Locations help reduce latency by caching content closer to end users, improving the overall experience of your applications.
            
            Currently, AWS maintains 550+ edge locations globally.
            """)

# AWS Services Content
def show_aws_services():
    st.title("Introduction to AWS Services")
    
    # Create tabs for different service categories
    service_tabs = st.tabs(["Compute", "Storage", "Database", "Networking", "Other Key Services"])
    
    with service_tabs[0]:
        st.markdown("### AWS Compute Services")
        st.markdown("""
        AWS offers a comprehensive portfolio of compute services to support a wide variety of workloads.
        """)
        
        # EC2 section
        st.subheader("Amazon EC2 - Elastic Compute Cloud")
        col1, col2 = st.columns([3, 2])
        
        with col1:
            st.markdown("""
            Amazon Elastic Compute Cloud (Amazon EC2) provides resizable compute capacity in the cloud. It is designed to make 
            web-scale cloud computing easier for developers.
            
            **Key Features:**
            - Virtual servers in the cloud
            - Choose your operating system and configuration
            - Complete control over your computing resources
            - Secure and resizable compute capacity
            - Pay only for what you use
            """)
            
            with st.expander("EC2 Instance Types"):
                instance_types = {
                    "Type": ["General Purpose", "Compute Optimized", "Memory Optimized", "Storage Optimized", "Accelerated Computing"],
                    "Use Case": ["Balanced resources, web servers, code repositories", 
                               "Batch processing, media transcoding, gaming servers",
                               "High-performance databases, in-memory analytics",
                               "Data warehousing, log processing, distributed file systems",
                               "Machine learning, video processing, graphics applications"]
                }
                
                df = pd.DataFrame(instance_types)
                st.table(df)
        
        with col2:
            st.image("https://d1.awsstatic.com/Products/product-name/diagrams/product-page-diagram_Amazon-EC2_HIW.cf4c2bd7a7f2d3be0f8dd9f43e68ae37082284fc.png",
                    caption="How Amazon EC2 Works")
            
            st.markdown("#### EC2 Pricing Options")
            pricing_options = [
                ("On-Demand", "Pay by the hour with no commitments"),
                ("Reserved Instances", "1 or 3-year terms with significant discounts"),
                ("Spot Instances", "Bid for unused capacity at up to 90% discount"),
                ("Dedicated Hosts", "Physical servers dedicated for your use")
            ]
            
            for option, description in pricing_options:
                st.markdown(f"- **{option}**: {description}")
        
        # Lambda section
        st.markdown("---")
        st.subheader("AWS Lambda - Serverless Computing")
        
        col1, col2 = st.columns([3, 2])
        
        with col1:
            st.markdown("""
            AWS Lambda lets you run code without provisioning or managing servers. You pay only for the compute time 
            you consume - there is no charge when your code is not running.
            
            **Key Features:**
            - Run code without thinking about servers
            - Pay only for compute time
            - Automatic scaling
            - Built-in fault tolerance
            - Supports multiple languages (Node.js, Python, Java, Go, etc.)
            """)
            
            with st.expander("Sample Lambda Function (Python)"):
                st.code('''
import json

def lambda_handler(event, context):
    # Simple Lambda function that returns a greeting
    name = event.get('name', 'World')
    return {
        'statusCode': 200,
        'body': json.dumps(f'Hello, {name}!')
    }
                ''', language='python')
        
        with col2:
            st.image("https://d1.awsstatic.com/product-marketing/Lambda/Diagrams/product-page-diagram_Lambda-HowItWorks.68a0bcacfcf46fccf04b97f16b686ea44494303f.png",
                    caption="How AWS Lambda Works")
            
            st.markdown("#### Common Lambda Use Cases")
            use_cases = [
                "Real-time file processing",
                "Real-time stream processing",
                "Backend for web, mobile, IoT",
                "API endpoints",
                "Task automation"
            ]
            
            for use_case in use_cases:
                st.markdown(f"- {use_case}")
        
        # Container services
        st.markdown("---")
        st.subheader("Container Services")
        
        container_services = {
            "Service": ["Amazon ECS (Elastic Container Service)", "Amazon EKS (Elastic Kubernetes Service)", "AWS Fargate"],
            "Description": [
                "Fully managed container orchestration service for Docker containers",
                "Fully managed Kubernetes service to run Kubernetes without installing or maintaining control plane",
                "Serverless compute engine for containers that works with both ECS and EKS"
            ]
        }
        
        df = pd.DataFrame(container_services)
        st.table(df)
        
        st.info("**Key Difference:** Choose ECS for a simplified AWS-native experience, EKS if you're already using Kubernetes, and Fargate when you want to run containers without managing servers.")
    
    with service_tabs[1]:
        st.markdown("### AWS Storage Services")
        st.markdown("""
        AWS provides multiple storage options to support your applications and data requirements.
        """)
        
        # Storage types
        st.markdown("#### Types of Storage in AWS")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.markdown("##### Object Storage")
            st.markdown("""
            - Stores data as objects in buckets
            - Ideal for static files like images, videos
            - Example: Amazon S3
            """)
        
        with col2:
            st.markdown("##### Block Storage")
            st.markdown("""
            - Data stored in fixed-sized blocks
            - Used as hard drives for EC2 instances
            - Example: Amazon EBS
            """)
        
        with col3:
            st.markdown("##### File Storage")
            st.markdown("""
            - Shared file storage with file-level access
            - Works like networked file systems
            - Example: Amazon EFS, FSx
            """)
        
        # S3 section
        st.markdown("---")
        st.subheader("Amazon S3 (Simple Storage Service)")
        
        col1, col2 = st.columns([3, 2])
        
        with col1:
            st.markdown("""
            Amazon S3 is object storage built to store and retrieve any amount of data from anywhere. It delivers 
            99.999999999% (11 9's) durability and stores data for millions of applications.
            
            **Key Features:**
            - Unlimited storage capacity
            - High durability and availability
            - Rich security and access controls
            - Query-in-place functionality
            - Flexible management features
            """)
            
            with st.expander("S3 Storage Classes"):
                storage_classes = {
                    "Storage Class": ["S3 Standard", "S3 Standard-IA", "S3 One Zone-IA", "S3 Intelligent-Tiering", 
                                    "S3 Glacier Instant Retrieval", "S3 Glacier Flexible Retrieval", "S3 Glacier Deep Archive"],
                    "Use Case": [
                        "General-purpose storage for frequently accessed data",
                        "Long-lived, infrequently accessed data",
                        "Non-critical, infrequently accessed data",
                        "Data with unknown or changing access patterns",
                        "Archive data that needs immediate access",
                        "Long-term data archive with retrieval times of minutes to hours",
                        "Long-term data archive with retrieval times of hours"
                    ]
                }
                
                df = pd.DataFrame(storage_classes)
                st.table(df)
        
        with col2:
            st.image("https://d1.awsstatic.com/s3-pdp-redesign/product-page-diagram_Amazon-S3_HIW.cf4c2bd7a7f2d3be0f8dd9f43e68ae37082284fc.png",
                    caption="How Amazon S3 Works")
            
            st.success("S3 Standard provides 99.999999999% (11 9's) durability and 99.99% availability over the calendar year.")
        
        # EBS section
        st.markdown("---")
        st.subheader("Amazon EBS (Elastic Block Store)")
        
        col1, col2 = st.columns([3, 2])
        
        with col1:
            st.markdown("""
            Amazon EBS provides persistent block storage volumes for use with Amazon EC2 instances. Each Amazon EBS volume is 
            automatically replicated within its Availability Zone to protect from component failure.
            
            **Key Features:**
            - High performance block storage
            - Designed for EC2 instances
            - Snapshot capability for point-in-time backups
            - Different volume types for different workloads
            - Independent lifecycle from EC2 instances
            """)
            
            with st.expander("EBS Volume Types"):
                volume_types = {
                    "Type": ["General Purpose SSD (gp2/gp3)", "Provisioned IOPS SSD (io1/io2)", 
                           "Throughput Optimized HDD (st1)", "Cold HDD (sc1)"],
                    "Use Case": [
                        "Boot volumes, dev/test environments",
                        "I/O intensive workloads, databases",
                        "Big data, data warehouses, log processing",
                        "Infrequently accessed data, lowest cost"
                    ]
                }
                
                df = pd.DataFrame(volume_types)
                st.table(df)
        
        with col2:
            st.image("https://d1.awsstatic.com/product-marketing/Elastic%20Block%20Store/Product-Page-Diagram_Amazon-Elastic-Block-Store.9fed315519e1cecae3669bb094ef5351654f020f.png",
                    caption="How Amazon EBS Works")
        
        # Other storage services
        st.markdown("---")
        st.subheader("Other Storage Services")
        
        other_storage = {
            "Service": ["Amazon EFS (Elastic File System)", "Amazon FSx", "AWS Storage Gateway", "AWS Snow Family"],
            "Description": [
                "Fully managed elastic file system for use with AWS Cloud and on-premises resources",
                "Fully managed file storage services for Windows (FSx for Windows) and Lustre (FSx for Lustre)",
                "Hybrid cloud storage service that connects on-premises environments with cloud storage",
                "Physical devices to migrate data into and out of AWS (Snowcone, Snowball, Snowmobile)"
            ]
        }
        
        df = pd.DataFrame(other_storage)
        st.table(df)
    
    with service_tabs[2]:
        st.markdown("### AWS Database Services")
        st.markdown("""
        AWS offers purpose-built database services to support diverse application requirements.
        """)
        
        # Database types
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("#### Relational Databases")
            st.markdown("""
            **Characteristics:**
            - Structured data in tables with rows and columns
            - Relationships between tables
            - ACID transactions
            - SQL query language
            
            **AWS Services:**
            - Amazon RDS
            - Amazon Aurora
            """)
        
        with col2:
            st.markdown("#### Non-Relational Databases")
            st.markdown("""
            **Characteristics:**
            - Various data models (document, key-value, graph)
            - Schema flexibility
            - Horizontal scalability
            - Designed for specific use cases
            
            **AWS Services:**
            - Amazon DynamoDB
            - Amazon DocumentDB
            - Amazon Neptune
            - Amazon Keyspaces
            """)
        
        # RDS section
        st.markdown("---")
        st.subheader("Amazon RDS (Relational Database Service)")
        
        col1, col2 = st.columns([3, 2])
        
        with col1:
            st.markdown("""
            Amazon RDS makes it easy to set up, operate, and scale a relational database in the cloud. It provides 
            cost-efficient and resizable capacity while automating time-consuming administration tasks.
            
            **Key Features:**
            - Automated patching and backups
            - High availability with Multi-AZ option
            - Read replicas for improved performance
            - Automated failover capability
            - Easy scaling of compute and storage
            """)
            
            with st.expander("Supported Database Engines"):
                engines = {
                    "Engine": ["MySQL", "PostgreSQL", "MariaDB", "Oracle", "Microsoft SQL Server", "Amazon Aurora"],
                    "Use Case": [
                        "Web applications, e-commerce",
                        "Geographic applications, enterprise applications",
                        "Website databases, CMS systems",
                        "Enterprise applications, legacy applications",
                        "Enterprise applications, Windows ecosystem",
                        "High-performance enterprise applications"
                    ]
                }
                
                df = pd.DataFrame(engines)
                st.table(df)
        
        with col2:
            st.image("https://d1.awsstatic.com/video-thumbs/RDS/product-page-diagram_Amazon-RDS-Regular-Deployment_HIW.96244168f48394137b1faf3b4149a5185eac33f0.png",
                    caption="How Amazon RDS Works")
        
        # DynamoDB section
        st.markdown("---")
        st.subheader("Amazon DynamoDB")
        
        col1, col2 = st.columns([3, 2])
        
        with col1:
            st.markdown("""
            Amazon DynamoDB is a fully managed NoSQL database service that provides fast and predictable performance with seamless scalability.
            
            **Key Features:**
            - Serverless with automatic scaling
            - Millisecond latency at any scale
            - Built-in security and backup
            - Multi-region, multi-active replication
            - In-memory caching capability
            """)
            
            with st.expander("Sample DynamoDB Table Structure"):
                st.code('''
{
  "TableName": "Users",
  "KeySchema": [
    { "AttributeName": "user_id", "KeyType": "HASH" }
  ],
  "AttributeDefinitions": [
    { "AttributeName": "user_id", "AttributeType": "S" },
    { "AttributeName": "email", "AttributeType": "S" }
  ],
  "GlobalSecondaryIndexes": [
    {
      "IndexName": "EmailIndex",
      "KeySchema": [
        { "AttributeName": "email", "KeyType": "HASH" }
      ],
      "Projection": { "ProjectionType": "ALL" }
    }
  ]
}
                ''', language='json')
        
        with col2:
            st.image("https://d1.awsstatic.com/product-page-diagram_Amazon-DynamoDBa.1f8742b4f5bfb8cd41a3d4d2d7c5286aac97d9ff.png",
                    caption="How Amazon DynamoDB Works")
            
            st.markdown("#### Common DynamoDB Use Cases")
            use_cases = [
                "Mobile and web applications",
                "Gaming applications",
                "Digital ad serving",
                "Live voting",
                "E-commerce shopping carts"
            ]
            
            for use_case in use_cases:
                st.markdown(f"- {use_case}")
        
        # Other database services
        st.markdown("---")
        st.subheader("Other Database Services")
        
        other_dbs = {
            "Service": ["Amazon Aurora", "Amazon ElastiCache", "Amazon Neptune", "Amazon DocumentDB", "Amazon Keyspaces", "Amazon MemoryDB"],
            "Type": [
                "Relational", "In-Memory", "Graph", "Document", "Wide Column", "In-Memory"
            ],
            "Description": [
                "MySQL/PostgreSQL-compatible relational database with up to 5x performance",
                "Fully managed Redis or Memcached for in-memory caching",
                "Fully managed graph database service for connected datasets",
                "MongoDB-compatible document database service",
                "Apache Cassandra-compatible wide column database",
                "Redis-compatible, durable in-memory database"
            ]
        }
        
        df = pd.DataFrame(other_dbs)
        st.table(df)
    
    with service_tabs[3]:
        st.markdown("### AWS Networking Services")
        st.markdown("""
        AWS networking services enable you to isolate cloud infrastructure, scale resource delivery, and connect data centers.
        """)
        
        # VPC section
        st.subheader("Amazon VPC (Virtual Private Cloud)")
        
        col1, col2 = st.columns([3, 2])
        
        with col1:
            st.markdown("""
            Amazon VPC lets you provision a logically isolated section of the AWS Cloud where you can launch AWS resources 
            in a virtual network that you define.
            
            **Key Features:**
            - Complete control over your virtual networking environment
            - Secure and monitor traffic using security groups and NACLs
            - Connect to your own data center
            - Multiple connectivity options
            - Custom network configurations
            """)
            
            with st.expander("VPC Components"):
                components = [
                    "**Subnets**: Range of IP addresses in your VPC (public or private)",
                    "**Route Tables**: Set of rules (routes) to direct network traffic",
                    "**Internet Gateway**: Connects VPC to the internet",
                    "**NAT Gateway**: Enables internet access for private subnets",
                    "**Security Groups**: Virtual firewall at the instance level",
                    "**Network ACLs**: Virtual firewall at the subnet level",
                    "**VPC Endpoints**: Connect to AWS services privately"
                ]
                
                for component in components:
                    st.markdown(f"- {component}")
        
        with col2:
            st.image("https://d1.awsstatic.com/Digital%20Marketing/House/1up/products/VPC/Product-Page-Diagram_Amazon-VPC_Basic-VPC.e05a31086b7591a144088d0ce38b479551903329.png",
                    caption="Amazon VPC Architecture")
        
        # Security Groups vs NACLs
        st.markdown("---")
        st.subheader("Security Groups vs. Network ACLs")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("#### Security Groups")
            st.markdown("""
            - Acts as a virtual firewall for EC2 instances
            - Controls inbound and outbound traffic at the instance level
            - Stateful: Return traffic automatically allowed
            - Allow rules only (no explicit deny)
            - Evaluated as a whole before traffic is allowed
            """)
        
        with col2:
            st.markdown("#### Network ACLs")
            st.markdown("""
            - Acts as a firewall for subnets
            - Controls inbound and outbound traffic at the subnet level
            - Stateless: Return traffic must be explicitly allowed
            - Both allow and deny rules
            - Rules processed in order, starting with lowest numbered rule
            """)
        
        # Route 53 section
        st.markdown("---")
        st.subheader("Amazon Route 53")
        
        col1, col2 = st.columns([3, 2])
        
        with col1:
            st.markdown("""
            Amazon Route 53 is a highly available and scalable Domain Name System (DNS) web service. Route 53 connects user 
            requests to infrastructure running in AWS and can also route users to infrastructure outside of AWS.
            
            **Key Features:**
            - Domain registration
            - DNS routing
            - Health checking
            - Traffic flow
            - Latency-based routing
            - Geo DNS
            """)
            
            with st.expander("Route 53 Routing Policies"):
                policies = {
                    "Policy": ["Simple", "Weighted", "Latency-based", "Failover", "Geolocation", "Multivalue Answer"],
                    "Use Case": [
                        "Single resource serving content",
                        "Distribute traffic across multiple resources",
                        "Route users to the lowest-latency endpoint",
                        "Active-passive failover configuration",
                        "Route traffic based on user location",
                        "Respond with multiple healthy records selected randomly"
                    ]
                }
                
                df = pd.DataFrame(policies)
                st.table(df)
        
        with col2:
            st.image("https://d1.awsstatic.com/Route53/product-page-diagram_Amazon-Route-53_HIW%402x.4c2af00405a0825f83fcc6b3497ffaee6981be53.png",
                    caption="How Route 53 Works")
        
        # Other networking services
        st.markdown("---")
        st.subheader("Other Networking Services")
        
        other_networking = {
            "Service": ["AWS Direct Connect", "Elastic Load Balancing", "Amazon CloudFront", "AWS Transit Gateway", "AWS Global Accelerator"],
            "Description": [
                "Dedicated network connection from on-premises to AWS",
                "Distributes incoming application traffic across multiple targets",
                "Global content delivery network (CDN) service",
                "Centrally manage connectivity between VPCs and on-premises networks",
                "Improve availability and performance of applications with global users"
            ]
        }
        
        df = pd.DataFrame(other_networking)
        st.table(df)
    
    with service_tabs[4]:
        st.markdown("### Other Key AWS Services")
        
        # Management & Governance
        st.subheader("Management & Governance")
        
        mgmt_services = {
            "Service": ["AWS CloudFormation", "AWS CloudTrail", "Amazon CloudWatch", "AWS Config", "AWS Systems Manager"],
            "Description": [
                "Create and manage resources with templates (Infrastructure as Code)",
                "Track user activity and API usage for compliance and audit",
                "Monitor resources and applications with metrics, logs, and alarms",
                "Assess, audit, and evaluate configurations of resources",
                "Operational insights and actions across resources"
            ]
        }
        
        df = pd.DataFrame(mgmt_services)
        st.table(df)
        
        # Security & Identity
        st.markdown("---")
        st.subheader("Security, Identity & Compliance")
        
        security_services = {
            "Service": ["AWS Identity and Access Management (IAM)", "Amazon Cognito", "AWS Shield", "AWS WAF", "Amazon GuardDuty"],
            "Description": [
                "Securely control access to AWS services and resources",
                "Add user sign-up, sign-in, and access control to apps",
                "DDoS protection service for applications",
                "Web application firewall to protect against common exploits",
                "Intelligent threat detection service"
            ]
        }
        
        df = pd.DataFrame(security_services)
        st.table(df)
        
        # Application Integration
        st.markdown("---")
        st.subheader("Application Integration")
        
        integration_services = {
            "Service": ["Amazon SQS", "Amazon SNS", "AWS Step Functions", "Amazon EventBridge", "Amazon MQ"],
            "Description": [
                "Fully managed message queuing service",
                "Fully managed pub/sub messaging service",
                "Coordinate components of distributed applications",
                "Serverless event bus for applications",
                "Managed message broker service for ActiveMQ and RabbitMQ"
            ]
        }
        
        df = pd.DataFrame(integration_services)
        st.table(df)
        
        # Machine Learning
        st.markdown("---")
        st.subheader("Machine Learning")
        
        ml_services = {
            "Service": ["Amazon SageMaker", "Amazon Rekognition", "Amazon Transcribe", "Amazon Comprehend", "Amazon Lex"],
            "Description": [
                "Build, train, and deploy machine learning models",
                "Add image and video analysis to applications",
                "Convert speech to text",
                "Natural language processing service",
                "Build conversational interfaces (chatbots)"
            ]
        }
        
        df = pd.DataFrame(ml_services)
        st.table(df)
        
        # Developer Tools
        st.markdown("---")
        st.subheader("Developer Tools")
        
        dev_services = {
            "Service": ["AWS CodeCommit", "AWS CodeBuild", "AWS CodeDeploy", "AWS CodePipeline", "AWS Cloud9"],
            "Description": [
                "Fully managed source control service",
                "Compile source code, run tests, and produce packages",
                "Automate code deployments to any instance",
                "Continuous delivery service for fast updates",
                "Cloud-based IDE for writing, running, and debugging code"
            ]
        }
        
        df = pd.DataFrame(dev_services)
        st.table(df)

# Knowledge Check Content
def show_knowledge_check():
    st.title("Knowledge Check")
    
    # Display progress
    st.progress(st.session_state['knowledge_check_progress'] / 5)
    
    # Button to restart knowledge check
    if st.button("Restart Knowledge Check"):
        st.session_state['knowledge_check_progress'] = 0
        st.session_state['knowledge_check_answers'] = {}
        st.session_state['knowledge_check_results'] = False
        st.experimental_rerun()
    
    # Show results button
    if st.session_state['knowledge_check_progress'] == 5 and not st.session_state['knowledge_check_results']:
        if st.button("Show Results"):
            st.session_state['knowledge_check_results'] = True
            st.experimental_rerun()
    
    # Display results if complete
    if st.session_state['knowledge_check_results']:
        show_results()
        return
    
    # Setup questions
    questions = [
        {
            "question": "Which of the following is an advantage of cloud computing?",
            "options": [
                "Trade variable expense for fixed expense",
                "Benefit from massive economies of scale",
                "Stop guessing capacity",
                "Increase spending on data center operations"
            ],
            "answer": 1,
            "explanation": "One of the main advantages of cloud computing is benefiting from massive economies of scale. When hundreds of thousands of customers aggregate in the cloud, AWS can achieve higher economies of scale, which translates into lower pay-as-you-go prices."
        },
        {
            "question": "Which of these is an example of an AWS Region?",
            "options": [
                "us-east-1",
                "us-east-1a",
                "North America",
                "Edge Location"
            ],
            "answer": 0,
            "explanation": "us-east-1 (N. Virginia) is an example of an AWS Region. Regions are geographic areas where AWS clusters data centers. us-east-1a would be an example of an Availability Zone within a Region."
        },
        {
            "question": "What is the durability percentage that Amazon S3 Standard storage class is designed to provide?",
            "options": [
                "99.9%",
                "99.99%",
                "99.999999999% (9 9's)",
                "99.999999999% (11 9's)"
            ],
            "answer": 3,
            "explanation": "Amazon S3 Standard is designed to provide 99.999999999% (11 9's) of durability over a given year. This is one of the highest durability levels available in storage systems."
        },
        {
            "question": "Which AWS service is a compute service that lets you run code without provisioning or managing servers?",
            "options": [
                "Amazon EC2",
                "AWS Lambda",
                "Amazon ECS",
                "AWS Fargate"
            ],
            "answer": 1,
            "explanation": "AWS Lambda is a serverless compute service that runs your code in response to events and automatically manages the computing resources for you, eliminating the need to provision or manage servers."
        },
        {
            "question": "Which of the following statements about AWS Availability Zones is true? (Select all that apply)",
            "options": [
                "They are located in different cities within a country",
                "They are physically separated facilities within a Region",
                "They are connected with high bandwidth, low latency networking",
                "All AWS services automatically replicate data across multiple Availability Zones"
            ],
            "answer": [1, 2],
            "type": "multiple",
            "explanation": "Availability Zones are physically separated facilities within an AWS Region, and they are connected via high bandwidth, low latency networking. However, they are typically in the same metropolitan area (not different cities), and not all AWS services automatically replicate data across multiple Availability Zones."
        }
    ]
    
    # Display current question
    current_q = st.session_state['knowledge_check_progress']
    
    if current_q < len(questions):
        q = questions[current_q]
        st.subheader(f"Question {current_q + 1} of {len(questions)}")
        st.markdown(f"**{q['question']}**")
        
        # Handle radio button or checkbox based on question type
        if q.get("type") == "multiple":
            options = q["options"]
            # Initialize answer in session state if not present
            if f"q{current_q}" not in st.session_state['knowledge_check_answers']:
                st.session_state['knowledge_check_answers'][f"q{current_q}"] = []
            
            # Display checkboxes
            selected = []
            for i, option in enumerate(options):
                if st.checkbox(option, key=f"q{current_q}_option{i}"):
                    selected.append(i)
            
            st.session_state['knowledge_check_answers'][f"q{current_q}"] = selected
        else:
            options = q["options"]
            # Initialize answer in session state if not present
            if f"q{current_q}" not in st.session_state['knowledge_check_answers']:
                st.session_state['knowledge_check_answers'][f"q{current_q}"] = None
            
            # Display radio buttons
            answer = st.radio("Select your answer:", options, key=f"q{current_q}")
            st.session_state['knowledge_check_answers'][f"q{current_q}"] = options.index(answer)
        
        # Navigation buttons
        col1, col2 = st.columns(2)
        
        with col1:
            if current_q > 0:
                if st.button("Previous"):
                    st.session_state['knowledge_check_progress'] -= 1
                    st.experimental_rerun()
        
        with col2:
            if st.button("Next"):
                st.session_state['knowledge_check_progress'] += 1
                st.experimental_rerun()

def show_results():
    st.subheader("Knowledge Check Results")
    
    questions = [
        {
            "question": "Which of the following is an advantage of cloud computing?",
            "options": [
                "Trade variable expense for fixed expense",
                "Benefit from massive economies of scale",
                "Stop guessing capacity",
                "Increase spending on data center operations"
            ],
            "answer": 1,
            "explanation": "One of the main advantages of cloud computing is benefiting from massive economies of scale. When hundreds of thousands of customers aggregate in the cloud, AWS can achieve higher economies of scale, which translates into lower pay-as-you-go prices."
        },
        {
            "question": "Which of these is an example of an AWS Region?",
            "options": [
                "us-east-1",
                "us-east-1a",
                "North America",
                "Edge Location"
            ],
            "answer": 0,
            "explanation": "us-east-1 (N. Virginia) is an example of an AWS Region. Regions are geographic areas where AWS clusters data centers. us-east-1a would be an example of an Availability Zone within a Region."
        },
        {
            "question": "What is the durability percentage that Amazon S3 Standard storage class is designed to provide?",
            "options": [
                "99.9%",
                "99.99%",
                "99.999999999% (9 9's)",
                "99.999999999% (11 9's)"
            ],
            "answer": 3,
            "explanation": "Amazon S3 Standard is designed to provide 99.999999999% (11 9's) of durability over a given year. This is one of the highest durability levels available in storage systems."
        },
        {
            "question": "Which AWS service is a compute service that lets you run code without provisioning or managing servers?",
            "options": [
                "Amazon EC2",
                "AWS Lambda",
                "Amazon ECS",
                "AWS Fargate"
            ],
            "answer": 1,
            "explanation": "AWS Lambda is a serverless compute service that runs your code in response to events and automatically manages the computing resources for you, eliminating the need to provision or manage servers."
        },
        {
            "question": "Which of the following statements about AWS Availability Zones is true? (Select all that apply)",
            "options": [
                "They are located in different cities within a country",
                "They are physically separated facilities within a Region",
                "They are connected with high bandwidth, low latency networking",
                "All AWS services automatically replicate data across multiple Availability Zones"
            ],
            "answer": [1, 2],
            "type": "multiple",
            "explanation": "Availability Zones are physically separated facilities within an AWS Region, and they are connected via high bandwidth, low latency networking. However, they are typically in the same metropolitan area (not different cities), and not all AWS services automatically replicate data across multiple Availability Zones."
        }
    ]
    
    correct = 0
    total = len(questions)
    
    for i, q in enumerate(questions):
        user_answer = st.session_state['knowledge_check_answers'].get(f"q{i}")
        
        if q.get("type") == "multiple":
            is_correct = sorted(user_answer) == sorted(q["answer"]) if user_answer else False
        else:
            is_correct = user_answer == q["answer"] if user_answer is not None else False
        
        if is_correct:
            correct += 1
        
        if q.get("type") == "multiple":
            selected_options = [q["options"][j] for j in user_answer] if user_answer else []
            correct_options = [q["options"][j] for j in q["answer"]]
            
            st.markdown(f"### Question {i + 1}: {q['question']}")
            st.markdown(f"**Your answer:** {', '.join(selected_options) if selected_options else 'No selection'}")
            st.markdown(f"**Correct answer:** {', '.join(correct_options)}")
        else:
            st.markdown(f"### Question {i + 1}: {q['question']}")
            st.markdown(f"**Your answer:** {q['options'][user_answer] if user_answer is not None else 'No selection'}")
            st.markdown(f"**Correct answer:** {q['options'][q['answer']]}")
        
        if is_correct:
            st.success("Correct! ✓")
        else:
            st.error("Incorrect ✗")
        
        st.info(f"**Explanation:** {q['explanation']}")
        st.markdown("---")
    
    # Display final score
    st.subheader(f"Final Score: {correct}/{total} ({int(correct/total*100)}%)")
    
    # Restart button
    if st.button("Try Again"):
        st.session_state['knowledge_check_progress'] = 0
        st.session_state['knowledge_check_answers'] = {}
        st.session_state['knowledge_check_results'] = False
        st.experimental_rerun()

# Main application
def main():
    # Apply custom styles
    apply_custom_styles()
    
    # Initialize session
    initialize_session()
    
    # Sidebar content
    with st.sidebar:
        st.image("https://d1.awsstatic.com/training-and-certification/certification-badges/AWS-Certified-Cloud-Practitioner_badge.634f8a21af2e0e956ed8905a72366146ba22b74c.png", width=150)
        st.markdown("## AWS Cloud Practitioner")
        st.markdown("### Content Review Session 1")
        
        with st.expander("About this App", expanded=False):
            st.markdown("""
            This interactive e-learning app covers the following topics:
            
            - **Value Proposition of AWS** - Understand the main advantages of cloud computing
            - **AWS Global Infrastructure** - Learn about Regions, Availability Zones, and Edge Locations
            - **AWS Services** - Explore key AWS services including:
                - Compute (EC2, Lambda)
                - Storage (S3, EBS)
                - Database (RDS, DynamoDB)
                - Networking (VPC, Route 53)
            - **Knowledge Check** - Test your understanding with practice questions
            
            This application is designed to help prepare for the AWS Cloud Practitioner certification.
            """)
        
        if st.button("Reset Session"):
            reset_session()
        
        st.markdown(f"**Session ID:** {st.session_state['session_id'][:8]}...")
    
    # Main content tabs
    tabs = st.tabs(["🏠 Home", "💰 Value Proposition", "🌎 Global Infrastructure", "🛠️ AWS Services", "📝 Knowledge Check"])
    
    with tabs[0]:
        show_home()
    
    with tabs[1]:
        show_value_proposition()
    
    with tabs[2]:
        show_global_infrastructure()
    
    with tabs[3]:
        show_aws_services()
    
    with tabs[4]:
        show_knowledge_check()
    
    # Footer
    st.markdown("""
    <div class="footer">
        © 2025, Amazon Web Services, Inc. or its affiliates. All rights reserved.
    </div>
    """, unsafe_allow_html=True)

if __name__ == "__main__":
    main()
