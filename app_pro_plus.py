import streamlit as st
import requests
import json
import os
import base64
import time

# ============================================================
# 配置区
# ============================================================

DEEPSEEK_API_KEY = os.environ.get("DEEPSEEK_API_KEY", "")
ZHIPU_API_KEY = os.environ.get("ZHIPU_API_KEY", "")


# ============================================================
# localStorage 持久化（7天免重新输入 Key）
# ============================================================

def init_local_storage():
    """注入 JS：从 localStorage 读取保存的 Key，写回 session_state"""
    st.components.v1.html(f"""
    <script>
    (function() {{
        const now = Date.now();
        const dsData = localStorage.getItem('canteen_ds_key');
        const zpData = localStorage.getItem('canteen_zp_key');

        let dsKey = '';
        let zpKey = '';
        let needUpdate = false;

        if (dsData) {{
            try {{
                const parsed = JSON.parse(dsData);
                if (parsed.expiry > now) {{
                    dsKey = parsed.key;
                }} else {{
                    localStorage.removeItem('canteen_ds_key');
                    needUpdate = true;
                }}
            }} catch(e) {{
                localStorage.removeItem('canteen_ds_key');
            }}
        }}

        if (zpData) {{
            try {{
                const parsed = JSON.parse(zpData);
                if (parsed.expiry > now) {{
                    zpKey = parsed.key;
                }} else {{
                    localStorage.removeItem('canteen_zp_key');
                    needUpdate = true;
                }}
            }} catch(e) {{
                localStorage.removeItem('canteen_zp_key');
            }}
        }}

        if (dsKey || zpKey) {{
            const params = new URLSearchParams();
            if (dsKey) params.set('ds_key', dsKey);
            if (zpKey) params.set('zp_key', zpKey);
            const currentUrl = window.location.href.split('?')[0];
            const newUrl = currentUrl + '?' + params.toString();
            window.parent.postMessage({{
                type: 'canteen_keys',
                ds_key: dsKey,
                zp_key: zpKey
            }}, '*');
        }}
    }})();
    </script>
    """, height=0)


def save_keys_to_localStorage(ds_key, zp_key):
    """注入 JS：把 Key 保存到 localStorage，7天有效期"""
    expiry = int(time.time() * 1000) + 7 * 24 * 60 * 60 * 1000
    st.components.v1.html(f"""
    <script>
    (function() {{
        const dsData = JSON.stringify({{
            key: "{ds_key}",
            expiry: {expiry}
        }});
        const zpData = JSON.stringify({{
            key: "{zp_key}",
            expiry: {expiry}
        }});
        localStorage.setItem('canteen_ds_key', dsData);
        localStorage.setItem('canteen_zp_key', zpData);
    }})();
    </script>
    """, height=0)


def clear_keys_from_localStorage():
    """清除 localStorage 里的 Key"""
    st.components.v1.html("""
    <script>
    localStorage.removeItem('canteen_ds_key');
    localStorage.removeItem('canteen_zp_key');
    </script>
    """, height=0)


# ============================================================
# 拍照识别（智谱 GLM-4V）
# ============================================================

def recognize_dish_from_image(image_bytes, zhipu_key):
    img_b64 = base64.b64encode(image_bytes).decode("utf-8")
    url = "https://open.bigmodel.cn/api/paas/v4/chat/completions"
    headers = {"Authorization": f"Bearer {zhipu_key}", "Content-Type": "application/json"}
    payload = {
        "model": "glm-4v-flash",
        "messages": [{"role": "user", "content": [
            {"type": "text", "text": "这是什么菜？只返回菜名，不要其他任何内容。"},
            {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{img_b64}"}}
        ]}]
    }
    resp = requests.post(url, headers=headers, json=payload, timeout=30)
    result = resp.json()
    dish_name = result["choices"][0]["message"]["content"].strip()
    for char in ['"', '"', '"', '「', '」', '。', '.', '！', '!', '?', '？']:
        dish_name = dish_name.replace(char, '')
    return dish_name.strip()


# ============================================================
# 营养估算参考数据库（基于《中国食物成分表》常见菜品）
# ============================================================

DISH_REFERENCE = {
    "宫保鸡丁": {"weight": 250, "calories": 480, "protein": 25, "carb": 30, "fat": 28},
    "红烧肉": {"weight": 200, "calories": 650, "protein": 20, "carb": 15, "fat": 55},
    "番茄炒蛋": {"weight": 220, "calories": 220, "protein": 12, "carb": 15, "fat": 12},
    "麻婆豆腐": {"weight": 250, "calories": 310, "protein": 18, "carb": 12, "fat": 22},
    "鱼香肉丝": {"weight": 230, "calories": 420, "protein": 22, "carb": 28, "fat": 24},
    "米饭": {"weight": 200, "calories": 260, "protein": 5, "carb": 55, "fat": 1},
    "酸辣土豆丝": {"weight": 220, "calories": 180, "protein": 4, "carb": 30, "fat": 6},
    "清炒时蔬": {"weight": 200, "calories": 90, "protein": 3, "carb": 12, "fat": 4},
    "回锅肉": {"weight": 250, "calories": 580, "protein": 25, "carb": 20, "fat": 45},
    "糖醋排骨": {"weight": 250, "calories": 550, "protein": 28, "carb": 35, "fat": 32},
    "水煮鱼": {"weight": 300, "calories": 420, "protein": 35, "carb": 10, "fat": 28},
    "青椒肉丝": {"weight": 220, "calories": 320, "protein": 20, "carb": 15, "fat": 20},
    "土豆炖牛肉": {"weight": 250, "calories": 380, "protein": 22, "carb": 25, "fat": 20},
    "蒸蛋羹": {"weight": 150, "calories": 120, "protein": 10, "carb": 3, "fat": 8},
    "紫菜蛋花汤": {"weight": 250, "calories": 60, "protein": 5, "carb": 4, "fat": 2},
    "酸菜鱼": {"weight": 300, "calories": 350, "protein": 30, "carb": 12, "fat": 20},
    "黄焖鸡": {"weight": 300, "calories": 450, "protein": 30, "carb": 20, "fat": 28},
    "辣子鸡": {"weight": 250, "calories": 520, "protein": 25, "carb": 15, "fat": 40},
    "西红柿鸡蛋面": {"weight": 350, "calories": 420, "protein": 15, "carb": 55, "fat": 15},
    "扬州炒饭": {"weight": 300, "calories": 520, "protein": 15, "carb": 65, "fat": 20},
}

INGREDIENT_REFERENCE = {
    "猪肉(瘦)": {"cal": 143, "p": 20.3, "c": 1.5, "f": 6.2},
    "猪肉(肥瘦)": {"cal": 395, "p": 13.2, "c": 2.4, "f": 37.0},
    "五花肉": {"cal": 508, "p": 14.0, "c": 0, "f": 50.0},
    "鸡肉": {"cal": 167, "p": 19.3, "c": 1.3, "f": 9.4},
    "鸡胸肉": {"cal": 133, "p": 31.0, "c": 0, "f": 1.2},
    "牛肉(瘦)": {"cal": 106, "p": 20.2, "c": 1.2, "f": 2.3},
    "鸡蛋": {"cal": 144, "p": 13.3, "c": 2.8, "f": 8.8},
    "豆腐": {"cal": 81, "p": 8.1, "c": 4.2, "f": 3.7},
    "米饭": {"cal": 116, "p": 2.6, "c": 25.9, "f": 0.3},
    "面条": {"cal": 110, "p": 3.5, "c": 22.5, "f": 0.7},
    "土豆": {"cal": 76, "p": 2.0, "c": 17.2, "f": 0.2},
    "番茄": {"cal": 18, "p": 0.9, "c": 4.0, "f": 0.2},
    "白菜": {"cal": 17, "p": 1.5, "c": 3.2, "f": 0.1},
    "青椒": {"cal": 22, "p": 1.0, "c": 5.4, "f": 0.2},
    "胡萝卜": {"cal": 39, "p": 1.0, "c": 8.8, "f": 0.2},
    "鱼肉": {"cal": 103, "p": 17.6, "c": 0, "f": 3.2},
    "虾仁": {"cal": 48, "p": 10.4, "c": 0.1, "f": 0.7},
    "花生米": {"cal": 567, "p": 25.8, "c": 16.1, "f": 44.3},
    "食用油": {"cal": 899, "p": 0, "c": 0, "f": 99.9},
    "白糖": {"cal": 400, "p": 0, "c": 99.9, "f": 0},
}


def find_reference(dish_name):
    for key, val in DISH_REFERENCE.items():
        if key in dish_name or dish_name in key:
            return val
    return None


def call_deepseek(messages, deepseek_key, timeout=60):
    headers = {
        "Authorization": f"Bearer {deepseek_key}",
        "Content-Type": "application/json"
    }
    payload = {
        "model": "deepseek-chat",
        "messages": messages,
        "temperature": 0.3
    }
    resp = requests.post(
        "https://api.deepseek.com/chat/completions",
        headers=headers, json=payload, timeout=timeout
    )
    result = resp.json()
    return result["choices"][0]["message"]["content"]


def parse_json_response(raw):
    try:
        cleaned = raw.strip()
        if cleaned.startswith("```"):
            cleaned = cleaned.split("```")[1]
            if cleaned.startswith("json"):
                cleaned = cleaned[4:]
        cleaned = cleaned.strip()
        return json.loads(cleaned)
    except Exception:
        return None


# ============================================================
# 四步协作分析
# ============================================================

def step1_analyze_dish(dish_name, deepseek_key):
    messages = [
        {"role": "system", "content": (
            "你是一位资深中餐厨师兼营养师，精通各大菜系。"
            "你熟悉中国大学食堂的菜品分量和做法。分析简洁准确。"
        )},
        {"role": "user", "content": (
            f"分析大学食堂的「{dish_name}」，返回以下内容（每项一行）：\n"
            "1. 菜系/类型\n"
            "2. 主要食材（列出具体食材，如：鸡肉、花生、青椒）\n"
            "3. 口味特点\n"
            "4. 烹饪方式（炒/炸/蒸/炖/煮/凉拌等）\n"
            "5. 食堂标准份量（克，通常150-300g）"
        )}
    ]
    return call_deepseek(messages, deepseek_key)


def step2_ingredient_breakdown(dish_name, dish_analysis, deepseek_key):
    messages = [
        {"role": "system", "content": (
            "你是专业营养分析师。根据菜品做法，精确拆解每种食材的克重。"
            "必须考虑烹饪用油（炒菜通常用油10-20g，油炸更多）。"
            "只返回合法JSON，不要多余文字。"
        )},
        {"role": "user", "content": (
            f"菜品「{dish_name}」\n分析：{dish_analysis}\n\n"
            "请拆解这道菜（食堂标准份）的所有食材及克重，返回JSON：\n"
            '{"ingredients":[{"name":"食材名","weight":克数}],'
            '"cooking_oil_g":用油克数,'
            '"total_weight_g":总重量克数}\n\n'
            "示例：{\"ingredients\":[{\"name\":\"鸡肉\",\"weight\":120},"
            "{\"name\":\"花生\",\"weight\":30}],\"cooking_oil_g\":15,\"total_weight_g\":250}"
        )}
    ]
    raw = call_deepseek(messages, deepseek_key)
    return parse_json_response(raw) or {"raw": raw}


def step3_calculate_nutrition(dish_name, dish_analysis, ingredients, deepseek_key):
    ref = find_reference(dish_name)
    ref_str = json.dumps(ref, ensure_ascii=False) if ref else "无"
    ingredients_str = json.dumps(ingredients, ensure_ascii=False) if ingredients else "无"

    messages = [
        {"role": "system", "content": (
            "你是营养计算专家。基于食材明细和参考数据，精确计算营养。"
            "规则：1.蛋白质主要来自肉类/蛋/豆制品 2.碳水主要来自主食/淀粉类 "
            "3.脂肪=食材脂肪+烹饪用油 4.热量=蛋白质×4+碳水×4+脂肪×9。"
            "只返回合法JSON，不要多余文字。"
        )},
        {"role": "user", "content": (
            f"菜品「{dish_name}」\n"
            f"菜品分析：{dish_analysis}\n"
            f"食材明细：{ingredients_str}\n"
            f"参考数据库值：{ref_str}\n\n"
            "请计算食堂一份的完整营养，返回JSON：\n"
            '{"weight":总重量(克),'
            '"calories":总热量(千卡),'
            '"protein":蛋白质(克),'
            '"carb":碳水(克),'
            '"fat":脂肪(克),'
            '"detail":"简要计算说明(一句话)"}\n\n'
            "要求：\n"
            "- 数值必须基于食材明细计算，不能凭空估算\n"
            "- 如果与参考数据库值偏差超过30%，请在detail中说明原因\n"
            "- weight应等于食材总重量+用油量"
        )}
    ]
    raw = call_deepseek(messages, deepseek_key)
    result = parse_json_response(raw)

    if result and ref and "calories" in result:
        cal = result["calories"]
        ref_cal = ref["calories"]
        if isinstance(cal, (int, float)):
            ratio = abs(cal - ref_cal) / ref_cal
            if ratio > 0.5:
                result["calories"] = round((cal + ref_cal) / 2)
                result["detail"] = result.get("detail", "") + f" [