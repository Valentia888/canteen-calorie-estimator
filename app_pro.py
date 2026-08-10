import streamlit as st
import requests
import json
import os

DEEPSEEK_API_KEY = os.environ.get("DEEPSEEK_API_KEY", "")

def call_deepseek(messages, deepseek_key, timeout=60):
    headers = {"Authorization": f"Bearer {deepseek_key}", "Content-Type": "application/json"}
    payload = {"model": "deepseek-chat", "messages": messages, "temperature": 0.5}
    resp = requests.post("https://api.deepseek.com/chat/completions", headers=headers, json=payload, timeout=timeout)
    result = resp.json()
    return result["choices"][0]["message"]["content"]

def step1_analyze(dish_name, deepseek_key):
    messages = [
        {"role": "system", "content": "你是一位资深中餐厨师，精通各大菜系。分析简洁准确。"},
        {"role": "user", "content": f"分析「{dish_name}」：1.菜系 2.主要食材 3.口味 4.烹饪方式。每项一行，简洁中文。"}
    ]
    return call_deepseek(messages, deepseek_key)

def step2_estimate(dish_name, dish_analysis, deepseek_key):
    messages = [
        {"role": "system", "content": "你是专业营养师，熟悉中国大学食堂分量。用JSON格式回答。"},
        {"role": "user", "content": (
            f"菜品「{dish_name}」分析：\n{dish_analysis}\n\n"
            '请估算大学食堂一份的营养。返回JSON（必须是合法JSON）：'
            '{"weight":数字(克),"calories":数字(千卡),"protein":数字(克),"carb":数字(克),"fat":数字(克)}'
        )}
    ]
    raw = call_deepseek(messages, deepseek_key)
    try:
        cleaned = raw.strip()
        if cleaned.startswith("```"):
            cleaned = cleaned.split("```")[1]
            if cleaned.startswith("json"):
                cleaned = cleaned[4:]
        cleaned = cleaned.strip()
        return json.loads(cleaned)
    except Exception:
        return {"raw": raw}

def step3_advise(dish_name, dish_analysis, nutrition, deepseek_key):
    nutrition_str = json.dumps(nutrition, ensure_ascii=False) if isinstance(nutrition, dict) else str(nutrition)
    messages = [
        {"role": "system", "content": "你是健康饮食顾问，简洁实用，不超过150字。"},
        {"role": "user", "content": (
            f"菜品「{dish_name}」\n分析：{dish_analysis}\n营养：{nutrition_str}\n\n"
            "给大学生饮食建议：1.搭配什么 2.减脂/增肌能不能吃 3.注意事项 4.一句话总结"
        )}
    ]
    return call_deepseek(messages, deepseek_key)

def run_analysis(dish_name, deepseek_key):
    analysis = step1_analyze(dish_name, deepseek_key)
    nutrition = step2_estimate(dish_name, analysis, deepseek_key)
    advice = step3_advise(dish_name, analysis, nutrition, deepseek_key)
    report = []
    report.append(f"## ① 菜品分析\n{analysis}\n")
    if isinstance(nutrition, dict) and "calories" in nutrition:
        report.append("## ② 营养估算")
        report.append(f"- 份量：{nutrition.get('weight', '?')} g")
        report.append(f"- 热量：**{nutrition.get('calories', '?')} kcal**")
        report.append(f"- 蛋白质：{nutrition.get('protein', '?')} g")
        report.append(f"- 碳水：{nutrition.get('carb', '?')} g")
        report.append(f"- 脂肪：{nutrition.get('fat', '?')} g\n")
    else:
        report.append(f"## ② 营养估算\n{nutrition}\n")
    report.append(f"## ③ 饮食建议\n{advice}")
    return "\n".join(report)

st.set_page_config(page_title="食堂热量估算器 Pro", page_icon="🍱", layout="centered")
st.title("🍱 食堂热量估算器 Pro")
st.caption("多 AI 协作版 · 菜品分析 → 营养估算 → 饮食建议")

if DEEPSEEK_API_KEY:
    st.success("✅ 已连接 DeepSeek AI · 三步协作模式")
else:
    st.warning("⚠️ 未检测到 API Key。请在部署平台的 Secrets 里配置 DEEPSEEK_API_KEY")

dish = st.text_input("今天吃什么？", placeholder="比如：宫保鸡丁、酸汤肥牛...", max_chars=20)

if st.button("🔍 开始分析", type="primary") and dish:
    if not DEEPSEEK_API_KEY:
        st.error("❌ 没有 API Key，请先在部署平台配置")
    else:
        with st.spinner(f"三步 AI 正在协作分析「{dish}」...（约 30-60 秒）"):
            try:
                result = run_analysis(dish, DEEPSEEK_API_KEY)
                st.success("✅ 分析完成！")
                st.subheader(f"📋 「{dish}」完整分析报告")
                st.markdown(result)
            except Exception as e:
                st.error(f"出错了：{e}")

with st.expander("ℹ️ 这个版本和基础版的区别？"):
    st.write("""
    **基础版**（app.py）：一个 AI 一次性返回热量数据
    **Pro 版**（app_pro.py）：三步串行调用 DeepSeek
    - ① 分析菜系、食材、做法
    - ② 估算营养（更准确）
    - ③ 给饮食建议
    """)