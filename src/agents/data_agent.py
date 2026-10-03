import os
import io
import re
import urllib.request
import numpy as np
import pandas as pd
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

try:
    from ddgs import DDGS
except ImportError:
    try:
        from duckduckgo_search import DDGS
    except ImportError:
        DDGS = None

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
GENERATED_DIR = PROJECT_ROOT / "generated"


def extract_search_queries(query: str) -> list[str]:
    """
    Extracts short, high-relevance search queries from long conversational prompts.
    """
    stop_words = {
        "analysis", "of", "and", "the", "in", "for", "with", "a", "an", "to", "on", 
        "project", "study", "prediction", "system", "using", "based", "classification",
        "detection", "overview", "show", "shows", "give", "me", "predict", "analyze"
    }
    words = [w for w in re.findall(r'[a-zA-Z0-9]+', query.lower()) if len(w) > 1]
    core_words = [w for w in words if w not in stop_words]

    queries = []
    if "tata" in words or "steel" in words:
        queries.append("tata steel stock price csv github")
        queries.append("tata steel historical stock data csv")
    elif any(k in words for k in ["stock", "share", "price", "crypto", "forex", "trading"]):
        queries.append(f"{' '.join(core_words[:2])} stock price csv github")
        queries.append(f"{' '.join(core_words[:2])} historical data csv")
    elif "netflix" in words:
        queries.append("netflix movies dataset csv")
        queries.append("netflix comments reviews csv")
    elif len(core_words) >= 2:
        queries.append(f"{' '.join(core_words[:3])} github csv")
        queries.append(f"{' '.join(core_words[:2])} dataset filetype:csv")
    elif core_words:
        queries.append(f"{core_words[0]} dataset csv")
    else:
        queries.append(f"{query[:25]} csv")

    return queries[:2]


def search_tavily_for_csv(query: str, max_results: int = 5) -> tuple[pd.DataFrame | None, str | None]:
    """
    Uses Tavily Search API for AI-optimized web retrieval of raw CSV datasets.
    """
    api_key = os.environ.get("TAVILY_API_KEY")
    if not api_key:
        return None, None

    try:
        from tavily import TavilyClient
        client = TavilyClient(api_key=api_key)
        search_queries = extract_search_queries(query)

        # Enhance queries to explicitly target GitHub CSV repositories and files
        candidate_queries = []
        for sq in search_queries:
            candidate_queries.append(f"site:github.com {sq} csv")
            candidate_queries.append(sq)

        headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}

        for cq in candidate_queries[:3]:
            try:
                resp = client.search(cq, max_results=max_results, search_depth="basic")
                results = resp.get("results", [])
            except Exception:
                continue

            for r in results:
                url = r.get("url", "")
                if not url:
                    continue

                candidate_urls = []
                # Direct CSV or blob
                if "raw.githubusercontent.com" in url and ".csv" in url.lower():
                    candidate_urls.append(url)
                elif "github.com" in url and "/blob/" in url and ".csv" in url.lower():
                    clean_url = url.split("?")[0]
                    candidate_urls.append(clean_url.replace("github.com/", "raw.githubusercontent.com/").replace("/blob/", "/"))
                elif "github.com" in url and "/blob/" not in url:
                    # Check repository landing page for CSV links
                    try:
                        req = urllib.request.Request(url, headers=headers)
                        with urllib.request.urlopen(req, timeout=3) as page_stream:
                            page_html = page_stream.read(500_000).decode("utf-8", errors="replace")
                            matches = re.findall(r'href="([^"]+\.csv)"', page_html)
                            for m in matches:
                                if m.startswith("/"):
                                    m = f"https://github.com{m}"
                                if "/blob/" in m:
                                    raw_u = m.replace("github.com/", "raw.githubusercontent.com/").replace("/blob/", "/")
                                    candidate_urls.append(raw_u)
                    except Exception:
                        pass
                elif url.lower().endswith(".csv"):
                    candidate_urls.append(url)

                for target_url in candidate_urls:
                    try:
                        req = urllib.request.Request(target_url, headers=headers)
                        with urllib.request.urlopen(req, timeout=4) as resp_stream:
                            data = resp_stream.read(2_000_000)
                            text = data.decode("utf-8", errors="replace")
                            df = pd.read_csv(io.StringIO(text))

                            if len(df) >= 5 and len(df.columns) >= 2:
                                df.columns = [str(c).strip() for c in df.columns]

                                # Ensure financial datasets have actual price/numeric data
                                is_stock_req = any(k in query.lower() for k in ["stock", "price", "share", "tata", "steel", "forecast", "trading"])
                                if is_stock_req:
                                    has_price_col = any(any(k in str(c).lower() for k in ['close', 'price', 'open', 'high', 'low', 'nav', 'last']) for c in df.columns)
                                    has_numeric = len(df.select_dtypes(include=[np.number]).columns) > 0
                                    if not (has_price_col or has_numeric):
                                        continue

                                if len(df) > 250:
                                    if is_stock_req:
                                        df = df.tail(250).reset_index(drop=True)
                                    else:
                                        df = df.head(250).reset_index(drop=True)
                                return df, target_url
                    except Exception:
                        continue

    except Exception:
        pass

    return None, None


def search_duckduckgo_for_csv(query: str, max_results: int = 4) -> tuple[pd.DataFrame | None, str | None]:
    """
    Autonomously searches DuckDuckGo for real-world CSV datasets matching the query.
    """
    if DDGS is None:
        return None, None

    search_queries = extract_search_queries(query)

    for sq in search_queries:
        try:
            results = list(DDGS().text(sq, max_results=max_results))
        except Exception:
            continue

        for r in results:
            url = r.get("href", "")
            if not url:
                continue

            target_url = url
            if "github.com" in url and "/blob/" in url and url.lower().endswith(".csv"):
                target_url = url.replace("github.com/", "raw.githubusercontent.com/").replace("/blob/", "/")
            elif "raw.githubusercontent.com" in url:
                target_url = url
            elif not url.lower().endswith(".csv"):
                continue

            try:
                req = urllib.request.Request(
                    target_url,
                    headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
                )
                with urllib.request.urlopen(req, timeout=4) as resp:
                    data = resp.read(2_000_000)
                    text = data.decode("utf-8", errors="replace")
                    df = pd.read_csv(io.StringIO(text))

                    if len(df) >= 5 and len(df.columns) >= 2:
                        df.columns = [str(c).strip() for c in df.columns]

                        is_stock_req = any(k in query.lower() for k in ["stock", "price", "share", "tata", "steel", "forecast", "trading"])
                        if is_stock_req:
                            has_price_col = any(any(k in str(c).lower() for k in ['close', 'price', 'open', 'high', 'low', 'nav', 'last']) for c in df.columns)
                            has_numeric = len(df.select_dtypes(include=[np.number]).columns) > 0
                            if not (has_price_col or has_numeric):
                                continue

                        if len(df) > 250:
                            if is_stock_req:
                                df = df.tail(250).reset_index(drop=True)
                            else:
                                df = df.head(250).reset_index(drop=True)
                        return df, target_url
            except Exception:
                continue

    return None, None


def get_domain_fallback_dataset(topic: str) -> pd.DataFrame:
    """
    Intelligent domain-specific dataset generator ensuring realistic rows & columns
    whenever synthetic LLM parsing needs a structured backup.
    """
    topic_lower = topic.lower()
    np.random.seed(42)
    n = 40

    # 1. Telecom / Churn (e.g. Reliance, Jio, Airtel, Telecom Churn)
    if any(k in topic_lower for k in ["churn", "reliance", "telecom", "jio", "customer", "retention"]):
        return pd.DataFrame({
            "customer_id": [f"REL_{1000 + i}" for i in range(n)],
            "plan_type": np.random.choice(["Prepaid 4G", "Postpaid 5G", "JioFiber Home", "Prepaid Unlimited"], n),
            "tenure_months": np.random.randint(1, 48, n),
            "monthly_recharge_inr": np.random.choice([199, 299, 499, 666, 999, 1499], n),
            "data_usage_gb": np.round(np.random.uniform(5.0, 95.0, n), 1),
            "customer_service_calls": np.random.randint(0, 6, n),
            "contract_type": np.random.choice(["Month-to-Month", "1-Year", "2-Year"], n, p=[0.6, 0.25, 0.15]),
            "churn": np.random.choice([0, 1], n, p=[0.72, 0.28])
        })

    # 2. Student / Education
    if any(k in topic_lower for k in ["student", "exam", "grade", "education", "school"]):
        return pd.DataFrame({
            "student_id": [f"STU_{2000 + i}" for i in range(n)],
            "study_hours_per_week": np.random.randint(5, 35, n),
            "attendance_pct": np.random.randint(60, 100, n),
            "sleep_hours": np.random.choice([5.5, 6.0, 6.5, 7.0, 7.5, 8.0, 8.5], n),
            "previous_score": np.random.randint(50, 95, n),
            "tutoring": np.random.choice(["Yes", "No"], n),
            "final_score": np.random.randint(45, 100, n)
        })

    # 3. Sales / Retail / Revenue
    if any(k in topic_lower for k in ["sale", "revenue", "retail", "store", "product", "ecommerce"]):
        return pd.DataFrame({
            "order_id": [f"ORD_{5000 + i}" for i in range(n)],
            "product_category": np.random.choice(["Electronics", "Fashion", "Groceries", "Home & Living"], n),
            "units_sold": np.random.randint(1, 15, n),
            "unit_price_usd": np.round(np.random.uniform(10.0, 250.0, n), 2),
            "discount_pct": np.random.choice([0.0, 0.05, 0.10, 0.15, 0.20], n),
            "customer_rating": np.random.choice([3, 4, 5], n, p=[0.2, 0.5, 0.3]),
            "payment_method": np.random.choice(["UPI", "Credit Card", "Net Banking", "Cash on Delivery"], n)
        })

    # 4. Movies / Netflix / Entertainment / Comments / Sentiment
    if any(k in topic_lower for k in ["netflix", "movie", "tv", "comment", "review", "sentiment", "film", "positive", "negative", "show"]):
        titles = [
            "Stranger Things", "The Crown", "Squid Game", "Wednesday", "Black Mirror",
            "Ozark", "Money Heist", "The Witcher", "Breaking Bad", "Dark"
        ]
        pos_comments = [
            "Exceptional storytelling, brilliant character arcs, and fantastic cinematography.",
            "Visual effects and soundtrack are top-tier. Highly recommended binge-watch!",
            "Brilliant acting and gripping plot twists from start to finish.",
            "Masterpiece! One of the best productions ever released on the platform.",
            "Compelling dialogue, high production quality, and perfect pacing."
        ]
        neg_comments = [
            "Pacing dragged heavily in the middle episodes with too much filler.",
            "Disappointing finale with unresolved storylines and shallow character choices.",
            "Predictable storyline, weak acting, and clichéd dialogue.",
            "Not worth the hype; season started strong but lost all direction.",
            "Felt rushed, confusing timeline, and lacked emotional depth."
        ]
        sentiments = np.random.choice(["Positive", "Negative"], n, p=[0.62, 0.38])
        comments = [
            np.random.choice(pos_comments) if s == "Positive" else np.random.choice(neg_comments)
            for s in sentiments
        ]
        ratings = [
            np.random.choice([4, 5]) if s == "Positive" else np.random.choice([1, 2, 3])
            for s in sentiments
        ]

        return pd.DataFrame({
            "comment_id": [f"REV_{1000 + i}" for i in range(n)],
            "title": np.random.choice(titles, n),
            "content_type": np.random.choice(["TV Show", "Movie"], n, p=[0.65, 0.35]),
            "sentiment": sentiments,
            "user_comment": comments,
            "rating_stars": ratings,
            "helpful_votes": np.random.randint(0, 45, n)
        })

    # 5. Financial / Stock / Tata Steel / Time-Series
    if any(k in topic_lower for k in ["stock", "share", "tata", "steel", "price", "forecast", "predict", "trading", "finance", "market"]):
        n_days = 60
        dates = pd.date_range(end=pd.Timestamp.now().date(), periods=n_days, freq='B')
        base_price = 152.50
        returns = np.random.normal(loc=0.0012, scale=0.016, size=n_days)
        price_series = base_price * np.exp(np.cumsum(returns))
        highs = price_series * (1 + np.abs(np.random.normal(0, 0.008, n_days)))
        lows = price_series * (1 - np.abs(np.random.normal(0, 0.008, n_days)))
        opens = (price_series + lows) / 2
        closes = price_series
        volumes = np.random.randint(18_000_000, 48_000_000, n_days)

        return pd.DataFrame({
            "Date": dates.strftime('%Y-%m-%d'),
            "Open": np.round(opens, 2),
            "High": np.round(highs, 2),
            "Low": np.round(lows, 2),
            "Close": np.round(closes, 2),
            "Volume": volumes
        })

    # 6. Fraud Detection / Credit Card / Banking
    if any(k in topic_lower for k in ["fraud", "anomaly", "credit", "card", "transaction", "banking"]):
        amounts = np.round(np.random.exponential(scale=75.0, size=n) + np.random.uniform(5.0, 30.0, n), 2)
        fraud_flags = np.zeros(n, dtype=int)
        outlier_indices = np.random.choice(n, size=max(2, int(n * 0.1)), replace=False)
        amounts[outlier_indices] = np.round(amounts[outlier_indices] * np.random.uniform(6.0, 14.0, len(outlier_indices)), 2)
        fraud_flags[outlier_indices] = 1

        return pd.DataFrame({
            "transaction_id": [f"TXN_{9000 + i}" for i in range(n)],
            "customer_age": np.random.randint(18, 72, n),
            "transaction_amount": amounts,
            "merchant_category": np.random.choice(["Grocery", "Online Electronics", "Travel & Airlines", "Dining", "Luxury Goods"], n),
            "distance_from_home_km": np.round(np.random.uniform(1.0, 120.0, n), 1),
            "is_foreign": np.random.choice([0, 1], n, p=[0.85, 0.15]),
            "is_fraud": fraud_flags
        })

    # 7. Healthcare / Disease / Patient Vitals
    if any(k in topic_lower for k in ["health", "patient", "disease", "heart", "diabetes", "medical", "hospital", "clinic"]):
        ages = np.random.randint(25, 78, n)
        bmis = np.round(np.random.normal(26.5, 4.2, n), 1)
        glucose = np.random.randint(70, 190, n)
        risks = ((glucose > 130) | (bmis > 30.0) | (ages > 60)).astype(int)

        return pd.DataFrame({
            "patient_id": [f"PAT_{3000 + i}" for i in range(n)],
            "age": ages,
            "gender": np.random.choice(["Male", "Female"], n),
            "bmi": bmis,
            "blood_pressure": np.random.randint(90, 160, n),
            "glucose_level": glucose,
            "cholesterol_mg_dl": np.random.randint(150, 280, n),
            "risk_label": risks
        })

    # 8. HR / Employee Attrition & Retention
    if any(k in topic_lower for k in ["employee", "attrition", "turnover", "hr", "salary", "workplace"]):
        tenures = np.random.randint(1, 15, n)
        satisfactions = np.random.choice([1, 2, 3, 4, 5], n, p=[0.15, 0.2, 0.35, 0.2, 0.1])
        attrition = ((satisfactions <= 2) | (tenures < 2)).astype(int)

        return pd.DataFrame({
            "employee_id": [f"EMP_{4000 + i}" for i in range(n)],
            "department": np.random.choice(["Engineering", "Sales", "Marketing", "HR", "Support"], n),
            "tenure_years": tenures,
            "monthly_salary": np.random.choice([45000, 65000, 85000, 110000, 145000], n),
            "satisfaction_score": satisfactions,
            "overtime": np.random.choice(["Yes", "No"], n, p=[0.35, 0.65]),
            "attrition": attrition
        })

    # 9. General Adaptive Default
    return pd.DataFrame({
        "id": range(1, n + 1),
        "category": np.random.choice(["Alpha", "Beta", "Gamma", "Delta"], n),
        "metric_a": np.round(np.random.uniform(10.0, 100.0, n), 2),
        "metric_b": np.random.randint(50, 500, n),
        "performance_score": np.round(np.random.uniform(1.0, 10.0, n), 1),
        "status": np.random.choice(["Active", "Pending", "Completed"], n),
        "target": np.random.choice([0, 1], n, p=[0.7, 0.3])
    })


def data_agent(state):
    """
    Agent 1: Data Agent
    Searches for and downloads real-world CSV datasets via Tavily Web-RAG (primary) or DuckDuckGo (fallback),
    falling back instantly to domain-specific generation if offline.
    Saves to generated/dataset.csv.
    """
    GENERATED_DIR.mkdir(exist_ok=True)
    csv_file_path = GENERATED_DIR / "dataset.csv"

    dataset_url = state.get("dataset_url")
    request = state.get("request", "Data Analysis")
    df = None
    dataset_source_url = None
    source_type = "Domain Synthetic Generation"

    # 1. User-Specified Online Source Attempt
    if dataset_url and dataset_url.strip().startswith(("http://", "https://")):
        user_url = dataset_url.strip()
        try:
            req = urllib.request.Request(
                user_url,
                headers={"User-Agent": "Mozilla/5.0"}
            )
            with urllib.request.urlopen(req, timeout=10) as resp:
                raw_bytes = resp.read(2_000_000)
                csv_text = raw_bytes.decode("utf-8", errors="replace")
                df_temp = pd.read_csv(io.StringIO(csv_text))
                if len(df_temp) >= 5 and len(df_temp.columns) >= 2:
                    df = df_temp.head(250) if len(df_temp) > 250 else df_temp
                    df.columns = [str(c).strip() for c in df.columns]
                    dataset_source_url = user_url
                    source_type = f"Online Source ({user_url})"
        except Exception:
            pass

    # 2. Tavily Web-RAG Search (High-speed AI search)
    if df is None:
        try:
            df_tavily, found_url = search_tavily_for_csv(request)
            if df_tavily is not None and len(df_tavily) >= 5:
                df = df_tavily
                dataset_source_url = found_url
                source_type = f"Tavily Web-RAG ({found_url})"
        except Exception:
            pass

    # 3. DuckDuckGo Web-RAG Search (Fallback)
    if df is None:
        try:
            df_web, found_url = search_duckduckgo_for_csv(request)
            if df_web is not None and len(df_web) >= 5:
                df = df_web
                dataset_source_url = found_url
                source_type = f"DuckDuckGo Web-RAG ({found_url})"
        except Exception:
            pass

    # 4. Instant Domain Generation (Sub-second fallback)
    if df is None or len(df) == 0:
        df = get_domain_fallback_dataset(request)
        source_type = "Domain Synthetic Generation"

    # Save CSV
    csv_content = df.to_csv(index=False)
    csv_file_path.write_text(csv_content, encoding="utf-8")

    # Construct rich schema summary for code_agent and report_agent
    summary_lines = [
        f"Source: {source_type}",
        f"Dataset Shape: {len(df)} rows, {len(df.columns)} columns",
        f"Columns: {', '.join(df.columns.tolist())}",
        f"Data Types: {', '.join([f'{c} ({t})' for c, t in df.dtypes.items()])}"
    ]
    summary = "\n".join(summary_lines)

    return {
        "dataset_csv": csv_content,
        "dataset_path": str(csv_file_path),
        "dataset_summary": summary,
        "dataset_source_url": dataset_source_url
    }
