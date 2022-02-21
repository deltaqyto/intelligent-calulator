import math


def process_inputs(inputs):
    key_vals = []
    for tokenq in inputs:
        tokenq = tokenq.split(" ")
        for token in tokenq:
            try:
                token = float(token)
                key_vals.append(["", token])
            except ValueError:
                key_vals[-1][0] += token
    return key_vals
            

def verify_input(prompt, condition=lambda v: True, error_value="", repeat_until=None, repeat_message=None):
    outvals = []
    while True:
        while True:
            inval = input(prompt)
            try:
                process = condition(inval)
                if process:
                    break
                else:
                    if error_value:
                        print(error_value)
            except ValueError:
                if error_value:
                    print(error_value)
        if inval == repeat_until:
            break
        outvals.append(inval)
        if repeat_until is None:
            break
        if repeat_message is not None:
            prompt = repeat_message

    return outvals


class BaseItem:
    def __init__(self):
        self.type = "base"
        self.parameters = []
        self.aliases = {}

        self.solutions = {}

        self.matched_params = {}
        self.unmatched_params = []
        self.unknown_params = {}

    def sort_tokens(self, token_pairs):
        self.unmatched_params = self.parameters  # Sort and de-alias the token pairs into matched, unmatched and unknown
        for token, value in token_pairs:
            token = self.de_alias(token)
            if token in self.parameters:
                self.unmatched_params.remove(token)
                self.matched_params[token] = value
            else:
                self.unknown_params[token] = value

    def de_alias(self, parameter):
        return self.aliases.get(parameter, parameter)

    def solve_for(self, target):
        target = self.de_alias(target)
        if target not in self.parameters:
            print(f"Target {target} was not recognised by {self.type}")
            return None
        if target not in self.solutions:
            print(f"Target {target} is not a solvable parameter for {self.type}")

        solver = self.solutions[target]
        known_params = set(self.matched_params.keys())

        for name, sol in solver.items():
            if not name.issubset(known_params):
                continue
            data_block = []
            for token in name:
                data_block.append(self.matched_params[token])
            return sol(*data_block)
        return None


class Vector(BaseItem):
    def __init__(self, token_pairs):
        super().__init__()
        self.type = "Vector"
        self.parameters = ["x", "y", "mag", "dr"]
        self.aliases = {"rise": "y", "run": "x", "h": "mag", "hyp": "mag", "deg": "dr", "d": "dr"}

        self.solutions = {
            "x": {frozenset(["y", "mag"]): lambda y, mag: (mag ** 2 - y ** 2) ** 0.5,  # Solution field for different target and input combinations
                  frozenset(["y", "dr"]): lambda y, dr: y / math.tan(math.radians(dr)),
                  frozenset(["mag", "dr"]): lambda mag, dr: mag * math.cos(math.radians(dr))},
            "y": {frozenset(["x", "mag"]): lambda x, mag: (mag ** 2 - x ** 2) ** 0.5,
                  frozenset(["x", "dr"]): lambda x, dr: x / math.tan(math.radians(dr)),
                  frozenset(["mag", "dr"]): lambda mag, dr: mag * math.sin(math.radians(dr))},

            "mag": {frozenset(["x", "y"]): lambda x, y: (x ** 2 + y ** 2) ** 0.5,
                    frozenset(["x", "dr"]): lambda x, dr: x / math.cos(math.radians(dr)),
                    frozenset(["y", "dr"]): lambda y, dr: y / math.sin(math.radians(dr))},
            "dr": {frozenset(["x", "y"]): lambda x, y: math.degrees(math.atan2(y, x)),
                   frozenset(["x", "mag"]): lambda x, mag: math.degrees(math.acos(x / mag)),
                   frozenset(["y", "mag"]): lambda y, mag: math.degrees(math.asin(y / mag))}}

        self.sort_tokens(token_pairs)


def main():
    solve_table = {"vector": Vector}
    base_table = {"vector": Vector([])}

    finished = False
    saved_vals = {}
    while not finished:
        command_phrase = verify_input("Please specify problem: ")[0]
        command_phrase = command_phrase.split()
        match command_phrase:
            case ["new", chosen_solver]:
                solver = solve_table[chosen_solver]
                solver_name = chosen_solver
                invals = verify_input("Please specify variables: ", repeat_until="", repeat_message="Specify additional vars: ")
                processed_inputs = process_inputs(invals)
                continue
            case ["remove" | "erase" | "r", var]:
                if var in saved_vals:
                    saved_vals.pop(var)
                else:
                    print(f"{var} is not part of the saved list")
                continue
            case ["clear"]:
                saved_vals.clear()
                continue
            case ["modify", saved_var, *mods]:           # todo modify
                if saved_var not in saved_vals:
                    print(f"{saved_var} is not part of the saved list")
                    continue
                saved_vals[saved_var].modify(mods)
                continue
            case ["combine", saved_var, *others]:
                if saved_var not in saved_vals:
                    print(f"{saved_var} is not part of the saved list")
                    continue
                saved_vals[saved_var].include(others)
                continue
            case ["solve", saved_var, target]:
                if saved_var not in saved_vals:
                    print(f"{saved_var} is not part of the saved list")
                    continue
                saved_vals[saved_var].solve_for(target)
                continue
            case _:
                print("Unrecognised input, please try something else")
                continue

        target = verify_input("Please specify target: ", lambda inval: base_table[solver_name].de_alias(inval) in base_table[solver_name].solutions.keys(),
                     f"Target was not recognised in {solver_name}")[0]

        solution_object = solver(processed_inputs)
        result = solution_object.solve_for(target)

        if result is not None:
            print(result)
        else:
            print("An error was encountered during operation")
        save_name = input("Save as? ")
        if save_name:
            saved_vals[save_name] = solution_object
        if input("Quit now? ").lower() in ["yes", "y", "x"]:
            finished = True
        last_solver = solver


if __name__ == "__main__":
    main()
