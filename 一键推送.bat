@echo off
chcp 65001 >nul
title 食堂热量估算器 - 一键推送脚本
color 0A

echo ============================================
echo    食堂热量估算器 - 一键推送脚本
echo ============================================
echo.

cd /d "D:\新建文件夹\食堂热量估算器"
if errorlevel 1 (
    echo [错误] 找不到项目目录 C:\workspace\食堂热量估算器
    pause
    exit /b 1
)

echo [1/5] 当前目录: %CD%
echo.

echo [2/5] 修复 requirements.txt...
(
echo streamlit^>=1.32.0
echo requests^>=2.31.0
echo crewai^>=0.80.0
) > requirements.txt
echo      ✅ requirements.txt 已更新
echo.

echo [3/5] 添加所有文件到 Git...
git add .
if errorlevel 1 (
    echo      [错误] git add 失败
    pause
    exit /b 1
)
echo      ✅ 文件已添加
echo.

echo [4/5] 提交更改...
git commit -m "修复requirements版本约束和LLM导入问题"
echo      ✅ 已提交
echo.

echo [5/5] 推送到 GitHub...
git push origin main
if errorlevel 1 (
    echo.
    echo      push 失败,尝试强制推送...
    git push --force origin main
)
echo.
echo ============================================
echo    完成! 代码已推送到 GitHub
echo ============================================
echo.
echo Streamlit Cloud 会自动重新部署,等2-3分钟刷新页面
echo.
pause