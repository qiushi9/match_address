# -*- coding: utf-8 -*-
import jieba
import pymysql


class Match_Address():
    def __init__(self, product_description, superlative_code):
        self.product_description = product_description
        self.superlative_code = superlative_code
        self.jieba_description_list = ''
        self.shortest_code_list = []
        with open('code_name_text.txt', 'r') as F:
            self.all_code_name_list = F.read().split('\n')

    # 根据行政区域代码的规则。如省级为2位、市级为4位
    # 返回所有行政区域代码的上一级单位代码
    def get_add_father_code(self, add_name_code_str):
        all_add_father_code = ''
        add_name_code_list = add_name_code_str.split(',')
        # print(add_name_code_list)
        for add_code in add_name_code_list:
            if len(add_code) == 4:
                add_father_code = add_code[:2]
            elif len(add_code) == 6:
                add_father_code = add_code[:4]
            elif len(add_code) == 9:
                add_father_code = add_code[:6]
            elif len(add_code) == 12:
                add_father_code = add_code[:9]
            if add_code != add_name_code_list[-1]:
                all_add_father_code += (str(add_father_code) + ',')
            else:
                try:
                    all_add_father_code += str(add_father_code)
                except:
                    all_add_father_code = ''
        # print(all_add_father_code)
        return all_add_father_code

    # 根据行政区域代码的规则。如省级为2位、市级为4位
    # 返回所有行政区域的等级
    def generate_add_code_level(self, zone_id_str):
        zone_level_str = ''
        for code in zone_id_str.split(','):
            if len(code) == 1:
                code_level = 0
            elif len(code) == 2:
                code_level = 1
            elif len(code) == 4:
                code_level = 2
            elif len(code) == 6:
                code_level = 3
            elif len(code) == 9:
                code_level = 4
            elif len(code) == 12:
                code_level = 5
            if zone_id_str.split(',')[-1] != code:
                zone_level_str += str(code_level) + ','
            else:
                zone_level_str += str(code_level)
        return zone_level_str

    # 传入结巴分词结果 和 最高级的行政区域代码
    # 返回产品简介中所有的行政区域代码
    def match_all_name_code(self):
        addr_code_list = []
        addr_code_str = ''
        washed_add_code_list = []
        for code_name in self.all_code_name_list:
            # print(code_name)
            addr_code = code_name.split(',')[0].replace('code:', '')
            addr_name = code_name.split('name:')[-1].strip()
            if len(addr_name[:-1]) >= 1:
                if '自治' in addr_name:
                    autonomy_addr_name = addr_name[:2] + addr_name[-1]
                    if ((autonomy_addr_name[:2] in self.jieba_description_list) or (autonomy_addr_name in self.jieba_description_list)) and (
                            (addr_code[:2] == self.superlative_code) and (addr_code != self.superlative_code)):
                        if len(addr_code_list) < len(self.jieba_description_list):
                            addr_code_list.append(addr_code)
                else:
                    if ((addr_name[:2] in self.jieba_description_list) or (addr_name in self.jieba_description_list)) and (
                            (addr_code[:2] == self.superlative_code) and (addr_code != self.superlative_code)):
                        if len(addr_code_list) < len(self.jieba_description_list):
                            addr_code_list.append(addr_code)
        if len(addr_code_list[0]) == 2:
            del addr_code_list[0]
        # 获取所有地址的代码，并排序
        addr_code_list = sorted(addr_code_list, key=lambda i: len(i), reverse=False)
        # 找出长度最短的行政区域代码（即已经匹配出的最大的行政区域代码），并将没有在最短行政区域代码下的代码从列表中删除
        for i in addr_code_list:
            if len(i) == len(addr_code_list[0]):
                self.shortest_code_list.append(i)
        for i in addr_code_list:
            if i[:len(addr_code_list[0])] in self.shortest_code_list:
                washed_add_code_list.append(i)
        for addr_code in washed_add_code_list:
            if washed_add_code_list[-1] != addr_code:
                addr_code_str += addr_code + ','
            else:
                addr_code_str += addr_code
        return addr_code_str

    # 根据传入的所有行政区域的代码，匹配行政单位名称
    # 目的是行政单位名称与数据库一致，如 某某县已经升级为县级市，改名为某某市。以数据库为准。
    def get_sql_zone_name(self, zone_id_str):
        zone_id_list = zone_id_str.split(',')
        zone_name_str = ''
        for zone_id in zone_id_list:
            conn = pymysql.Connect(host='192.168.11.164', user='root', password='dg123456', db='video', port=3306, charset='utf8mb4', autocommit=True)  # 数据库连接
            cursor = conn.cursor()
            sql = """SELECT `name` FROM ad_zone WHERE id=%s;""" % zone_id
            try:
                cursor.execute(sql)
                result = cursor.fetchone()
                zone_name = result[0]
                if zone_id_list[-1] != zone_id:
                    zone_name_str += zone_name + ','
                else:
                    zone_name_str += zone_name
            except Exception as e:
                print(e, id)
            finally:
                cursor.close()
        return zone_name_str

    # 导入jieba_dict.txt,文档中包含所有的地名
    # 将特产描述文字传入，对描述进行精准分词（避免如太和县，却将和县、太和县都匹配出的bug），返回分词后的列表
    def jieba_fenci(self):
        jieba.load_userdict("jieba_dict.txt")
        self.jieba_description_list = jieba.lcut(self.product_description)
        for word in self.jieba_description_list:
            # 去除分词后列表中的符号 如：，。等
            if len(word.strip()) <= 1:
                del self.jieba_description_list[self.jieba_description_list.index(word)]
        return self.jieba_description_list

    def match_superlative_code(self):
        addr_code_list = []
        self.jieba_fenci()
        for code_name in self.all_code_name_list:
            addr_code = code_name.split(',')[0].replace('code:', '')
            addr_name = code_name.split('name:')[-1].strip()
            if (len(addr_name[:-1]) >= 1) and ((addr_name[:-1] in self.jieba_description_list) or (addr_name in self.jieba_description_list)):
                addr_code_list.append(addr_code)
        addr_code_list = sorted(addr_code_list, key=lambda i: len(i), reverse=False)
        self.superlative_code = addr_code_list[0][:2]

    def match_all(self):
        if self.superlative_code == '99999999':
            try:
                self.match_superlative_code()
            except:
                return {'zone_id': None, 'zone_name': None, 'zone_pid': None, 'zone_level': None}
        self.jieba_fenci()
        zone_id_str = self.match_all_name_code()
        zone_name_str = self.get_sql_zone_name(zone_id_str)
        zone_pid_str = self.get_add_father_code(zone_id_str)
        zone_level_str = self.generate_add_code_level(zone_id_str)
        return {'zone_id': zone_id_str, 'zone_name': zone_name_str, 'zone_pid': zone_pid_str, 'zone_level': zone_level_str}


if __name__ == '__main__':
    product_description = '宜宾市、泸州市、成都市、德阳市、遂宁市、绵阳市、自贡市、乐山市、南充市、广安市、达州市、巴中市、眉山市、资阳市、内江市、雅安市、广元市、凉山州等18个市（州）现辖行政区域'
    code = '51'
    match_address = Match_Address(product_description, code)
    match_address_dict = match_address.match_all()
    print('zone_id', match_address_dict['zone_id'])
    print('zone_name', match_address_dict['zone_name'])
    print('zone_pid', match_address_dict['zone_pid'])
    print('zone_level', match_address_dict['zone_level'])
