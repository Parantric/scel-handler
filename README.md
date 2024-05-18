# ![Static Badge](https://img.shields.io/badge/python-blue)🐍 搜狗细胞词库爬虫&转`RIME`风格词库
![](https://gitee.com/justdoitor/gitee-images-plus/raw/master/images/202405161455397.jpg)

>**一个简单的搜狗词库处理代码，当然基本都是我抄来的，原有大佬的代码仓库基本都不维护了，正好最近喜欢上了基于小狼毫输入法定制的「雾凇输入法」，迁移搜狗词库的时候，看到有人做过这样的代码，就直接拿来了。**

## 📄 文件说明

> ① `📄 main/scel_handler.py` ：搜狗细胞词库 `scel` 文件解析及转换成 `RIME` 风格的 `.dict.yaml` 文件代码.
>
> ② `📄 main/scel_spider.py ` ： 搜狗词库官方网站词库爬虫代码.

## 📅 更新说明

### 📅 ﹝ 2024年05月18日 ﹞

> 添加搜狗细胞词库爬虫代码，已测试除【城市信息】的全部词库类别;
>
> 修复搜狗细胞词库解析时，如果遇到 `scel` 文件含有「黑名单」即：`Unicode` 编码含有「DELTAB」时解析失败的问题;![](https://gitee.com/justdoitor/gitee-images-plus/raw/master/images/202405181530556.png)
>
> P.S. 目前仅仅是通过解析词汇表时，「黑名单」部分开始解析的字符为空字符串判断，至于逻辑上怎么判断，暂时还没找到思路.



## 🔗 参考

> **🙏  感谢以下文章作者提供的思路和代码**

1. [**蔷薇词库转换**](https://github.com/nopdan/rose)

2. [**输入法词库解析（二）搜狗拼音细胞词库.scel (.qcel)**](https://nopdan.com/2022/05/02-sogou-scel/)

3. [**搜狗 `scel` 细胞词库文件详解**](https://egg.moe/2021/06/sogou-scel-format/)

