"""
AI 助手 App - 演示如何使用 AI Gateway SDK
这是一个简单的文本对话助手
"""
from mpos import Activity
import sys
sys.path.insert(0, '/apps/com.test.aiassistant/assets')
from ai_gateway_client import AIClient

class AIAssistant(Activity):

    def onCreate(self):
        # 创建屏幕
        self.screen = lv.obj()
        self.screen.set_style_pad_all(10, lv.PART.MAIN)

        # 标题
        title = lv.label(self.screen)
        title.set_text("AI Assistant")
        title.align(lv.ALIGN.TOP_MID, 0, 5)
        title.set_style_text_font(lv.font_montserrat_20, lv.PART.MAIN)

        # 显示区域（滚动容器）
        self.chat_area = lv.textarea(self.screen)
        self.chat_area.set_size(lv.pct(100), 150)
        self.chat_area.align(lv.ALIGN.TOP_MID, 0, 35)
        self.chat_area.set_text("Welcome! Ask me anything...\n")
        self.chat_area.add_flag(lv.obj.FLAG.SCROLL_ON_FOCUS)

        # 输入框
        self.input_box = lv.textarea(self.screen)
        self.input_box.set_size(lv.pct(100), 60)
        self.input_box.align(lv.ALIGN.BOTTOM_MID, 0, -50)
        self.input_box.set_placeholder_text("Type your question...")
        self.input_box.set_one_line(False)

        # 按钮容器
        btn_cont = lv.obj(self.screen)
        btn_cont.set_size(lv.pct(100), 40)
        btn_cont.align(lv.ALIGN.BOTTOM_MID, 0, 0)
        btn_cont.set_flex_flow(lv.FLEX_FLOW.ROW)
        btn_cont.set_flex_align(lv.FLEX_ALIGN.SPACE_EVENLY, lv.FLEX_ALIGN.CENTER, lv.FLEX_ALIGN.CENTER)
        btn_cont.set_style_pad_all(0, lv.PART.MAIN)

        # 发送按钮
        send_btn = lv.button(btn_cont)
        send_btn.set_size(100, 35)
        send_label = lv.label(send_btn)
        send_label.set_text("Send")
        send_label.center()
        send_btn.add_event_cb(self.on_send_click, lv.EVENT.CLICKED, None)

        # 清空按钮
        clear_btn = lv.button(btn_cont)
        clear_btn.set_size(100, 35)
        clear_label = lv.label(clear_btn)
        clear_label.set_text("Clear")
        clear_label.center()
        clear_btn.add_event_cb(self.on_clear_click, lv.EVENT.CLICKED, None)

        # 初始化 AI 客户端
        try:
            self.ai = AIClient(config_path="/apps/com.test.aiassistant/assets/config.json")
            self.append_message("System", "AI Client initialized")
        except Exception as e:
            self.append_message("Error", f"Failed to init AI: {str(e)}")
            self.ai = None

        self.setContentView(self.screen)

    def append_message(self, sender, message):
        """添加消息到聊天区域"""
        current = self.chat_area.get_text()
        new_text = f"{current}\n[{sender}] {message}\n"
        self.chat_area.set_text(new_text)
        # 滚动到底部
        self.chat_area.scroll_to_view(lv.ANIM.ON)

    def on_send_click(self, event):
        """发送按钮点击事件"""
        if not self.ai:
            self.append_message("Error", "AI Client not initialized")
            return

        # 获取用户输入
        user_input = self.input_box.get_text().strip()
        if not user_input:
            return

        # 显示用户消息
        self.append_message("You", user_input)
        self.input_box.set_text("")

        # 显示加载提示
        self.append_message("AI", "Thinking...")

        try:
            # 调用 AI（这里会阻塞，实际应该用异步）
            response = self.ai.generate(
                prompt=user_input,
                max_tokens=150,
                temperature=0.7
            )

            # 移除 "Thinking..." 并显示结果
            current = self.chat_area.get_text()
            current = current.replace("\n[AI] Thinking...\n", "")
            self.chat_area.set_text(current)

            if response.success:
                self.append_message("AI", response.text)
            else:
                self.append_message("Error", response.text)

        except Exception as e:
            current = self.chat_area.get_text()
            current = current.replace("\n[AI] Thinking...\n", "")
            self.chat_area.set_text(current)
            self.append_message("Error", f"Request failed: {str(e)}")

    def on_clear_click(self, event):
        """清空按钮点击事件"""
        self.chat_area.set_text("Chat cleared.\n")
        self.input_box.set_text("")
