#!/usr/bin/env python
# _*_ coding:utf-8 _*_
""" 计算社保和个人所得税

步骤：[(解析参数 (Args)-> 读取社保配置文件 (ShebaoConfig)-> 读取员工数据 (EmployeeData)] Process1
|
|
(queue1)->
|
|
计算 Process2
|
|
(queue2)->
|
|
Process3 输出

每一个步骤都实现为相应的类，通过类实例完成相应的工作。

执行方式:

    python3 calculator.py  -c test.cfg -d user.csv -o gongzi.csv

"""

import sys
from multiprocessing import Process, Queue


class ArgError(Exception):
    pass


class Args:
    """命令行参数解析类
    """
    def __init__(self, args):
        """
        Args:
            args (list): 参数列表
        """
        self.args = args

    def __parse_arg(self, arg):
        try:
            # 通过索引获取相应的参数的值
            value = self.args[self.args.index(arg) + 1]
        except (ValueError, IndexError):
            value = None
        return value

    def get_arg(self, arg):
        """获取指定参数的值
        """
        value = self.__parse_arg(arg)
        if value is None:
            raise ArgError('not found arg %s' % arg)
        return value


class SheBaoConfig:
    """社保配置文件类
    """

    def __init__(self, file):
        """
        Args:
            file (str): 社保配置文件
        """

        self.jishu_low, self.jishu_high, self.total_rate = self.__parse_config(file)

    def __parse_config(self, file):
        """解析社保参数配置文件
        """
        rate = 0
        jishu_low = 0
        jishu_high = 0

        with open(file) as f:
            for line in f:
                key, value = line.split('=')
                key = key.strip()
                try:
                    value = float(value.strip())
                except ValueError:
                    continue
                if key == 'JiShuL':
                    jishu_low = value
                elif key == 'JiShuH':
                    jishu_high = value
                else:
                    rate += value
        return jishu_low, jishu_high, rate


class EmployeeData(Process):
    """员工数据实现类
    """

    def __init__(self, file):
        """
        Args:
            file (str): 员工数据文件
        """
        self.data = self.__parse_file(file)

    def __parse_file(self, file):
        """解析员工数据文件
        """
        data = []
        for line in open(file):
            employee_id, gongzi = line.split(',')
            data = (employee_id, gongzi)
        yield data # 節省內存


    def run(self):  # 繼承自 Process
        for data in self.data:
            q_user.put(data)  # put()  繼承自 Process


class Calculator(Process):
    """社保，个人所得税计算实现类

    计算方法:

    应纳税所得额 = 工资金额 － 各项社会保险费 - 起征点(3500元)
    应纳税额 = 应纳税所得额 × 税率 － 速算扣除数
    最终工资 = 工资金额 - 各项社会保险费 - 应纳税额

    个人所得税税率因应纳税所得额不同而不同，具体可以查询税率速查表得知。
    """

    # 个人所得税起征点
    tax_start = 3500

    # 个人所得税税率速查表
    # 列表中每一项为元组，包含三项数据: (应纳税额, 税率，速算扣除数)
    tax_table = [
        (80000, 0.45, 13505),
        (55000, 0.35, 5505),
        (35000, 0.3, 2755),
        (9000, 0.25, 1005),
        (4500, 0.2, 555),
        (1500, 0.1, 105),
        (0, 0.03, 0),
    ]

    def __init__(self, config):
        """
        Args:
            config (object): SheBaoConfig 实例
        """
        self.config = config

    def calculate(self, data_item):
        """
        Args:
            data_item (tuple):  有员工号和工资组成的元组，如 (101, 5000)
        """

        employee_id, gongzi = data_item

        # 计算社保金额
        if gongzi < self.config.jishu_low:
            shebao = self.config.jishu_low * self.config.total_rate
        elif gongzi > self.config.jishu_high:
            shebao = self.config.jishu_high * self.config.total_rate
        else:
            shebao = gongzi * self.config.total_rate

        # 工资减去社保后的剩余金额
        left_gongzi = gongzi - shebao

        # 应纳税所得额 = 工资 - 社保 - 起征点
        tax_gongzi = left_gongzi - self.tax_start

        # 如果应纳税所得额 小于 0，那么就不用缴纳个人所得税
        if tax_gongzi < 0:
            tax = 0
        else:
            # 否则查询税率速查表计算应该缴纳的个人所得税税额
            # item 包含三项数据，(应纳税额, 税率，速算扣除数)
            for item in self.tax_table:
                if tax_gongzi > item[0]:
                    tax = tax_gongzi * item[1] - item[2]
                    break

        # 最终工资 = 工资 - 社保 - 个人所得税
        last_gongzi = left_gongzi - tax

        yield [str(employee_id), str(gongzi), '{:.2f}'.format(shebao), '{:.2f}'.format(tax), '{:.2f}'.format(
            last_gongzi)]


    def run(self):
        while True:
            try:
                data_item = q_user.get(timeout=1) #timeout 1 second 為 empty queue 時確認 Queue真為空
            except:
                break #Queue 為空退出 Process
        for data in self.calculate(data_item):
            q_result.put(data)

class Exporter(Process):
    """导出类实现
    """

    def __init__(self, file):
        """
        Args:
            file (str): 需要导出的目标文件
        """
        self.file = file

    def run(self):
        """
        Args:
            data (list): data 是一个由元组组成的列表，元组每一项应为字符串
        """
        content = ''
        with open(self.file, 'w') as f:
        # 拼接内容
            while True:
                try:
                    data = q_result.get(timeout=1)
                    for item in data:
                        line = ','.join(item) + '\n'
                        content += line
                except:
                    break
            # 写入文件
            f.write(content)





if __name__ == '__main__':
    q_user = Queue()
    q_result = Queue()
    # 除了使用 Executor 来执行代码，也可以直接使用下面的代码
    args = Args(sys.argv[1:])
    config = SheBaoConfig(args.get_arg('-c'))
    employee_data = EmployeeData(args.get_arg('-d'))
    exporter = Exporter(args.get_arg('-o'))
    calculator = Calculator(config)
    workers = [
        employee_data,
        calculator,
        exporter
    ]
    for worker in workers:
        worker.run()
    #results = []
    #for item in employee_data:
    #    result = calculator.calculate(item)
    #    results.append(result)
    #exporter.export(results)
