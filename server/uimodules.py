from tornado.web import TemplateModule

class Map(TemplateModule):
    def render(self):
        return self.render_string("module-entry.html")