@echo off
chcp 65001 >nul
setlocal enabledelayedexpansion

rem ============================================================
rem  麦麦活动雷达助手 - GitHub 仓库初始化脚本
rem  用法：先安装 Git（https://git-scm.com/download/win），
rem        再修改下方「你的 GitHub 用户名」和「仓库名」，双击运行即可
rem ============================================================

rem >>>>>> 修改这里：你的 GitHub 用户名 和 仓库名（仅英文/数字/横线） <<<<<<
set "GITHUB_USER=Kikisun114"
set "REPO_NAME=mai-activity-radar"
set "BRANCH=main"

echo [1/6] 检查 Git 是否已安装...
where git >nul 2>&1
if errorlevel 1 (
  echo [错误] 未检测到 Git，请先安装：https://git-scm.com/download/win
  echo        或执行：winget install --id Git.Git -e --source winget
  pause
  exit /b 1
)

echo [2/6] 检查 Git 身份配置（首次提交需要）...
git config --global user.name  >nul 2>&1
if errorlevel 1 echo [提示] 未配置全局用户名，请执行：git config --global user.name "你的名字"
git config --global user.email >nul 2>&1
if errorlevel 1 echo [提示] 未配置全局邮箱，请执行：git config --global user.email "你的邮箱"

cd /d "%~dp0"

echo [3/6] 初始化仓库（默认分支 %BRANCH%）...
git init -b %BRANCH% 2>nul || (git init && git branch -M %BRANCH%)

echo [4/6] 安全校验：mcp-config.local.json 必须被 .gitignore 忽略...
git check-ignore mcp-config.local.json >nul 2>&1
if errorlevel 1 (
  echo [错误] mcp-config.local.json 未被忽略，禁止提交真实 Token！请检查 .gitignore
  pause
  exit /b 1
)

echo [5/6] 添加并提交全部文件...
git add -A
git commit -m "feat: 麦麦活动雷达助手 - 麦当劳 MCP Skill 参赛作品"
if errorlevel 1 (
  echo [错误] 提交失败（通常是没有配置身份或没有变更），请查看上方提示
  pause
  exit /b 1
)

echo [6/6] 创建远程仓库并推送...
where gh >nul 2>&1
if errorlevel 1 (
  echo 未检测到 GitHub CLI(gh)，请手动完成最后两步：
  echo   1. 打开 https://github.com/new
  echo      仓库名填 %REPO_NAME%，选择 Public，不要勾选任何初始化文件
  echo   2. 回到本目录执行：
  echo      git remote add origin https://github.com/%GITHUB_USER%/%REPO_NAME%.git
  echo      git push -u origin %BRANCH%
) else (
  echo 使用 GitHub CLI 自动创建公开仓库并推送...
  gh repo create %GITHUB_USER%/%REPO_NAME% --public --source . --push
)

echo.
echo 完成！仓库地址：https://github.com/%GITHUB_USER%/%REPO_NAME%
echo 提交后别忘了：
echo   - 在官方仓库提 Issue 报名（标题与正文之间不要多余换行）
echo   - 用 WorkBuddy 导出的真实开发对话替换 workbuddy.md
pause
