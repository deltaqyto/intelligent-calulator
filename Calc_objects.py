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
            "res": {frozenset(["x", "y"]): lambda in_args: Vector(args={"x": sum(in_args["x"]), "y": sum(in_args["y"])})
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

