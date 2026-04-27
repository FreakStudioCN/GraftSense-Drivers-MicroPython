from mpos import Activity

class HelloWorld(Activity):

    def onCreate(self):
        # 创建屏幕对象
        screen = lv.obj()
        screen.set_style_pad_all(20, lv.PART.MAIN)

        # 创建标签显示 Hello World
        label = lv.label(screen)
        label.set_text("Hello World!")
        label.center()
        label.set_style_text_font(lv.font_montserrat_20, lv.PART.MAIN)

        # 设置为内容视图
        self.setContentView(screen)
