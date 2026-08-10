# 🍽️ 食堂热量估算器

用 AI 帮你估算食堂饭菜的热量和营养成分，三个版本任你选。

## 版本说明

| 版本 | 文件 | 功能 |
|------|------|------|
| 基础版 | `app.py` | Streamlit + DeepSeek API，文本输入菜品，估算热量 |
| Pro 版 | `app_pro.py` | CrewAI 三 Agent 协作：菜品识别 → 营养估算 → 饮食建议 |
| Pro+ 版 | `app_pro_plus.py` | Pro 版 + 拍照识别（智谱 GLM-4V）+ 访问密码 + 用户自带 Key |

## 快速开始

### 1. 安装依赖

```bash
pip install streamlit requests crewai
```

### 2. 配置环境变量

```bash
cp .env.example .env
# 编辑 .env 填入你的 API Key
```

### 3. 运行

```bash
# 基础版
streamlit run app.py

# Pro 版
streamlit run app_pro.py

# Pro+ 版
streamlit run app_pro_plus.py
```

## 环境变量

| 变量名 | 说明 | 必填 |
|--------|------|------|
| `DEEPSEEK_API_KEY` | DeepSeek API Key | ✅ |
| `ZHIPU_API_KEY` | 智谱 API Key（Pro+ 拍照识别用） | Pro+ 需要 |
| `ACCESS_PASSWORD` | 访问密码（Pro+ 用，留空则无需密码） | Pro+ 可选 |

## API 说明

| 服务 | URL | 模型 |
|------|-----|------|
| DeepSeek | `https://api.deepseek.com` | `deepseek-chat` |
| 智谱 GLM-4V | `https://open.bigmodel.cn/api/paas/v4/chat/completions` | `glm-4v-flash` |

## 技术栈

- [Streamlit](https://streamlit.io/) — Web 界面
- [DeepSeek](https://www.deepseek.com/) — 大语言模型
- [CrewAI](https://github.com/joaomdmoura/crewAI) — 多 Agent 协作框架
- [智谱 GLM-4V](https://open.bigmodel.cn/) — 视觉识别模型
