# AI Gateway SDK 设计文档

## 1. 核心理念

**让 MCU 成为 AI 网络中的标准节点**

- App 开发者不需要关心后端是魔搭/Claude/自建模型
- 统一接口，随时切换后端
- 自动处理网络/内存/并发问题

---

## 2. SDK 架构

```python
# 文件结构
upypi_packages/
└── ai_gateway/
    ├── __init__.py          # 主入口
    ├── client.py            # 统一客户端
    ├── providers/           # 各种后端适配器
    │   ├── modelscope.py
    │   ├── claude.py
    │   ├── openai.py
    │   └── custom.py
    ├── cache.py             # 本地缓存
    ├── queue.py             # 请求队列
    └── utils.py             # 工具函数
```

---

## 3. 使用示例

### 3.1 基础用法（App 开发者视角）

```python
from ai_gateway import AIClient

# 初始化（自动读取配置）
ai = AIClient()

# 文本生成
response = ai.generate(
    prompt="帮我写一个温度监控的逻辑",
    max_tokens=200
)
print(response.text)

# 图像识别
image = camera.capture()
result = ai.classify_image(
    image=image,
    labels=["cat", "dog", "bird"]
)
print(f"识别结果: {result.label}, 置信度: {result.confidence}")

# 语音识别
audio = mic.record(3000)
text = ai.transcribe(audio)
print(f"你说的是: {text}")
```

**关键点：App 开发者不需要知道后端是谁！**

---

### 3.2 配置文件（设备管理员视角）

```json
// /data/ai_gateway/config.json
{
  "default_provider": "modelscope",
  "providers": {
    "modelscope": {
      "api_key": "your_key",
      "endpoint": "https://api.modelscope.cn/v1",
      "models": {
        "text_generation": "qwen-turbo",
        "image_classification": "damo/cv_resnet50",
        "speech_recognition": "damo/speech_paraformer"
      }
    },
    "claude": {
      "api_key": "sk-ant-xxx",
      "endpoint": "https://api.anthropic.com/v1",
      "proxy": "http://192.168.1.100:8080"  // 本地代理解决 HTTPS
    }
  },
  "cache": {
    "enabled": true,
    "max_size_kb": 100,
    "ttl_seconds": 3600
  },
  "queue": {
    "max_pending": 5,
    "timeout_ms": 30000
  }
}
```

---

### 3.3 高级用法（多模型协同）

```python
from ai_gateway import AIClient

ai = AIClient()

# 场景：智能门禁
image = camera.capture()

# 第一步：人脸检测（快速本地模型）
has_face = ai.detect_face(image, provider="local")

if has_face:
    # 第二步：人脸识别（云端精确模型）
    person = ai.recognize_face(image, provider="modelscope")
    
    if person.confidence < 0.9:
        # 第三步：不确定时，调用 LLM 辅助决策
        decision = ai.generate(
            prompt=f"人脸识别置信度{person.confidence}，是否放行？考虑安全性。",
            provider="claude"
        )
        return decision
    else:
        return f"欢迎 {person.name}"
```

---

## 4. 核心功能设计

### 4.1 统一接口层

```python
# client.py
class AIClient:
    def __init__(self, config_path="/data/ai_gateway/config.json"):
        self.config = self._load_config(config_path)
        self.providers = self._init_providers()
        self.cache = Cache(self.config['cache'])
        self.queue = RequestQueue(self.config['queue'])
    
    def generate(self, prompt, provider=None, **kwargs):
        """文本生成统一接口"""
        provider = provider or self.config['default_provider']
        
        # 检查缓存
        cache_key = f"gen:{hash(prompt)}"
        if cached := self.cache.get(cache_key):
            return cached
        
        # 调用后端
        result = self.providers[provider].generate(prompt, **kwargs)
        
        # 写入缓存
        self.cache.set(cache_key, result)
        return result
    
    def classify_image(self, image, labels, provider=None):
        """图像分类统一接口"""
        provider = provider or self.config['default_provider']
        return self.providers[provider].classify_image(image, labels)
    
    def transcribe(self, audio, provider=None):
        """语音识别统一接口"""
        provider = provider or self.config['default_provider']
        return self.providers[provider].transcribe(audio)
```

---

### 4.2 Provider 适配器

```python
# providers/modelscope.py
class ModelScopeProvider:
    def __init__(self, config):
        self.api_key = config['api_key']
        self.endpoint = config['endpoint']
        self.models = config['models']
    
    def generate(self, prompt, max_tokens=200):
        import urequests, ujson
        
        url = f"{self.endpoint}/chat/completions"
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        data = {
            "model": self.models['text_generation'],
            "messages": [{"role": "user", "content": prompt}],
            "max_tokens": max_tokens
        }
        
        resp = urequests.post(url, headers=headers, json=data)
        result = ujson.loads(resp.text)
        resp.close()
        
        return AIResponse(
            text=result['choices'][0]['message']['content'],
            provider="modelscope",
            model=self.models['text_generation']
        )
    
    def classify_image(self, image, labels):
        # 实现图像分类
        pass
    
    def transcribe(self, audio):
        # 实现语音识别
        pass
```

```python
# providers/claude.py
class ClaudeProvider:
    def __init__(self, config):
        self.api_key = config['api_key']
        self.endpoint = config['endpoint']
        self.proxy = config.get('proxy')  # 可选代理
    
    def generate(self, prompt, max_tokens=200):
        import urequests, ujson
        
        # 如果配置了代理，使用代理
        url = self.proxy or self.endpoint
        if self.proxy:
            url = f"{self.proxy}/v1/messages"
        else:
            url = f"{self.endpoint}/messages"
        
        headers = {
            "x-api-key": self.api_key,
            "anthropic-version": "2023-06-01",
            "content-type": "application/json"
        }
        data = {
            "model": "claude-3-haiku-20240307",
            "max_tokens": max_tokens,
            "messages": [{"role": "user", "content": prompt}]
        }
        
        resp = urequests.post(url, headers=headers, json=data)
        result = ujson.loads(resp.text)
        resp.close()
        
        return AIResponse(
            text=result['content'][0]['text'],
            provider="claude",
            model="claude-3-haiku"
        )
```

---

### 4.3 缓存机制

```python
# cache.py
class Cache:
    def __init__(self, config):
        self.enabled = config['enabled']
        self.max_size = config['max_size_kb'] * 1024
        self.ttl = config['ttl_seconds']
        self.store = {}  # {key: (value, timestamp)}
    
    def get(self, key):
        if not self.enabled:
            return None
        
        if key in self.store:
            value, timestamp = self.store[key]
            if time.time() - timestamp < self.ttl:
                return value
            else:
                del self.store[key]  # 过期删除
        return None
    
    def set(self, key, value):
        if not self.enabled:
            return
        
        # 简单的 LRU：如果超过大小限制，删除最老的
        if self._get_size() > self.max_size:
            oldest_key = min(self.store.keys(), 
                           key=lambda k: self.store[k][1])
            del self.store[oldest_key]
        
        self.store[key] = (value, time.time())
```

---

### 4.4 请求队列（防止并发过载）

```python
# queue.py
import uasyncio as asyncio

class RequestQueue:
    def __init__(self, config):
        self.max_pending = config['max_pending']
        self.timeout = config['timeout_ms']
        self.queue = []
        self.processing = 0
    
    async def submit(self, func, *args, **kwargs):
        """提交请求到队列"""
        if len(self.queue) >= self.max_pending:
            raise Exception("Queue full")
        
        future = asyncio.Future()
        self.queue.append((func, args, kwargs, future))
        
        # 触发处理
        asyncio.create_task(self._process())
        
        # 等待结果
        return await asyncio.wait_for(future, self.timeout / 1000)
    
    async def _process(self):
        if self.processing > 0 or not self.queue:
            return
        
        self.processing += 1
        func, args, kwargs, future = self.queue.pop(0)
        
        try:
            result = func(*args, **kwargs)
            future.set_result(result)
        except Exception as e:
            future.set_exception(e)
        finally:
            self.processing -= 1
```

---

## 5. 部署方式

### 5.1 作为系统服务（推荐）

```python
# builtin/apps/com.micropythonos.aigateway/assets/aigateway_service.py
from mpos import Activity
from ai_gateway import AIClient

class AIGatewayService(Activity):
    """后台服务，常驻内存"""
    
    def onCreate(self):
        self.client = AIClient()
        # 预热：加载配置、建立连接
        self.client.warmup()
    
    def onStart(self):
        # 启动后台任务
        import uasyncio as asyncio
        asyncio.create_task(self._background_sync())
    
    async def _background_sync(self):
        """后台同步缓存、更新模型列表等"""
        while True:
            await asyncio.sleep(300)  # 5分钟
            self.client.sync()
```

### 5.2 作为库（轻量级）

```python
# App 直接导入使用
from ai_gateway import AIClient

ai = AIClient()
result = ai.generate("hello")
```

---

## 6. 优势分析

### 6.1 对 App 开发者
- ✅ 统一接口，学习成本低
- ✅ 不用管网络/缓存/重试
- ✅ 随时切换后端（魔搭→Claude→自建）

### 6.2 对设备管理员
- ✅ 集中配置（一个文件管所有 App）
- ✅ 成本控制（限流、缓存）
- ✅ 灵活切换（测试用免费模型，生产用付费模型）

### 6.3 对生态
- ✅ 降低开发门槛 → 更多 AI App
- ✅ 标准化接口 → App 可移植性强
- ✅ 网络效应 → 越多人用，价值越大

---

## 7. 与竞品对比

| 方案 | 优势 | 劣势 |
|------|------|------|
| **直接调 API** | 简单 | 每个 App 重复造轮子 |
| **云端网关** | 功能强大 | 依赖网络，延迟高 |
| **本地推理** | 快速 | 模型能力受限 |
| **AI Gateway SDK** ✅ | 统一、灵活、可扩展 | 需要维护 SDK |

---

## 8. 商业化路径

### 8.1 开源 + 增值服务
- SDK 开源（吸引开发者）
- 云端管理平台收费（设备监控、API 统计）

### 8.2 硬件捆绑
- "AI 开发板" = 硬件 + 预装 SDK + API 额度
- 售价 299 元，包含 1000 次 API 调用

### 8.3 企业授权
- 私有部署版本
- 自定义后端适配器
- 技术支持

---

## 9. 下一步

1. **实现 MVP**（1周）
   - 基础 AIClient
   - ModelScope Provider
   - 简单缓存

2. **做 Demo App**（1周）
   - 语音助手
   - 图像识别

3. **发布到 upypi**（1天）
   - `upypi install ai-gateway`

4. **推广**（持续）
   - 魔搭社区发文章
   - B站录教程
   - 找标杆用户
