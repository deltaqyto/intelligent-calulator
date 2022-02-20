import math


def process_inputs(solver, inputs, target, solutions):
    known_vals = []
    for token in inputs.split():
        try:
            token = float(token)
            known_vals.append([None, token])
        except ValueError:
            if token in solutions[solver][0]:
                known_vals[-1][0] = solutions[solver][0][token]
            else:
                print(f"Token {token} was not recognised in solver {solver}")
                known_vals.pop(-1)
    known_vals = dict(known_vals)
    print(known_vals)
    run_str = []
    run_vals = []
    for i in sorted(known_vals.keys()):
        run_str.append(i)
        run_vals.append(known_vals[i])
    if target not in solutions[solver][0]:
        print(f"Target unit {target} was not recognised")
        return None
    run_str = f"{solutions[solver][0][target]}:{','.join(run_str)}"
    print(run_str, run_vals)
    if run_str not in solutions[solver][1]:
        print(f"Your request was not matched by a solution in {solver}")
        return None
    return solutions[solver][1][run_str](*run_vals)


def verify_input(prompt, condition, error_value="", repeat_until=None):
    outvals = []
    while True:
        while True:
            inval = input(prompt)
            try:
                process = condition(inval)
                if process:
                    break
            except ValueError:
                if error_value:
                    print(error_value)
        if inval == repeat_until:
            break
        outvals.append(inval)
        if repeat_until is None:
            break

    return outvals


class BaseItem:
    def __init__(self):
        pass


def main():
    solve_table = {"": None,
                   "pythag": [{"c": "hyp", "a": "rise", "run": "run", "deg_f": "deg_f", "rise": "rise", "b": "run", "diag": "hyp", "hyp": "hyp",
                               "deg": "deg_f", "h": "hyp", "d": "deg_f"},
                              {"hyp:rise,run": lambda rise, run: (rise ** 2 + run ** 2) ** 0.5,
                               "rise:deg_f,hyp": lambda deg_f, hyp: math.sin(math.radians(deg_f)) * hyp,
                               "run:deg_f,hyp": lambda deg_f, hyp: math.cos(math.radians(deg_f)) * hyp,
                               "rise:hyp,run": lambda hyp, run: (hyp ** 2 - run ** 2) ** 0.5}],
                   "levers": [{"f1": "f1", "d1": "d1", "f2": "f2", "d2": "d2", "f": "f2", "a1": "a1", "a2": "a2"},
                              {"f2:d1,d2,f1": lambda d1, d2, f1: f1 * d1 / d2, "d2:d1,f1,f2": lambda d1, f1, f2: f1 * d1 / f2}]}
    finished = False
    last_solver = None
    while not finished:
        solver = verify_input("Please specify problem: ", lambda inval: inval in solve_table)[0]
        print(solver)
        if not solver:
            solver = last_solver
            print(f"Assuming solver to be {solver}")
        invals = input("Please enter known variables: ")
        solve_for = input("Please specify target: ")
        processed_inputs = process_inputs(solver, invals, solve_for, solve_table)
        if processed_inputs is not None:
            print(processed_inputs)
        if input("Quit now? ").lower() in ["yes", "y", "x"]:
            finished = True
        last_solver = solver


if __name__ == "__main__":
    main()
