# SEMagi API 客户端工具包

这是一个完整的SEMagi API客户端工具包，提供了统一的接口与SEMagi API交互，支持关键词分组和搜索功能。

## ⭐ 核心特性

### 🐍 Python客户端
- 🚀 **功能完整**: 支持所有API功能
- ⏳ **智能等待**: 基于预计时间的动态轮询机制
- 📊 **格式化输出**: 美观的结果展示
- 🔄 **错误处理**: 完善的异常处理

### 🌐 全平台支持
- **Unix/Linux/macOS**: 使用Bash脚本
- **Windows**: 使用批处理脚本
- **跨环境**: Git Bash、WSL等环境

### 📦 系统要求
- **Python 3.x**: 必需
- **requests库**: 必需 (pip install requests)
- **跨平台**: 支持Unix/Linux/macOS/Windows

## 🚀 快速开始

### 1. 配置API密钥

```bash
# 复制示例配置文件
cp settings.example.json settings.json

# 编辑配置文件，填入你的API密钥
```

配置文件示例：
```json
{
  "api_key": "sk_your_api_key_here",
  "base_url": "http://localhost:8000",
  "task": {
    "function": "scrap-and-group",
    "file": "keywords.csv",
    "task_name": "my_task"
  },
  "defaults": {
    "grouper": "hierarchical_clustering",
    "min_similarity": 0.5,
    "range": 10,
    "country": "us",
    "language": "en",
    "numbers": 10,
    "force_group": true,
    "force_group_min_similarity": 0.2
  }
}
```

### 2. 超简洁使用

**配置一次，终身受益**
```bash
# Unix/Linux/macOS
./semagi create-task

# Windows
semagi.bat create-task
```

**如需覆盖特定参数**
```bash
# 覆盖文件和任务名
./semagi -i custom.json -n "custom_task" create-task
```

统一脚本会自动：
1. 检测Python环境
2. 加载配置文件
3. 调用Python客户端
4. 返回格式化的结果

## 📖 详细使用说明

### 1. 配置文件详解

配置文件 `settings.json` 支持以下配置项：

```json
{
  "api_key": "你的API密钥",
  "base_url": "API服务器地址",
  "task": {
    "function": "group-only | scrap-and-group",
    "file": "默认文件路径",
    "task_name": "默认任务名称"
  },
  "defaults": {
    "grouper": "分组算法",
    "min_similarity": 0.5,
    "range": 10,
    "country": "us",
    "language": "en", 
    "numbers": 10,
    "force_group": true,
    "force_group_min_similarity": 0.2
  },
  "timeout": {
    "request_timeout": 30,
    "max_wait_time": 1800
  },
  "display": {
    "show_debug": false,
    "show_progress": true
  }
}
```

### 2. 获取API密钥

在SEMagi网站上生成API密钥：

1. 登录你的SEMagi账户
2. 进入API页面 (`/api`)
3. 生成新的API密钥
4. 复制密钥备用

### 3. 基本操作

#### 🎯 超简洁方式（推荐）

```bash
# 创建任务（使用配置文件中的所有参数）
./semagi create-task

# 查询任务状态
./semagi -t "task_id" check-status

# 获取任务结果
./semagi -t "task_id" get-results
```

#### ⚙️ 参数覆盖方式

```bash
# 覆盖特定参数
./semagi -f scrap-and-group -i "custom.csv" -n "custom_task" create-task

# 覆盖功能类型
./semagi -f scrap-and-group create-task
```

#### 📋 任务管理

```bash
# 检查系统环境
./semagi --check-env

# 显示客户端信息
./semagi --show-client create-task
```

#### 📁 支持的功能类型

**关键词分组功能 (group-only)**
- 适用于已有关键词数据，只需要进行分组
- **文件格式要求**: JSON文件

**搜索+分组功能 (scrap-and-group)**
- 适用于需要先搜索相关关键词，再进行分组
- **文件格式要求**: CSV/TXT文件，包含基础关键词

### 4. 高级参数设置

可在配置文件中预设所有参数，或通过命令行临时覆盖：

```bash
# 覆盖高级参数
./semagi --country us --language en --numbers 50 create-task
```

#### 参数说明

所有参数都可以在配置文件中预设，无需每次输入：

| 配置项 | 类型 | 默认值 | 说明 |
|--------|------|--------|------|
| `api_key` | string | **必需** | API密钥 |
| `task.function` | string | `group-only` | 功能类型 |
| `task.file` | string | `keywords.json` | 输入文件路径 |
| `task.task_name` | string | `my_task` | 任务名称 |
| `base_url` | string | `http://localhost:8000` | API基础URL |
| `--grouper` | string | `hierarchical_clustering` | 分组算法 (`hierarchical_clustering` 或 `jaccard`) |
| `--min-similarity` | float | `0.5` | 最小相似度 (0.0-1.0) |
| `--range` | int | `10` | 搜索范围 (1-1000) |
| `--country` | string | `us` | 搜索国家代码 |
| `--language` | string | `en` | 搜索语言代码 |
| `--numbers` | int | `10` | 搜索结果数量 |
| `--no-wait` | flag | `false` | 不等待任务完成 |

### 4. 查询操作

#### 查询任务状态

```bash
python api_client.py \
  --api-key "your_api_key_here" \
  --check-status "task_id_here"
```

#### 获取任务结果

```bash
python api_client.py \
  --api-key "your_api_key_here" \
  --get-results "task_id_here"
```

## 📝 文件格式要求

### group-only 功能 (JSON格式)

**基础格式：**
```json
{
  "keywords": [
    "SEO tools",
    "keyword research", 
    "search engine optimization"
  ]
}
```

**包含数据的格式：**
```json
[
  {
    "keyword": "SEO tools",
    "search_volume": 1000,
    "competition": 0.5
  }
]
```

### scrap-and-group 功能 (CSV格式)

**基础格式：**
```csv
keyword
SEO
marketing
analytics
```

**包含分类的格式：**
```csv
keyword,category
SEO,search
marketing,general
analytics,tools
```

### 3. 环境依赖检查

使用 `--check-env` 选项检查系统环境：

```bash
./semagi --check-env
```

这将检查：
- Python 3.x 是否可用
- requests 库是否已安装
- 显示详细的环境信息

## 智能等待机制

客户端包含智能轮询机制，根据预计时间动态调整查询间隔：

- **前50%时间**: 较长间隔轮询 (5-30秒)
- **50%-80%时间**: 中等间隔轮询 (3-15秒)  
- **80%+时间**: 短间隔轮询 (2-10秒)
- **无预计时间**: 渐进式间隔 (5→10→15秒)

## 输出示例

```
🚀 创建任务: my_grouping_task
   功能: group-only
   文件: keywords.json (1245 bytes)
✅ 任务创建成功!
   任务ID: 550e8400-e29b-41d4-a716-446655440000
   预计完成时间: 120秒

⏳ 等待任务完成: 550e8400-e29b-41d4-a716-446655440000
   预计等待时间: 120秒
   [01] 状态: running (已等待 5.0s) - 预计剩余: 115s
   [02] 状态: running (已等待 25.0s) - 预计剩余: 95s
   [03] 状态: completed (已等待  89.3s)
✅ 任务完成! (总耗时: 89.3s)

============================================================
📊 任务结果
============================================================
任务名称: my_grouping_task
处理功能: group-only
处理时间: 87.45秒
消耗积分: 5
处理关键词数: 1500
创建分组数: 25

📁 下载链接:
  CSV: https://storage.googleapis.com/files/result.csv
  JSON: https://storage.googleapis.com/files/result.json

🔍 分组预览 (前3个分组):
  [1] group_1:
      主关键词: SEO tools
      关键词数: 12
      示例: SEO tools, search engine optimization tools, SEO software
      搜索量: 1200
  [2] group_2:
      主关键词: keyword research
      关键词数: 8
      示例: keyword research, keyword analysis, keyword finder
      搜索量: 800
  [3] group_3:
      主关键词: google analytics
      关键词数: 15
      示例: google analytics, web analytics, site analytics
      搜索量: 2500
  ... 还有 22 个分组
============================================================

🎉 任务完成成功!
```

## 错误处理

客户端包含完善的错误处理机制：

- **文件错误**: 自动检查文件存在性和格式
- **参数验证**: 验证必需参数和参数范围
- **网络错误**: 自动重试和友好的错误信息
- **API错误**: 详细的错误代码和解决建议
- **中断处理**: 优雅处理Ctrl+C中断

## 常见问题

### Q: 支持哪些文件格式？

A: 
- `group-only`: 仅支持 `.json` 格式
- `scrap-and-group`: 支持 `.csv` 和 `.txt` 格式

### Q: 任务需要多长时间完成？

A: 处理时间取决于：
- 关键词数量
- 选择的功能 (`scrap-and-group` 通常需要更长时间)
- 搜索参数 (搜索数量、范围等)
- 服务器负载

通常：
- 100个关键词的分组：1-3分钟
- 100个关键词的搜索+分组：3-10分钟

### Q: 如何查看任务的详细日志？

A: 客户端会显示实时状态，包括：
- 任务创建状态
- 预计完成时间
- 轮询进度
- 错误信息
- 最终结果

### Q: 可以同时运行多个任务吗？

A: 根据API限制，每个用户同时只能运行一个任务。如果尝试创建新任务时有任务正在运行，会收到相应的错误提示。

### Q: 如何处理大文件？

A: API有文件大小限制 (10MB)。对于大文件，建议：
1. 分割成多个小文件
2. 使用更高的相似度阈值减少处理时间
3. 分批处理关键词

## 📁 文件清单

```
client/
├── ⭐ semagi                    # 统一入口脚本 (Unix/Linux/macOS)
├── ⭐ semagi.bat                # 统一入口脚本 (Windows)
├── 📄 README.md                # 使用说明文档
├── 📋 requirements.txt         # Python依赖
├── ⚙️ settings.json            # 配置文件
├── 📋 settings.example.json    # 配置文件示例
├── 📄 keywords.json            # 示例关键词文件
└── 📁 scripts/                 # 具体实现脚本目录
    └── 🐍 api_client.py        # Python API客户端
```

### 文件说明

- **统一入口** (推荐使用):
  - `semagi`: Unix/Linux/macOS统一入口脚本
  - `semagi.bat`: Windows统一入口脚本
  - 自动检测Python环境，调用Python客户端

- **配置文件**:
  - `settings.json`: 主配置文件（包含API密钥等）
  - `settings.example.json`: 配置文件模板
  - `README.md`: 完整的使用说明和API文档
  - `requirements.txt`: Python客户端所需的依赖包

- **具体实现** (`scripts/`目录):
  - `api_client.py`: Python客户端实现
  - 由统一入口脚本自动调用，用户无需直接使用

## 🛠️ 技术支持

如果遇到问题：

1. 检查Python环境：`./semagi --check-env`
2. 检查API密钥是否正确配置在settings.json中
3. 确认文件格式符合要求
4. 检查网络连接
5. 查看错误信息和状态码
6. 参考相应的文档和示例
7. 联系技术支持

## 📄 许可证

版权所有 © 2025 SEMagi。保留所有权利。
