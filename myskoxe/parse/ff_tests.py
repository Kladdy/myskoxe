import random

import fortranformat as ff

choices = [1.23, 4.56, 7.89]

random_choice = random.choices(choices, k=5)

random_choice_str = " ".join(map(str, random_choice))

# Parse the string, which has a variable number of elements
fmt_F = ff.FortranRecordReader("(1P,5F5.2)")
parsed_F = fmt_F.read(random_choice_str)

scientific_notation_str = " ".join(f"{x:.2e}" for x in random_choice)
fmt_E = ff.FortranRecordReader("(30P,5E9.2)")
parsed_E = fmt_E.read(scientific_notation_str)

print(random_choice)
print(parsed_F)

print(scientific_notation_str)
print(parsed_E)

# fmt_F_w = ff.FortranRecordWriter("(1P,5(F5.2))")
# fmt_E_w = ff.FortranRecordWriter("(1P,5(E5.2))")
# str_F = fmt_F_w.write(parsed_F)
# str_E = fmt_E_w.write(parsed_E)

# print(random_choice_str)
# print(str_F)
# print(str_E)
