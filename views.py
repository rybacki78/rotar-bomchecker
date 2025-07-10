from backend import *
from flask import Blueprint, request, redirect, url_for, render_template

views = Blueprint(__name__, "views")

VERSION = 0.1


@views.route("/", methods=["GET", "POST"])
def index():
    boms = fetch_boms()
    items = fetch_it_data()
    roots = root_items(boms)
    problematic_boms = []
    for root, data in traverse_all_issues(roots, boms).items():
        problematic_boms.append(
            {
                "root_item": root,
                "max_level": data["issues"]["max_level"],
                "violations": data["issues"]["violation_count"],
            }
        )

    if request.method == "POST":
        if "refresh" in request.form:
            fetch_boms_from_server()
            fetch_it_data_from_server()
            return redirect(url_for("views.index"))
        selected = request.form["root"]
        traverse_result = traverse_bom(selected, boms)
        levels = []
        violation_list = []
        for _, lvl, _, violation in traverse_result:
            levels.append(lvl)
            if violation != "":
                violation_list.append(violation)
        violations_count = len(violation_list)
        max_levels = max(levels)
        return render_template(
            "result.html",
            selected=selected,
            traverse_result=traverse_result,
            violations_count=violations_count,
            max_levels=max_levels,
            version=VERSION,
        )
    return render_template(
        "index.html", roots=roots, problematic_boms=problematic_boms, version=VERSION
    )
