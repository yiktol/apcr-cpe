import streamlit as st
import pandas as pd
import time

# Set page config
st.set_page_config(
    page_title="SQL Injection Attack Simulation",
    page_icon="🛡️",
    layout="wide"
)

# CSS for styling
st.markdown("""
<style>
.big-font {
    font-size:24px !important;
    font-weight: bold;
}
.vulnerable-code {
    background-color: #ffdddd;
    border-left: 6px solid #f44336;
    padding: 10px;
    font-family: monospace;
}
.safe-code {
    background-color: #ddffdd;
    border-left: 6px solid #4CAF50;
    padding: 10px;
    font-family: monospace;
}
.terminal {
    background-color: #1e1e1e;
    color: #dcdcdc;
    padding: 10px;
    border-radius: 5px;
    font-family: monospace;
}
.warning {
    background-color: #fffacd;
    border-left: 6px solid #ffd700;
    padding: 10px;
}
</style>
""", unsafe_allow_html=True)

# Title and disclaimer
st.title("SQL Injection Attack Simulation")
st.markdown("""
<div class="warning">
<b>DISCLAIMER:</b> This application is for educational purposes only. 
Performing SQL injection attacks on real websites without permission is illegal and unethical.
The simulated target website "https://www.aws.yikyakyu.com" is fictional.
</div>
""", unsafe_allow_html=True)

# Sidebar with explanation
with st.sidebar:
    st.markdown("### What is SQL Injection?")
    st.write("""
    SQL Injection is a code injection technique that exploits vulnerabilities in 
    applications that interact with databases. Attackers can insert malicious SQL 
    statements that can read, modify, or delete data from databases.
    """)
    
    st.markdown("### Common SQL Injection Techniques")
    st.write("""
    - **Union-based**: Using UNION operator to combine results
    - **Error-based**: Extracting data through error messages
    - **Boolean-based**: Using TRUE/FALSE conditions
    - **Time-based**: Inferring data based on response time
    """)
    
    st.markdown("### Prevention Methods")
    st.write("""
    - Use parameterized queries
    - Input validation
    - Least privilege principle
    - Web Application Firewalls (WAF)
    - Regular security testing
    """)

# Mock database setup
@st.cache_data
def load_mock_data():
    users = pd.DataFrame({
        'id': range(1, 6),
        'username': ['admin', 'john', 'alice', 'bob', 'carol'],
        'password': ['s3cur3p@ss!', 'john123', 'alice456', 'bob789', 'carol101'],
        'email': ['admin@company.com', 'john@example.com', 'alice@example.com', 'bob@example.com', 'carol@example.com'],
        'role': ['admin', 'user', 'user', 'user', 'user']
    })
    
    products = pd.DataFrame({
        'id': range(1, 6),
        'name': ['Laptop', 'Phone', 'Tablet', 'Smartwatch', 'Headphones'],
        'price': [999.99, 699.99, 499.99, 299.99, 149.99],
        'stock': [45, 120, 75, 60, 200]
    })
    
    return users, products

users_db, products_db = load_mock_data()

# Tabs for different parts of the simulation
tab1, tab2, tab3 = st.tabs(["Login Form Attack", "Search Form Attack", "Prevention Methods"])

with tab1:
    st.header("Login Form SQL Injection")
    
    st.markdown("""
    <p class="big-font">Vulnerable Login Form</p>
    <p>This simulates a typical login form vulnerable to SQL injection.</p>
    """, unsafe_allow_html=True)
    
    col1, col2 = st.columns(2)
    
    with col1:
        username = st.text_input("Username")
        password = st.text_input("Password", type="password")
        login_btn = st.button("Login")
        
        st.markdown("""
        <p>Try these SQL injection payloads:</p>
        <ul>
            <li><code>' OR '1'='1</code> (as username, leave password empty)</li>
            <li><code>admin' --</code> (as username, leave password empty)</li>
        </ul>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown("""
        <p>Vulnerable server-side code:</p>
        <div class="vulnerable-code">
        query = "SELECT * FROM users WHERE username = '" + username + "' AND password = '" + password + "'";
        </div>
        """, unsafe_allow_html=True)
    
    if login_btn:
        st.markdown("### Query executed:")
        vulnerable_query = f"SELECT * FROM users WHERE username = '{username}' AND password = '{password}'"
        st.code(vulnerable_query, language="sql")
        
        # Simulate SQL injection vulnerability
        if "' OR '1'='1" in username or "' OR '1'='1" in password:
            st.success("Login successful! You've bypassed authentication.")
            st.dataframe(users_db)
        elif "admin' --" in username:
            st.success("Login successful as admin! The comment (--) ignored the password check.")
            st.dataframe(users_db[users_db['username'] == 'admin'])
        elif username in users_db['username'].values:
            user = users_db[users_db['username'] == username]
            if password in user['password'].values:
                st.success(f"Login successful as {username}")
                st.dataframe(user)
            else:
                st.error("Incorrect password")
        else:
            st.error("Login failed")

with tab2:
    st.header("Product Search SQL Injection")
    
    st.markdown("""
    <p class="big-font">Vulnerable Search Form</p>
    <p>This simulates a product search feature vulnerable to SQL injection.</p>
    """, unsafe_allow_html=True)
    
    col1, col2 = st.columns(2)
    
    with col1:
        search_term = st.text_input("Search products")
        search_btn = st.button("Search")
        
        st.markdown("""
        <p>Try these SQL injection payloads:</p>
        <ul>
            <li><code>' OR '1'='1</code> (to see all products)</li>
            <li><code>' UNION SELECT id, username, password, email, role FROM users --</code> (to extract user data)</li>
            <li><code>' OR 1=1 ORDER BY price DESC --</code> (to order results)</li>
        </ul>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown("""
        <p>Vulnerable server-side code:</p>
        <div class="vulnerable-code">
        query = "SELECT * FROM products WHERE name LIKE '%" + search_term + "%'";
        </div>
        """, unsafe_allow_html=True)
    
    if search_btn:
        st.markdown("### Query executed:")
        vulnerable_query = f"SELECT * FROM products WHERE name LIKE '%{search_term}%'"
        st.code(vulnerable_query, language="sql")
        
        # Simulate the search results including SQL injection vulnerability
        if "' OR '1'='1" in search_term:
            st.success("Query successful - showing all products!")
            st.dataframe(products_db)
        elif "UNION SELECT" in search_term and "FROM users" in search_term:
            st.success("SQL Injection successful! Extracted user data:")
            st.dataframe(users_db)
            st.error("Critical security breach - user credentials exposed!")
        elif "ORDER BY" in search_term:
            if "DESC" in search_term:
                st.success("Query successful - ordered by price descending!")
                st.dataframe(products_db.sort_values('price', ascending=False))
            else:
                st.success("Query successful - ordered by price ascending!")
                st.dataframe(products_db.sort_values('price'))
        else:
            # Normal search behavior
            results = products_db[products_db['name'].str.contains(search_term, case=False)]
            if not results.empty:
                st.dataframe(results)
            else:
                st.info("No products found matching your search.")

with tab3:
    st.header("SQL Injection Prevention")
    
    st.markdown("""
    <p class="big-font">How to Prevent SQL Injection Attacks</p>
    """, unsafe_allow_html=True)
    
    # Demonstrate parameterized queries
    st.subheader("1. Use Parameterized Queries")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("""
        <div class="vulnerable-code">
        // Vulnerable code
        query = "SELECT * FROM users WHERE username = '" + username + "' AND password = '" + password + "'";
        stmt = connection.createStatement();
        rs = stmt.executeQuery(query);
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown("""
        <div class="safe-code">
        // Secure code with parameterized query
        query = "SELECT * FROM users WHERE username = ? AND password = ?";
        PreparedStatement stmt = connection.prepareStatement(query);
        stmt.setString(1, username);
        stmt.setString(2, password);
        rs = stmt.executeQuery();
        </div>
        """, unsafe_allow_html=True)
    
    # Input validation
    st.subheader("2. Input Validation")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("""
        <div class="vulnerable-code">
        // No validation
        username = request.getParameter("username");
        // Use directly in query
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown("""
        <div class="safe-code">
        // With validation
        username = request.getParameter("username");
        if (!username.matches("[a-zA-Z0-9_]+")) {
            throw new ValidationException("Invalid username");
        }
        </div>
        """, unsafe_allow_html=True)
    
    # ORM Usage
    st.subheader("3. Use ORM Frameworks")
    
    st.markdown("""
    <div class="safe-code">
    // Using an ORM like SQLAlchemy (Python)
    user = session.query(User).filter(
        User.username == username,
        User.password == password
    ).first()
    </div>
    """, unsafe_allow_html=True)
    
    # Least privilege
    st.subheader("4. Apply Least Privilege Principle")
    
    st.markdown("""
    <div class="safe-code">
    // Create a database user with limited permissions
    CREATE USER 'app_user'@'localhost' IDENTIFIED BY 'password';
    GRANT SELECT, INSERT, UPDATE ON application.* TO 'app_user'@'localhost';
    // No DROP, ALTER, or other admin privileges
    </div>
    """, unsafe_allow_html=True)
    
    # WAF
    st.subheader("5. Implement Web Application Firewalls")
    
    st.image("https://miro.medium.com/max/1400/1*qXS8XBUDr6x04Ou7xCj8Ng.png", 
             caption="Web Application Firewall Protection", width=600)

    # Live protection demo
    st.subheader("Demo: Input Sanitization")
    
    dangerous_input = st.text_input("Enter a potentially dangerous input:")
    if st.button("Sanitize Input"):
        with st.spinner("Sanitizing input..."):
            time.sleep(1)
            
            # Show the sanitization process
            st.markdown("### Sanitization Process:")
            st.code(f"""
# Original input
input = "{dangerous_input}"

# Remove SQL injection patterns
input = input.replace("'", "''")  # Escape single quotes
input = re.sub(r"(?i)(SELECT|UNION|INSERT|UPDATE|DELETE|DROP|ALTER|EXEC|--|;)", "", input)

# Result
sanitized_input = "{dangerous_input.replace("'", "''").replace(';', '').replace('--', '')}"
            """)
            
            st.success(f"Sanitized input: {dangerous_input.replace('\'', '\'\'').replace(';', '').replace('--', '')}")

# Footer
st.markdown("---")
st.markdown("""
<center>⚠️ Remember: Use this knowledge responsibly and ethically. SQL injection attacks against real systems without permission are illegal. ⚠️</center>
""", unsafe_allow_html=True)
