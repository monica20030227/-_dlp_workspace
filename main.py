import os
import csv
from datetime import datetime

import pandas as pd
import streamlit as st

from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError


SCOPES = [
    "https://www.googleapis.com/auth/drive"
]

COMPANY_DOMAINS = [
    "smail.nchu.edu.tw",
    "mail.nchu.edu.tw",
    "nchu.edu.tw"
]

SENSITIVE_KEYWORDS = [
    "薪資", "財報", "個資", "身份證", "身分證", "密碼",
    "合約", "客戶名單", "機密", "confidential",
    "salary", "password", "contract", "finance"
]

OUTPUT_CSV = f"dlp_scan_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"


st.set_page_config(
    page_title="Google Workspace DLP 監控系統",
    page_icon="🛡️",
    layout="wide"
)


def get_drive_service():
    creds = None

    if os.path.exists("token.json"):
        creds = Credentials.from_authorized_user_file("token.json", SCOPES)

    if not creds or not creds.valid:
        if not os.path.exists("credentials.json"):
            st.error("找不到 credentials.json，請確認它和 app.py 放在同一個資料夾。")
            st.stop()

        flow = InstalledAppFlow.from_client_secrets_file(
            "credentials.json",
            SCOPES
        )

        creds = flow.run_local_server(port=0)

        with open("token.json", "w", encoding="utf-8") as token:
            token.write(creds.to_json())

    return build("drive", "v3", credentials=creds)


def is_internal_email(email):
    if not email:
        return False

    email = email.lower()
    return any(email.endswith("@" + domain) for domain in COMPANY_DOMAINS)


def has_sensitive_keyword(file_name):
    matched = []
    lower_name = file_name.lower()

    for keyword in SENSITIVE_KEYWORDS:
        if keyword.lower() in lower_name:
            matched.append(keyword)

    return matched


def check_permissions(service, file_id):
    try:
        permissions = service.permissions().list(
            fileId=file_id,
            fields="permissions(id,type,emailAddress,role,displayName)"
        ).execute()

        perms = permissions.get("permissions", [])

        external_users = []
        anyone_with_link = False
        has_writer_external = False

        for p in perms:
            p_type = p.get("type", "")
            email = p.get("emailAddress", "")
            role = p.get("role", "")

            if p_type == "anyone":
                anyone_with_link = True
                external_users.append(f"anyone_with_link ({role})")

                if role in ["writer", "organizer", "fileOrganizer"]:
                    has_writer_external = True

            elif email and not is_internal_email(email):
                external_users.append(f"{email} ({role})")

                if role in ["writer", "organizer", "fileOrganizer"]:
                    has_writer_external = True

        return {
            "error": None,
            "is_external": len(external_users) > 0,
            "external_users": external_users,
            "anyone_with_link": anyone_with_link,
            "has_writer_external": has_writer_external
        }

    except HttpError:
        return {
            "error": "no_permission",
            "is_external": False,
            "external_users": [],
            "anyone_with_link": False,
            "has_writer_external": False
        }


def calculate_risk(file_name, permission_info):
    score = 0
    reasons = []

    sensitive_keywords = has_sensitive_keyword(file_name)

    if permission_info["is_external"]:
        score += 40
        reasons.append("檔案分享給外部帳號")

    if permission_info["anyone_with_link"]:
        score += 50
        reasons.append("檔案開啟 anyone with link 權限")

    if permission_info["has_writer_external"]:
        score += 25
        reasons.append("外部帳號具有編輯權限")

    if sensitive_keywords:
        score += 20
        reasons.append(f"檔名包含敏感關鍵字：{', '.join(sensitive_keywords)}")

    if permission_info["error"] == "no_permission":
        score += 10
        reasons.append("無法讀取檔案權限，可能不是擁有者或權限不足")

    if score >= 71:
        level = "High"
    elif score >= 31:
        level = "Medium"
    else:
        level = "Low"

    if not reasons:
        reasons.append("未偵測到明顯外洩風險")

    return score, level, "；".join(reasons)


def save_to_csv(rows):
    if not rows:
        return

    fieldnames = [
        "scan_time",
        "file_name",
        "file_id",
        "mime_type",
        "owner_email",
        "webViewLink",
        "is_external_shared",
        "external_users",
        "anyone_with_link",
        "has_writer_external",
        "permission_error",
        "risk_score",
        "risk_level",
        "reason"
    ]

    with open(OUTPUT_CSV, mode="w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def scan_drive_files(page_size=50):
    service = get_drive_service()

    results = service.files().list(
        pageSize=page_size,
        fields="files(id,name,mimeType,owners,webViewLink)"
    ).execute()

    files = results.get("files", [])
    rows = []

    progress = st.progress(0)
    status = st.empty()

    for i, f in enumerate(files):
        file_id = f.get("id", "")
        file_name = f.get("name", "")
        mime_type = f.get("mimeType", "")
        link = f.get("webViewLink", "")

        status.write(f"正在掃描：{file_name}")

        owner_email = ""
        owners = f.get("owners", [])
        if owners:
            owner_email = owners[0].get("emailAddress", "")

        permission_info = check_permissions(service, file_id)
        risk_score, risk_level, reason = calculate_risk(file_name, permission_info)

        row = {
            "scan_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "file_name": file_name,
            "file_id": file_id,
            "mime_type": mime_type,
            "owner_email": owner_email,
            "webViewLink": link,
            "is_external_shared": permission_info["is_external"],
            "external_users": ", ".join(permission_info["external_users"]),
            "anyone_with_link": permission_info["anyone_with_link"],
            "has_writer_external": permission_info["has_writer_external"],
            "permission_error": permission_info["error"] or "",
            "risk_score": risk_score,
            "risk_level": risk_level,
            "reason": reason
        }

        rows.append(row)

        progress.progress((i + 1) / len(files) if files else 1)

    status.write("掃描完成")
    save_to_csv(rows)

    return pd.DataFrame(rows)


st.title("🛡️ Google Workspace DLP 監控系統")
st.caption("偵測 Google Drive 外部分享、anyone with link、外部編輯權限與敏感檔名關鍵字。")

with st.sidebar:
    st.header("掃描設定")

    page_size = st.slider(
        "掃描檔案數量",
        min_value=10,
        max_value=200,
        value=50,
        step=10
    )

    st.subheader("內部網域")
    for domain in COMPANY_DOMAINS:
        st.write(f"✅ {domain}")

    st.subheader("敏感關鍵字")
    st.write("、".join(SENSITIVE_KEYWORDS))

    st.warning("第一次執行會跳出 Google 登入授權視窗。")


if st.button("開始掃描 Google Drive", type="primary"):
    with st.spinner("正在進行 DLP 掃描..."):
        df = scan_drive_files(page_size)

    st.session_state["df"] = df
    st.success(f"掃描完成，共掃描 {len(df)} 個檔案。")


if "df" in st.session_state:
    df = st.session_state["df"]

    total_files = len(df)
    high_count = len(df[df["risk_level"] == "High"])
    medium_count = len(df[df["risk_level"] == "Medium"])
    external_count = len(df[df["is_external_shared"] == True])
    anyone_count = len(df[df["anyone_with_link"] == True])

    col1, col2, col3, col4, col5 = st.columns(5)

    col1.metric("掃描檔案數", total_files)
    col2.metric("高風險", high_count)
    col3.metric("中風險", medium_count)
    col4.metric("外部分享", external_count)
    col5.metric("Anyone Link", anyone_count)

    st.divider()

    st.subheader("🚨 高風險與中風險檔案")
    risk_df = df[df["risk_level"].isin(["High", "Medium"])].copy()
    risk_df = risk_df.sort_values(by="risk_score", ascending=False)

    if risk_df.empty:
        st.success("目前沒有偵測到高風險或中風險檔案。")
    else:
        st.dataframe(
            risk_df[
                [
                    "risk_level",
                    "risk_score",
                    "file_name",
                    "external_users",
                    "anyone_with_link",
                    "has_writer_external",
                    "reason",
                    "webViewLink"
                ]
            ],
            use_container_width=True
        )

    st.subheader("📄 全部掃描結果")
    st.dataframe(df, use_container_width=True)

    csv_data = df.to_csv(index=False, encoding="utf-8-sig")

    st.download_button(
        label="下載 CSV 結果",
        data=csv_data.encode("utf-8-sig"),
        file_name="dlp_scan_results.csv",
        mime="text/csv"
    )

    st.subheader("🤖 AI 分析用摘要")
    summary_text = f"""
本次 DLP 掃描共掃描 {total_files} 個檔案。
高風險檔案數：{high_count}
中風險檔案數：{medium_count}
外部分享檔案數：{external_count}
Anyone with link 檔案數：{anyone_count}

請特別關注 risk_level 為 High 或 Medium 的檔案。
"""

    st.text_area("可貼到 Workspace Studio / Gemini 的摘要", summary_text, height=180)

else:
    st.info("請按下「開始掃描 Google Drive」進行第一次掃描。")