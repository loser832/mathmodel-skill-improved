import json
x, y = 0, 10
print(json.dumps({"x": x, "y": y, "objective": 3*x+2*y, "feasible": x >= 0 and y >= 0 and x+y >= 10}))
