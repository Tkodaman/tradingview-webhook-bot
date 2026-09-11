from fastapi.templating import Jinja2Templates
try:
    templates = Jinja2Templates(directory="templates")
    # try to get the template
    template = templates.get_template("dashboard.html")
    print("Template loaded successfully!")
except Exception as e:
    import traceback
    traceback.print_exc()
