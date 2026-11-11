# 多轮互动与记忆仿真演示

`output/rich_full.mp4` 是本次运行的三栏视频：左上是仿真 RGB 话题，左下根据 ROS 位姿和关节状态在同一 MuJoCo 模型中重建旁观视角；右侧是运行时生成的简要事件摘要和模型生成语句，不展示模型内部思维链。视频为墙钟时间录制，图像更新慢时重复帧。

本次演示使用已有的 `semantic_video_map.json`，其 map_sha256 与 `improved_map.db` 的 SHA-256 均为 `e2498a4a75659e062d72a81b8c049f20517005851454398490abaab1260656c8`。模型实际读取了地图，第一轮选择 `potted_plant`，第三轮选择 `tv`。该地图是之前保存的识别结果，不是此次实时重建；其坐标系为 map，而本次仿真移动使用单独指定的 world 固定活动点，不能证明从地图对象坐标完成了语义导航或到达了植物、电视。

`seed_memory.json` 为合成的先前记忆，初始偏好植物；用户状态、照护者许可、所有成员回应均由脚本模拟，情绪只表示低置信度估计。第一轮模型结合地图和旧记忆生成建议；第二轮明确给出电视、视觉提示、轻声偏好并要求写入；第三轮不再给出具体偏好，要求读取最新记忆与地图。Worker 输出显示选择了电视和相应交互方式。显示与语音只是模型生成的文字提议，本次没有实际播放或屏幕控制。

`output/requests.jsonl` 保存完整模拟事件与任务指令，`output/replies.jsonl` 保存官方 Super-agent Channel 原始回复；`output/timeline.jsonl` 为视频右侧精简摘要。`output/scenario_result.json`、`output/round*.json`、`output/memory.json`、`output/motion_result.json` 可核对输出；记忆 JSON 是演示存储，并非实现了授权和生命周期管理的长期记忆系统。

运行使用官方 DeepSeek Harness/Super-agent 的本地仿真适配与 DeepSeek API。此演示在隔离容器、合成输入下完成，不应接入真实儿童、实物机器人或未授权数据。
