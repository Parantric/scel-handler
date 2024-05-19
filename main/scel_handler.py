# -*- coding:utf-8 -*-

'''
1️⃣ RIME 词库文件头部信息模板
    ❗注意：RIME 词库文件的头部信息作为词库文件的一种描述性元信息和下边的词条要空一行

    # 自定义词典
    # encoding: utf-8
    # 字条格式：词汇<tab>ci<空格>hui<tab>权重
    # 权重数字越大，表示优先级越高，排名越靠前。
    # 模板
    ---
    name: daike
    version: "2024-04-15"
    sort: by_weight
    ...
    <空一行>
'''
import datetime
import io
import os
import struct

from typing import List, Tuple

RIME_DICT_EXT = r'.dict.yaml'


class BufferedIOWrapper:
    def __init__(self, bufferedReader: io.BufferedIOBase):
        self._buffer = bufferedReader

    def read_uint16(self) -> int:
        '''
        读取一个字符，并返回表示这个字符的 uint16 整数.
        :return:
        '''
        buffer = self._buffer.read(2)
        if buffer:
            return struct.unpack('<H', buffer)[0]
        else:
            return 0

    def read_uint32(self) -> int:
        # return struct.unpack('<H', self._buffer.read(2))[0]
        bytes = self._buffer.read(4)
        str = struct.unpack('<I', bytes)[0]
        return str

    def read_str(self) -> str:
        '''
        将二进制字节转成 16 位无符号整数，然后再转换成字符.
        搜狗自定义的二进制文件是使用的小端模式存储，所有'<H'.用两个字节表示一个字符，故每次读取 2 个字节.
        :return:
        ''.join(
            chr(struct.unpack('<H', self._buffer.read(2))[0])
            for i in range(int(self.read_uint16() / 2)))
        int(self.read_uint16() / 2))：读取 2 位，此 2 位 无符号 16 进制整数表示的是当前这个拼音表索引上的拼音的占多少个字节，
        除以 2 表示有几个拼音（字节=>字符），因为每次读取都是 read(2),所以这里必须除以 2 作为循环读取的界限。
        '''

        return ''.join(
            chr(struct.unpack('<H', self._buffer.read(2))[0])
            for i in range(int(self.read_uint16() / 2)))

    def seek(self, offset):
        self._buffer.seek(offset)

    def tell(self) -> int:
        return self._buffer.tell()

    def skip(self, offset):
        '''
        将光标从当前位置（seek 的 whence 参数为 1 表示以当前位置作为参考）移动 offset 个位置.
        :param offset:
        :return:
        '''
        self._buffer.seek(offset, 1)

    def skip_uint16(self):
        '''
        将光标从当前位置，移动 2 位.
        当前项目应用场景：
            ①：解析拼音表的时候，拼音表的每个元素的前两位表示的是索引，没实际意义，故：可以跳过.
        :return:
        '''
        self.skip(2)


class Scel:
    PINYIN_START = 0x1544
    CHAR_START = 0x2628

    def __init__(self, bufferedReader: io.BufferedIOBase):
        self._buffer = BufferedIOWrapper(bufferedReader)
        self._table = []

    def _read_pinyin_palette(self) -> List[str]:
        '''
        读取拼音表
        :return:
        '''
        pinyin_palette = []
        # 固定模式：拼音表从 0x1544 位置开始.
        self._buffer.seek(self.PINYIN_START)
        # 拼音表之后因为是词汇表，所以，到了词汇表的范围，就代表是拼音表的末尾了.
        while self._buffer.tell() < self.CHAR_START:
            # 跳过拼音表中每个元素表示的索引.
            self._buffer.skip_uint16()
            pinyin_palette.append(self._buffer.read_str())

        return pinyin_palette

    def _read_pinyin(self, pinyin_palette: List[str]) -> str:
        try:
            return ' '.join(pinyin_palette[self._buffer.read_uint16()]
                            for i in range(int(self._buffer.read_uint16() /
                                               2)))
        except IndexError:
            return ''

    def _read_word_table(self,
                         pinyin_palette: List[str]) -> List[Tuple[str, str, int]]:
        '''
        读取词汇表
        :param pinyin_palette:
        :return:
        '''
        table = []
        self._buffer.seek(self.CHAR_START)
        word_item_count = 0
        # word_count：词组数量，使用海象表达式，在这里仅作非零判断.
        while word_count := self._buffer.read_uint16():
            # 继续读取就是读取词组的数量了.
            pinyin = self._read_pinyin(pinyin_palette)
            if not pinyin:
                break
            for i in range(word_count):
                phrase = self._buffer.read_str()
                # 这个条件是为了排除‘黑名单’，测试发现，很多 scel 文件末尾含有「DELTAB」表示‘黑名单’.如果不排除，程序会解析出错.
                if phrase == '':
                    break
                skip_length = self._buffer.read_uint16()
                order = self._buffer.read_uint32()
                self._buffer.skip(skip_length - 4)
                table.append((phrase, pinyin, order))
                word_item_count += 1
        # 这个 sort 可以不用执行，默认按照拼音 a=>z 顺序排列
        # table.sort(key=lambda x: x[2])
        # print('词条的数目：=>', word_item_count, '条！')
        return table

    def get_table(self):
        if not self._table:
            pinyin_palette = self._read_pinyin_palette()
            self._table = self._read_word_table(pinyin_palette)

        return list(map(lambda x: x[:2], self._table))


class RimeWriter:

    def __init__(self, table: List[Tuple[str, str]], name: str, version: str):
        self._table = table
        self._name = name
        self._version = version

    def write(self, file_path, result):
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(
                f'''# \\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\n# 程序自动生成 Start ···\n# 来源【搜狗词库】\n# encoding: utf-8\n# 字条格式：词汇<tab>ci<空格>hui<tab>权重\n# 权重数字越大，表示优先级越高，排名越靠前。\n# 模板\n#\n# 词库详情如下：\n# 词库名称： {result['dict_name']}\n# 词库类型： {result['dict_type']}\n# 词库信息： {result['dict_msg']}\n# 词库示例： {result['dict_exp']}\n# 词条数目： {len(self._table)} 条.\n# 程序自动生成 End ···\n# \\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\n# P.S. \n# ① 以上生成内容请不要修改，如有需要，请直接在以下追加.\n# ② 如需添加词组到该文件，不要打乱顺序，请直接在最后词条后面追加.\n# \n---\nname: {self._name}\nversion: {self._version}\nsort: by_weight\nuse_preset_vocabulary: false\n...\n\n''')
            for i in self._table:
                f.write('\t'.join(i) + '\t1\n')


def read_scel_msg(scel_path: str):
    dict_scel_detail = {}
    msg_reader = lambda data: ''.join(
        map(lambda x: '\n' if x == '\r' else x,
            map(lambda x: ' ' if x == '\u3000' else x,
                filter(lambda x: x != '\0',
                       (chr(struct.unpack('H', data[i: i + 2])[0]) for i in range(0, len(data), 2))
                       ))))

    with open(scel_path, 'rb') as f:
        f.seek(0x130)
        dict_scel_detail['dict_name'] = msg_reader(f.read(0x338 - 0x130))
        dict_scel_detail['dict_type'] = msg_reader(f.read(0x540 - 0x338))
        dict_scel_detail['dict_msg'] = msg_reader(f.read(0xD40 - 0x540))
        dict_exp_temp = msg_reader(f.read(0x1540 - 0xD40))
        dict_scel_detail['dict_exp'] = dict_exp_temp.replace('\n', '\n#') + '\n# ... ...'
    return dict_scel_detail


def scel_to_rime(scel_path: str, rime_dir: str, rime_name: str,
                 rime_version: str, dict_scel_detail: {}):
    '''
    搜狗细胞词库「scel」转换 RIME 词库风格程序调用方法

    :param scel_path:细胞词库文件路径
    :param rime_dir:待生成的 RIME 词库文件的存放目录（如果目录不存在则自动创建）
    :param rime_name:RIME 词库文件中头部名称，推荐：
                    「xxx.dict.yaml」取 xxx 作为该参数的实参﹝推荐但是不强求﹞
    :param rime_version:版本号，一般采用当前日期，例如：2024-05-16
    :param dict_scel_detail:原搜狗细胞词库解析出来的词库详情信息.
    :return:
    '''
    # 判断输出文件目录是否存在，不存在则自动创建.
    if not os.path.exists(rime_dir):
        os.makedirs(rime_dir)
        print(r'[ ' + rime_dir + ' ] 不存在，已自动创建！')
    # 生成的文件名称
    rime_dict_yaml = os.path.join(rime_dir, rime_name + RIME_DICT_EXT)

    scel_file = open(scel_path, 'rb')  # 'rb':表示以二进制的方式读取文件，默认当然是读取一个字节.
    scel = Scel(scel_file)
    rime_writer = RimeWriter(scel.get_table(), rime_name, rime_version)
    scel_file.close()

    rime_writer.write(rime_dict_yaml, dict_scel_detail)





