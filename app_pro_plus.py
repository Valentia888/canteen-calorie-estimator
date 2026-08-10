# -*- coding: utf-8 -*-
import streamlit as st
import requests
import json
import base64
import time

st.set_page_config(page_title="食堂热量估算器 Pro+", page_icon="\U0001F373", layout="centered")
st.title("\U0001F373 食堂热量估算器 Pro+")
st.caption("拍照 / 输入菜名 → 四步 AI 估算热量")

# ============ API Key 管理（session_state） ============
with st.sidebar:
    st.header("\U0001F511 API 设置")
    if "ds_key" not in st.session_state:
        st.session_state["ds_key"] = ""
    if "glm_key" not in st.session_state:
        st.session_state["glm_key"] = ""
    st.session_state["ds_key"] = st.text_input("DeepSeek API Key", value=st.session_state["ds_key"], type="password")
    st.session_state["glm_key"] = st.text_input("智谱 GLM-4V Key（拍照用，可选）", value=st.session_state["glm_key"], type="password")
    active_ds_key = st.session_state["ds_key"].strip()
    active_glm_key = st.session_state["glm_key"].strip()
    if active_ds_key:
        st.success("DeepSeek Key 已就绪")
    if active_glm_key:
        st.success("GLM Key 已就绪")

# ============ 参考数据库（用于校准） ============
REFERENCE_DB = {
    "宫保鸡丁": {"calorie": 250, "protein": 22, "fat": 14, "carb": 18, "weight": 250},
    "红烧肉": {"calorie": 480, "protein": 18, "fat": 40, "carb": 8, "weight": 150},
    "西红柿炒鸡蛋": {"calorie": 180, "protein": 12, "fat": 11, "carb": 10, "weight": 200},
    "麻婆豆腐": {"calorie": 200, "protein": 14, "fat": 13, "carb": 12, "weight": 250},
    "鱼香肉丝": {"calorie": 260, "protein": 18, "fat": 16, "carb": 16, "weight": 220},
    "青椒土豆丝": {"calorie": 120, "protein": 3, "fat": 6, "carb": 18, "weight": 200},
    "糖醋里脊": {"calorie": 380, "protein": 20, "fat": 22, "carb": 28, "weight": 180},
    "蒜蓉西兰花": {"calorie": 90, "protein": 5, "fat": 4, "carb": 10, "weight": 200},
    "蛋炒饭": {"calorie": 350, "protein": 10, "fat": 12, "carb": 55, "weight": 250},
    "白米饭": {"calorie": 200, "protein": 4, "fat": 0.5, "carb": 45, "weight": 150},
    "水煮鱼": {"calorie": 320, "protein": 28, "fat": 20, "carb": 8, "weight": 300},
    "回锅肉": {"calorie": 460, "protein": 22, "fat": 38, "carb": 10, "weight": 180},
    "可乐鸡翅": {"calorie": 320, "protein": 18, "fat": 18, "carb": 22, "weight": 200},
    "干煸豆角": {"calorie": 180, "protein": 6, "fat": 10, "carb": 18, "weight": 200},
    "酸辣土豆丝": {"calorie": 130, "protein": 3, "fat": 7, "carb": 18, "weight": 200},
    "拍黄瓜": {"calorie": 60, "protein": 2, "fat": 3, "carb": 7, "weight": 150},
    "小米粥": {"calorie": 100, "protein": 3, "fat": 1, "carb": 20, "weight": 250},
    "蒸蛋羹": {"calorie": 110, "protein": 10, "fat": 7, "carb": 2, "weight": 200},
    "馒头": {"calorie": 220, "protein": 7, "fat": 1, "carb": 47, "weight": 100},
    "煎饼果子": {"calorie": 400, "protein": 14, "fat": 18, "carb": 50, "weight": 200},
}

# ============ AI 调用 ============
def call_deepseek(prompt, api_key, system="你是营养学专家"):
    url = "https://api.deepseek.com/v1/chat/completions"
    headers = {"Authorization": "Bearer " + api_key, "Content-Type": "application/json"}
    data = {
        "model": "deepseek-chat",
        "messages": [{"role": "system", "content": system}, {"role": "user", "content": prompt}],
        "temperature": 0.3,
    }
    r = requests.post(url, headers=headers, json=data, timeout=60)
    r.raise_for_status()
    return r.json()["choices"][0]["message"]["content"]

def call_glm4v(image_bytes, api_key):
    url = "https://open.bigmodel.cn/api/paas/v4/chat/completions"
    headers = {"Authorization": "Bearer " + api_key, "Content-Type": "application/json"}
    img_b64 = base64.b64encode(image_bytes).decode("utf-8")
    data = {
        "model": "glm-4v-flash",
        "messages": [{"role": "user", "content": [{"type": "image_url", "image_url": {"url": "data:image/jpeg;base64," + img_b64}}, {"type": "text", "text": "请用一句话告诉我这张图里最可能的一道菜名（中文），不要解释。"}]}],
    }
    r = requests.post(url, headers=headers, json=data, timeout=60)
    r.raise_for_status()
    return r.json()["choices"][0]["message"]["content"].strip()

def lookup_ref(dish_name):
    for k, v in REFERENCE_DB.items():
        if k in dish_name or dish_name in k:
            return v, k
    return None, None

def calibrate(ai_result, ref):
    if not ref:
        return ai_result + "\n\n（本菜暂无本地参考数据，未做校准）"
    text = ai_result
    parts = []
    for key_cn, key_en, unit in [("热量", "calorie", "kcal"), ("蛋白质", "protein", "g"), ("脂肪", "fat", "g"), ("碳水", "carb", "g")]:
        val = ref[key_en]
        parts.append("- " + key_cn + "：参考值约 **" + str(val) + " " + unit + "**（一份约 " + str(ref["weight"]) + " g）")
    return ai_result + "\n\n### \U0001F4D0 参考校准\n" + "\n".join(parts) + "\n\n> 若 AI 估算与上述差异过大，以参考值为准并适当微调。"

def run_analysis(dish_name, api_key):
    ref, hit = lookup_ref(dish_name)
    s1 = call_deepseek("请用一句话介绍这道菜：「" + dish_name + "」，不要列举食材。", api_key, system="你是菜品百科编辑")
    s2 = call_deepseek("请把「" + dish_name + "」拆解为 4-8 种主要食材及大致克重（一份估重），仅输出列表。", api_key, system="你是食堂称重员")
    s3 = call_deepseek("基于以下食材清单，计算「" + dish_name + "」每份的总热量 / 蛋白质 / 脂肪 / 碳水，用表格输出，每行一种营养素。\n\n食材列表：" + s2, api_key, system="你是营养学专家")
    s4 = call_deepseek("基于这份营养报告，给出一句 30 字内的健康食用建议。报告：" + s3, api_key, system="你是营养顾问")
    out = "## \U0001F37D " + dish_name + "\n\n### \U0001F4D6 简介\n" + s1 + "\n\n### \U0001F33E 食材拆解\n" + s2 + "\n\n### \U0001F4CA 营养估算\n" + s3 + "\n\n### \U0001F4A1 食用建议\n" + s4
    if hit:
        out = out + "\n\n*匹配参考菜品：「" + hit + "」*"
    return calibrate(out, ref)

# ============ 拍照识别 ============
img_file = st.file_uploader("\U0001F4F7 拍照识别（可选）", type=["jpg", "jpeg", "png"])
dish_name = ""
if img_file and active_glm_key:
    if st.button("\U0001F50D 识别图片"):
        with st.spinner("智谱 GLM-4V 识别中..."):
            try:
                dish_name = call_glm4v(img_file.read(), active_glm_key)
                st.success("识别结果：" + dish_name)
            except Exception as e:
                st.error("识别失败：" + str(e))

# ============ 分析入口 ============
if not dish_name:
    st.subheader("或直接输入菜名")
    dish_name = st.text_input("", placeholder="如：宫保鸡丁 / 红烧肉 / 西红柿炒鸡蛋")

if not active_ds_key:
    st.warning("请先在左侧填写 DeepSeek API Key")
elif dish_name:
    with st.spinner("\U0001F9E0 四步 AI 分析中（约 40-90 秒）..."):
        try:
            result = run_analysis(dish_name, active_ds_key)
            st.success("分析完成")
            st.markdown(result)
        except Exception as e:
            st.error("出错：" + str(e))

st.markdown("---")
st.caption("由 DeepSeek + 智谱 GLM-4V 提供分析能力")