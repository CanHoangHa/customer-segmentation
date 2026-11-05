"""Load and validate dashboard artifacts without recalculating model KPIs."""

from dataclasses import dataclass
import json
from pathlib import Path
from typing import Any

import pandas as pd


METHOD_NAMES = {
    "rfm_threshold": "Ngưỡng RFM",
    "kmeans": "K-Means",
    "gmm": "Gaussian Mixture",
    "birch": "BIRCH",
}


class DashboardDataError(RuntimeError):
    """Raised when a required dashboard artifact is missing or inconsistent."""


@dataclass(frozen=True)
class DashboardData:
    segments: pd.DataFrame
    profiles: pd.DataFrame
    comparison: pd.DataFrame
    run_metadata: dict[str, Any]
    model_selection: dict[str, Any]
    cleaning_summary: dict[str, Any]
    rfm_summary: dict[str, Any]


def _json(path: Path) -> dict[str, Any]:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as error:
        raise DashboardDataError(f"Thiếu artifact: {path}") from error
    except json.JSONDecodeError as error:
        raise DashboardDataError(f"JSON không hợp lệ: {path}") from error


def load_dashboard_data(root: str | Path) -> DashboardData:
    project = Path(root)
    segment_path = project / "data/curated/customer_segments.parquet"
    profile_path = project / "reports/segment_profiles.csv"
    comparison_path = project / "reports/model_comparison.csv"
    for path in (segment_path, profile_path, comparison_path):
        if not path.is_file():
            raise DashboardDataError(f"Thiếu artifact: {path}")
    try:
        segments = pd.read_parquet(segment_path, engine="pyarrow")
        profiles = pd.read_csv(profile_path)
        comparison = pd.read_csv(comparison_path)
    except Exception as error:
        raise DashboardDataError(f"Không đọc được artifact dashboard: {error}") from error

    required_segments = {
        "customer_id",
        "recency_days",
        "frequency_orders",
        "monetary_value",
        "is_repeat_customer",
        "method",
        "model_config_id",
        "segment_id",
        "segment_name",
    }
    missing = sorted(required_segments.difference(segments.columns))
    if missing:
        raise DashboardDataError(f"customer_segments thiếu cột: {missing}")
    if segments[["customer_id", "method"]].duplicated().any():
        raise DashboardDataError("customer_segments trùng khóa customer_id/method")
    if segments[["method", "segment_id", "segment_name"]].isna().any().any():
        raise DashboardDataError("customer_segments có nhãn phân khúc trống")

    methods = set(segments["method"].unique())
    selected = _json(project / "reports/model_selection.json")
    if methods != set(selected.get("selected", {})):
        raise DashboardDataError("Danh sách phương pháp không khớp model_selection.json")
    if set(profiles["method"].unique()) != methods:
        raise DashboardDataError("segment_profiles không đủ các phương pháp đã chọn")

    return DashboardData(
        segments=segments,
        profiles=profiles,
        comparison=comparison,
        run_metadata=_json(project / "reports/run_metadata.json"),
        model_selection=selected,
        cleaning_summary=_json(project / "reports/cleaning_summary.json"),
        rfm_summary=_json(project / "reports/rfm_summary.json"),
    )


def method_label(method: str) -> str:
    return METHOD_NAMES.get(method, method)


def crm_hypotheses(profiles: pd.DataFrame, method: str) -> pd.DataFrame:
    frame = profiles[profiles["method"] == method].copy()
    if frame.empty:
        raise DashboardDataError(f"Không có profile cho phương pháp {method}")
    weighted_recency = float(
        (frame["median_recency_days"] * frame["customers"]).sum() / frame["customers"].sum()
    )
    overall_repeat = float(
        frame["repeat_customers"].sum() / frame["customers"].sum() * 100
    )
    records = []
    for row in frame.itertuples(index=False):
        value_concentration = row.monetary_share_pct / max(row.customer_pct, 1e-9)
        if value_concentration >= 1.5 and row.median_recency_days > weighted_recency:
            hypothesis = "Thử chiến dịch tái tương tác có giới hạn ưu đãi"
            kpi = "Tỷ lệ mua lại sau chiến dịch và chi phí trên đơn quay lại"
            risk = "Ưu đãi có thể làm giảm biên giá trị nếu nhắm quá rộng"
        elif row.repeat_customer_pct > overall_repeat and row.median_frequency_orders >= 2:
            hypothesis = "Thử quyền lợi duy trì tần suất mua thay vì giảm giá đại trà"
            kpi = "Tần suất đơn và tỷ lệ mua lại trong cửa sổ theo dõi"
            risk = "Kết quả mô tả chưa chứng minh quyền lợi làm tăng tần suất"
        elif row.median_recency_days <= weighted_recency / 2 and row.median_frequency_orders <= 1:
            hypothesis = "Thử chuỗi chào mừng hướng đến đơn mua thứ hai"
            kpi = "Tỷ lệ phát sinh đơn thứ hai trong cửa sổ thử nghiệm"
            risk = "Nhóm mới mua chưa có đủ lịch sử để suy ra sở thích ổn định"
        else:
            hypothesis = "Theo dõi thêm và thử nội dung chăm sóc chi phí thấp"
            kpi = "Tỷ lệ tương tác và mua lại so với nhóm đối chứng"
            risk = "Phân khúc có thể gộp nhiều hành vi khác nhau"
        observation = (
            f"{row.customer_pct:.1f}% khách, {row.monetary_share_pct:.1f}% tổng M, "
            f"median R/F/M = {row.median_recency_days:.0f}/"
            f"{row.median_frequency_orders:.0f}/{row.median_monetary_value:,.2f}"
        )
        records.append(
            {
                "Phân khúc": row.segment_name,
                "Quan sát": observation,
                "Giả thuyết thử nghiệm": hypothesis,
                "KPI theo dõi": kpi,
                "Rủi ro": risk,
            }
        )
    return pd.DataFrame(records)
