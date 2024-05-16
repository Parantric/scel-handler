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
        buffer = self._buffer.read(2)
        if buffer:
            return struct.unpack('<H', buffer)[0]
        else:
            return 0

    def read_uint32(self) -> int:
        return struct.unpack('<I', self._buffer.read(4))[0]

    def read_str(self) -> str:
        return ''.join(
            chr(struct.unpack('<H', self._buffer.read(2))[0])
            for i in range(int(self.read_uint16() / 2)))

    def seek(self, offset):
        self._buffer.seek(offset)

    def tell(self) -> int:
        return self._buffer.tell()

    def skip(self, offset):
        self._buffer.seek(offset, 1)

    def skip_uint16(self):
        self.skip(2)


class Scel:
    PINYIN_START = 0x1544
    CHAR_START = 0x2628

    def __init__(self, bufferedReader: io.BufferedIOBase):
        self._buffer = BufferedIOWrapper(bufferedReader)
        self._table = []

    def _read_pinyin_palette(self) -> List[str]:
        pinyin_palette = []
        self._buffer.seek(self.PINYIN_START)
        while self._buffer.tell() < self.CHAR_START:
            # skipped index, doesn't need.
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

    def _read_table(self,
                    pinyin_palette: List[str]) -> List[Tuple[str, str, int]]:
        table = []
        self._buffer.seek(self.CHAR_START)
        while word_count := self._buffer.read_uint16():
            pinyin = self._read_pinyin(pinyin_palette)
            if not pinyin:
                break
            for _ in range(word_count):
                phrase = self._buffer.read_str()
                # usually 10, at least 4 bytes after this is the order of the phrase (uint32), doesn't seen to matter.
                skip_length = self._buffer.read_uint16()
                order = self._buffer.read_uint32()
                self._buffer.skip(skip_length - 4)

                table.append((phrase, pinyin, order))

        table.sort(key=lambda x: x[2])
        return table

    def get_table(self):
        if not self._table:
            pinyin_palette = self._read_pinyin_palette()
            self._table = self._read_table(pinyin_palette)

        return list(map(lambda x: x[:2], self._table))


class RimeWriter:

    def __init__(self, table: List[Tuple[str, str]], name: str, version: str):
        self._table = table
        self._name = name
        self._version = version

    def write(self, file_path, result):
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(
                f'''# 程序自动生成\n# 来源【搜狗词库】\n# encoding: utf-8\n# 字条格式：词汇<tab>ci<空格>hui<tab>权重\n# 权重数字越大，表示优先级越高，排名越靠前。\n# 模板\n#\n# 词库详情如下：\n# 词库名称：{result['dict_name']}\n# 词库类型：{result['dict_type']}\n# 词库信息：{result['dict_msg']}\n# 词库示例：{result['dict_exp']}\n---\nname: {self._name}\nversion: {self._version}\nsort: by_weight\nuse_preset_vocabulary: false\n...\n\n''')
            for i in self._table:
                f.write('\t'.join(i) + '\t1\n')


def read_scel_msg(scel_path: str):
    result = {}
    msg_reader = lambda data: ''.join(
        map(lambda x: '\n' if x == '\r' else x,
            map(lambda x: ' ' if x == '\u3000' else x,
                filter(lambda x: x != '\0',
                       (chr(struct.unpack('H', data[i: i + 2])[0]) for i in range(0, len(data), 2))
                       ))))

    with open(scel_path, 'rb') as f:
        f.seek(0x130)
        result['dict_name'] = msg_reader(f.read(0x338 - 0x130))
        result['dict_type'] = msg_reader(f.read(0x540 - 0x338))
        result['dict_msg'] = msg_reader(f.read(0xD40 - 0x540))
        result['dict_exp'] = msg_reader(f.read(0x1540 - 0xD40))

        print(r'词库名称：' + result['dict_name'])
        print(r'词库类型：' + result['dict_type'])
        print(r'词库信息：' + result['dict_msg'])
        print(r'词库示例：' + result['dict_exp'])
    return result


def scel_to_rime(scel_path: str, rime_dir: str, rime_name: str,
                 rime_version: str, result: {}):
    '''
    搜狗细胞词库「scel」转换 RIME 词库风格程序调用方法

    :param scel_path:细胞词库文件路径
    :param rime_dir:待生成的 RIME 词库文件的存放目录（如果目录不存在则自动创建）
    :param rime_name:RIME 词库文件中头部名称，推荐：
                    「xxx.dict.yaml」取 xxx 作为该参数的实参﹝推荐但是不强求﹞
    :param rime_version:版本号，一般采用当前日期，例如：2024-05-16
    :return:
    '''
    # 判断输出文件目录是否存在，不存在则自动创建.
    if not os.path.exists(rime_dir):
        os.makedirs(rime_dir)
        print(r'[ ' + rime_dir + ' ] 不存在，已自动创建！')
    # 生成的文件名称
    rime_dict_yaml = os.path.join(rime_dir, rime_name + RIME_DICT_EXT)

    scel_file = open(scel_path, 'rb')
    scel = Scel(scel_file)
    rime_writer = RimeWriter(scel.get_table(), rime_name, rime_version)
    scel_file.close()

    rime_writer.write(rime_dict_yaml, result)


if __name__ == '__main__':
    scel_path = r'E:\workspace_home\git_work_home\scel2txt\scel\庄子全集【官方推荐】.scel'
    rime_dir = r'F:\Home\Users\renjy\Desktop'
    rime_name = r'sougou.pinyin.wanmeishijie'
    rime_version = str(datetime.date.today())

    result = read_scel_msg(scel_path)

    scel_to_rime(scel_path, rime_dir, rime_name, rime_version, result)
