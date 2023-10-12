import z3


def example():
    a = z3.Int("a")
    b = z3.Int("b")
    x1 = z3.Int("x1")
    y1 = z3.Int("y1")
    e1 = x1 == a * 20
    e2 = y1 == b + 5
    e3 = y1 < x1
    solver = z3.Solver()
    solver.add(e1, e2, e3)
    result = solver.check()
    print(result)
    if (result == z3.sat):
        print(solver.model())

if __name__ == "__main__":
    example()
    solver = z3.Solver()

    result = solver.check()
    print(result)