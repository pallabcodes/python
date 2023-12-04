def add_all(*args):
    print(f"ARGS: {args}")
    return sum(args)


print(add_all(1, 2))


def pretty_print(**kwargs):
    print(f" kwargs {kwargs} ->> dictToList => {kwargs.items()}")

    for k, v in kwargs.items():
        print(f"For {k} we have {v}.")


pretty_print(**{"username": "jose123", "access_level": "admin"})


# *args will work prmitive and **kwargs will work for non-primitive ( whereas for both passsing argument is optional )
