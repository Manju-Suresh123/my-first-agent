import streamlit as st
from openai import OpenAI
import os

# Page configuration
st.set_page_config(page_title="PL/SQL to Java Migration Analyzer", layout="wide")
st.title("🏦 PL/SQL-to-Java Migration Analyzer")
st.caption("AI-Augmented Senior Tech Lead Utility: Deconstruct legacy procedures into Java 21 services.")

# Synthetic banking sample stored procedure
SAMPLE_PLSQL = """CREATE OR REPLACE PROCEDURE sp_calculate_late_penalty (
    p_account_no       IN  VARCHAR2,
    p_overdue_days     IN  NUMBER,
    p_overdue_balance  IN  NUMBER,
    p_customer_tier    IN  VARCHAR2,
    p_penalty_amount   OUT NUMBER,
    p_status_code      OUT VARCHAR2
) AS
    v_daily_rate NUMBER := 0.0005; -- 0.05% daily rate
    v_base_fee   NUMBER := 25.00;
BEGIN
    -- Grace period: No penalty if overdue <= 5 days
    IF p_overdue_days <= 5 THEN
        p_penalty_amount := 0;
        p_status_code := 'GRACE_PERIOD';
        RETURN;
    END IF;

    -- Calculate base penalty
    p_penalty_amount := v_base_fee + (p_overdue_balance * v_daily_rate * (p_overdue_days - 5));

    -- Cap penalty for VIP customers
    IF p_customer_tier = 'VIP' AND p_penalty_amount > 200.00 THEN
        p_penalty_amount := 200.00;
    ELSIF p_penalty_amount > 500.00 THEN
        p_penalty_amount := 500.00;
    END IF;

    p_status_code := 'PENALTY_ASSESSED';
EXCEPTION
    WHEN OTHERS THEN
        p_penalty_amount := 0;
        p_status_code := 'ERROR_PROCESSING';
END sp_calculate_late_penalty;"""

# Split screen into two columns
col_left, col_right = st.columns([1, 1])

with col_left:
    st.subheader("1. Input PL/SQL Procedure")
    
    if st.button("Load Sample Banking Procedure"):
        st.session_state["plsql_code"] = SAMPLE_PLSQL

    plsql_input = st.text_area(
        "Paste PL/SQL code here:",
        value=st.session_state.get("plsql_code", ""),
        height=380,
        placeholder="CREATE OR REPLACE PROCEDURE..."
    )
    
    analyze_btn = st.button("🚀 Analyze & Generate Migration Report", type="primary")

with col_right:
    st.subheader("2. Modernization Report")
    
    if analyze_btn:
        if not plsql_input.strip():
            st.warning("Please paste or load a PL/SQL procedure first.")
        else:
            api_key = os.getenv("OPENAI_API_KEY")
            if not api_key:
                try:
                    api_key = st.secrets.get("OPENAI_API_KEY") or st.secrets.get("AI_API_KEY")
                except Exception:
                    api_key = None
            if not api_key:
                st.error("API key not found. Please set OPENAI_API_KEY or AI_API_KEY in Streamlit secrets.")
            else:
                client = OpenAI(api_key=api_key)

                # Safe string construction (no f-string syntax conflicts)
                prompt = (
                    "Act as a Principal Java Architect specializing in Banking Modernization.\n"
                    "Analyze this legacy PL/SQL stored procedure and generate a complete Migration Report:\n\n"
                    "```sql\n" + plsql_input + "\n```\n\n"
                    "Format the report strictly with these three sections:\n"
                    "# Section 1: Business Rules Extracted\n"
                    "- Numbered list of all business rules, grace periods, fees, tiers, and caps in plain English.\n"
                    "- Identify any hidden risks, hardcoded constants, or silent exception handling.\n\n"
                    "# Section 2: Modern Java 21 Equivalent Code\n"
                    "- Write a clean Spring Boot @Service using Java 21 (records for DTOs, BigDecimal for math, explicit Scale 2 and RoundingMode.HALF_EVEN).\n"
                    "- Ensure thread safety and immutability.\n\n"
                    "# Section 3: Parity Unit Tests (JUnit 5 & Mockito)\n"
                    "- Generate a test class covering:\n"
                    "  1. Grace period boundary (day 5 vs. day 6).\n"
                    "  2. Tier capping (VIP cap vs. standard cap).\n"
                    "  3. Negative or zero balance handling.\n"
                    "  4. Banker's rounding precision verification.\n"
                )

                with st.spinner("Analyzing rules, generating Java 21 service, and drafting test cases..."):
                    try:
                        response = client.chat.completions.create(
                            model="gpt-4o-mini",
                            messages=[{"role": "user", "content": prompt}],
                            temperature=0.2
                        )
                        report_content = response.choices[0].message.content
                        st.session_state["report"] = report_content
                    except Exception as e:
                        st.error("Error calling API: " + str(e))

    # Display report if available
    if "report" in st.session_state:
        st.markdown(st.session_state["report"])
        
        st.download_button(
            label="📥 Download Report (.md)",
            data=st.session_state["report"],
            file_name="plsql_migration_report.md",
            mime="text/markdown"
        )