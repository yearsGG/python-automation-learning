# EVE-NG 自动化测试环境配置完成

## 📋 配置摘要

✅ **EVE-NG主机网络配置完成**
- 接口: pnet9
- IP地址: 192.168.10.100/24
- 状态: UP and RUNNING
- 连通性: ✓ 可以ping通192.168.10.1

✅ **Python环境准备完成**
- 虚拟环境: `/root/github/python-automation-learning/venv`
- 依赖包: paramiko ✓, colorama ✓

⚠️ **待完成: AR路由器配置**
- SSH服务需要在AR路由器上启用
- 配置命令已准备好

---

## 🚀 快速开始

### 1. 配置AR路由器

在EVE-NG Web界面中，打开AR1000v的控制台，复制粘贴以下命令：

```
system-view
sysname AR1
interface GigabitEthernet 0/0/1
 ip address 192.168.10.1 255.255.255.0
 undo shutdown
 quit
stelnet server enable
rsa local-key-pair create
aaa
 local-user admin password cipher admin123
 local-user admin privilege level 15
 local-user admin service-type ssh telnet
 quit
user-interface vty 0 4
 authentication-mode aaa
 protocol inbound ssh telnet
 user privilege level 15
 quit
quit
save
```

### 2. 验证网络连接

```bash
# 运行快速测试脚本
/root/github/python-automation-learning/quick_test.sh
```

### 3. 运行Python自动化脚本

```bash
cd /root/github/python-automation-learning
source venv/bin/activate
python test_eve_connection.py
```

---

## 📁 文件说明

### 配置文件
- `docs/EVE-NG配置指南.md` - 详细的配置步骤和故障排查
- `docs/AR路由器配置命令.txt` - AR路由器完整配置命令
- `EVE-NG-README.md` - 本文件（快速参考）

### 测试脚本
- `test_eve_connection.py` - Python SSH连接测试脚本
- `quick_test.sh` - 网络连接快速测试脚本

### 核心模块
- `src/my_visual_ssh.py` - SSH可视化交互类
- `src/my_visual_telnet.py` - Telnet可视化交互类

---

## 🌐 网络拓扑

```
     Internet
         |
    [G0/0/0] (DHCP)
         |
    AR1000v (192.168.10.1)
         |
    [G0/0/1]
         |
    Cloud (pnet9)
         |
EVE-NG Host (192.168.10.100)
```

---

## 🔧 常用命令

### EVE-NG主机端

```bash
# 查看pnet9接口状态
ifconfig pnet9

# Ping测试
ping 192.168.10.1

# SSH手动连接
ssh admin@192.168.10.1

# Telnet手动连接
telnet 192.168.10.1

# 抓包分析
tcpdump -i pnet9 -n
```

### AR路由器端

```
# 查看接口状态
display ip interface brief

# 查看SSH服务状态
display ssh server status

# 查看用户配置
display aaa local-user

# Ping测试EVE-NG主机
ping 192.168.10.100
```

---

## 📊 测试结果

### 网络层测试
- ✅ pnet9接口配置: 192.168.10.100/24
- ✅ Ping 192.168.10.1: 成功
- ⏳ SSH端口22: 待AR路由器配置后测试
- ⏳ Telnet端口23: 待AR路由器配置后测试

### Python环境测试
- ✅ 虚拟环境: 已创建
- ✅ paramiko: 已安装
- ✅ colorama: 已安装

---

## 🎯 下一步操作

1. **配置AR路由器SSH服务**
   - 在EVE-NG控制台执行配置命令
   - 保存配置

2. **验证SSH连接**
   ```bash
   ssh admin@192.168.10.1
   # 密码: admin123
   ```

3. **运行自动化测试**
   ```bash
   cd /root/github/python-automation-learning
   source venv/bin/activate
   python test_eve_connection.py
   ```

4. **开始自动化脚本开发**
   - 使用 `src/my_visual_ssh.py` 进行SSH自动化
   - 参考 `test_eve_connection.py` 示例代码

---

## 🐛 故障排查

### 问题: 无法ping通192.168.10.1

**解决方法:**
1. 检查AR路由器G0/0/1接口是否配置IP并启用
2. 检查EVE-NG Cloud是否绑定到pnet9
3. 检查pnet9接口是否UP

```bash
# 重新配置pnet9
ip addr add 192.168.10.100/24 dev pnet9
ip link set pnet9 up
```

### 问题: SSH连接被拒绝

**解决方法:**
1. 确认AR路由器已启用SSH服务
2. 确认已生成RSA密钥对
3. 确认用户已创建并授权SSH服务

```
# 在AR路由器上检查
display ssh server status
display aaa local-user
```

### 问题: 认证失败

**解决方法:**
1. 确认用户名: admin
2. 确认密码: admin123
3. 重新创建用户

```
aaa
 local-user admin password cipher admin123
 local-user admin privilege level 15
 local-user admin service-type ssh
 quit
```

---

## 📚 参考文档

- [EVE-NG配置指南](docs/EVE-NG配置指南.md) - 完整配置文档
- [AR路由器配置命令](docs/AR路由器配置命令.txt) - 配置命令参考
- [项目README](README.md) - 项目总体说明

---


