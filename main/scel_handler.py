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

import io
import struct

from typing import List, Tuple


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

    def write(self, file_path):
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(f'''---
name: {self._name}
version: "{self._version}"
sort: by_weight
use_preset_vocabulary: false
...
''')
            for i in self._table:
                f.write('\t'.join(i) + '\t1\n')


def scel_to_rime(scel_path: str, rime_path: str, rime_name: str,
                 rime_version: str):
    '''
    搜狗细胞词库「scel」转换 RIME 词库风格程序调用方法

    :param scel_path:细胞词库文件路径
    :param rime_path:待生成的 RIME 风格的词库文件「xxx.dict.yaml」
    :param rime_name:RIME 词库文件中头部名称，推荐：
                    「xxx.dict.yaml」取 xxx 作为该参数的实参﹝推荐但是不强求﹞
    :param rime_version:版本号，一般采用当前日期，例如：2024-05-16
    :return:
    '''
    scel_file = open(scel_path, 'rb')
    scel = Scel(scel_file)
    rime_writer = RimeWriter(scel.get_table(), rime_name, rime_version)
    scel_file.close()
    rime_writer.write(rime_path)


if __name__ == '__main__':
    scel_to_rime(r'E:\workspace_home\git_work_home\scel2txt\test\《凡人修仙传》词库.scel',
                 r'E:\workspace_home\git_work_home\scel2txt\output\demo.yaml', r'demo', r'1.0')
