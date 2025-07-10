from flask import Flask
from views import views

app = Flask(__name__)
app.register_blueprint(views, url_prefix="/")


if __name__ == "__main__":
    app.run(debug=True, port=9980)

    # serve(app, host="0.0.0.0", port=9980)

    # traverse_result = traverse_bom('RSS.0850.000.B')
    #
    # violation_list = []
    # max_lvl = 0
    # levels = []
    # for it, lvl, c_center, violation in traverse_result:
    #     indent = "    " * lvl
    #     cost_center_info = f" - {c_center}" if c_center else ""
    #     print(f"{indent}├── {lvl} - {it}{cost_center_info}{violation}")
    #     levels.append(lvl)
    #     if violation != "":
    #         violation_list.append(violation)
    #
    # if len(violation_list) != 0:
    #     print(f"\nWarning: {len(violation_list)} violations found!")
    # else:
    #     print("\nNo violations found!")
    #
    # if max(levels) >= 8:
    #     print(f"Warning: BOM structure is too deep! {max(levels)} levels!")
    # else:
    #     print(f"BOM structure is OK! {max(levels)} levels!")
    #
    # results = check_all_root_items()
    #
    # # Print cost center violations
    # print("\nCost Center Violations:")
    # for violation in results['cc_violations']:
    #     print(f"Violation: {violation['child_item']} ({violation['child_cc']}) "
    #           f"is child of {violation['parent_item']} ({violation['parent_cc']})")
    #
    # # Print deep BOMs
    # print("\nDeep BOMs (>7 levels):")
    # for deep_bom in results['deep_boms']:
    #     print(f"Deep BOM found in {deep_bom['root_item']}: "
    #           f"max depth = {deep_bom['max_depth']}")
    #
