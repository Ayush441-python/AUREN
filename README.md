# AUREN

> **See the risk before it sees you.**  
> *Financial risk intelligence · Analytics only, not investment advice.*

AUREN is an open-source, deterministic risk engine for portfolios of stocks and crypto. It measures portfolio risk with plain, tested mathematics, stress-tests against market shocks, and explains findings in transparent language without hallucinations.

---

## What AUREN Measures

1. **Concentration Risk:**
   - **Top Weight:** Percentage of the portfolio in the single largest holding.
   - **Effective Number of Assets ($1 / \text{HHI}$):** Inverse Herfindahl-Hirschman Index showing how many equal-weight assets the portfolio behaves like.
2. **Sector Exposure & Hidden Bets:**
   - Catches portfolios that look diversified across names but are concentrated in a single sector (e.g. Big Tech + correlated assets).
3. **Volatility (Annualised):**
   - Annualised standard deviation of daily portfolio returns ($\sigma \times \sqrt{252}$).
4. **Maximum Drawdown:**
   - Worst peak-to-trough decline over the 2-year lookback period.
5. **Correlation Heatmap & Clustering:**
   - Asset pairwise correlation matrix, highlighting pairs moving tightly together ($r > 0.70$).
6. **Scenario Stress Tests:**
   - Preset shocks (*Big Tech falls 20%*, *Crypto crash 40%*, *NVDA falls 15%*, *Broad selloff*) and custom per-sector sliders with dollar impact estimates.
7. **Liquidity Check (Days to Exit):**
   - Estimated trading days to liquidate each holding assuming 10% of 30-day Average Daily Volume (ADV).
8. **AI Risk Report:**
   - AI report (via Groq/OpenAI/Anthropic) grounded strictly on the deterministic metrics JSON—explains numbers without inventing them.

---

## Transparent Risk Score Rules (0–100)

Every point added to the 0–100 risk score comes with a clear, audited rule:

| Condition / Trigger | Points | Rule Reason Displayed |
| :--- | :---: | :--- |
| **Top holding $> 30\%$** | +20 | Largest holding is $X\%$ (over 30%) |
| **Effective assets $< 4$** | +15 | Behaves like only $X$ assets |
| **Annualised Volatility $> 30\%$** | +20 | Volatility is $X\%$ a year (over 30%) |
| **Max Drawdown $< -30\%$** | +15 | Worst past fall was $X\%$ (deeper than -30%) |
| **Correlated Pairs $\ge 2$ ($r > 0.7$)** | +15 | $N$ pairs of assets move closely together |
| **Sector Concentration $> 50\%$** | +15 | $X\%$ sits in one sector |

- **0 – 34:** Low Risk
- **35 – 64:** Medium Risk
- **65 – 100:** High Risk

---

## Quickstart & Local Setup

### 1. Clone & Install
```bash
git clone https://github.com/Ayush441-python/AUREN.git
cd AUREN
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

### 2. Configure Environment Secrets
Create `.streamlit/secrets.toml` or `.env`:
```toml
LLM_BASE_URL = "https://api.groq.com/openai/v1"
LLM_MODEL = "openai/gpt-oss-120b"
LLM_REASONING_EFFORT = "low"
LLM_API_KEY = "your-api-key-here"
```

### 3. Run the Streamlit Dashboard
```bash
streamlit run app.py
```
Open [http://localhost:8501](http://localhost:8501) in your browser.

### 4. Run the Risk API (FastAPI)
```bash
uvicorn api:app --reload --port 8000
```
- API Docs: [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)
- Interactive Swagger UI to test `/risk` requests.

### 5. Run the Test Suite
```bash
pytest
```

---

## Risk API Example

### `POST /risk`

**Request:**
```json
{
  "weights": {
    "NVDA": 40,
    "MSFT": 30,
    "GOOGL": 20,
    "ETH-USD": 10
  }
}
```

**Response:**
```json
{
  "score": 70,
  "level": "High",
  "reasons": [
    "Largest holding is 40% (over 30%)",
    "Behaves like only 3.3 assets",
    "2 pairs of assets move closely together",
    "90.0% sits in one sector"
  ],
  "concentration": {
    "top_asset": "NVDA",
    "top_weight": 0.4,
    "effective_assets": 3.3333333333333335
  },
  "volatility": 0.285,
  "max_drawdown": -0.221,
  "sector_exposure": {
    "Big Tech": 0.9,
    "Crypto": 0.1
  },
  "stress": {
    "Big Tech falls 20%": -0.18,
    "NVDA falls 15%": -0.06,
    "Crypto crash 40%": -0.04,
    "Broad selloff": -0.165
  },
  "disclaimer": "Analytics only, not investment advice."
}
```

---

## Disclaimer

**Analytics only, not investment advice.** Past performance and statistical correlations do not guarantee future results. AUREN never provides buy, sell, or individualized investment advice.
