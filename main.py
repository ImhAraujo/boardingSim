import numpy as np
from multiprocessing import Pool
import matplotlib.pyplot as plt
import pandas as pd
import plane as pl

"""
methods = ((pl.random_order, "random"),
           (pl.group_order, "groups"),
           (pl.WMA_order, "WMA"),
           (pl.reversePyramid_order, "reversePyramid"),
           (pl.Steffen_order, "Steffen"),
           )

for (method, m_name) in methods:
    print(m_name)
    with open(m_name, "a", encoding="utf-8") as f:
        for i in range(90):
            myPlane = pl.DefaultPlane()
            line = method(myPlane)
            result = pl.simulate(myPlane, line)
            # print(result)
            f.write(f"{i},{result}\n")

total = [pd.read_csv(m_name, index_col=0, header=None, names=[m_name]) 
 for (_, m_name) in methods]
print(pd.concat(total).describe())

def calculate(chance, line):
    myPlane = pl.DefaultPlane()
    line = pl.organize_test(line, int(np.round(180*chance/100)))
    result = pl.simulate(myPlane, line)
    print(result)
    return result

with open("testOrder_random", "w", encoding="utf-8") as f:
    for chance in range(101):
        f.write(f"{chance},")
        print(f"Chance: {chance}")
        with Pool() as p:
            result=p.map_async(calculate, [chance]*100)
            # print(result.get())
            f.write(",".join([str(x) for x in result.get()]))

"""


