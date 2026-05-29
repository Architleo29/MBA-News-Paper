import os
from jinja2 import Template
from datetime import datetime

class NewsRenderer:
    def __init__(self, template_path=None, output_path=None):
        self.workspace_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        
        self.template_path = template_path or os.path.join(
            self.workspace_dir, ".jetro", "frames", "newsletter.html"
        )
        self.output_path = output_path or os.path.join(
            self.workspace_dir, ".jetro", "frames", "newsletter_rendered.html"
        )

    def render(self, articles):
        """Renders the newsletter HTML template with parsed articles."""
        if not os.path.exists(self.template_path):
            print(f"Error: Template not found at {self.template_path}")
            return False

        try:
            with open(self.template_path, "r", encoding="utf-8") as f:
                template_content = f.read()

            # Create a Jinja2 template
            template = Template(template_content)
            
            # Format time
            now = datetime.now()
            last_updated = now.strftime("%Y-%m-%d %H:%M:%S")

            # Render HTML
            rendered_html = template.render(
                articles=articles,
                last_updated=last_updated
            )

            # Ensure the output directory exists
            os.makedirs(os.path.dirname(self.output_path), exist_ok=True)

            # Save rendered HTML to file
            with open(self.output_path, "w", encoding="utf-8") as f:
                f.write(rendered_html)
            print(f"Rendered newsletter HTML to {self.output_path}")

            # Also save to root index.html for static hosting platforms (like Vercel)
            root_index_path = os.path.join(self.workspace_dir, "index.html")
            with open(root_index_path, "w", encoding="utf-8") as f:
                f.write(rendered_html)
            print(f"Rendered Vercel Home HTML to {root_index_path}")

            return True
        except Exception as e:
            print(f"Error rendering newsletter: {e}")
            return False
