# -*- coding: utf-8 -*-
"""
extract_tables.py —— 从参考源码（TypeScript）中程序化提取解密用字节表，
生成 crypto_tables.py。避免手工抄写长字节表引入抄写错误。

参考源码（下载于 2026-08-19，原始出处见生成的文件头）：
  ref/tables.ts        —— KGM table1/table2/tableV2/vprKey
                           (jsxiaosi/kugou-crypto, MIT, 系 @jixun/kugou-crypto 的公开镜像)
  ref/qmc_cipher.ts    —— QMCv1 静态密码盒 staticCipherBox
                           (kbtxwer/unlock-music-web, MIT, 系 unlock-music 的公开镜像)
  ref/qmc_key.ts       —— QMCv2 EncV2 密钥 mixKey1/mixKey2

用法：
  python tools/extract_tables.py  （在项目根目录运行，需 ref/*.ts 存在）

生成结果经过三重校验：
  1. 表长度断言（272/272/272/17/256/16/16）
  2. 每张表的 SHA256 写入生成文件头注释，可用 hashlib 独立复核
  3. selftest.py 中的 mask 流 SHA256 权威对照（与 unlock-music/cli 的
     kgm.v2.mask / kgm.v2.1.mask 生成结果哈希一致）
"""
import hashlib
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
REF = os.path.join(ROOT, "ref")


def read_ts(name):
    path = os.path.join(REF, name)
    if not os.path.exists(path):
        sys.exit("缺少参考源码: %s（见文件头说明）" % path)
    return open(path, encoding="utf-8").read()


def extract_array(src, varname):
    """从 TS 源码里提取 `const name = [ 0x.., ... ]` 形式的字节数组。"""
    # 先去掉行注释（表数据每行末尾带 //0x00 形式的偏移标注，会干扰提取）
    src = re.sub(r"//[^\n]*", "", src)
    m = re.search(
        r"\b" + re.escape(varname) + r"\s*(?::[^=\n]+)?=\s*(?:new\s+Uint8Array\s*\()?\[",
        src,
    )
    if not m:
        sys.exit("在参考源码中找不到数组: " + varname)
    start = m.end() - 1  # 指向 '['
    end = src.find("]", start)
    if end < 0:
        sys.exit("数组未闭合: " + varname)
    vals = [int(x, 16) for x in re.findall(r"0x[0-9a-fA-F]+", src[start:end])]
    return bytes(vals)


def fmt_bytes(data, per_line=16, indent="    "):
    lines = []
    for i in range(0, len(data), per_line):
        chunk = data[i:i + per_line]
        lines.append(indent + "".join("0x%02X, " % b for b in chunk).rstrip())
    return "\n".join(lines)


def main():
    tables_ts = read_ts("tables.ts")
    qmc_cipher_ts = read_ts("qmc_cipher.ts")
    qmc_key_ts = read_ts("qmc_key.ts")

    table1 = extract_array(tables_ts, "table1")
    table2 = extract_array(tables_ts, "table2")
    table_v2 = extract_array(tables_ts, "tableV2")
    vpr_key = extract_array(tables_ts, "vprKey")
    qmc_static_box = extract_array(qmc_cipher_ts, "staticCipherBox")
    mix_key1 = extract_array(qmc_key_ts, "mixKey1")
    mix_key2 = extract_array(qmc_key_ts, "mixKey2")

    expect = {
        "KGM_TABLE_1": (table1, 272),
        "KGM_TABLE_2": (table2, 272),
        "KGM_TABLE_V2": (table_v2, 272),
        "KGM_VPR_KEY": (vpr_key, 17),
        "QMC_STATIC_BOX": (qmc_static_box, 256),
        "QMC_MIX_KEY_1": (mix_key1, 16),
        "QMC_MIX_KEY_2": (mix_key2, 16),
    }
    for name, (data, n) in expect.items():
        if len(data) != n:
            sys.exit("表 %s 长度异常: %d (期望 %d)" % (name, len(data), n))

    def sha(data):
        return hashlib.sha256(data).hexdigest()

    out = []
    out.append('# -*- coding: utf-8 -*-')
    out.append('"""')
    out.append('crypto_tables.py —— 解密用字节常量表（机器生成，请勿手工编辑）')
    out.append('')
    out.append('本文件由 tools/extract_tables.py 从下列开源参考实现中程序化提取生成，')
    out.append('生成时间：2026-08-19。表内容未经任何手工抄写，各表 SHA256 附后，')
    out.append('可独立复核；selftest.py 另有 KGM mask 流级别的权威哈希对照。')
    out.append('')
    out.append('参考实现（均为公开的开源项目镜像）：')
    out.append('  - KGM 表: jsxiaosi/kugou-crypto (main 分支 src/data/tables.ts)')
    out.append('    https://github.com/jsxiaosi/kugou-crypto  (MIT License)')
    out.append('    该库与 unlock-music/cli 的解密结果做过哈希级 1:1 对照。')
    out.append('  - QMC 表: kbtxwer/unlock-music-web (master 分支 src/decrypt/qmc_cipher.ts,')
    out.append('    src/decrypt/qmc_key.ts)  https://github.com/kbtxwer/unlock-music-web')
    out.append('    (原项目 unlock-music, MIT License)。')
    out.append('')
    out.append('原始参考文件当时存放于 <项目>/ref/ 目录（不随项目分发），')
    out.append('需要重新生成时可按上述 URL 下载后运行 tools/extract_tables.py。')
    out.append('"""')
    out.append('')
    for name, (data, n) in expect.items():
        out.append("# %s: len=%d sha256=%s" % (name, len(data), sha(data)))
        out.append("%s = bytes.fromhex(" % name)
        hexstr = data.hex()
        for i in range(0, len(hexstr), 64):
            out.append('    "%s"' % hexstr[i:i + 64])
        out.append(")")
        out.append("")
    out.append("__all__ = [%s]" % ", ".join('"%s"' % k for k in expect))

    dst = os.path.join(ROOT, "crypto_tables.py")
    with open(dst, "w", encoding="utf-8", newline="\n") as f:
        f.write("\n".join(out) + "\n")
    print("已生成:", dst)
    for name, (data, n) in expect.items():
        print("  %-16s len=%-4d sha256=%s" % (name, len(data), sha(data)))


if __name__ == "__main__":
    main()
