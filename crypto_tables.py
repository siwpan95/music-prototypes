# -*- coding: utf-8 -*-
"""
crypto_tables.py —— 解密用字节常量表（机器生成，请勿手工编辑）

本文件由 tools/extract_tables.py 从下列开源参考实现中程序化提取生成，
生成时间：2026-08-19。表内容未经任何手工抄写，各表 SHA256 附后，
可独立复核；selftest.py 另有 KGM mask 流级别的权威哈希对照。

参考实现（均为公开的开源项目镜像）：
  - KGM 表: jsxiaosi/kugou-crypto (main 分支 src/data/tables.ts)
    https://github.com/jsxiaosi/kugou-crypto  (MIT License)
    该库与 unlock-music/cli 的解密结果做过哈希级 1:1 对照。
  - QMC 表: kbtxwer/unlock-music-web (master 分支 src/decrypt/qmc_cipher.ts,
    src/decrypt/qmc_key.ts)  https://github.com/kbtxwer/unlock-music-web
    (原项目 unlock-music, MIT License)。

原始参考文件当时存放于 <项目>/ref/ 目录（不随项目分发），
需要重新生成时可按上述 URL 下载后运行 tools/extract_tables.py。
"""

# KGM_TABLE_1: len=272 sha256=7d81de689ca1421888a6a1602dd98b9b4d1d47f90ad817d3382c5a4594badf8d
KGM_TABLE_1 = bytes.fromhex(
    "000000000000000000000000000000000001210161012101e101210161012101"
    "d223020242420202c2c2020242420202d3d3020363436303e3c3e30363436303"
    "94b494650404040484848484040404049595959504052505e585a585e5052505"
    "d6b696b6d6270606c6c68686c6c60606d7d79797d7d70607e7c7e787e7c7e707"
    "18381878183818e9080808080808080819191919191919190809290969092909"
    "da3a1a3a5a3a1a3ada2b0a0a4a4a0a0adbdb1b1b5b5b1b1bdbdb0a0b6b4b6b0b"
    "9cbc9c7c1c3c1c7c9cbc9c6d0c0c0c0c9d9d9d9d1d1d1d1d9d9d9d9d0c0d2d0d"
    "debe9ebede3e1e3edebe9ebede2f0e0edfdf9f9fdfdf1f1fdfdf9f9fdfdf0e0f"
    "00200060002000e000200060002000f1"
)

# KGM_TABLE_2: len=272 sha256=fcd16660927378ee9f136f5fcf332a9aa0829e7ea63b98cee248c4cf782c6fe5
KGM_TABLE_2 = bytes.fromhex(
    "000000000000000000000000000000000001230167012301ef01230167012301"
    "df21020246460202cece020246460202dede020365476503edcfed0365476503"
    "9dbf9d63040404048c8c8c8c040404049c9c9c9c04052705eb8daf8deb052705"
    "dbbd9fbddb250606caca8e8ecaca0606dada9e9edada0607e9cbe98fe9cbe907"
    "193b197f193b19e70808080808080808181818181818181808092b096f092b09"
    "d7391b395f391b39d7290a0a4e4e0a0ad6d61a1a5e5e1a1ad6d60a0b6d4f6d0b"
    "95b7957b1d3f1d7b95b7956b0c0c0c0c949494941c1c1c1c949494940c0d2f0d"
    "d3b597b5d33d1f3dd3b597b5d32d0e0ed2d29696d2d21e1ed2d29696d2d20e0f"
    "00220066002200ee00220066002200fe"
)

# KGM_TABLE_V2: len=272 sha256=be882964c82568b8324bde2412a1d8793aa7cf66fc2a8fe04e884818a041c976
KGM_TABLE_V2 = bytes.fromhex(
    "b8d53db2e9af788c8333715176a0cd372f3e358da9be98b7e78c22ce5a61df68"
    "6989fea5b6dea977fcc8bdbde56d3e5a36ef694ebee1e9661cf3d902b6f2129b"
    "44d06fb93589b6466d73820669c1edd785c230dfa262be792d62623d0d7ebe48"
    "892302a0e4d57551320253fd163a213b160fc3b2bbb3e2ba3a3d13ecf6014584"
    "a5700f93490c64cd31d5cc4c07019e001a2390bf881e3baba63ec47347107e3b"
    "5ebce30084ff09d4e0890f5b58704ffb65d85c531bd3c8c6bfef98b0504f0fea"
    "e583588c282c8467cdd09e47db2750caf46363e8977f1b4b0cc2c1214ccc58f5"
    "9452a3f3d3e068f40023f35e0a7b93ddab12b213e884d7a79f0f324c551d0436"
    "52dc03f3f94e42e93d61ef7cb6b39350"
)

# KGM_VPR_KEY: len=17 sha256=095e6404b5282496f6553513c813b36be6e25c1a38008e6620d43da819c10147
KGM_VPR_KEY = bytes.fromhex(
    "25dfe8a6751e750e2f80f32db8b6e31100"
)

# QMC_STATIC_BOX: len=256 sha256=771a9b8588ec7cb87d033184d71b0025addea173f51bfb957d004a443f513ebf
QMC_STATIC_BOX = bytes.fromhex(
    "77483273def2c0c895ec30b251c3e1a09ee69dcffa7f14d1ceb8dcc34a6793d6"
    "28c29170ca8da2a4f00861907e6fa2e0ebae3eb667c792f491b5f66c5e8440f7"
    "f31b027fd5ab418928f425cc5211ad4368a6418b84b5ff2c924a26d8476a7c95"
    "61cce6cbbb3f47588975c375a1d9afcc087317dcaa9aa21641d8a206c68bfc66"
    "349fcf1823a00a74e72b277092e9af37e68ca7bc62659cc208c988b3f343ac74"
    "2c0fd4afa1c30164954e489ff43578957a39d66aa06d40e84fa8ef111df31b3f"
    "3f07dd6f5b193019fbef0e37f00ecd1649fe5347131abda4f14019600eed6809"
    "065f4dcf3d1afe2077e4d9daf9a42b761c71db00bcfd0c6ca547f7f600794a11"
)

# QMC_MIX_KEY_1: len=16 sha256=bb2253776893dc9412f2c524c1d3a8a9b628d0a698950e2c37510a65bba47f0f
QMC_MIX_KEY_1 = bytes.fromhex(
    "3338365a4a592140232a24255e262928"
)

# QMC_MIX_KEY_2: len=16 sha256=c36ce48c032c276a3b8fbf8bf54ee4fbaa9279b903238c1cde26076e1254d36c
QMC_MIX_KEY_2 = bytes.fromhex(
    "2a2a232128232425265e6131635a2c54"
)

__all__ = ["KGM_TABLE_1", "KGM_TABLE_2", "KGM_TABLE_V2", "KGM_VPR_KEY", "QMC_STATIC_BOX", "QMC_MIX_KEY_1", "QMC_MIX_KEY_2"]
