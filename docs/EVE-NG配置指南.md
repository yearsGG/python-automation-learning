# EVE-NG 网络配置指南

## 网络拓扑说明

```
Internet (Net)
      |
   G0/0/0 (DHCP或固定IP)
      |
   AR1000v 路由器
      |
   G0/0/1 (192.168.10.1/24)
      |
   Cloud (pnet9)
      |
EVE-NG主机 (192.168.10.100/24)
```

## 1. EVE-NG主机网络配置

### 配置pnet9接口

```bash
# 添加IP地址
ip addr add 192.168.10.100/24 dev pnet9

# 启用接口
ip link set pnet9 up

# 验证配置
ifconfig pnet9
```

### 持久化配置（可选）

创建网络配置文件 `/etc/network/interfaces.d/pnet9`:

```bash
auto pnet9
iface pnet9 inet static
    address 192.168.10.100
    netmask 255.255.255.0
```

## 2. AR路由器配置

### 基础配置

```
# 进入系统视图
system-view

# 配置主机名
sysname AR1

# 配置G0/0/1接口（连接EVE-NG主机）
interface GigabitEthernet 0/0/1
 ip address 192.168.10.1 255.255.255.0
 undo shutdown
 quit

# 配置G0/0/0接口（连接外网）
interface GigabitEthernet 0/0/0
 ip address 192.168.1.254 255.255.255.0  # 根据实际网络修改
 undo shutdown
 quit
```

### SSH服务配置

```
# 启用SSH服务
stelnet server enable

# 配置VTY用户界面
user-interface vty 0 4
 authentication-mode aaa
 protocol inbound ssh
 quit

# 创建本地用户
aaa
 local-user admin password cipher admin123
 local-user admin privilege level 15
 local-user admin service-type ssh
 quit

# 生成RSA密钥对
rsa local-key-pair create
```

### Telnet服务配置（备选）

```
# 配置VTY用户界面
user-interface vty 0 4
 authentication-mode aaa
 protocol inbound telnet
 quit

# 创建本地用户
aaa
 local-user admin password cipher admin123
 local-user admin privilege level 15
 local-user admin service-type telnet
 quit
```

### 保存配置

```
# 保存配置
save
# 选择 Y 确认
```

## 3. 连接测试

### Ping测试

```bash
# 从EVE-NG主机ping AR路由器
ping 192.168.10.1

# 从AR路由器ping EVE-NG主机
ping 192.168.10.100
```

### SSH连接测试

```bash
# 手动SSH连接测试
ssh admin@192.168.10.1

# 使用Python脚本测试
cd /root/github/python-automation-learning
source venv/bin/activate
python test_eve_connection.py
```

## 4. EVE-NG Cloud配置

在EVE-NG Web界面中：

1. 右键点击Cloud节点 → Edit
2. 选择 **pnet9** 作为网络接口
3. 点击 Save

## 5. 常见问题排查

### 问题1: 无法ping通路由器

**检查项：**
- pnet9接口是否配置了正确的IP地址
- pnet9接口是否处于UP状态
- AR路由器G0/0/1接口是否配置了IP并启用
- EVE-NG Cloud是否绑定到pnet9

**排查命令：**
```bash
# 检查接口状态
ifconfig pnet9

# 检查路由表
ip route

# 抓包分析
tcpdump -i pnet9 icmp
```

### 问题2: SSH连接被拒绝

**检查项：**
- AR路由器是否启用了SSH服务
- 是否创建了SSH用户
- 是否生成了RSA密钥对
- 防火墙是否阻止了22端口

**在AR路由器上检查：**
```
# 检查SSH服务状态
display ssh server status

# 检查用户配置
display aaa local-user

# 检查VTY配置
display current-configuration | include user-interface
```

### 问题3: 认证失败

**可能原因：**
- 用户名或密码错误
- 用户权限不足
- 认证模式配置错误

**解决方法：**
```
# 重新配置用户
aaa
 local-user admin password cipher NewPassword123
 local-user admin privilege level 15
 local-user admin service-type ssh
 quit
```

## 6. Python脚本配置

### 修改连接参数

编辑测试脚本中的连接信息：

```python
HOST = '192.168.10.1'       # AR路由器IP
USER = 'admin'              # SSH用户名
PASSWORD = 'admin123'       # SSH密码
PORT = 22                   # SSH端口
```

### 运行测试脚本

```bash
cd /root/github/python-automation-learning
source venv/bin/activate
python test_eve_connection.py
```

## 7. 网络拓扑扩展

### 添加更多设备

可以在192.168.10.0/24网段中添加更多设备：

- AR路由器: 192.168.10.1
- EVE-NG主机: 192.168.10.100
- 交换机1: 192.168.10.2
- 交换机2: 192.168.10.3
- 其他设备: 192.168.10.10-254

### 配置NAT（可选）

如果需要让内网设备访问外网：

```
# 在AR路由器上配置NAT
acl number 2000
 rule 5 permit source 192.168.10.0 0.0.0.255
 quit

interface GigabitEthernet 0/0/0
 nat outbound 2000
 quit
```

## 8. 自动化脚本示例

### 批量配置多台设备

```python
devices = [
    {'host': '192.168.10.1', 'name': 'AR1'},
    {'host': '192.168.10.2', 'name': 'SW1'},
    {'host': '192.168.10.3', 'name': 'SW2'},
]

for device in devices:
    ssh = VisualSSH(device['host'], username='admin', password='admin123')
    # 执行配置命令
    ssh.close()
```

## 9. 参考资料

- EVE-NG官方文档: https://www.eve-ng.net/index.php/documentation/
- 华为VRP命令参考: https://support.huawei.com/
- Paramiko文档: https://www.paramiko.org/

---

**配置完成时间**: 2024-11-18
**测试状态**: ✓ 网络连通性正常
**下一步**: 运行Python自动化脚本进行设备配置
