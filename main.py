from Calc_objects import *


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


def main(override_input="", do_override_input=False):
    solve_table = {"vector": Vector, "single_acc": SingleAcc, "single": SingleAcc}

    saved_vals = {}
    context = None
    state = "idle"

    finished = False
    input_prompt = None

    faker = [line.strip() for line in override_input.split("\n") if line.strip()]
    while not finished:
        if not do_override_input:
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
    main("""
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
            
            """, True)
