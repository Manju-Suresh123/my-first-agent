import os
import re
import streamlit as st

# Page configuration
st.set_page_config(page_title="PL/SQL to Java Migration Analyzer", layout="wide")
st.title("🏦 PL/SQL-to-Java Migration Analyzer")
st.caption("AI-Augmented Senior Tech Lead Utility: Deconstruct legacy procedures into Java 21 services.")


def setting(name: str, default: str = "") -> str:
    """Read a setting from Streamlit secrets first, then from the environment."""
    try:
        value = st.secrets.get(name, "")
    except Exception:
        value = ""
    return str(value or os.getenv(name, default)).strip()


api_key = setting("AI_API_KEY") or setting("OPENAI_API_KEY")
base_url = setting("AI_BASE_URL")
model = setting("AI_MODEL")

# Auto-detect or normalize Google Gemini endpoint
if base_url:
    if "generativelanguage.googleapis.com" in base_url.lower():
        base_url = "https://generativelanguage.googleapis.com/v1beta/openai/"
        if not model or model in ("gpt-4o-mini", "gemini-2.5-flash", "gemini-2.5"):
            model = "gemini-1.5-flash"
    else:
        base_url = re.sub(r"/openai/?$", "/openai/", base_url, flags=re.I)
elif api_key and (api_key.startswith("AIza") or api_key.startswith("AQ.")):
    base_url = "https://generativelanguage.googleapis.com/v1beta/openai/"
    if not model or model in ("gpt-4o-mini", "gemini-2.5-flash", "gemini-2.5"):
        model = "gemini-1.5-flash"

if not base_url:
    base_url = "https://api.openai.com/v1"
if not model:
    model = "gpt-4o-mini"

is_demo = not api_key or api_key.lower() in ("demo", "paste-your-key-here", "none")

if is_demo:
    st.info("ℹ️ **Demo Mode:** The app runs without an API key using built-in analyzer rules. Add an API key in Streamlit secrets anytime to use a live AI model.")
else:
    st.success(f"✅ **Live AI Mode:** Connected using model `{model}`.")

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


def generate_demo_report(plsql: str) -> str:
    """Generate a realistic modernization report in Demo Mode without requiring an API key."""
    if "sp_calculate_late_penalty" in plsql:
        return """# Section 1: Business Rules Extracted
1. **Grace Period**: No late penalty is assessed if overdue days are 5 or fewer (`p_overdue_days <= 5`).
2. **Base Penalty Assessment**: For overdue periods exceeding 5 days, a base fee of $25.00 is assessed plus a daily penalty fee.
3. **Daily Penalty Rate**: Daily rate of 0.05% (`0.0005`) calculated on the overdue balance for each day beyond the grace period:
   `penalty = 25.00 + (overdue_balance * 0.0005 * (overdue_days - 5))`
4. **Tier Capping**:
   - **VIP Tier**: Penalty is capped at a maximum of $200.00.
   - **Standard / Non-VIP Tier**: Penalty is capped at a maximum of $500.00.
5. **Exception Handling**: Unhandled errors reset penalty amount to $0.00 and return status code `ERROR_PROCESSING`.

### Identified Risks & Technical Debt:
- **Hardcoded Constants**: Base fee ($25), daily rate (0.0005), and tier caps ($200/$500) are embedded in code rather than configured in database parameters.
- **Silent Exception Swallowing**: `WHEN OTHERS` block catches all errors and resets penalty to 0 without logging or raising alerts.
- **Missing Validations**: No input validation for negative balance or negative overdue days.

---

# Section 2: Modern Java 21 Equivalent Code

```java
package com.bank.billing.service;

import org.springframework.stereotype.Service;
import java.math.BigDecimal;
import java.math.RoundingMode;
import java.util.Objects;

@Service
public class PenaltyCalculationService {

    private static final int GRACE_PERIOD_DAYS = 5;
    private static final BigDecimal BASE_FEE = new BigDecimal("25.00");
    private static final BigDecimal DAILY_RATE = new BigDecimal("0.0005");
    private static final BigDecimal VIP_CAP = new BigDecimal("200.00");
    private static final BigDecimal STANDARD_CAP = new BigDecimal("500.00");

    public record PenaltyRequest(
        String accountNo,
        int overdueDays,
        BigDecimal overdueBalance,
        String customerTier
    ) {}

    public record PenaltyResponse(
        BigDecimal penaltyAmount,
        String statusCode
    ) {}

    public PenaltyResponse calculatePenalty(PenaltyRequest request) {
        Objects.requireNonNull(request, "Request must not be null");

        // 1. Grace period check
        if (request.overdueDays() <= GRACE_PERIOD_DAYS) {
            return new PenaltyResponse(BigDecimal.ZERO.setScale(2, RoundingMode.HALF_EVEN), "GRACE_PERIOD");
        }

        // 2. Base + Daily rate calculation
        int billableDays = request.overdueDays() - GRACE_PERIOD_DAYS;
        BigDecimal dailyCharge = request.overdueBalance()
                .multiply(DAILY_RATE)
                .multiply(BigDecimal.valueOf(billableDays));

        BigDecimal rawPenalty = BASE_FEE.add(dailyCharge).setScale(2, RoundingMode.HALF_EVEN);

        // 3. Customer tier cap
        BigDecimal cap = "VIP".equalsIgnoreCase(request.customerTier()) ? VIP_CAP : STANDARD_CAP;
        BigDecimal finalPenalty = rawPenalty.min(cap);

        return new PenaltyResponse(finalPenalty, "PENALTY_ASSESSED");
    }
}
```

---

# Section 3: Parity Unit Tests (JUnit 5 & Mockito)

```java
package com.bank.billing.service;

import org.junit.jupiter.api.DisplayName;
import org.junit.jupiter.api.Test;
import java.math.BigDecimal;
import static org.junit.jupiter.api.Assertions.*;

class PenaltyCalculationServiceTest {

    private final PenaltyCalculationService service = new PenaltyCalculationService();

    @Test
    @DisplayName("1. Grace period boundary: Day 5 has no penalty, Day 6 assesses penalty")
    void testGracePeriodBoundary() {
        var day5 = service.calculatePenalty(new PenaltyCalculationService.PenaltyRequest(
            "ACC001", 5, new BigDecimal("1000.00"), "STANDARD"));
        assertEquals(new BigDecimal("0.00"), day5.penaltyAmount());
        assertEquals("GRACE_PERIOD", day5.statusCode());

        var day6 = service.calculatePenalty(new PenaltyCalculationService.PenaltyRequest(
            "ACC001", 6, new BigDecimal("1000.00"), "STANDARD"));
        // 25.00 + (1000 * 0.0005 * 1) = 25.50
        assertEquals(new BigDecimal("25.50"), day6.penaltyAmount());
        assertEquals("PENALTY_ASSESSED", day6.statusCode());
    }

    @Test
    @DisplayName("2. Tier capping: VIP capped at 200, Standard capped at 500")
    void testTierCapping() {
        var vip = service.calculatePenalty(new PenaltyCalculationService.PenaltyRequest(
            "ACC002", 60, new BigDecimal("100000.00"), "VIP"));
        assertEquals(new BigDecimal("200.00"), vip.penaltyAmount());

        var std = service.calculatePenalty(new PenaltyCalculationService.PenaltyRequest(
            "ACC003", 60, new BigDecimal("100000.00"), "STANDARD"));
        assertEquals(new BigDecimal("500.00"), std.penaltyAmount());
    }

    @Test
    @DisplayName("3. Banker's rounding precision verification")
    void testBankersRounding() {
        var res = service.calculatePenalty(new PenaltyCalculationService.PenaltyRequest(
            "ACC004", 7, new BigDecimal("1333.33"), "STANDARD"));
        assertNotNull(res.penaltyAmount());
        assertEquals(2, res.penaltyAmount().scale());
    }
}
```
*(Report generated in Demo Mode)*"""
    else:
        lines = [line.strip() for line in plsql.splitlines() if line.strip()]
        return f"""# Section 1: Business Rules Extracted (Demo Mode)
- **Extracted Procedure**: Analyzed {len(lines)} lines of PL/SQL stored procedure.
- **Key Logic Identified**: Conditional branching (`IF/THEN`), variable assignment, and exception handling blocks.
- **Potential Modernization Areas**: Replace database procedural logic with Spring Boot stateless services.

---

# Section 2: Modern Java 21 Equivalent Code

```java
package com.bank.service;

import org.springframework.stereotype.Service;

@Service
public class ModernizedService {{
    public record RequestDto(String id, double amount) {{}}
    public record ResponseDto(String status, String message) {{}}

    public ResponseDto execute(RequestDto request) {{
        return new ResponseDto("SUCCESS", "Processed successfully in Java 21");
    }}
}}
```

---

# Section 3: Parity Unit Tests (JUnit 5)

```java
package com.bank.service;

import org.junit.jupiter.api.Test;
import static org.junit.jupiter.api.Assertions.*;

class ModernizedServiceTest {{
    @Test
    void testExecution() {{
        var service = new ModernizedService();
        var response = service.execute(new ModernizedService.RequestDto("001", 100.0));
        assertEquals("SUCCESS", response.status());
    }}
}}
```
*(Report generated in Demo Mode. Add an API key in Streamlit secrets for a custom live LLM analysis)*"""


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
        placeholder="CREATE OR REPLACE PROCEDURE...",
    )

    analyze_btn = st.button("🚀 Analyze & Generate Migration Report", type="primary")

with col_right:
    st.subheader("2. Modernization Report")

    if analyze_btn:
        if not plsql_input.strip():
            st.warning("Please paste or load a PL/SQL procedure first.")
        elif is_demo:
            with st.spinner("Analyzing rules and generating modernization report (Demo Mode)..."):
                st.session_state["report"] = generate_demo_report(plsql_input)
        else:
            from openai import OpenAI

            client = OpenAI(api_key=api_key, base_url=base_url or None)

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

            with st.spinner(f"Analyzing rules, generating Java 21 service, and drafting test cases with {model}..."):
                try:
                    response = client.chat.completions.create(
                        model=model,
                        messages=[{"role": "user", "content": prompt}],
                        temperature=0.2,
                    )
                    report_content = response.choices[0].message.content
                    st.session_state["report"] = report_content
                except Exception as e:
                    st.error(f"Error calling API ({base_url}): {e}")

    # Display report if available
    if "report" in st.session_state:
        st.markdown(st.session_state["report"])

        st.download_button(
            label="📥 Download Report (.md)",
            data=st.session_state["report"],
            file_name="plsql_migration_report.md",
            mime="text/markdown",
        )
