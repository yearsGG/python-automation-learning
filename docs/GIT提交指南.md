# Git 提交指南

由于PowerShell环境编码问题，无法通过自动化脚本提交，请手动执行以下命令。

## 📋 提交步骤

### 1. 查看当前修改状态

```bash
git status
```

你应该看到以下新增/修改的文件：
- `device_inspector.py` (新增)
- `main_inspection.py` (新增)
- `inspection_config.ini` (新增)
- `README.md` (修改)
- `培训计划与职业发展路线图.md` (新增)
- `实验网络拓扑设计.md` (新增)
- `简历项目描述_优化版.md` (新增)
- `GIT提交指南.md` (新增)
- `main_refactored.py` (修改)
- `text1.py` (修改)

### 2. 添加所有修改到暂存区

```bash
git add -A
```

或者分别添加：

```bash
git add device_inspector.py
git add main_inspection.py
git add inspection_config.ini
git add README.md
git add "培训计划与职业发展路线图.md"
git add "实验网络拓扑设计.md"
git add "简历项目描述_优化版.md"
git add "GIT提交指南.md"
git add main_refactored.py
git add text1.py
```

### 3. 提交修改

```bash
git commit -m "feat: v2.0 - 添加自动化巡检平台功能

- 新增device_inspector.py巡检核心模块（Ping检测、SSH采集、报告生成）
- 新增main_inspection.py完整巡检主程序
- 新增inspection_config.ini巡检配置文件
- 更新README.md文档，添加v2.0功能说明
- 新增培训计划与职业发展路线图文档
- 新增实验网络拓扑设计方案文档
- 新增简历项目描述优化版文档
- 优化main_refactored.py和text1.py代码

功能亮点：
- 批量设备巡检（支持多线程并发）
- Ping连通性检测
- SSH性能数据采集（CPU/内存/接口）
- 阈值告警和邮件通知
- 自动生成巡检报告"
```

### 4. 推送到远程仓库

```bash
git push origin master
```

如果是第一次推送，可能需要设置上游分支：

```bash
git push -u origin master
```

## 🔍 验证提交

### 查看提交历史

```bash
git log --oneline -5
```

### 查看最新提交的详细信息

```bash
git show
```

### 查看远程仓库状态

```bash
git remote -v
```

## ⚠️ 常见问题

### 问题1：提交时出现中文乱码

**解决方案**：
```bash
git config --global core.quotepath false
git config --global i18n.commitencoding utf-8
git config --global i18n.logoutputencoding utf-8
```

### 问题2：推送时需要身份验证

**解决方案**：
- 如果使用HTTPS，需要输入GitHub用户名和Personal Access Token
- 如果使用SSH，确保已配置SSH密钥

生成SSH密钥（如果没有）：
```bash
ssh-keygen -t rsa -b 4096 -C "your_email@example.com"
```

添加公钥到GitHub：
1. 复制 `~/.ssh/id_rsa.pub` 的内容
2. GitHub Settings → SSH and GPG keys → New SSH key
3. 粘贴公钥并保存

### 问题3：合并冲突

如果在推送前有其他人修改了远程仓库：

```bash
# 拉取远程修改
git pull origin master

# 如果有冲突，手动解决后：
git add .
git commit -m "merge: 解决合并冲突"
git push origin master
```

## 📝 Git 最佳实践

### Commit Message 规范

采用约定式提交（Conventional Commits）：

```
<type>(<scope>): <subject>

<body>

<footer>
```

**Type类型**：
- `feat`: 新功能
- `fix`: Bug修复
- `docs`: 文档更新
- `refactor`: 代码重构
- `test`: 测试相关
- `chore`: 构建/工具链更新
- `style`: 代码格式调整

**示例**：
```bash
feat(inspector): 添加SNMP数据采集功能

- 使用pysnmp库采集设备CPU/内存数据
- 支持SNMPv2c和SNMPv3协议
- 添加OID配置文件

Closes #12
```

### 分支管理建议

```bash
# 创建功能分支
git checkout -b feature/snmp-collection

# 开发完成后合并到主分支
git checkout master
git merge feature/snmp-collection

# 删除已合并的分支
git branch -d feature/snmp-collection
```

### .gitignore 文件

确保以下内容在 `.gitignore` 中：

```
# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
venv/
env/
ENV/

# 敏感信息
config.ini
inspection_config.ini
*.log

# IDE
.vscode/
.idea/
*.swp

# 报告文件
reports/*.txt
reports/*.xlsx

# 临时文件
*.tmp
~$*
```

**注意**：配置文件模板应保留，但包含真实密码的配置文件不应提交！

## 🎯 提交检查清单

提交前请确认：

- [ ] 代码已通过基本测试（至少运行过一次）
- [ ] 删除了调试用的print语句（或改为logging）
- [ ] 更新了相关文档（README、注释等）
- [ ] 敏感信息（密码、IP）已从代码中移除
- [ ] Commit message清晰描述了修改内容
- [ ] 没有提交不必要的文件（临时文件、日志等）

## 📚 进阶学习

### 推荐教程
- Git官方文档：https://git-scm.com/doc
- Pro Git电子书（中文）：https://git-scm.com/book/zh/v2
- Learn Git Branching（可视化学习）：https://learngitbranching.js.org/?locale=zh_CN

### 常用Git命令速查

```bash
# 初始化仓库
git init

# 克隆远程仓库
git clone <url>

# 查看状态
git status

# 查看差异
git diff

# 暂存修改
git add <file>
git add .

# 提交
git commit -m "message"

# 查看历史
git log
git log --oneline --graph

# 撤销修改
git checkout -- <file>      # 撤销工作区修改
git reset HEAD <file>        # 撤销暂存
git reset --hard HEAD^       # 回退到上一个版本（危险！）

# 分支操作
git branch                   # 查看分支
git branch <name>            # 创建分支
git checkout <name>          # 切换分支
git checkout -b <name>       # 创建并切换分支
git merge <name>             # 合并分支
git branch -d <name>         # 删除分支

# 远程操作
git remote -v                # 查看远程仓库
git fetch origin             # 拉取远程更新
git pull origin master       # 拉取并合并
git push origin master       # 推送到远程

# 标签
git tag v1.0                 # 创建标签
git push origin v1.0         # 推送标签
```

---

**准备好了吗？现在就打开PowerShell/Git Bash，执行上面的命令吧！** 🚀

