# GetQzonehistory(获取qq发布的历史说说)

该项目通过获取QQ空间的历史消息列表来获取该账号下发布的所有说说（当然消息列表中没有的就获取不到，例如一些仅自己可见的说说）[单文件版]

主要实现还是通过模拟登录QQ空间来获取历史消息列表，然后进行数据分析，最后将爬取的说说存放到/resource/result目录下

由于对python编程还不是很熟悉，所以代码有很多疏漏，可以通过自己的想法来完善代码
## 目录结构

```text
project/
├── resource/           # 资源目录
│   ├── result/         # 导出结果的目录，格式为“你的qq.xlsx”
│   │   ├── ...
│   │   └── ...
│   ├── temp/           # 缓存目录
│   │   ├── ...
│   │   └── ...
├── main.py             # 主程序入口
├── config.ini			# 配置目录，文件保存位置配置
├── README.md           # 项目说明文件
└── requirements.txt    # 依赖项列表
```

## 安装

#### 使用虚拟环境（推荐）
```bash
# 克隆储存库
git clone -b single https://github.com/LibraHp/GetQzonehistory.git
# 打开目录
cd GetQzonehistory
# 创建名为 myenv 的虚拟环境
python -m venv myenv
# 激活虚拟环境。在终端或命令提示符中运行以下命令：
# 对于 Windows：
myenv\Scripts\activate
# 对于 macOS/Linux：
source myenv/bin/activate
# 安装依赖
pip install -i https://mirrors.aliyun.com/pypi/simple/ -r requirements.txt
# 运行脚本
python main.py
```
#### 使用本机环境（不推荐）
```bash
# 克隆储存库
git clone -b single https://github.com/LibraHp/GetQzonehistory.git
# 打开目录
cd GetQzonehistory
# 安装依赖
pip install -i https://mirrors.aliyun.com/pypi/simple/ -r requirements.txt
# 运行脚本
python main.py
```


## 参考

登录方法参考自
[python-QQ空间扫码登录](https://blog.csdn.net/m0_50153253/article/details/113780595)

