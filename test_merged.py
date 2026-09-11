from fastapi.templating import Jinja2Templates
try:
    templates = Jinja2Templates(directory="templates")
    template = templates.get_template("cand_merged.html")
    print("Template parsed successfully!")
except Exception as e:
    import traceback
    traceback.print_exc()
