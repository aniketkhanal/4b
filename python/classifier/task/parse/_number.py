import logging


def intervals(arg: str, max: int = None) -> list[int]:
    result = []
    for r in arg:
        rs = r.split("-")
        try:
            match len(rs):
                case 1:
                    result.append(int(rs[0]))
                case 2:
                    result.extend(range(int(rs[0]), int(rs[1]) + 1))
                case _:
                    raise ValueError
        except ValueError:
            logging.error(f"Invalid range {r}")
    return sorted(
        filter(lambda x: 0 <= x if max is None else lambda x: 0 <= x < max, set(result))
    )
