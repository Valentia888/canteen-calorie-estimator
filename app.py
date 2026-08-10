"""
食堂热量估算器 - 基础版
Streamlit + DeepSeek API
从环境变量读取 API Key
"""

import os
import re
import json

import requests
import streamlit as st

# --- 配置 ---
DEEPSEEK_API_KEY = os.environ.get("DEEPSEEK_API_KEY", "")
DEEPSEEK_URL = "https://api.deepseek.com"
DEEPSEEK_MODEL = "deepseek-chat"

# --- 页面配置 ---
st.set_page_config(page_title="食堂热量估算器", page_icon="🍽️", layout="centered")
st.title("🍽️ 食堂热量估算器")
st.markdown("输入你今天在食堂吃了什么，AI 帮你估算热量和营养成分。")

# --- 检查 API Key ---
if not DEEPSEEK_API_KEY:
    st.warning("⚠️ 未检测到 DEEPSEEK_API_KEY 环境变量，请在 .env 文件或系统环境变量中配置。")
    st.code("DEEPSEEK_API_KEY=your_key_here", language="bash")
    st.stop()

# --- 用户输入 ---
user_input = st.text_area(
    "📝 输入你吃的菜品",
    placeholder="例如：红烧肉一份、清炒西兰花、米饭一碗、紫菜蛋花汤",
    height=120,
)

# --- 估算逻辑 ---
def estimate_calories(dish_text: str) -> dict:
    """调用 DeepSeek API 估算菜品热量和营养。"""
    headers = {
        "Authorization": f"Bearer {DEEPSEEK_API_KEY}",
        "Content-Type": "application/json",
    }
    payload = {
        "model": DEEPSEEK_MODEL,
        "messages": [
            {
                "role": "system",
                "content": (
                    "你是一位专业营养师。根据用户描述的菜品，估算每道菜的热量（千卡）"
                    "和主要营养成分（蛋白质、碳水化合物、脂肪，单位克）。"
                    "请严格以 JSON 格式返回，结构如下：\n"
                    '{"dishes": [{"name": "菜名", "calories": 0, "protein": 0, '
                    '"carbs": 0, "fat": 0}], "total": {"calories": 0, '
                    '"protein": 0, "carbs": 0, "fat": 0}}'
                ),
            },
            {"role": "user", "content": dish_text},
        ],
        "temperature": 0.3,
    }

    resp = requests.post(
        f"{DEEPSEEK_URL}/v1/chat/completions",
        headers=headers,
        json=payload,
        timeout=30,
    )
    resp.raise_for_status()
    content = resp.json()["choices"][0]["message"]["content"]

    # 尝试直接解析 JSON；失败则从代码块中提取
    try:
        return json.loads(content)
    except json.JSONDecodeError:
        match = re.search(r"```(?:json)?\s*(.*?)```", content, re.DOTALL)
        if match:
            return json.loads(match.group(1))
        raise


# --- 按钮触发 ---
if st.button("估算热量", type="primary"):
    if not user_input.strip():
        st.error("请先输入菜品内容")
        st.stop()

    with st.spinner("正在估算中…"):
        try:
            data = estimate_calories(user_input)
        except requests.exceptions.RequestException as e:
            st.error(f"API 请求失败: {e}")
            st.stop()
        except (json.JSONDecodeError, KeyError) as e:
            st.error(f"解析响应失败: {e}")
            st.stop()

    # --- 展示结果 ---
    dishes = data.get("dishes", [])
    if not dishes:
        st.warning("未能解析出菜品信息，原始响应如下：")
        st.json(data)
        st.stop()

    st.subheader("📊 估算结果")
    for dish in dishes:
        with st.expander(f"🍽️ {dish.get('name', '未知菜品')} — {dish.get('calories', '?')} kcal"):
            col1, col2, col3 = st.columns(3)
            col1.metric("蛋白质", f"{dish.get('protein', 0)} g")
            col2.metric("碳水", f"{dish.get('carbs', 0)} g")
            col3.metric("脂肪", f"{dish.get('fat', 0)} g")

    total = data.get("total")
    if total:
        st.divider()
        st.subheader("📈 总计")
        col1, col2, col3, col4 = st.columns(4)
        col1.metric("总热量", f"{total.get('calories', 0)} kcal")
        col2.metric("蛋白质", f"{total.get('protein', 0)} g")
        col3.metric("碳水", f"{total.get('carbs', 0)} g")
        col4.metric("脂肪", f"{total.get('fat', 0)} g")
