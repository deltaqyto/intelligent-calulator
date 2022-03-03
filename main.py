import math
import string


class BaseItem:
    def __init__(self, parents=None, args=None, target=None):
        self.type = "base"
        self.parameters = []
        self.private_params = []
        self.aliases = {}
        self.combine_pairs = {}
        self.others = []

        self.solutions = {}

        self.matched_params = {}
        self.unmatched_params = set()
        self.unknown_params = {}

        self.target = target

        if parents is not None:
            temp_params = [parent.digest() for parent in parents]
            for digest in temp_params:
                for key, value in digest.items():
                    if key not in self.matched_params:
                        self.matched_params[key] = []
                    self.matched_params[key].append(value)
        self.persistant_args = args

    def finish_init(self):
        if self.persistant_args is not None:
            for key, value in self.persistant_args.items():
                self.sort_token(key, value)

    def sort_token(self, token, value):
        token = self.de_alias(token)
        if token in self.parameters + self.private_params:
            self.matched_params[token] = value
        else:
            self.unknown_params[token] = value

    def insert_token(self, token, value):
        token = self.de_alias(token)
        if token in self.parameters + self.private_params:
            if value is not self.matched_params[token]:
                self.matched_params[token] += [value]
        else:
            if value is not self.unknown_params[token]:
                self.unknown_params[token] += [value]

    def de_alias(self, parameter):
        return self.aliases.get(parameter, parameter)

    def set_target(self, target):
        self.target = target

    def solve_for(self, caller_message="", silent=False):
        caller_message = caller_message + ": " if caller_message else caller_message
        if self.target is None:
            if not silent:
                print("No target was specified.")
            return None
        target = self.de_alias(self.target)
        if target in self.matched_params:
            return self.matched_params[target]
        if target not in self.parameters:
            if not silent:
                print(f"{caller_message}Target {target} was not recognised by {self.type}")
            return None
        if target not in self.solutions:
            if not silent:
                print(f"{caller_message}Target {target} is not a solvable parameter for {self.type}")
            return None

        solver = self.solutions[target]
        known_params = set(self.matched_params.keys())

        for name, sol in solver.items():
            if not name.issubset(known_params):
                continue
            data_block = {}
            for token in name:
                data_block[token] = (self.matched_params[token])
            try:
                return sol(data_block)
            except ValueError:
                print("Solving caused a value error")
            except TypeError:
                print("Solving caused a type error")
        if not silent:
            print(f"{caller_message}{self.type} was unable to find a solution for {self.target} with knowns: {known_params}")
        return None

    def can_attempt_solve(self):
        return self.target is not None

    def pairify(self, in_str):
        state = "idle"
        letters = [l for l in string.ascii_lowercase] + ["_"]
        nums = [str(i) for i in range(10)] + [".", "-"]
        key_val_pairs = {}
        temp_pair = [None, None]

        current = ""
        for char in in_str:
            char = char.lower()

            if char in nums and state == "idle":
                state = "value"
                current = char
            elif char in letters and state == "idle":
                state = "key"
                current = char

            elif char in letters and state == "value":
                state = "key"
                temp_pair[1] = float(current)
                current = char
            elif char in nums and state == "key":
                state = "value"
                temp_pair[0] = current
                current = char

            elif char == " ":
                if state == "value":
                    key_val_pairs[temp_pair[0]] = current
                elif state == "key":
                    key_val_pairs[current] = temp_pair[1]
                temp_pair = [None, None]
                state = "idle"
                current = ""

            elif char in letters and state == "key":
                current += char
            elif char in nums and state == "value":
                current += char
        if state == "key":
            key_val_pairs[current] = temp_pair[1]
        elif state == "value":
            key_val_pairs[temp_pair[0]] = current
        return key_val_pairs

    def process_tokens(self, tokens):
        token_pairs = self.pairify(" ".join(tokens))
        for token, value in token_pairs.items():
            if value is None:
                self.target = token
                continue
            self.sort_token(token, value)

    def digest(self, silent=False):
        out_digest = {}
        current_target = self.target
        for param in self.parameters + self.private_params:
            self.set_target(param)
            out_digest[param] = self.solve_for(caller_message="Digest", silent=silent)
        self.target = current_target
        return out_digest

    def __repr__(self):
        return f"{self.type}({f'target={self.target}, ' if self.target is not None else ''}args={self.digest(silent=True)})"

    def combine(self, member):
        if member.type not in self.combine_pairs:
            print(f"Member {member.type} is not compatible with {self.type}")
            return None
        out_object = self.combine_pairs[member.type](parents=(self, member))
        return out_object

    def custom_combine_intro(self, parents):
        if not parents:
            print(f"No parents were provided to {self.type}")

    def default_combine(self, parents=()):
        self.custom_combine_intro(parents)



class MultiVector(BaseItem):
    def __init__(self, parents=None, args=None, target=None):
        super().__init__(parents=parents, args=args, target=target)
        self.type = "MultiVector"
        self.parameters = ["res"]
        self.private_params = ["x", "y", "mag", "dr"]
        self.aliases = {"resultant": "res"}
        self.combine_pairs = {"Vector": self.vector_combine, "MultiVector": self.multivector_combine}

        self.solutions = {
            "res": {frozenset(["x", "y"]): lambda in_args: self.debug(in_args)
                    }}

        self.finish_init()

    def multivector_combine(self, parents=()):
        self.custom_combine_intro(parents)
        for parent in parents:
            digest = parent.digest()
            for param in self.private_params:
                self.insert_token(param, digest[param])

    def vector_combine(self, parents=()):
        self.custom_combine_intro(parents)
        for parent in parents:
            digest = parent.digest()
            for param in self.private_params:
                self.insert_token(param, digest[param])

    def debug(self, in_args):
        return Vector(
            args={"x": sum(in_args["x"]),
                  "y": sum(in_args["y"])})


class Vector(BaseItem):
    def __init__(self, parents=None, args=None, target=None):
        super().__init__(parents=parents, args=args, target=target)
        self.type = "Vector"
        self.parameters = ["x", "y", "mag", "dr"]
        self.aliases = {"rise": "y", "run": "x", "h": "mag", "hyp": "mag", "deg": "dr", "d": "dr"}

        self.combine_pairs = {"Vector": MultiVector}

        self.solutions = {
            "x": {frozenset(["y", "mag"]): lambda in_args: (in_args["mag"] ** 2 - in_args["y"] ** 2) ** 0.5,
                  frozenset(["y", "dr"]): lambda in_args: in_args["y"] / math.tan(math.radians(in_args["dr"])),
                  frozenset(["mag", "dr"]): lambda in_args: in_args["mag"] * math.cos(math.radians(in_args["dr"]))},
            "y": {frozenset(["x", "mag"]): lambda in_args: (in_args["mag"] ** 2 - in_args["x"] ** 2) ** 0.5,
                  frozenset(["x", "dr"]): lambda in_args: in_args["x"] / math.tan(math.radians(in_args["dr"])),
                  frozenset(["mag", "dr"]): lambda in_args: in_args["mag"] * math.sin(math.radians(in_args["dr"]))},
            "mag": {frozenset(["x", "y"]): lambda in_args: (in_args["x"] ** 2 + in_args["y"] ** 2) ** 0.5,
                    frozenset(["x", "dr"]): lambda in_args: in_args["x"] / math.cos(math.radians(in_args["dr"])),
                    frozenset(["y", "dr"]): lambda in_args: in_args["y"] / math.sin(math.radians(in_args["dr"]))},
            "dr": {frozenset(["x", "y"]): lambda in_args: math.degrees(math.atan2(in_args["y"], in_args["x"])),
                   frozenset(["x", "mag"]): lambda in_args: math.degrees(math.acos(in_args["x"] / in_args["mag"])),
                   frozenset(["y", "mag"]): lambda in_args: math.degrees(math.asin(in_args["y"] / in_args["mag"]))}}

        self.finish_init()


class SingleAcc(BaseItem):
    def __init__(self, parents=None, args=None, target=None):
        super().__init__(parents=parents, args=args, target=target)
        self.type = "SingleAcc"
        self.parameters = ["u", "v", "a", "t", "s"]
        self.aliases = {"start": "u", "finish": "v", "acc": "a", "time": "t", "dist": "s"}

        self.combine_pairs = {}

        self.solutions = {
            "v": {frozenset(["u", "a", "t"]): lambda in_args: in_args["u"] + in_args["a"] * in_args["t"],
                  frozenset(["u", "a", "s"]): lambda in_args: (in_args["u"] ** 2 + 2 * in_args["a"] * in_args["s"])**0.5,
                  frozenset(["u", "t", "s"]): lambda in_args: 2 * in_args["s"]/in_args["t"] - in_args["u"],
                  frozenset(["a", "t", "s"]): lambda in_args: (2 * in_args["s"] + in_args["t"] ** 2 * in_args["a"])/(2 * in_args["t"])},

            "u": {frozenset(["v", "a", "t"]): lambda in_args: in_args["v"] - in_args["a"] * in_args["t"],
                  frozenset(["v", "a", "s"]): lambda in_args: (in_args["v"] ** 2 - 2 * in_args["a"] * in_args["s"])**0.5,
                  frozenset(["v", "t", "s"]): lambda in_args: 2 * in_args["s"]/in_args["t"] - in_args["v"],
                  frozenset(["a", "t", "s"]): lambda in_args: (2 * in_args["s"] - in_args["t"] ** 2 * in_args["a"])/(2 * in_args["t"])},

            "a": {frozenset(["v", "u", "t"]): lambda in_args: (in_args["v"] - in_args["u"]) / in_args["t"],
                  frozenset(["v", "u", "s"]): lambda in_args: (in_args["v"] ** 2 - in_args["u"]**2) / (2 * in_args["s"]),
                  frozenset(["v", "t", "s"]): lambda in_args: (-2 * in_args["s"] + 2 * in_args["v"] * in_args["t"]) / in_args["t"]**2,
                  frozenset(["u", "t", "s"]): lambda in_args: (2 * in_args["s"] - 2 * in_args["u"] * in_args["t"]) / in_args["t"]**2},

            "t": {frozenset(["v", "u", "a"]): lambda in_args: (in_args["v"] - in_args["u"]) / in_args["a"],
                  frozenset(["v", "u", "s"]): lambda in_args: 2 * in_args["s"] / (in_args["u"] + in_args["v"]),
                  frozenset(["v", "a", "s"]): lambda in_args: ((in_args["v"]+(in_args["v"]**2 + 2 * in_args["s"] * in_args["a"])**0.5)/in_args["a"],
                                                                  -(-in_args["v"]+(in_args["v"]**2 + 2 * in_args["s"] * in_args["a"])**0.5)/in_args["a"]),
                  frozenset(["u", "a", "s"]): lambda in_args: ((-in_args["u"]+(in_args["u"]**2 + 2 * in_args["s"] * in_args["a"])**0.5)/in_args["a"],
                                                                  -(in_args["u"]+(in_args["u"]**2 + 2 * in_args["s"] * in_args["a"])**0.5)/in_args["a"])},

            "s": {frozenset(["v", "u", "t"]): lambda in_args: (in_args["v"] + in_args["u"]) / (2 * in_args["t"]),
                  frozenset(["v", "u", "a"]): lambda in_args: (in_args["v"] ** 2 - in_args["u"]**2) / (2 * in_args["a"]),
                  frozenset(["v", "t", "a"]): lambda in_args: in_args["v"] * in_args["t"] - 0.5 * in_args["a"] * in_args["t"]**2,
                  frozenset(["u", "t", "a"]): lambda in_args: in_args["u"] * in_args["t"] + 0.5 * in_args["a"] * in_args["t"]**2}
        }

        self.finish_init()


"""
User log start
---------------------------------------------------------------
new                 -> Specify creation
vector              -> Create vector
3x                  -> Provide attrs
get hyp             -> Err: not enough vars. Provide y or dir
-4y                 -> More attrs
hyp                 -> 5
save v1             -> save vector as v1

new vector 3x 4y dr-> Create new vector inline and ask for dir: 37 deg
combine v1          -> combine v1 into current vector
resultant           -> 6x
save r1             -> store combined vector
open v1             -> change context to v1
dir                 -> -37 deg
del r1              -> delete r1
quit                -> Session complete

"""


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


def main():
    solve_table = {"vector": Vector, "single_acc": SingleAcc, "single": SingleAcc}

    saved_vals = {}
    context = None
    state = "idle"

    finished = False
    input_prompt = None

    faker = [l.strip() for l in """
            new                
            vector             
            3x                 
            get hyp            
            -4y                
            hyp                
            save v1            
            
            new vector 3x 4y dr
            combine v1         
            resultant yield mag 
            verify        
            save r1            
            open v1            
            dr 
            open r1
            res yield run            
            del v1
            open v1             
            
            new vector 1x 1y
            save v1
            new vector -1x 1y
            save v2
            new vector 1x -1y
            save v3
            new vector -1x -1y
            combine v3 v2
            verify
            res yield mag
            res
            
            quit          
            
            """.split("\n") if l.strip()]
    do_faker = True
    while not finished:
        if not do_faker:
            prompt = input(input_prompt if input_prompt is not None else ">: ")
        else:
            prompt = faker.pop(0)
            print(">: ", prompt)
        input_prompt = None
        match prompt.split():
            case ["quit" | "exit"]:
                finished = True
                print("Bye")
                continue
            case ["new", *args]:
                state = "creating"
                if not args:
                    input_prompt = "Specify type of object: "
                    continue
                context = solve_table[args.pop(0)]()
                if args:
                    context.process_tokens(args)
                if context.can_attempt_solve():
                    solution = context.solve_for()
                    if solution is not None:
                        print(solution)
                state = "in context"
                print(f"Created {context}")
                continue
            case ["verify"]:
                if context is None:
                    print("No object is currently in context")
                else:
                    print(f"Context is {context}")
            case ["open", name]:
                if name not in saved_vals:
                    print(f"{name} was not found")
                    continue
                context = saved_vals.get(name)
                print(f"Context has been set to {name}")
                continue
            case ["eval"]:
                print(eval(input("Eval >: ")))  # todo very unsafe
            case ["eval", *continued]:
                print(eval(" ".join(continued)))  # todo very unsafe
            case [target, "yield", secondary]:
                if context is None:
                    print("No context found")
                    continue
                context.set_target(target)
                solution = context.solve_for()
                if solution is None:
                    continue
                if not issubclass(type(solution), BaseItem):
                    print(f"{solution} is not further solvable")
                    continue
                solution.set_target(secondary)
                solution = solution.solve_for()
                if solution is None:
                    continue
                print(solution)
            case ["get", target]:
                if context is None:
                    print("No context found")
                    continue
                context.set_target(target)
                solution = context.solve_for()
                if solution is not None:
                    print(solution)
                continue
            case ["combine", *names]:
                for name in names:
                    if name not in saved_vals:
                        print(f"{name} was not found")
                        continue
                    temp_context = context.combine(saved_vals[name])
                    context = temp_context if temp_context is not None else context
            case ["save", name]:
                if state == "in context":
                    saved_vals[name] = context
                    print(f"Saved as {name}")
                else:
                    print("No current object in context")
                continue
            case ["del" | "delete", name]:
                if name not in saved_vals:
                    print(f"{name} was not found")
                    continue
                saved_vals.pop(name)
            case in_val:
                if state == "in context":
                    context.process_tokens(in_val)
                    if context.can_attempt_solve():
                        solution = context.solve_for()
                        if solution is not None:
                            print(solution)
                elif state == "creating":
                    if in_val and in_val[0] in solve_table:
                        context = solve_table[in_val.pop(0)]()
                        if in_val:
                            context.process_tokens(in_val)
                        if context.can_attempt_solve():
                            solution = context.solve_for()
                            if solution is not None:
                                print(solution)
                        state = "in context"
                else:
                    print("Unknown command")
                continue


if __name__ == "__main__":
    main()
