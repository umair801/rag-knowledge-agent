"""
Business metrics reporter.
Prints an enterprise-ready performance summary.
"""
from dotenv import load_dotenv
from app.metrics.tracker import get_metrics_summary

load_dotenv()


def print_metrics_report() -> None:
    """Print a formatted business metrics report to console."""
    stats = get_metrics_summary()

    if not stats:
        print("No metrics available yet.")
        return

    print("\n" + "="*55)
    print("   RAG KNOWLEDGE BASE -- PERFORMANCE REPORT")
    print("="*55)
    print(f"  Total Queries Handled   : {stats['total_queries']}")
    print(f"  Unique Sessions         : {stats['unique_sessions']}")
    print(f"  Avg Response Latency    : {stats['avg_latency_ms']}ms")
    print(f"  Avg Retrieval Score     : {stats['avg_retrieval_score']}")
    print(f"  Queries Under 3s        : {stats['queries_under_3s_pct']}%")
    print("="*55)
    print(f"  Report Generated        : {stats['report_generated_at']}")
    print("="*55)

    # Business narrative
    if stats["total_queries"] > 0:
        hours_saved = round(stats["total_queries"] * 4 / 60, 1)
        cost_saved = round(stats["total_queries"] * 4 * 0.50, 2)
        print(f"\n  Estimated Agent Hours Saved : {hours_saved}hrs")
        print(f"  Estimated Cost Saved        : ${cost_saved}")
        print(f"  (Based on 4 min/query at $0.50/min agent cost)\n")


if __name__ == "__main__":
    print_metrics_report()