# Family Agent 测试框架

本仓库包含 Family Agent 的架构草案与基于 DeepSeek Super-agent 的家庭仿真原型。原型的运行方式、已验证功能及安全边界见 [Super_Agent_test/README.md](Super_Agent_test/README.md)，多轮交互与激光演示的说明位于其子目录。

`Super_Agent_test/upstream` 是固定到指定版本的 DeepSeek 官方代码子模块，`runtime` 是用于本项目实验的适配副本。克隆时请使用：

```sh
git clone --recurse-submodules https://github.com/Hang-42/Agent_test.git
```

已有克隆可运行 `git submodule update --init --recursive`。API 密钥、机器专用基础设施信息和缓存文件不包含在仓库中；演示中的家庭成员、情绪和交互数据为合成数据。
