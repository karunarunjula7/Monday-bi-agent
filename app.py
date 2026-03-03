from fastapi import FastAPI
from pydantic import BaseModel
import requests
import json
import os
from datetime import datetime

app = FastAPI()

# ===============================
# CONFIGURATION
# ===============================

MONDAY_API_KEY = os.getenv("MONDAY_API_KEY")

if not MONDAY_API_KEY:
    raise ValueError("MONDAY_API_KEY environment variable not set.")

DEALS_BOARD_ID = 5026959985
WORK_ORDERS_BOARD_ID = 5026960021

MONDAY_URL = "https://api.monday.com/v2"

headers = {
    "Authorization": MONDAY_API_KEY,
    "Content-Type": "application/json"
}


class QueryRequest(BaseModel):
    question: str


# ===============================
# UTILITY FUNCTIONS
# ===============================

def parse_number(value):
    if not value:
        return 0
    try:
        cleaned = (
            str(value)
            .replace("₹", "")
            .replace("$", "")
            .replace(",", "")
            .strip()
        )
        return float(cleaned)
    except:
        return 0


def parse_date(value):
    if not value:
        return None

    formats = ["%Y-%m-%d", "%d-%m-%Y", "%b %d, %Y"]

    for fmt in formats:
        try:
            return datetime.strptime(value, fmt)
        except:
            continue

    return None


def is_current_quarter(date_obj):
    if not date_obj:
        return False

    now = datetime.now()
    current_q = (now.month - 1) // 3 + 1
    item_q = (date_obj.month - 1) // 3 + 1

    return now.year == date_obj.year and current_q == item_q


def fetch_board_data(board_id, trace_log):
    trace_log.append(f"Live API Call → Fetching board {board_id}")

    query = f"""
    query {{
        boards(ids: {board_id}) {{
            items_page(limit: 500) {{
                items {{
                    name
                    column_values {{
                        text
                        value
                        column {{
                            title
                        }}
                    }}
                }}
            }}
        }}
    }}
    """

    try:
        response = requests.post(
            MONDAY_URL,
            json={"query": query},
            headers=headers
        )
        result = response.json()
    except Exception as e:
        trace_log.append(f"API Error: {str(e)}")
        return None

    if "data" not in result or not result["data"]["boards"]:
        trace_log.append("No board data returned.")
        return None

    return result


# ===============================
# MAIN ENDPOINT
# ===============================

@app.post("/ask")
def ask_question(request: QueryRequest):

    question = request.question.lower()
    trace_log = ["User question received"]

    # Basic Intent Detection
    if not any(keyword in question for keyword in ["pipeline", "deal", "revenue", "work"]):
        return {
            "clarification_needed": "Are you asking about deals, pipeline, revenue, or work orders?"
        }

    deals_raw = fetch_board_data(DEALS_BOARD_ID, trace_log)
    work_raw = fetch_board_data(WORK_ORDERS_BOARD_ID, trace_log)

    if not deals_raw:
        return {"error": "Deals board not accessible."}

    if not work_raw:
        return {"error": "Work orders board not accessible."}

    deals_items = deals_raw["data"]["boards"][0]["items_page"]["items"]
    work_items = work_raw["data"]["boards"][0]["items_page"]["items"]

    total_pipeline = 0
    deal_count = 0
    sector_summary = {}
    missing_values = 0

    known_sectors = [
        "mining", "powerline", "tender", "renewables",
        "railways", "construction", "aviation",
        "manufacturing", "dsp", "security", "others"
    ]

    sector_filter = None
    for sec in known_sectors:
        if sec in question:
            sector_filter = sec
            trace_log.append(f"Sector filter detected: {sec}")
            break

    quarter_filter = "quarter" in question
    if quarter_filter:
        trace_log.append("Quarter filter applied: Current Quarter")

    for item in deals_items:

        sector = "unknown"
        value = 0
        close_date = None

        for col in item["column_values"]:

            title = col["column"]["title"].lower()
            text_val = col.get("text")
            raw_val = col.get("value")

            final_value = text_val

            if (not text_val) and raw_val:
                try:
                    parsed = json.loads(raw_val)
                    if isinstance(parsed, dict):
                        final_value = parsed.get("label") or parsed.get("text")
                except:
                    final_value = raw_val

            if not final_value:
                missing_values += 1

            if any(x in title for x in ["sector", "industry", "vertical"]):
                sector = final_value.strip().lower() if final_value else "unknown"

            if any(x in title for x in ["value", "amount", "revenue"]):
                value = parse_number(final_value)

            if "date" in title:
                close_date = parse_date(final_value)

        if sector_filter and sector_filter not in sector:
            continue

        if quarter_filter and not is_current_quarter(close_date):
            continue

        total_pipeline += value
        deal_count += 1
        sector_summary[sector] = sector_summary.get(sector, 0) + value

    # Work order only query
    if "work" in question and "pipeline" not in question:
        trace_log.append("Work order insight generated")
        return {
            "trace": trace_log,
            "insight": f"There are {len(work_items)} total work orders.",
            "data_quality_note": f"{missing_values} empty fields handled safely."
        }

    if deal_count == 0:
        return {
            "trace": trace_log,
            "insight": "No matching data found for requested filters.",
            "data_quality_note": f"{missing_values} empty fields handled safely."
        }

    # ===============================
    # EXECUTIVE INSIGHTS
    # ===============================

    avg_deal_size = total_pipeline / deal_count if deal_count else 0

    largest_sector = max(sector_summary, key=sector_summary.get)
    concentration_ratio = sector_summary[largest_sector] / total_pipeline

    if total_pipeline > 10_000_000:
        health = "Strong"
    elif total_pipeline > 5_000_000:
        health = "Moderate"
    else:
        health = "Weak"

    executive_summary = (
        f"Pipeline health is {health}. "
        f"Total pipeline is ₹{total_pipeline:,.2f} across {deal_count} deals. "
        f"Average deal size is ₹{avg_deal_size:,.2f}. "
        f"Largest sector is '{largest_sector}' contributing {concentration_ratio:.0%} of pipeline."
    )

    trace_log.append("Executive-level insight generated")

    return {
        "trace": trace_log,
        "executive_summary": executive_summary,
        "sector_breakdown": sector_summary,
        "data_quality_note": f"{missing_values} empty fields handled safely."
    }