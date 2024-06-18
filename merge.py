#!/usr/bin/env python3

from sys import argv
import glob
from typing import Tuple

factors = {
    'meV': 1e-3, # ? does this come up?
    'eV': 1.0,
    'keV': 1e3,
    'MeV': 1e6,
    'GeV': 1e9,
    'TeV': 1e12, # don't think our lil cyclotron is gonna produce these
}

class particle_data:
    def __init__(self, line: str = ''):
        chunks = line.split('\t')
        if len(chunks) == 1:
            return
        self.name = chunks[0]
        self.count = int(chunks[1])

        if len(chunks) < 6:
            return

        self.emean = float(
            list(filter(
                lambda s: s != '',
                chunks[2].split('=')[1].split(' ')
            ))[0]
        )

        self.emean_unit = list(filter(
            lambda s: s != '',
            chunks[2].split('=')[1].split(' ')
        ))[-1]

        self.mystery_bracket = chunks[3]

        self.stable = chunks[4]
        self.decay_time = chunks[5]


    def __str__(self) -> str:
        return '\t'.join([
            self.name,
            str(self.count),
            'Emean = ' + str(self.emean) + ' ' + str(self.emean_unit),
            self.mystery_bracket,
            self.stable,
            self.decay_time
        ])


    def __eq__(self, other) -> bool:
        return self.name == other.name \
            and self.count == other.count \
            and self.emean == other.emean \
            and self.emean_unit == other.emean_unit \
            and self.mystery_bracket == other.mystery_bracket \
            and self.stable == other.stable \
            and self.decay_time == other.decay_time


    def __add__(self, other):
        res = self
        res.count = self.count + other.count
        res.emean, res.emean_unit = unit_aware_mean(self.emean, self.emean_unit, other.emean, other.emean_unit)
        res.mystery_bracket = merge_eranges(self.mystery_bracket, other.mystery_bracket)
        res.stable = self.stable
        res.decay_time = self.decay_time
        return res


def unit_aware_min(values):
    smallest = (0.0, "eV")
    for num, unit in values:
        if num * factors[unit] < smallest[0] * factors[smallest[1]]:
            smallest = (num, unit)
    return smallest

def unit_aware_max(values):
    biggest = (0.0, "eV")
    for num, unit in values:
        if num * factors[unit] > biggest[0] * factors[biggest[1]]:
            biggest = (num, unit)
    return biggest


def merge_eranges(a: str, b: str) -> str:
    a.replace("(", "")
    a.replace(")", "")
    a_lower = float(a.split()[0])
    a_lower_unit = a.split()[1]
    a_upper = float(a.split()[-2])
    a_upper_unit = a.split()[-1]

    b.replace("(", "")
    b.replace(")", "")
    b_lower = float(b.split()[0])
    b_lower_unit = b.split()[1]
    b_upper = float(b.split()[-2])
    b_upper_unit = b.split()[-1]

    values = [(a_lower, a_lower_unit), (a_upper, a_upper_unit), (b_lower, b_lower_unit), (b_upper, b_upper_unit)]

    smallest, s_uint = unit_aware_min(values)
    biggest, b_unit = unit_aware_max(values)

    lower = str(smallest) + s_uint
    upper = str(biggest) + b_unit
    return "(" + lower + "-->" + upper + ")"


def unit_aware_mean(value_a: float, unit_a: str, value_b: float, unit_b: str) -> Tuple[float, str]:
    if unit_a == unit_b:
        return 0.5 * (value_a + value_b), unit_a

    value = 0.5 * (value_a * factors[unit_a] + value_b + factors[unit_b])
    for unit in factors.__reversed__():
        if value * (1.0 / factors[unit]) > 1.0:
            return value * (1.0 / factors[unit]), unit

    return value, 'eV'


def test_parse(file: str):
    with open(file) as handle:
        lines = handle.readlines()
        # filter out the files which only count particles
        if "PARTICLE COUNT" in "\n".join(lines):
            return {}# todo: handle this

        for line in lines[2:]:
            assert(particle_data(str(particle_data(line))) == particle_data(line))

    print("finished test parsing " + file)


def to_dict(file: str) -> dict:
    with open(file) as handle:
        lines = handle.readlines()
        # filter out the files which only count particles
        if "PARTICLE COUNT" in "\n".join(lines):
            return {}# todo: handle this

        res = {}
        for line in lines[2:]:
            pd = particle_data(line)
            res[pd.name] = pd
        return res


def main():
    argc = len(argv)
    if argc < 2:
        print("please provide a pattern to find the files to merge")
        return

    output_file = "out.txt"
    if "-o" in argv:
        output_file = argv[argv.index("-o") + 1]

    ignore_stable = False
    if "--ignore-stable" in argv:
        ignore_stable = True

    files = argv
    if output_file in files:
        files.remove(output_file)
    if "-o" in files:
        files.remove("-o")
    if "--ignore-stable" in files:
        files.remove("--ignore_stable")

    master_dict = {}

    for file in files:
        #test_parse(file)
        master_dict = {**master_dict, **to_dict(file)}

    with open(output_file, 'w') as out_handle:
        out_handle.writelines([str(master_dict[pd]) for pd in master_dict])
    #print(master_dict)


if __name__ == "__main__":
    main()
