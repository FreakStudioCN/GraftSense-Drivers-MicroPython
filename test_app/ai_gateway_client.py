"""
AI Gateway SDK - 核心客户端
让 MicroPython 设备成为 AI 网络节点
"""
import ujson
import urequests
import gc

class AIResponse:
    """统一的响应对象"""
    def __init__(self, text=None, data=None, provider=None, model=None):
        self.text = text
        self.data = data
        self.provider = provider
        self.model = model
        self.success = text is not None or data is not None

class AIClient:
    """AI Gateway 统一客户端"""

    def __init__(self, config_path="/data/ai_gateway/config.json"):
        self.config = self._load_config(config_path)
        self.default_provider = self.config.get('default_provider', 'modelscope')

    def _load_config(self, path):
        """加载配置文件"""
        try:
            with open(path, 'r') as f:
                return ujson.load(f)
        except:
            # 默认配置
            return {
                "default_provider": "modelscope",
                "providers": {
                    "modelscope": {
                        "api_key": "",
                        "endpoint": "https://api.modelscope.cn/v1"
                    }
                }
            }

    def generate(self, prompt, provider=None, max_tokens=200, temperature=0.7):
        """
        文本生成统一接口

        Args:
            prompt: 提示词
            provider: 指定后端 (modelscope/claude/openai)
            max_tokens: 最大生成长度
            temperature: 温度参数

        Returns:
            AIResponse 对象
        """
        provider = provider or self.default_provider
        provider_config = self.config['providers'].get(provider)

        if not provider_config:
            return AIResponse(text=f"Provider {provider} not configured")

        # 根据不同 provider 调用不同实现
        if provider == 'modelscope':
            return self._modelscope_generate(provider_config, prompt, max_tokens, temperature)
        elif provider == 'claude':
            return self._claude_generate(provider_config, prompt, max_tokens, temperature)
        elif provider == 'openai':
            return self._openai_generate(provider_config, prompt, max_tokens, temperature)
        else:
            return AIResponse(text=f"Unknown provider: {provider}")

    def _modelscope_generate(self, config, prompt, max_tokens, temperature):
        """魔搭社区文本生成"""
        url = f"{config['endpoint']}/chat/completions"
        headers = {
            "Authorization": f"Bearer {config['api_key']}",
            "Content-Type": "application/json"
        }
        data = {
            "model": config.get('model', 'qwen-turbo'),
            "messages": [{"role": "user", "content": prompt}],
            "max_tokens": max_tokens,
            "temperature": temperature
        }

        try:
            resp = urequests.post(url, headers=headers, json=data, timeout=30)
            result = ujson.loads(resp.text)
            resp.close()
            gc.collect()

            if 'choices' in result:
                return AIResponse(
                    text=result['choices'][0]['message']['content'],
                    provider='modelscope',
                    model=config.get('model', 'qwen-turbo')
                )
            else:
                return AIResponse(text=f"Error: {result.get('error', 'Unknown error')}")
        except Exception as e:
            return AIResponse(text=f"Request failed: {str(e)}")

    def _claude_generate(self, config, prompt, max_tokens, temperature):
        """Claude API 文本生成"""
        # 如果配置了代理，使用代理
        endpoint = config.get('proxy') or config['endpoint']
        url = f"{endpoint}/v1/messages"

        headers = {
            "x-api-key": config['api_key'],
            "anthropic-version": "2023-06-01",
            "content-type": "application/json"
        }
        data = {
            "model": config.get('model', 'claude-3-haiku-20240307'),
            "max_tokens": max_tokens,
            "temperature": temperature,
            "messages": [{"role": "user", "content": prompt}]
        }

        try:
            resp = urequests.post(url, headers=headers, json=data, timeout=30)
            result = ujson.loads(resp.text)
            resp.close()
            gc.collect()

            if 'content' in result:
                return AIResponse(
                    text=result['content'][0]['text'],
                    provider='claude',
                    model=config.get('model', 'claude-3-haiku')
                )
            else:
                return AIResponse(text=f"Error: {result.get('error', {}).get('message', 'Unknown error')}")
        except Exception as e:
            return AIResponse(text=f"Request failed: {str(e)}")

    def _openai_generate(self, config, prompt, max_tokens, temperature):
        """OpenAI API 文本生成"""
        url = f"{config['endpoint']}/chat/completions"
        headers = {
            "Authorization": f"Bearer {config['api_key']}",
            "Content-Type": "application/json"
        }
        data = {
            "model": config.get('model', 'gpt-3.5-turbo'),
            "messages": [{"role": "user", "content": prompt}],
            "max_tokens": max_tokens,
            "temperature": temperature
        }

        try:
            resp = urequests.post(url, headers=headers, json=data, timeout=30)
            result = ujson.loads(resp.text)
            resp.close()
            gc.collect()

            if 'choices' in result:
                return AIResponse(
                    text=result['choices'][0]['message']['content'],
                    provider='openai',
                    model=config.get('model', 'gpt-3.5-turbo')
                )
            else:
                return AIResponse(text=f"Error: {result.get('error', {}).get('message', 'Unknown error')}")
        except Exception as e:
            return AIResponse(text=f"Request failed: {str(e)}")

    def classify_image(self, image_bytes, labels=None, provider=None):
        """
        图像分类接口

        Args:
            image_bytes: 图像字节数据
            labels: 可选的标签列表
            provider: 指定后端

        Returns:
            AIResponse 对象，data 包含分类结果
        """
        provider = provider or self.default_provider
        provider_config = self.config['providers'].get(provider)

        if not provider_config:
            return AIResponse(text=f"Provider {provider} not configured")

        # TODO: 实现图像分类
        return AIResponse(text="Image classification not implemented yet")

    def transcribe(self, audio_bytes, provider=None):
        """
        语音识别接口

        Args:
            audio_bytes: 音频字节数据
            provider: 指定后端

        Returns:
            AIResponse 对象，text 包含识别文本
        """
        provider = provider or self.default_provider
        provider_config = self.config['providers'].get(provider)

        if not provider_config:
            return AIResponse(text=f"Provider {provider} not configured")

        # TODO: 实现语音识别
        return AIResponse(text="Speech recognition not implemented yet")

    def ask(self, question, context=None, provider=None):
        """
        简化的问答接口

        Args:
            question: 问题
            context: 可选的上下文信息
            provider: 指定后端

        Returns:
            AIResponse 对象
        """
        if context:
            prompt = f"Context: {context}\n\nQuestion: {question}"
        else:
            prompt = question

        return self.generate(prompt, provider=provider, max_tokens=300)
