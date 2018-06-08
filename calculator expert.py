#!/usr/bin/env python
# _*_ coding:utf-8 _*_
import sys, csv

class Config:
    def __init__(self):
        config = {'s': 0}
        with open(args.c) as cfg:
            for lin in cfg.readlines():
                a, b = lin.split('=')
                a, b = a.strip(), float(b)
                if b > 1:
                    config[a] = b
                else:
                    config['s'] += b
        self.config = config

config = Config().config
class Args(object):  # input args arrangement
    def __init__(self):
        l = sys.argv[1:]
        self.c = l[l.index('-c')+1]
        self.d = l[l.index('-d')+1]
        self.o = l[l.index('-o')+1]

args = Args()




class UserData(object):  # process userdata
    def __init__(self):
        with open(args.d) as f:
            data = list(csv.reader(f))
        self.userdata = data

userdata = UserData().userdata

def cal(a, b):
    salary = int(b)
    shebao = salary * config['s']
    if salary < config['JiShuL']:
        shebao = config['JiShuL'] * config['s']
    if salary > config['JiShuH']:
        shebao = config['JiShuH'] * config['s']
    t = salary - shebao - 3500
    if t <= 0:
        tax = 0
    elif t <= 1500:
        tax = t * 0.03
    elif t <= 4500:
        tax = t * 0.1 - 105
    elif t <= 9000:
        tax = t * 0.2 - 555
    elif t <= 35000:
        tax = t * 0.25 - 1005
    elif t <= 55000:
        tax = t * 0.3 - 2755
    elif t <= 80000:
        tax = t * 0.35 - 5505
    elif t > 80000:
        tax = t * 0.45 -13505
    return [a, salary, format(shebao, '.2f'), 
        format(tax, '.2f'), format(salary-tax-shebao, '.2f')]

with open(args.o, 'w') as f:
    for a, b in userdata:
        csv.writer(f).writerow(cal(a, b))