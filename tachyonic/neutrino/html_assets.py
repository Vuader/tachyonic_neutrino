
js = []
css = []

def render(req):
    r = []

    for j in js:
        r.append("    <script src='%s/%s'></script>" % (req.get_app_static(), j))

    for c in css:
        r.append("    <link rel='stylesheet' href='%s/%s'/>" % (req.get_app_static(), c))

    return "\n".join(r)
